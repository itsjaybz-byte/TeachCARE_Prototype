from extensions import db


teacher_qualification = db.Table(
    "teacher_qualification",
    db.Column(
        "teacher_id",
        db.Integer,
        db.ForeignKey("teacher.id"),
        primary_key=True,
    ),
    db.Column(
        "qualification_id",
        db.Integer,
        db.ForeignKey("qualification.id"),
        primary_key=True,
    ),
)


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    major = db.Column(db.String(150), nullable=False)
    educational_attainment = db.Column(db.String(150), nullable=False)
    jhs_eligible = db.Column(db.Boolean, default=False, nullable=False)
    shs_eligible = db.Column(db.Boolean, default=False, nullable=False)

    qualifications = db.relationship(
        "Qualification",
        secondary=teacher_qualification,
        back_populates="teachers",
    )

    availabilities = db.relationship(
        "TeacherAvailability",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )

    schedule_entries = db.relationship(
        "ScheduleEntry",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )


class Qualification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)

    teachers = db.relationship(
        "Teacher",
        secondary=teacher_qualification,
        back_populates="qualifications",
    )

    subjects = db.relationship(
        "Subject",
        back_populates="required_qualification",
    )


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    grade_level = db.Column(db.String(50), nullable=False)
    educational_level = db.Column(db.String(10), nullable=False)
    strand = db.Column(db.String(100), nullable=True)

    curriculum_requirements = db.relationship(
        "CurriculumRequirement",
        back_populates="section",
        cascade="all, delete-orphan",
    )

    schedule_entries = db.relationship(
        "ScheduleEntry",
        back_populates="section",
        cascade="all, delete-orphan",
    )


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    # Minimum educational attainment required for assignment.
    #
    # Controlled prototype assumption:
    # Bachelor's Degree is the minimum attainment for
    # the teaching assignments represented in the dataset.
    minimum_educational_attainment = db.Column(
        db.String(150),
        nullable=False,
        default="Bachelor's Degree",
    )

    # Changed from a text field to a foreign key.
    required_qualification_id = db.Column(
        db.Integer,
        db.ForeignKey("qualification.id"),
        nullable=False,
    )

    required_qualification = db.relationship(
        "Qualification",
        back_populates="subjects",
    )

    curriculum_requirements = db.relationship(
        "CurriculumRequirement",
        back_populates="subject",
        cascade="all, delete-orphan",
    )

    schedule_entries = db.relationship(
        "ScheduleEntry",
        back_populates="subject",
        cascade="all, delete-orphan",
    )


class CurriculumRequirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    section_id = db.Column(
        db.Integer,
        db.ForeignKey("section.id"),
        nullable=False,
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False,
    )

    required_periods = db.Column(db.Integer, nullable=False)

    # Prevent duplicate section + subject curriculum requirements.
    __table_args__ = (
        db.UniqueConstraint(
            "section_id",
            "subject_id",
            name="uq_curriculum_requirement_section_subject",
        ),
    )

    section = db.relationship(
        "Section",
        back_populates="curriculum_requirements",
    )

    subject = db.relationship(
        "Subject",
        back_populates="curriculum_requirements",
    )


class SchedulePeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(30), nullable=False)
    period = db.Column(db.String(50), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)

    availabilities = db.relationship(
        "TeacherAvailability",
        back_populates="schedule_period",
        cascade="all, delete-orphan",
    )

    schedule_entries = db.relationship(
        "ScheduleEntry",
        back_populates="schedule_period",
        cascade="all, delete-orphan",
    )


class TeacherAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teacher.id"),
        nullable=False,
    )

    period_id = db.Column(
        db.Integer,
        db.ForeignKey("schedule_period.id"),
        nullable=False,
    )

    available = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    # A teacher should have only one availability record
    # for a particular scheduling period.
    __table_args__ = (
        db.UniqueConstraint(
            "teacher_id",
            "period_id",
            name="uq_teacher_availability_teacher_period",
        ),
    )

    teacher = db.relationship(
        "Teacher",
        back_populates="availabilities",
    )

    schedule_period = db.relationship(
        "SchedulePeriod",
        back_populates="availabilities",
    )


class ScheduleEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teacher.id"),
        nullable=False,
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subject.id"),
        nullable=False,
    )

    section_id = db.Column(
        db.Integer,
        db.ForeignKey("section.id"),
        nullable=False,
    )

    period_id = db.Column(
        db.Integer,
        db.ForeignKey("schedule_period.id"),
        nullable=False,
    )

    teacher = db.relationship(
        "Teacher",
        back_populates="schedule_entries",
    )

    subject = db.relationship(
        "Subject",
        back_populates="schedule_entries",
    )

    section = db.relationship(
        "Section",
        back_populates="schedule_entries",
    )

    schedule_period = db.relationship(
        "SchedulePeriod",
        back_populates="schedule_entries",
    )