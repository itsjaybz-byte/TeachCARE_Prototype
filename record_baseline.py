from datetime import datetime
import json

from app import create_app
from extensions import db
from models import ScheduleEntry
from services.optimizer import generate_schedule


app = create_app()


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 2.12 - EXPERIMENT 1")
    print("BASELINE FEASIBLE RESULT")
    print("========================================")
    print()

    # ---------------------------------------------------------
    # Run the baseline scenario
    # ---------------------------------------------------------

    result = generate_schedule(db)

    # Count generated schedule entries.
    schedule_count = ScheduleEntry.query.count()

    # ---------------------------------------------------------
    # Build experiment record
    # ---------------------------------------------------------

    experiment = {
        "experiment": "Sprint 2.12 - Experiment 1",
        "scenario": "Baseline feasible demonstration dataset",
        "timestamp": datetime.now().isoformat(timespec="seconds"),

        "solver_status": result.get("status"),
        "message": result.get("message"),
        "schedule_entries": schedule_count,
        "objective_value": result.get("objective_value"),
    }

    # ---------------------------------------------------------
    # Display concise result
    # ---------------------------------------------------------

    print("Scenario:         Baseline feasible demonstration dataset")
    print(f"Solver status:    {experiment['solver_status']}")
    print(f"Schedule entries: {experiment['schedule_entries']}")
    print(f"Objective value:  {experiment['objective_value']}")
    print(f"Message:          {experiment['message']}")
    print()

    # ---------------------------------------------------------
    # Save result
    # ---------------------------------------------------------

    with open(
        "experiment_results.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            experiment,
            file,
            indent=4,
        )

    # ---------------------------------------------------------
    # Verify expected baseline
    # ---------------------------------------------------------

    if (
        experiment["solver_status"] == "OPTIMAL"
        and experiment["schedule_entries"] > 0
    ):
        print("[PASS] Baseline feasible experiment completed.")
        print("[OK] Result saved to experiment_results.json")
    else:
        print("[FAIL] Baseline experiment did not produce an optimal schedule.")

    print()
    print("========================================")
    print("SPRINT 2.12 EXPERIMENT COMPLETE")
    print("========================================")