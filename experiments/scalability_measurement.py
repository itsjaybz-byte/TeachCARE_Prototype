import os
import sys
import time

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from app import create_app
from extensions import db

from models import (
    Section,
    Subject,
    CurriculumRequirement,
    Teacher,
    SchedulePeriod,
    TeacherAvailability,
)

from services.optimizer import (
    teacher_is_qualified,
    teacher_is_level_eligible,
)


app = create_app()


def measure_candidates():

    teachers = Teacher.query.order_by(
        Teacher.id
    ).all()

    requirements = CurriculumRequirement.query.order_by(
        CurriculumRequirement.id
    ).all()

    periods = SchedulePeriod.query.order_by(
        SchedulePeriod.sequence
    ).all()

    availability_records = TeacherAvailability.query.all()

    availability = {
        (
            record.teacher_id,
            record.period_id,
        ):
        record.available
        for record in availability_records
    }

    start = time.perf_counter()

    candidates = []

    for req in requirements:

        for teacher in teachers:

            if not teacher_is_qualified(
                teacher,
                req.subject,
            ):
                continue

            if not teacher_is_level_eligible(
                teacher,
                req.section,
            ):
                continue

            for period in periods:

                if not availability.get(
                    (
                        teacher.id,
                        period.id,
                    ),
                    False,
                ):
                    continue

                candidates.append(
                    (
                        teacher.id,
                        req.id,
                        period.id,
                    )
                )

    elapsed = (
        time.perf_counter()
        - start
    )

    return {
        "teachers": len(teachers),
        "sections": len(
            {
                req.section_id
                for req in requirements
            }
        ),
        "requirements": len(requirements),
        "periods": len(periods),
        "candidates": len(candidates),
        "generation_time": elapsed,
    }


def add_sections(names):

    subjects = Subject.query.order_by(
        Subject.id
    ).all()

    required_periods = [3, 3, 2, 2]

    sections = []

    for name, grade in names:

        section = Section(
            name=name,
            grade_level=grade,
            educational_level="JHS",
        )

        db.session.add(section)
        sections.append(section)

    db.session.flush()

    for section in sections:

        for subject, required in zip(
            subjects,
            required_periods,
        ):

            db.session.add(
                CurriculumRequirement(
                    section_id=section.id,
                    subject_id=subject.id,
                    required_periods=required,
                )
            )

    db.session.commit()


with app.app_context():

    print("=" * 65)
    print("TEACHCARE SCALABILITY MEASUREMENT")
    print("=" * 65)

    original_section_ids = {
        section.id
        for section in Section.query.all()
    }

    original_requirement_ids = {
        requirement.id
        for requirement
        in CurriculumRequirement.query.all()
    }

    # ---------------------------------------------------------
    # S0
    # ---------------------------------------------------------

    baseline = measure_candidates()

    print()
    print("S0 — BASELINE")
    print("-" * 65)
    print("Teachers:", baseline["teachers"])
    print("Sections:", baseline["sections"])
    print("Requirements:", baseline["requirements"])
    print("Periods:", baseline["periods"])
    print("Candidate assignments:", baseline["candidates"])
    print(
        "Candidate generation time:",
        round(
            baseline["generation_time"],
            6,
        ),
    )

    # ---------------------------------------------------------
    # S3 — 7 SECTIONS
    # ---------------------------------------------------------

    add_sections([
    ("JHS-9A", "Grade 9"),
    ("JHS-9B", "Grade 9"),
    ("JHS-10A", "Grade 10"),
    ("JHS-10B", "Grade 10"),
])

    s3 = measure_candidates()

    print()
    print("S2 — 8 SECTION SCENARIO")
    print("-" * 65)
    print("Teachers:", s3["teachers"])
    print("Sections:", s3["sections"])
    print("Requirements:", s3["requirements"])
    print("Periods:", s3["periods"])
    print("Candidate assignments:", s3["candidates"])
    print(
        "Candidate generation time:",
        round(
            s3["generation_time"],
            6,
        ),
    )

    # ---------------------------------------------------------
    # RESTORE BASELINE
    # ---------------------------------------------------------

    CurriculumRequirement.query.filter(
        ~CurriculumRequirement.id.in_(
            original_requirement_ids
        )
    ).delete(
        synchronize_session=False
    )

    Section.query.filter(
        ~Section.id.in_(
            original_section_ids
        )
    ).delete(
        synchronize_session=False
    )

    db.session.commit()

    print()
    print("Baseline restored.")
    print(
        "Sections:",
        Section.query.count(),
    )
    print(
        "Requirements:",
        CurriculumRequirement.query.count(),
    )

    print("=" * 65)