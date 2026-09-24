from app import create_app
from extensions import db
from models import (
    Teacher,
    Section,
    Subject,
    CurriculumRequirement,
    SchedulePeriod,
    TeacherAvailability,
)

app = create_app()


with app.app_context():

    print("\n========================================")
    print("SPRINT 2.6 - DATABASE INTEGRITY TEST")
    print("========================================\n")

    # ---------------------------------------------------------
    # Load existing seeded records
    # ---------------------------------------------------------

    teacher = Teacher.query.first()
    section = Section.query.first()
    subject = Subject.query.first()
    period = SchedulePeriod.query.first()

    if not all([teacher, section, subject, period]):
        print("ERROR: Required seed data is missing.")
        print("Run 'python seed.py' first.")
        raise SystemExit(1)

    print("[OK] Seeded records found.")
    print(f"     Teacher:  {teacher.name}")
    print(f"     Section:  {section.name}")
    print(f"     Subject:  {subject.name}")
    print(f"     Period:   {period.day} - {period.period}")

    # ---------------------------------------------------------
    # TEST 1: Curriculum Requirement Uniqueness
    # ---------------------------------------------------------

    print("\n----------------------------------------")
    print("TEST 1: Curriculum Requirement")
    print("----------------------------------------")

    existing_requirement = CurriculumRequirement.query.filter_by(
        section_id=section.id,
        subject_id=subject.id,
    ).first()

    if existing_requirement:

        print("[OK] Existing curriculum requirement found.")

        duplicate = CurriculumRequirement(
            section_id=section.id,
            subject_id=subject.id,
            required_periods=99,
        )

        db.session.add(duplicate)

        try:
            db.session.commit()

            print("[FAIL] Duplicate curriculum requirement was accepted!")

            db.session.rollback()

        except Exception:
            db.session.rollback()

            print("[PASS] Duplicate curriculum requirement was rejected.")

    else:
        print("[FAIL] Expected curriculum requirement was not found.")

    # ---------------------------------------------------------
    # TEST 2: Teacher Availability Uniqueness
    # ---------------------------------------------------------

    print("\n----------------------------------------")
    print("TEST 2: Teacher Availability")
    print("----------------------------------------")

    existing_availability = TeacherAvailability.query.filter_by(
        teacher_id=teacher.id,
        period_id=period.id,
    ).first()

    if existing_availability:

        print("[OK] Existing availability record found.")

        duplicate = TeacherAvailability(
            teacher_id=teacher.id,
            period_id=period.id,
            available=not existing_availability.available,
        )

        db.session.add(duplicate)

        try:
            db.session.commit()

            print("[FAIL] Duplicate teacher availability was accepted!")

            db.session.rollback()

        except Exception:
            db.session.rollback()

            print("[PASS] Duplicate teacher availability was rejected.")

    else:
        print("[FAIL] Expected teacher availability was not found.")

    # ---------------------------------------------------------
    # TEST 3: Existing Valid Availability Records
    # ---------------------------------------------------------

    print("\n----------------------------------------")
    print("TEST 3: Valid Availability Records")
    print("----------------------------------------")

    total_availability = TeacherAvailability.query.count()

    expected_availability = (
        Teacher.query.count() *
        SchedulePeriod.query.count()
    )

    print(f"[INFO] Availability records found: {total_availability}")
    print(f"[INFO] Expected records:            {expected_availability}")

    if total_availability == expected_availability:
        print("[PASS] Every teacher-period combination has one availability record.")
    else:
        print("[FAIL] Availability record count is incorrect.")

    # ---------------------------------------------------------
    # TEST 4: Availability Values
    # ---------------------------------------------------------

    print("\n----------------------------------------")
    print("TEST 4: Availability Values")
    print("----------------------------------------")

    invalid_values = TeacherAvailability.query.filter(
        TeacherAvailability.available.notin_([True, False])
    ).count()

    if invalid_values == 0:
        print("[PASS] Availability values are valid.")
    else:
        print("[FAIL] Invalid availability values found.")

    # ---------------------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------------------

    print("\n========================================")
    print("SPRINT 2.6 DATA INTEGRITY TEST COMPLETE")
    print("========================================")