from app import create_app
from extensions import db

from models import Teacher, TeacherAvailability, ScheduleEntry
from services.optimizer import generate_schedule
from services.workload import calculate_workload_report


app = create_app()


def print_scenario_result(name, result, report):
    print("----------------------------------------")
    print(name)
    print("----------------------------------------")

    print(f"Solver status:     {result.get('status')}")
    print(f"Schedule entries:  {ScheduleEntry.query.count()}")
    print(f"Objective value:   {result.get('objective_value')}")
    print(f"MAD:               {report.get('mad')}")
    print(f"Total workload:    {report.get('total_workload')}")
    print()


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 3.2 - WORKLOAD COMPARISON")
    print("========================================")
    print()

    # ========================================================
    # TEST 1 - BASELINE
    # ========================================================

    print("TEST 1: Baseline Scenario")
    print()

    baseline_result = generate_schedule(db)

    if baseline_result.get("status") != "OPTIMAL":
        print("[FAIL] Baseline scenario should be feasible.")
        raise SystemExit(1)

    baseline_report = calculate_workload_report()

    print_scenario_result(
        "BASELINE",
        baseline_result,
        baseline_report,
    )

    # ========================================================
    # TEST 2 - AVAILABILITY-RESTRICTED SCENARIO
    # ========================================================

    print("TEST 2: Availability-Restricted Scenario")
    print()

    teacher = Teacher.query.filter_by(
        employee_id="T001"
    ).first()

    if teacher is None:
        print("[FAIL] T001 was not found.")
        raise SystemExit(1)

    records = TeacherAvailability.query.filter_by(
        teacher_id=teacher.id
    ).all()

    original_availability = {}

    for record in records:
        original_availability[record.id] = record.available
        record.available = False

    db.session.commit()

    print(
        f"[INFO] Temporarily restricted all availability "
        f"for {teacher.employee_id} - {teacher.name}."
    )

    try:

        restricted_result = generate_schedule(db)

        if restricted_result.get("status") != "OPTIMAL":
            print(
                "[FAIL] Availability-restricted scenario "
                "was expected to remain feasible."
            )
            raise SystemExit(1)

        restricted_report = calculate_workload_report()

        print_scenario_result(
            "AVAILABILITY-RESTRICTED",
            restricted_result,
            restricted_report,
        )

        # ====================================================
        # COMPARISON
        # ====================================================

        baseline_mad = baseline_report["mad"]
        restricted_mad = restricted_report["mad"]

        mad_change = restricted_mad - baseline_mad

        baseline_objective = baseline_result[
            "objective_value"
        ]

        restricted_objective = restricted_result[
            "objective_value"
        ]

        objective_change = (
            restricted_objective
            - baseline_objective
        )

        print("========================================")
        print("COMPARISON")
        print("========================================")

        print(
            f"Baseline objective:        "
            f"{baseline_objective}"
        )

        print(
            f"Restricted objective:      "
            f"{restricted_objective}"
        )

        print(
            f"Objective change:          "
            f"{objective_change}"
        )

        print()

        print(
            f"Baseline MAD:              "
            f"{baseline_mad}"
        )

        print(
            f"Restricted MAD:            "
            f"{restricted_mad}"
        )

        print(
            f"MAD change:                "
            f"{mad_change}"
        )

        print()

        if restricted_mad > baseline_mad:
            print(
                "[PASS] Availability restriction increased "
                "workload imbalance."
            )

        elif restricted_mad == baseline_mad:
            print(
                "[INFO] Availability restriction did not "
                "change MAD."
            )

        else:
            print(
                "[INFO] Availability restriction decreased "
                "MAD."
            )

    finally:

        # ====================================================
        # RESTORE ORIGINAL AVAILABILITY
        # ====================================================

        for record_id, original_value in (
            original_availability.items()
        ):

            record = db.session.get(
                TeacherAvailability,
                record_id,
            )

            if record:
                record.available = original_value

        db.session.commit()

        print()
        print(
            "[INFO] Original teacher availability restored."
        )

    print()
    print("========================================")
    print("SPRINT 3.2 TEST COMPLETE")
    print("========================================")
    