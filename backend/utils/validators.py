from datetime import datetime


class ValidationError(Exception):
    pass


def validate_student_profile(cgpa: float, branch: str, year: int):
    if cgpa < 0 or cgpa > 10:
        raise ValidationError("CGPA must be in range 0-10")
    if len(branch.strip()) < 2:
        raise ValidationError("Branch is invalid")
    if year < datetime.utcnow().year - 1 or year > datetime.utcnow().year + 8:
        raise ValidationError("Graduation year is invalid")


def validate_drive(deadline_iso: str, min_cgpa: float, grad_year: int):
    deadline = datetime.fromisoformat(deadline_iso)
    if deadline <= datetime.utcnow():
        raise ValidationError("Deadline must be in future")
    if min_cgpa < 0 or min_cgpa > 10:
        raise ValidationError("min_cgpa must be in range 0-10")
    if grad_year < datetime.utcnow().year - 1 or grad_year > datetime.utcnow().year + 8:
        raise ValidationError("graduation_year is invalid")
    return deadline
