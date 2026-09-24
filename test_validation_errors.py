from app import create_app
from extensions import db

from models import (
    ScheduleEntry,
    Teacher,
    TeacherAvailability,
)

from services.validator import validate_schedule

from services.optimizer import (
    teacher_is_qualified,
    teacher_meets_educational_attainment,
    teacher_is_level_eligible,
)


app = create_app()


def print_result(test_name, result, expected_text):
    print("----------------------------------------")
    print(test_name)
    print("----------------------------------------")

    found = any(
        expected_text.lower() in error.lower()
        for error in result["errors"]
    )

    print(f"Expected detection: {expected_text}")
    print(f"Validator valid:    {result['valid']}")

    if found:
        print("[PASS] Expected error was detected.")
    else:
        print("[FAIL] Expected error was NOT detected.")

    print("Detected errors:")

    for error in result["errors"]:
        print(f"  - {error}")

    print()


def find_valid_entry():
    """
    Find a schedule entry whose current assignment satisfies
    qualification, educational attainment, and level eligibility.
    """

    entries = ScheduleEntry.query.all()

    for entry in entries:

        teacher = entry.teacher
        subject = entry.subject
        section = entry.section

        if not teacher_is_qualified(
            teacher,
            subject
        ):
            continue

        if not teacher_meets_educational_attainment(
            teacher,
            subject
        ):
            continue

        if not teacher_is_level_eligible(
            teacher,
            section
        ):
            continue

        return entry

    return None


