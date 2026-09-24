from app import create_app
from extensions import db
from models import Teacher, TeacherAvailability, Qualification
from services.optimizer import generate_schedule


app = create_app()


def print_result(test_name, result, expected_status):
    actual_status = result.get("status")

    print("----------------------------------------")
    print(test_name)
    print("----------------------------------------")
    print(f"Expected: {expected_status}")
    print(f"Actual:   {actual_status}")

    if actual_status == expected_status:
        print("[PASS] Test produced the expected result.")
    else:
        print("[FAIL] Test produced an unexpected result.")

    print(f"Message:  {result.get('message')}")
    print()


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 2.10 - FEASIBLE/INFEASIBLE TESTS")
    print("========================================")
    print()

    # ========================================================
    # TEST 1 - BASELINE FEASIBLE CASE
    # ========================================================

    print("TEST 1: Known Feasible Scenario")
    print("----------------------------------------")

    result = generate_schedule(db)

    print(f"Solver status: {result.get('status')}")
    print(f"Message:       {result.get('message')}")

    if result.get("status") == "OPTIMAL":
        print("[PASS] Baseline scenario is feasible.")
    else:
        print("[FAIL] Baseline scenario should be feasible.")

    print()

    # ========================================================
    # TEST 2 - AVAILABILITY-INDUCED INFEASIBILITY
    # ========================================================

    print("TEST 2: Availability-Induced Infeasibility")
    print("----------------------------------------")

    # Mathematics is taught by T001 and T005 in the
    # controlled demonstration dataset.
    #
    # Temporarily make both Mathematics teachers unavailable
    # for every scheduling period.

    math_teachers = Teacher.query.filter(
        Teacher.employee_id.in_(["T001", "T005"])
    ).all()

    original_availability = {}

    for teacher in math_teachers:

        records = TeacherAvailability.query.filter_by(
            teacher_id=teacher.id
        ).all()

        for record in records:
            original_availability[record.id] = record.available
            record.available = False

    db.session.commit()

    result = generate_schedule(db)

    print(f"Solver status: {result.get('status')}")
    print(f"Message:       {result.get('message')}")

    if result.get("status") == "INFEASIBLE":
        print("[PASS] Removing availability caused infeasibility.")
    else:
        print("[FAIL] Availability restriction did not produce infeasibility.")

    # Restore original availability.
    for record_id, original_value in original_availability.items():

        record = TeacherAvailability.query.get(record_id)

        if record:
            record.available = original_value

    db.session.commit()

    print("[INFO] Original availability restored.")
    print()

    # ========================================================
    # TEST 3 - QUALIFICATION-INDUCED INFEASIBILITY
    # ========================================================

    print("TEST 3: Qualification-Induced Infeasibility")
    print("----------------------------------------")

    # English is required by the curriculum.
    #
    # In our controlled dataset, Ana Reyes (T003) is the
    # English-qualified teacher.
    #
    # Temporarily remove her English qualification by changing
    # her major and removing the qualification relationship.

    english = Qualification.query.filter_by(
        name="English"
    ).first()

    ana = Teacher.query.filter_by(
        employee_id="T003"
    ).first()

    original_major = ana.major
    original_qualifications = list(ana.qualifications)

    ana.major = "Temporary Test Major"

    ana.qualifications = [
        q for q in ana.qualifications
        if q.id != english.id
    ]

    db.session.commit()

    result = generate_schedule(db)

    print(f"Solver status: {result.get('status')}")
    print(f"Message:       {result.get('message')}")

    if result.get("status") == "INFEASIBLE":
        print("[PASS] Removing the English qualification caused infeasibility.")
    else:
        print("[FAIL] Qualification restriction did not produce infeasibility.")

    # Restore Ana's original data.
    ana.major = original_major
    ana.qualifications = original_qualifications

    db.session.commit()

    print("[INFO] Original teacher qualification data restored.")
    print()

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("========================================")
    print("SPRINT 2.10 TEST COMPLETE")
    print("========================================")