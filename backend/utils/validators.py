from datetime import datetime


class ValidationError(Exception):
    pass


def validate_student_profile(cgpa: float, branch: str, year: int):
    if cgpa < 0 or cgpa > 10:
        raise ValidationError("CGPA must be between 0 and 10")
    if len(branch.strip()) < 2:
        raise ValidationError("Branch is invalid")
    if year < datetime.utcnow().year - 1 or year > datetime.utcnow().year + 8:
        raise ValidationError("Graduation year is invalid")
