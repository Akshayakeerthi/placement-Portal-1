import io
import unittest
from datetime import datetime, timedelta

from backend.app import create_app
from backend.extensions import db


class ApiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            runner = self.app.test_cli_runner()
            out = runner.invoke(args=["init-db"])
            assert out.exit_code == 0

        self.client = self.app.test_client()

    def _register_and_login(self, name, email, role):
        r = self.client.post(
            "/api/auth/register",
            json={"name": name, "email": email, "password": "pass123", "role": role},
        )
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/auth/login", json={"email": email, "password": "pass123"})
        self.assertEqual(r.status_code, 200)
        return r.get_json()["token"]

    def _admin_token(self):
        r = self.client.post(
            "/api/auth/login",
            json={"email": "admin@ppa.local", "password": "Admin@123"},
        )
        self.assertEqual(r.status_code, 200)
        return r.get_json()["token"]

    def test_student_profile_and_resume_upload(self):
        token = self._register_and_login("Student", "student@test.com", "STUDENT")
        r = self.client.post(
            "/api/student/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"branch": "CSE", "graduation_year": 2026, "cgpa": 8.1},
        )
        self.assertEqual(r.status_code, 200)

        data = {"resume": (io.BytesIO(b"dummy resume"), "resume.pdf")}
        r = self.client.post(
            "/api/student/resume",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            content_type="multipart/form-data",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("uploads/", r.get_json()["resume_path"])

    def test_company_drive_admin_approve_student_apply(self):
        company_token = self._register_and_login("Company", "company@test.com", "COMPANY")
        student_token = self._register_and_login("Student", "student2@test.com", "STUDENT")
        admin_token = self._admin_token()

        r = self.client.post(
            "/api/company/profile",
            headers={"Authorization": f"Bearer {company_token}"},
            json={"company_name": "Acme Corp", "website": "https://acme.test", "description": "desc"},
        )
        self.assertEqual(r.status_code, 200)
        company_id = r.get_json()["id"]

        r = self.client.patch(
            f"/api/admin/companies/{company_id}/approval",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"approved": True},
        )
        self.assertEqual(r.status_code, 200)

        deadline = (datetime.utcnow() + timedelta(days=5)).isoformat()
        r = self.client.post(
            "/api/company/drives",
            headers={"Authorization": f"Bearer {company_token}"},
            json={
                "title": "SDE",
                "description": "Hiring",
                "eligible_branches": ["CSE"],
                "min_cgpa": 7.0,
                "graduation_year": 2026,
                "deadline": deadline,
            },
        )
        self.assertEqual(r.status_code, 201)
        drive_id = r.get_json()["id"]

        r = self.client.patch(
            f"/api/admin/drives/{drive_id}/approval",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"approved": True},
        )
        self.assertEqual(r.status_code, 200)

        r = self.client.post(
            "/api/student/profile",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"branch": "CSE", "graduation_year": 2026, "cgpa": 8.0},
        )
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/api/student/drives", headers={"Authorization": f"Bearer {student_token}"})
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.get_json()), 1)

        r = self.client.post(
            f"/api/student/drives/{drive_id}/apply",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        self.assertEqual(r.status_code, 201)

        r = self.client.post(
            f"/api/student/drives/{drive_id}/apply",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        self.assertEqual(r.status_code, 400)

    def test_company_can_close_drive(self):
        company_token = self._register_and_login("Company3", "company3@test.com", "COMPANY")
        admin_token = self._admin_token()

        r = self.client.post(
            "/api/company/profile",
            headers={"Authorization": f"Bearer {company_token}"},
            json={"company_name": "Close Corp", "website": "https://close.test", "description": "desc"},
        )
        self.assertEqual(r.status_code, 200)
        company_id = r.get_json()["id"]

        r = self.client.patch(
            f"/api/admin/companies/{company_id}/approval",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"approved": True},
        )
        self.assertEqual(r.status_code, 200)

        deadline = (datetime.utcnow() + timedelta(days=10)).isoformat()
        r = self.client.post(
            "/api/company/drives",
            headers={"Authorization": f"Bearer {company_token}"},
            json={
                "title": "Close Me",
                "description": "Hiring",
                "eligible_branches": ["CSE"],
                "min_cgpa": 7.0,
                "graduation_year": 2026,
                "deadline": deadline,
            },
        )
        self.assertEqual(r.status_code, 201)
        drive_id = r.get_json()["id"]

        r = self.client.patch(
            f"/api/admin/drives/{drive_id}/approval",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"approved": True},
        )
        self.assertEqual(r.status_code, 200)

        r = self.client.patch(
            f"/api/company/drives/{drive_id}/close",
            headers={"Authorization": f"Bearer {company_token}"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["closed"])


    def test_student_profile_allows_past_graduation_year(self):
        token = self._register_and_login("Alumni", "alumni@test.com", "STUDENT")
        r = self.client.post(
            "/api/student/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"branch": "ECE", "graduation_year": 2022, "cgpa": 7.4},
        )
        self.assertEqual(r.status_code, 200)



if __name__ == "__main__":
    unittest.main()
