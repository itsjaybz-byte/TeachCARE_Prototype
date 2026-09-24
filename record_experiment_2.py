from datetime import datetime
import json

from app import create_app
from extensions import db
from models import Teacher, TeacherAvailability, ScheduleEntry
from services.optimizer import generate_schedule


app = create_app()


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 2.12 - EXPERIMENT 2")
    print("AVAILABILITY-RESTRICTED SCENARIO")
    print("========================================")
    print()

    # ---------------------------------------------------------
    # Find Maria Santos
    # ---------------------------------------------------------

    teacher = Teacher.query.filter_by(
        employee_id="T001"
    ).first()

    if teacher is None:
        print("[FAIL] Teacher T001 was not found.")
        raise SystemExit(1)

    print(f"Teacher restricted: {teacher.name}")

    # ---------------------------------------------------------
    # Save original availability
    # ---------------------------------------------------------

    availability_records = TeacherAvailability.query.filter_by(
        teacher_id=teacher.id
    ).all()

    if not availability_records:
        print("[FAIL] No availability records found for T001.")
        raise SystemExit(1)

    original_availability = {
        record.id: record.available
        for record in availability_records
    }

    print(
        f"Availability records affected: "
        f"{len(availability_records)}"
    )

    try:

        # -----------------------------------------------------
        # Apply experimental restriction
        # -----------------------------------------------------
        #
        # Temporarily make Maria Santos unavailable during
        # every scheduling period.
        #
        # This leaves Liza Cruz as another Mathematics-qualified
        # teacher, so the scenario should remain feasible.
        # -----------------------------------------------------

        for record in availability_records:
            record.available = False

        db.session.commit()

        print()
        print("[INFO] T001 availability temporarily restricted.")
        print("[INFO] Running optimizer...")
        print()

        # -----------------------------------------------------
        # Run optimizer
        # -----------------------------------------------------

        result = generate_schedule(db)

        schedule_count = ScheduleEntry.query.count()

        # -----------------------------------------------------
        # Build experiment record
        # -----------------------------------------------------

        experiment = {
            "experiment": "Sprint 2.12 - Experiment 2",
            "scenario": (
                "Availability-restricted scenario: "
                "T001 unavailable for all scheduling periods"
            ),
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),

            "restricted_teacher": teacher.employee_id,
            "restricted_teacher_name": teacher.name,

            "solver_status": result.get("status"),
            "message": result.get("message"),
            "schedule_entries": schedule_count,
            "objective_value": result.get("objective_value"),
        }

        # -----------------------------------------------------
        # Display concise result
        # -----------------------------------------------------

        print("Scenario:         Availability-restricted")
        print(
            f"Restricted teacher: "
            f"{teacher.employee_id} - {teacher.name}"
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
            "experiment_2_results.json",
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

        if (
            experiment["solver_status"] == "OPTIMAL"
            and experiment["schedule_entries"] > 0
        ):
            print(
                "[PASS] Availability-restricted scenario "
                "remained feasible."
            )
            print(
                "[OK] Result saved to "
                "experiment_2_results.json"
            )
        else:
            print(
                "[FAIL] Availability restriction did not "
                "produce the expected feasible result."
            )

    finally:

        # -----------------------------------------------------
        # Restore original availability
        # -----------------------------------------------------

        for record_id, original_value in original_availability.items():

            record = db.session.get(
                TeacherAvailability,
                record_id,
            )

            if record is not None:
                record.available = original_value

        db.session.commit()

        print()
        print(
            "[INFO] Original teacher availability restored."
        )

    print()
    print("========================================")
    print("SPRINT 2.12 EXPERIMENT 2 COMPLETE")
    print("========================================")