from app import create_app
from extensions import db
from models import (
    Teacher,
    Qualification,
    Section,
    Subject,
    CurriculumRequirement,
    SchedulePeriod,
    TeacherAvailability,
)

app = create_app()

with app.app_context():

    # =========================================================
    # RESET DATABASE
    # =========================================================

    db.drop_all()
    db.create_all()

    # =========================================================
    # QUALIFICATIONS
    # =========================================================

    math = Qualification(
        name="Mathematics"
    )

    science = Qualification(
        name="Science"
    )

    english = Qualification(
        name="English"
    )

    filipino = Qualification(
        name="Filipino"
    )

    db.session.add_all([
        math,
        science,
        english,
        filipino,
    ])

    # =========================================================
    # TEACHERS
    # =========================================================

    teachers = [

        Teacher(
            employee_id="T001",
            name="Maria Santos",
            major="Mathematics",
            educational_attainment="Bachelor's Degree",
            jhs_eligible=True,
            shs_eligible=True,
            qualifications=[math],
        ),

        Teacher(
            employee_id="T002",
            name="Juan Dela Cruz",
            major="Science",
            educational_attainment="Bachelor's Degree",
            jhs_eligible=True,
            shs_eligible=True,
            qualifications=[science],
        ),

        Teacher(
            employee_id="T003",
            name="Ana Reyes",
            major="English",
            educational_attainment="Master's Degree",
            jhs_eligible=True,
            shs_eligible=True,
            qualifications=[english],
        ),

        Teacher(
            employee_id="T004",
            name="Pedro Garcia",
            major="Filipino",
            educational_attainment="Bachelor's Degree",
            jhs_eligible=True,
            shs_eligible=True,
            qualifications=[filipino],
        ),

        Teacher(
            employee_id="T005",
            name="Liza Cruz",
            major="Mathematics",
            educational_attainment="Master's Degree",
            jhs_eligible=True,
            shs_eligible=True,
            qualifications=[math],
        ),

        Teacher(
            employee_id="T006",
            name="Carlo Mendoza",
            major="Science",
            educational_attainment="Bachelor's Degree",
            jhs_eligible=True,
            shs_eligible=False,
            qualifications=[science],
        ),
    ]

    db.session.add_all(teachers)

    # =========================================================
    # SECTIONS
    # =========================================================

    sections = [

        Section(
            name="JHS-7A",
            grade_level="Grade 7",
            educational_level="JHS",
        ),

        Section(
            name="JHS-7B",
            grade_level="Grade 7",
            educational_level="JHS",
        ),

        Section(
            name="JHS-8A",
            grade_level="Grade 8",
            educational_level="JHS",
        ),

        Section(
            name="SHS-11A",
            grade_level="Grade 11",
            educational_level="SHS",
            strand="STEM",
        ),
    ]

    db.session.add_all(sections)

    # =========================================================
    # SUBJECTS
    # =========================================================

    subjects = [

        Subject(
            name="Mathematics",
            required_qualification=math,
            minimum_educational_attainment="Bachelor's Degree",
        ),

        Subject(
            name="Science",
            required_qualification=science,
            minimum_educational_attainment="Bachelor's Degree",
        ),

        Subject(
            name="English",
            required_qualification=english,
            minimum_educational_attainment="Bachelor's Degree",
        ),

        Subject(
            name="Filipino",
            required_qualification=filipino,
            minimum_educational_attainment="Bachelor's Degree",
        ),
    ]

    db.session.add_all(subjects)

    # Commit first so IDs exist before dependent records
    # are created.
    db.session.commit()

    # =========================================================
    # SCHEDULE PERIODS
    # =========================================================

    period_names = [

        ("Monday", "Period 1"),
        ("Monday", "Period 2"),
        ("Monday", "Period 3"),

        ("Tuesday", "Period 1"),
        ("Tuesday", "Period 2"),
        ("Tuesday", "Period 3"),

        ("Wednesday", "Period 1"),
        ("Wednesday", "Period 2"),
        ("Wednesday", "Period 3"),

        ("Thursday", "Period 1"),
        ("Thursday", "Period 2"),
        ("Thursday", "Period 3"),

        ("Friday", "Period 1"),
        ("Friday", "Period 2"),
        ("Friday", "Period 3"),
    ]

    periods = []

    for seq, (day, period) in enumerate(
        period_names,
        start=1,
    ):

        schedule_period = SchedulePeriod(
            day=day,
            period=period,
            sequence=seq,
        )

        periods.append(schedule_period)

        db.session.add(schedule_period)

    db.session.commit()

    # =========================================================
    # TEACHER AVAILABILITY
    # =========================================================
    #
    # Controlled demonstration availability dataset.
    #
    # Every teacher receives one availability record for
    # every scheduling period.
    #
    # True  = Available
    # False = Unavailable
    #
    # Each teacher has exactly two unavailable periods.
    #
    # 6 teachers x 15 periods = 90 records
    # 12 unavailable records
    # 78 available records
    # =========================================================

    unavailable_periods = {

        "T001": {5, 12},       # Maria Santos
        "T002": {2, 8},        # Juan Dela Cruz
        "T003": {3, 9},        # Ana Reyes
        "T004": {4, 10},       # Pedro Garcia
        "T005": {6, 13},       # Liza Cruz
        "T006": {1, 11},       # Carlo Mendoza
    }

    for teacher in teachers:

        unavailable = unavailable_periods.get(
            teacher.employee_id,
            set(),
        )

        for schedule_period in periods:

            availability = TeacherAvailability(
                teacher_id=teacher.id,
                period_id=schedule_period.id,
                available=(
                    schedule_period.sequence
                    not in unavailable
                ),
            )

            db.session.add(availability)

    db.session.commit()

    # =========================================================
    # CURRICULUM REQUIREMENTS
    # =========================================================
    #
    # Every section receives:
    #
    # Mathematics = 3 periods
    # Science     = 3 periods
    # English     = 2 periods
    # Filipino    = 2 periods
    #
    # 10 periods per section
    # 4 sections
    # = 40 total required teaching periods
    # =========================================================

    for section in sections:

        for subject, required in zip(
            subjects,
            [3, 3, 2, 2],
        ):

            db.session.add(
                CurriculumRequirement(
                    section_id=section.id,
                    subject_id=subject.id,
                    required_periods=required,
                )
            )

    db.session.commit()

    # =========================================================
    # FINAL VERIFICATION
    # =========================================================

    print(
        "TeachCARE demonstration database "
        "created successfully."
    )

    print(
        f"Teachers: {Teacher.query.count()}"
    )

    print(
        f"Schedule Periods: "
        f"{SchedulePeriod.query.count()}"
    )

    print(
        f"Teacher Availability Records: "
        f"{TeacherAvailability.query.count()}"
    )

    print(
        f"Available Records: "
        f"{TeacherAvailability.query.filter_by(available=True).count()}"
    )

    print(
        f"Unavailable Records: "
        f"{TeacherAvailability.query.filter_by(available=False).count()}"
    )

    print(
        f"Curriculum Requirements: "
        f"{CurriculumRequirement.query.count()}"
    )

    print(
        f"Total Required Teaching Periods: "
        f"{sum(
            r.required_periods
            for r in CurriculumRequirement.query.all()
        )}"
    )