with app.app_context():

    print()
    print("========================================")
    print("TEACHCARE - VALIDATION ERROR TESTS")
    print("========================================")
    print()

    # ========================================================
    # BASELINE VALIDATION
    # ========================================================

    entries = ScheduleEntry.query.all()

    if not entries:
        print("[ERROR] No schedule entries found.")
        print("Run the normal schedule generation first.")
        raise SystemExit

    baseline = validate_schedule()

    print("BASELINE VALIDATION")
    print("----------------------------------------")
    print(f"Valid:  {baseline['valid']}")
    print(f"Errors: {len(baseline['errors'])}")
    print()

    if not baseline["valid"]:
        print("[ERROR] Baseline schedule is already invalid.")
        print("Do not continue until the baseline is valid.")
        raise SystemExit


    # ========================================================
    # TEST 1 - QUALIFICATION VIOLATION
    # ========================================================

    print("TEST 1: Qualification Violation")
    print("----------------------------------------")

    entry = find_valid_entry()

    if entry is None:

        print("[SKIP] Could not find a valid schedule entry.")
        print()

    else:

        teacher = entry.teacher

        original_major = teacher.major
        original_qualifications = list(teacher.qualifications)

        # Make the assigned teacher unqualified by
        # temporarily removing all qualification records
        # and changing the major.
        teacher.major = "Temporary Test Major"
        teacher.qualifications = []

        db.session.flush()

        result = validate_schedule()

        print_result(
            "Qualification Violation",
            result,
            "Qualification violation"
        )

        # Restore original teacher data.
        teacher.major = original_major
        teacher.qualifications = original_qualifications

        db.session.flush()
        db.session.rollback()


    # ========================================================
    # TEST 2 - EDUCATIONAL ATTAINMENT VIOLATION
    # ========================================================

    print("TEST 2: Educational-Attainment Violation")
    print("----------------------------------------")

    entry = find_valid_entry()

    if entry is None:

        print("[SKIP] Could not find a suitable schedule entry.")
        print()

    else:

        teacher = entry.teacher

        original_attainment = teacher.educational_attainment

        # Temporarily lower the teacher's educational
        # attainment to the lowest level.
        teacher.educational_attainment = "High School"

        db.session.flush()

        result = validate_schedule()

        print_result(
            "Educational-Attainment Violation",
            result,
            "Educational-attainment violation"
        )

        # Restore original educational attainment.
        teacher.educational_attainment = original_attainment

        db.session.flush()
        db.session.rollback()


    # ========================================================
    # TEST 3 - EDUCATIONAL-LEVEL ELIGIBILITY VIOLATION
    # ========================================================

    print("TEST 3: Educational-Level Eligibility Violation")
    print("----------------------------------------")

    entry = find_valid_entry()

    if entry is None:

        print("[SKIP] Could not find a suitable schedule entry.")
        print()

    else:

        teacher = entry.teacher
        section = entry.section

        original_jhs_eligible = teacher.jhs_eligible
        original_shs_eligible = teacher.shs_eligible

        # Temporarily disable the teacher's eligibility
        # for the educational level of the selected section.
        if section.educational_level == "JHS":

            teacher.jhs_eligible = False

        elif section.educational_level == "SHS":

            teacher.shs_eligible = False

        else:

            print(
                "[SKIP] Unknown educational level: "
                f"{section.educational_level}"
            )

            teacher.jhs_eligible = original_jhs_eligible
            teacher.shs_eligible = original_shs_eligible

            db.session.rollback()

            print()

        if section.educational_level in ["JHS", "SHS"]:

            db.session.flush()

            result = validate_schedule()

            print_result(
                "Educational-Level Eligibility Violation",
                result,
                "Educational-level eligibility violation"
            )

            # Restore original eligibility values.
            teacher.jhs_eligible = original_jhs_eligible
            teacher.shs_eligible = original_shs_eligible

            db.session.flush()
            db.session.rollback()


    # ========================================================
    # TEST 4 - TEACHER SCHEDULE CONFLICT
    # ========================================================

    print("TEST 4: Teacher Schedule Conflict")
    print("----------------------------------------")

    entries = ScheduleEntry.query.all()

    conflict_pair = None

    for first in entries:

        for second in entries:

            if first.id == second.id:
                continue

            if (
                first.teacher_id == second.teacher_id
                and first.period_id != second.period_id
                and first.section_id != second.section_id
            ):

                conflict_pair = (first, second)
                break

        if conflict_pair:
            break

    if conflict_pair is None:

        print(
            "[SKIP] Could not find a suitable "
            "teacher conflict pair."
        )
        print()

    else:

        first, second = conflict_pair

        original_period_id = second.period_id

        second.period_id = first.period_id

        db.session.flush()

        result = validate_schedule()

        print_result(
            "Teacher Schedule Conflict",
            result,
            "Teacher schedule conflict"
        )

        # Restore original period.
        second.period_id = original_period_id

        db.session.flush()
        db.session.rollback()


    # ========================================================
    # TEST 5 - SECTION SCHEDULE CONFLICT
    # ========================================================

    print("TEST 5: Section Schedule Conflict")
    print("----------------------------------------")

    entries = ScheduleEntry.query.all()

    conflict_pair = None

    for first in entries:

        for second in entries:

            if first.id == second.id:
                continue

            if (
                first.section_id == second.section_id
                and first.period_id != second.period_id
                and first.subject_id != second.subject_id
            ):

                conflict_pair = (first, second)
                break

        if conflict_pair:
            break

    if conflict_pair is None:

        print(
            "[SKIP] Could not find a suitable "
            "section conflict pair."
        )
        print()

    else:

        first, second = conflict_pair

        original_period_id = second.period_id

        second.period_id = first.period_id

        db.session.flush()

        result = validate_schedule()

        print_result(
            "Section Schedule Conflict",
            result,
            "Section schedule conflict"
        )

        # Restore original period.
        second.period_id = original_period_id

        db.session.flush()
        db.session.rollback()


    # ========================================================
    # TEST 6 - TEACHER AVAILABILITY VIOLATION
    # ========================================================

    print("TEST 6: Teacher Availability Violation")
    print("----------------------------------------")

    entry = ScheduleEntry.query.first()

    availability = TeacherAvailability.query.filter_by(
        teacher_id=entry.teacher_id,
        period_id=entry.period_id
    ).first()

    if availability is None:

        print("[SKIP] No availability record found.")
        print()

    else:

        original_value = availability.available

        availability.available = False

        db.session.flush()

        result = validate_schedule()

        print_result(
            "Teacher Availability Violation",
            result,
            "Teacher availability violation"
        )

        # Restore original availability.
        availability.available = original_value

        db.session.flush()
        db.session.rollback()


    # ========================================================
    # TEST 7 - CURRICULUM COVERAGE ERROR
    # ========================================================

    print("TEST 7: Curriculum Coverage Error")
    print("----------------------------------------")

    entries = ScheduleEntry.query.all()

    if not entries:

        print("[SKIP] No schedule entries available.")
        print()

    else:

        entry = entries[0]

        db.session.delete(entry)

        db.session.flush()

        result = validate_schedule()

        print_result(
            "Curriculum Coverage Error",
            result,
            "Curriculum coverage error"
        )

        db.session.rollback()


    # ========================================================
    # FINAL BASELINE CHECK
    # ========================================================

    print("FINAL BASELINE CHECK")
    print("----------------------------------------")

    final_result = validate_schedule()

    print(f"Valid:  {final_result['valid']}")
    print(f"Errors: {len(final_result['errors'])}")

    if final_result["valid"]:

        print(
            "[PASS] Database restored to a valid baseline."
        )

    else:

        print(
            "[FAIL] Database was not restored correctly."
        )

        print("Remaining errors:")

        for error in final_result["errors"]:

            print(f"  - {error}")

    print()

    print("========================================")
    print("VALIDATION ERROR TESTS COMPLETE")
    print("========================================")