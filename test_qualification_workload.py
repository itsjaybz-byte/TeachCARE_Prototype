from app import create_app
from extensions import db

from models import (
    Teacher,
    Qualification,
    ScheduleEntry,
)

from services.optimizer import generate_schedule
from services.workload import calculate_workload_report


app = create_app()


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 3.3 - QUALIFICATION RESTRICTION")
    print("WORKLOAD ANALYSIS")
    print("========================================")
    print()

    # ========================================================
    # TEST 1 - BASELINE
    # ========================================================

    print("TEST 1: Baseline Scenario")
    print("----------------------------------------")

    baseline_result = generate_schedule(db)

    if baseline_result.get("status") != "OPTIMAL":
        print("[FAIL] Baseline scenario should be feasible.")
        raise SystemExit(1)

    baseline_report = calculate_workload_report()

    print(
        f"Solver status:     "
        f"{baseline_result.get('status')}"
    )

    print(
        f"Schedule entries:  "
        f"{ScheduleEntry.query.count()}"
    )

    print(
        f"Objective value:   "
        f"{baseline_result.get('objective_value')}"
    )

    print(
        f"MAD:               "
        f"{baseline_report.get('mad')}"
    )

    print()

    # ========================================================
    # FIND ENGLISH QUALIFICATION
    # ========================================================

    english = Qualification.query.filter_by(
        name="English"
    ).first()

    if english is None:
        print(
            "[FAIL] English qualification was not found."
        )
        raise SystemExit(1)

    # ========================================================
    # FIND ANA REYES
    # ========================================================

    teacher = Teacher.query.filter_by(
        employee_id="T003"
    ).first()

    if teacher is None:
        print(
            "[FAIL] T003 - Ana Reyes was not found."
        )
        raise SystemExit(1)

    print(
        f"Teacher restricted: "
        f"{teacher.employee_id} - {teacher.name}"
    )

    print(
        f"Qualification removed: "
        f"{english.name}"
    )

    # ========================================================
    # SAVE ORIGINAL DATA
    # ========================================================

    original_major = teacher.major

    original_qualifications = list(
        teacher.qualifications
    )

    # ========================================================
    # VERIFY ENGLISH QUALIFICATION EXISTS
    # ========================================================

    has_english = any(
        qualification.id == english.id
        for qualification in teacher.qualifications
    )

    if not has_english and (
        teacher.major.strip().lower()
        != english.name.strip().lower()
    ):
        print(
            "[FAIL] T003 does not currently have "
            "the English qualification."
        )
        raise SystemExit(1)

    try:

        # ====================================================
        # TEST 2 - APPLY QUALIFICATION RESTRICTION
        # ====================================================

        print()
        print(
            "TEST 2: Qualification-Restricted Scenario"
        )
        print("----------------------------------------")

        # Remove English from both the major and
        # qualification relationship.

        teacher.major = "Temporary Test Major"

        teacher.qualifications = [
            qualification
            for qualification in teacher.qualifications
            if qualification.id != english.id
        ]

        db.session.commit()

        print(
            "[INFO] English qualification temporarily removed."
        )

        print(
            "[INFO] Running optimizer..."
        )

        print()

        restricted_result = generate_schedule(db)

        schedule_count = ScheduleEntry.query.count()

        print(
            f"Solver status:     "
            f"{restricted_result.get('status')}"
        )

        print(
            f"Schedule entries:  "
            f"{schedule_count}"
        )

        print(
            f"Objective value:   "
            f"{restricted_result.get('objective_value')}"
        )

        print(
            f"Message:           "
            f"{restricted_result.get('message')}"
        )

        print()

        # ====================================================
        # TEST 3 - EXPECTED INFEASIBILITY
        # ====================================================

        if restricted_result.get("status") == "INFEASIBLE":

            print(
                "[PASS] Removing the critical English "
                "qualification caused infeasibility."
            )

        else:

            print(
                "[FAIL] Qualification restriction did not "
                "produce the expected infeasible result."
            )

            raise SystemExit(1)

        # ====================================================
        # TEST 4 - WORKLOAD INTERPRETATION
        # ====================================================

        print()
        print(
            "TEST 3: Workload Interpretation"
        )
        print("----------------------------------------")

        if restricted_result.get("status") == "INFEASIBLE":

            print(
                "[INFO] No valid schedule exists under "
                "the qualification restriction."
            )

            print(
                "[INFO] Workload and MAD are therefore "
                "not applicable to the restricted scenario."
            )

            restricted_mad = None

        else:

            restricted_report = calculate_workload_report()

            restricted_mad = restricted_report.get(
                "mad"
            )

        # ====================================================
        # COMPARISON
        # ====================================================

        print()
        print(
            "========================================"
        )
        print(
            "COMPARISON"
        )
        print(
            "========================================"
        )

        print(
            f"Baseline objective:  "
            f"{baseline_result.get('objective_value')}"
        )

        print(
            f"Restricted objective: "
            f"{restricted_result.get('objective_value')}"
        )

        print()

        print(
            f"Baseline MAD:         "
            f"{baseline_report.get('mad')}"
        )

        print(
            f"Restricted MAD:       "
            f"{restricted_mad}"
        )

        print()

        print(
            "[RESULT] Availability restrictions can produce "
            "a feasible but less balanced schedule."
        )

        print(
            "[RESULT] A critical qualification restriction "
            "can instead eliminate feasibility entirely."
        )

    finally:

        # ====================================================
        # RESTORE ORIGINAL QUALIFICATION DATA
        # ====================================================

        teacher.major = original_major

        teacher.qualifications = (
            original_qualifications
        )

        db.session.commit()

        print()
        print(
            "[INFO] Original teacher qualification "
            "data restored."
        )

        # ====================================================
        # REGENERATE BASELINE SCHEDULE
        # ====================================================

        print(
            "[INFO] Regenerating baseline schedule..."
        )

        restored_result = generate_schedule(db)

        if restored_result.get("status") == "OPTIMAL":

            print(
                "[PASS] Baseline schedule successfully restored."
            )

        else:

            print(
                "[FAIL] Baseline schedule could not "
                "be restored."
            )

    print()
    print("========================================")
    print("SPRINT 3.3 TEST COMPLETE")
    print("========================================")
    