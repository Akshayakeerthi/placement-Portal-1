import api from '../services/api.js';

export default {
  data() {
    return {
      section: 'dashboard',
      profile: { company_name: '', website: '', description: '' },
      profileDraft: { company_name: '', website: '', description: '' },
      drive: { title: '', description: '', eligible_branches: '', min_cgpa: 6.0, graduation_year: 2025, deadline: '' },
      drives: [],
      activeDrives: [],
      selectedDriveId: '',
      applicants: [],
      selectedApplicant: null,
      message: '',
      error: '',
    };
  },
  async mounted() {
    await this.refreshDrives();
  },
  methods: {
    async refreshDrives() {
      this.drives = (await api.get('/company/drives')).data;
      this.activeDrives = this.drives.filter((d) => d.approved && !d.closed);
      if (this.selectedDriveId) {
        const exists = this.activeDrives.find((d) => String(d.id) === String(this.selectedDriveId));
        if (!exists) {
          this.selectedDriveId = '';
          this.applicants = [];
          this.selectedApplicant = null;
        }
      }
    },
    openEditProfile() {
      this.profileDraft = { ...this.profile };
      this.section = 'edit-profile';
      this.error = '';
      this.message = '';
    },
    cancelEditProfile() {
      this.section = 'dashboard';
      this.error = '';
    },
    async saveProfile() {
      await api.post('/company/profile', this.profileDraft);
      this.profile = { ...this.profileDraft };
      this.message = 'Profile submitted for admin approval';
      this.section = 'dashboard';
    },
    openCreateDrive() {
      this.section = 'create-drive';
      this.error = '';
      this.message = '';
    },
    cancelCreateDrive() {
      this.section = 'dashboard';
      this.error = '';
    },
    async createDrive() {
      this.error = '';
      try {
        await api.post('/company/drives', {
          ...this.drive,
          eligible_branches: this.drive.eligible_branches.split(',').map((v) => v.trim()).filter(Boolean),
        });
        this.message = 'Drive submitted for approval';
        this.section = 'dashboard';
        await this.refreshDrives();
      } catch (e) {
        this.error = e.response?.data?.error || 'Could not create drive';
      }
    },
    async closeDrive(driveId) {
      await api.patch(`/company/drives/${driveId}/close`);
      this.message = 'Drive closed';
      await this.refreshDrives();
    },
    async loadApplicants() {
      this.selectedApplicant = null;
      if (!this.selectedDriveId) {
        this.applicants = [];
        return;
      }
      this.applicants = (await api.get(`/company/drives/${this.selectedDriveId}/applicants`)).data;
    },
    viewApplicant(applicant) {
      this.selectedApplicant = { ...applicant };
    },
    async updateApplicantStatus(applicant, status) {
      await api.patch(`/company/applications/${applicant.application_id}`, { status });
      this.message = `Applicant ${status.toLowerCase()}`;
      await this.loadApplicants();
      if (this.selectedApplicant && this.selectedApplicant.application_id === applicant.application_id) {
        this.selectedApplicant.status = status;
      }
    },
  },
  template: `
    <div class="glass-card p-3 p-md-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="section-title mb-0">Company Dashboard</h4>
        <div class="d-flex gap-2">
          <button v-if="section==='dashboard'" class="btn btn-outline-primary" @click="openEditProfile">Edit Profile</button>
          <button v-if="section==='dashboard'" class="btn btn-success" @click="openCreateDrive">Create Drive</button>
        </div>
      </div>

      <div v-if="section==='edit-profile'" class="card shadow-sm border-0 p-3 mb-3">
        <h6 class="fw-semibold">Edit Company Profile</h6>
        <label class="form-label">Company Name</label>
        <input class="form-control mb-2" v-model="profileDraft.company_name" placeholder="Enter company name" />
        <label class="form-label">Company Website</label>
        <input class="form-control mb-2" v-model="profileDraft.website" placeholder="https://example.com" />
        <label class="form-label">Company Description</label>
        <textarea class="form-control mb-2" v-model="profileDraft.description" placeholder="Describe your company"></textarea>
        <div class="d-flex gap-2">
          <button class="btn btn-primary" @click="saveProfile">Save Profile</button>
          <button class="btn btn-outline-secondary" @click="cancelEditProfile">Back to Dashboard</button>
        </div>
      </div>

      <div v-else-if="section==='create-drive'" class="card shadow-sm border-0 p-3 mb-3">
        <h6 class="fw-semibold">Create New Drive</h6>
        <label class="form-label">Drive Title</label>
        <input class="form-control mb-2" v-model="drive.title" placeholder="e.g. Software Engineer" />
        <label class="form-label">Drive Description</label>
        <textarea class="form-control mb-2" v-model="drive.description" placeholder="Role details"></textarea>
        <label class="form-label">Eligible Branches (comma separated)</label>
        <input class="form-control mb-2" v-model="drive.eligible_branches" placeholder="CSE, ECE, IT" />
        <label class="form-label">Minimum CGPA</label>
        <input class="form-control mb-2" type="number" step="0.1" v-model="drive.min_cgpa" placeholder="e.g. 7.0" />
        <label class="form-label">Eligible Graduation Year</label>
        <input class="form-control mb-2" type="number" v-model="drive.graduation_year" placeholder="e.g. 2026" />
        <label class="form-label">Application Deadline</label>
        <input class="form-control mb-2" type="datetime-local" v-model="drive.deadline" />
        <div class="d-flex gap-2">
          <button class="btn btn-success" @click="createDrive">Create Drive</button>
          <button class="btn btn-outline-secondary" @click="cancelCreateDrive">Back to Dashboard</button>
        </div>
      </div>

      <div v-else>
        <div class="card shadow-sm border-0 p-3 mb-3">
          <h6 class="fw-semibold">Active Drives</h6>
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead><tr><th>Drive</th><th>Deadline</th><th>Action</th></tr></thead>
              <tbody>
                <tr v-if="!activeDrives.length"><td colspan="3" class="text-center text-muted">No active drives</td></tr>
                <tr v-for="d in activeDrives" :key="d.id">
                  <td>{{d.title}}</td>
                  <td>{{d.deadline}}</td>
                  <td><button class="btn btn-sm btn-outline-dark" @click="closeDrive(d.id)">Close Drive</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card shadow-sm border-0 p-3 mb-3">
          <h6 class="fw-semibold">Applicants by Drive</h6>
          <label class="form-label">Select Active Drive</label>
          <select class="form-select mb-2" v-model="selectedDriveId" @change="loadApplicants">
            <option value="">Select drive</option>
            <option v-for="d in activeDrives" :key="d.id" :value="d.id">{{d.title}}</option>
          </select>

          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead><tr><th>Student</th><th>Email</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                <tr v-if="!applicants.length"><td colspan="4" class="text-center text-muted">No applicants found</td></tr>
                <tr v-for="a in applicants" :key="a.application_id">
                  <td>{{a.student_name}}</td>
                  <td>{{a.student_email}}</td>
                  <td><span class="badge status-badge text-bg-info">{{a.status}}</span></td>
                  <td class="d-flex gap-1 flex-wrap">
                    <button class="btn btn-sm btn-outline-primary" @click="viewApplicant(a)">View Details</button>
                    <button class="btn btn-sm btn-info" @click="updateApplicantStatus(a, 'SHORTLISTED')">Shortlist</button>
                    <button class="btn btn-sm btn-success" @click="updateApplicantStatus(a, 'SELECTED')">Select</button>
                    <button class="btn btn-sm btn-outline-danger" @click="updateApplicantStatus(a, 'REJECTED')">Reject</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="selectedApplicant" class="card shadow-sm border-0 p-3">
          <h6 class="fw-semibold">Applicant Details</h6>
          <p class="mb-1"><strong>Name:</strong> {{selectedApplicant.student_name}}</p>
          <p class="mb-1"><strong>Email:</strong> {{selectedApplicant.student_email}}</p>
          <p class="mb-1"><strong>Branch:</strong> {{selectedApplicant.branch}}</p>
          <p class="mb-1"><strong>CGPA:</strong> {{selectedApplicant.cgpa}}</p>
          <p class="mb-1"><strong>Graduation Year:</strong> {{selectedApplicant.graduation_year}}</p>
          <p class="mb-1"><strong>Resume:</strong> {{selectedApplicant.resume_path || 'Not uploaded'}}</p>
          <p class="mb-0"><strong>Current Status:</strong> {{selectedApplicant.status}}</p>
        </div>
      </div>

      <div class="alert alert-success py-2 mt-3 mb-0" v-if="message">{{message}}</div>
      <div class="alert alert-danger py-2 mt-3 mb-0" v-if="error">{{error}}</div>
    </div>
  `,
};
