import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

import time

from app import create_app
from extensions import db

from models import (
    Section,
    Subject,
    CurriculumRequirement,
    ScheduleEntry,
)

from services.optimizer import generate_schedule


app = create_app()


with app.app_context():

    print("=" * 65)
    print("TEACHCARE STRESS TEST — S1")
    print("=" * 65)

    # ---------------------------------------------------------
    # BASELINE
    # ---------------------------------------------------------

    original_section_ids = [
        section.id
        for section in Section.query.order_by(
            Section.id
        ).all()
    ]

    original_requirement_ids = [
        requirement.id
        for requirement in CurriculumRequirement.query.all()
    ]

    original_schedule_count = ScheduleEntry.query.count()

    print()
    print("BASELINE")
    print("-" * 65)
    print(
        "Sections:",
        Section.query.count(),
    )
    print(
        "Requirements:",
        CurriculumRequirement.query.count(),
    )
    print(
        "Schedule entries:",
        original_schedule_count,
    )

    # ---------------------------------------------------------
    # CREATE TWO ADDITIONAL SECTIONS
    # ---------------------------------------------------------

    section_a = Section(
        name="JHS-9A",
        grade_level="Grade 9",
        educational_level="JHS",
    )

    section_b = Section(
        name="JHS-9B",
        grade_level="Grade 9",
        educational_level="JHS",
    )

    db.session.add_all([
        section_a,
        section_b,
    ])

    db.session.flush()

    # ---------------------------------------------------------
    # SUBJECTS
    # ---------------------------------------------------------

    subjects = Subject.query.order_by(
        Subject.id
    ).all()

    required_periods = [3, 3, 2, 2]

    # ---------------------------------------------------------
    # CREATE CURRICULUM REQUIREMENTS
    # ---------------------------------------------------------

    for section in [
        section_a,
        section_b,
    ]:

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

    # ---------------------------------------------------------
    # STRESS SCENARIO SIZE
    # ---------------------------------------------------------

    print()
    print("STRESS SCENARIO S1")
    print("-" * 65)
    print(
        "Sections:",
        Section.query.count(),
    )
    print(
        "Requirements:",
        CurriculumRequirement.query.count(),
    )

    total_required = sum(
        requirement.required_periods
        for requirement in CurriculumRequirement.query.all()
    )

    print(
        "Total required assignments:",
        total_required,
    )

    # ---------------------------------------------------------
    # RUN OPTIMIZER
    # ---------------------------------------------------------

    start = time.perf_counter()

    result = generate_schedule(db)

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        "Solver status:",
        result.get("status"),
    )

    print(
        "Schedule entries:",
        ScheduleEntry.query.count(),
    )

    print(
        "Runtime seconds:",
        round(elapsed, 6),
    )

    print(
        "Message:",
        result.get("message"),
    )

    # ---------------------------------------------------------
    # RESTORE ORIGINAL DATASET
    # ---------------------------------------------------------

    print()
    print("RESTORING BASELINE")
    print("-" * 65)

    ScheduleEntry.query.delete()

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

    # ---------------------------------------------------------
    # REGENERATE BASELINE
    # ---------------------------------------------------------

    restored = generate_schedule(db)

    print(
        "Baseline regeneration status:",
        restored.get("status"),
    )

    print(
        "Baseline schedule entries:",
        ScheduleEntry.query.count(),
    )

    print("=" * 65)