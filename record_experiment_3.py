from datetime import datetime
import json

from app import create_app
from extensions import db
from models import Teacher, Qualification, ScheduleEntry
from services.optimizer import generate_schedule


app = create_app()


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 2.12 - EXPERIMENT 3")
    print("QUALIFICATION-RESTRICTED SCENARIO")
    print("========================================")
    print()

    # ---------------------------------------------------------
    # Find English qualification
    # ---------------------------------------------------------

    english = Qualification.query.filter_by(
        name="English"
    ).first()

    if english is None:
        print("[FAIL] English qualification was not found.")
        raise SystemExit(1)

    # ---------------------------------------------------------
    # Find Ana Reyes
    # ---------------------------------------------------------

    teacher = Teacher.query.filter_by(
        employee_id="T003"
    ).first()

    if teacher is None:
        print("[FAIL] Teacher T003 was not found.")
        raise SystemExit(1)

    print(
        f"Teacher restricted: "
        f"{teacher.name}"
    )

    print(
        f"Qualification removed: "
        f"{english.name}"
    )

    # ---------------------------------------------------------
    # Verify Ana currently has English qualification
    # ---------------------------------------------------------

    original_major = teacher.major
    original_qualifications = list(
        teacher.qualifications
    )

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

        # -----------------------------------------------------
        # Apply experimental restriction
        # -----------------------------------------------------
        #
        # Remove English from both the teacher's qualification
        # relationship and major so that the optimizer's
        # qualification check cannot match English.
        # -----------------------------------------------------

        teacher.major = "Temporary Test Major"

        teacher.qualifications = [
            qualification
            for qualification in teacher.qualifications
            if qualification.id != english.id
        ]

        db.session.commit()

        print()
        print(
            "[INFO] T003 English qualification temporarily removed."
        )

        print(
            "[INFO] Running optimizer..."
        )

        print()

        # -----------------------------------------------------
        # Run optimizer
        # -----------------------------------------------------

        result = generate_schedule(db)

        # IMPORTANT:
        # If the optimizer is infeasible, there is no newly
        # generated schedule. Any ScheduleEntry records that
        # remain are from a previous successful experiment.
        #
        # Therefore, record 0 for an infeasible experiment.

        if result.get("status") == "OPTIMAL":
            schedule_count = ScheduleEntry.query.count()
        else:
            schedule_count = 0

        # -----------------------------------------------------
        # Build experiment record
        # -----------------------------------------------------

        experiment = {
            "experiment": "Sprint 2.12 - Experiment 3",

            "scenario": (
                "Qualification-restricted scenario: "
                "T003 cannot teach English"
            ),

            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),

            "restricted_teacher": teacher.employee_id,

            "restricted_teacher_name": teacher.name,

            "removed_qualification": english.name,

            "solver_status": result.get("status"),

            "message": result.get("message"),

            "schedule_entries": schedule_count,

            "objective_value": result.get(
                "objective_value"
            ),
        }

        # -----------------------------------------------------
        # Display result
        # -----------------------------------------------------

        print(
            "Scenario:         Qualification-restricted"
        )

        print(
            f"Restricted teacher: "
            f"{teacher.employee_id} - {teacher.name}"
        )

        print(
            f"Removed qualification: "
            f"{english.name}"
        )

        print(
            f"Solver status:    "
            f"{experiment['solver_status']}"
        )

        print(
            f"Schedule entries: "
            f"{experiment['schedule_entries']}"
        )

        print(
            f"Objective value:  "
            f"{experiment['objective_value']}"
        )

        print(
            f"Message:          "
            f"{experiment['message']}"
        )

        print()

        # -----------------------------------------------------
        # Save result
        # -----------------------------------------------------

        with open(
            "experiment_3_results.json",
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                experiment,
                file,
                indent=4,
            )

        # -----------------------------------------------------
        # Evaluate experiment
        # -----------------------------------------------------
        #
        # We expect this experiment to become infeasible
        # because T003 is the only English-qualified teacher
        # in our controlled dataset.
        # -----------------------------------------------------

        if experiment["solver_status"] == "INFEASIBLE":

            print(
                "[PASS] Removing the English qualification "
                "caused infeasibility as expected."
            )

            print(
                "[OK] Result saved to "
                "experiment_3_results.json"
            )

        else:

            print(
                "[FAIL] The qualification restriction did "
                "not produce the expected infeasible result."
            )

    finally:

        # -----------------------------------------------------
        # Restore original teacher qualification data
        # -----------------------------------------------------

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

    print()
    print("========================================")
    print("SPRINT 2.12 EXPERIMENT 3 COMPLETE")
    print("========================================")