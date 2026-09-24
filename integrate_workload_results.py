import json

from app import create_app
from extensions import db

from models import ScheduleEntry
from services.workload import calculate_workload_report


app = create_app()


def load_json(filename):
    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 3.5 - EXPERIMENTAL RESULTS")
    print("INTEGRATION")
    print("========================================")
    print()

    # ========================================================
    # LOAD EXISTING EXPERIMENT RESULTS
    # ========================================================

    baseline = load_json(
        "experiment_results.json"
    )

    availability = load_json(
        "experiment_2_results.json"
    )

    qualification = load_json(
        "experiment_3_results.json"
    )

    # ========================================================
    # CURRENT BASELINE WORKLOAD REPORT
    # ========================================================

    # The database should currently contain the restored
    # baseline schedule.

    current_schedule_count = (
        ScheduleEntry.query.count()
    )

    current_report = calculate_workload_report()

    # ========================================================
    # BUILD INTEGRATED RESULTS
    # ========================================================

    baseline_objective = baseline.get(
        "objective_value"
    )

    availability_objective = availability.get(
        "objective_value"
    )

    qualification_objective = qualification.get(
        "objective_value"
    )

    baseline_mad = (
        baseline_objective / current_report["teacher_count"]
        if baseline_objective is not None
        and current_report["teacher_count"] > 0
        else None
    )

    availability_mad = (
        availability_objective
        / current_report["teacher_count"]
        if availability_objective is not None
        and current_report["teacher_count"] > 0
        else None
    )

    integrated_results = {
        "study": "TeachCARE",
        "analysis": "Sprint 3.5 - Experimental Results Integration",

        "baseline": {
            "scenario": "Baseline feasible",
            "feasibility": "FEASIBLE",
            "solver_status": baseline.get(
                "solver_status"
            ),
            "schedule_entries": baseline.get(
                "schedule_entries"
            ),
            "objective_value": baseline_objective,
            "mad": baseline_mad,
        },

        "availability_restricted": {
            "scenario": "Availability-restricted",
            "feasibility": "FEASIBLE",
            "solver_status": availability.get(
                "solver_status"
            ),
            "schedule_entries": availability.get(
                "schedule_entries"
            ),
            "objective_value": availability_objective,
            "mad": availability_mad,
            "objective_change_from_baseline": (
                availability_objective
                - baseline_objective
                if availability_objective is not None
                and baseline_objective is not None
                else None
            ),
            "mad_change_from_baseline": (
                availability_mad
                - baseline_mad
                if availability_mad is not None
                and baseline_mad is not None
                else None
            ),
        },

        "qualification_restricted": {
            "scenario": "Qualification-restricted",
            "feasibility": "INFEASIBLE",
            "solver_status": qualification.get(
                "solver_status"
            ),
            "schedule_entries": qualification.get(
                "schedule_entries"
            ),
            "objective_value": qualification_objective,
            "mad": None,
            "objective_change_from_baseline": None,
            "mad_change_from_baseline": None,
        },

        "current_baseline_workload": {
            "schedule_entries": current_schedule_count,
            "teacher_count": current_report[
                "teacher_count"
            ],
            "total_workload": current_report[
                "total_workload"
            ],
            "minimum_workload": current_report[
                "minimum_workload"
            ],
            "maximum_workload": current_report[
                "maximum_workload"
            ],
            "average_workload": current_report[
                "average_workload"
            ],
            "mad": current_report[
                "mad"
            ],
        },
    }

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    scenarios = [
        (
            "EXP-01",
            integrated_results["baseline"],
        ),
        (
            "EXP-02",
            integrated_results[
                "availability_restricted"
            ],
        ),
        (
            "EXP-03",
            integrated_results[
                "qualification_restricted"
            ],
        ),
    ]

    for experiment_id, scenario in scenarios:

        print(
            f"{experiment_id}: "
            f"{scenario['scenario']}"
        )

        print(
            f"  Feasibility:       "
            f"{scenario['feasibility']}"
        )

        print(
            f"  Solver status:     "
            f"{scenario['solver_status']}"
        )

        print(
            f"  Schedule entries:  "
            f"{scenario['schedule_entries']}"
        )

        print(
            f"  Objective value:   "
            f"{scenario['objective_value']}"
        )

        print(
            f"  MAD:               "
            f"{scenario['mad']}"
        )

        if (
            scenario.get(
                "objective_change_from_baseline"
            )
            is not None
        ):
            print(
                f"  Objective change:  "
                f"{scenario['objective_change_from_baseline']}"
            )

        if (
            scenario.get(
                "mad_change_from_baseline"
            )
            is not None
        ):
            print(
                f"  MAD change:        "
                f"{scenario['mad_change_from_baseline']}"
            )

        print()

    # ========================================================
    # BASELINE WORKLOAD SUMMARY
    # ========================================================

    print("========================================")
    print("BASELINE WORKLOAD SUMMARY")
    print("========================================")

    print(
        f"Teacher count:       "
        f"{current_report['teacher_count']}"
    )

    print(
        f"Total workload:      "
        f"{current_report['total_workload']}"
    )

    print(
        f"Minimum workload:    "
        f"{current_report['minimum_workload']}"
    )

    print(
        f"Maximum workload:    "
        f"{current_report['maximum_workload']}"
    )

    print(
        f"Average workload:    "
        f"{current_report['average_workload']}"
    )

    print(
        f"MAD:                 "
        f"{current_report['mad']}"
    )

    print()

    # ========================================================
    # SAVE INTEGRATED DATASET
    # ========================================================

    output_file = (
        "research_workload_results.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            integrated_results,
            file,
            indent=4,
        )

    print(
        f"[OK] Integrated research results saved to: "
        f"{output_file}"
    )

    print()

    # ========================================================
    # VALIDATION
    # ========================================================

    baseline_valid = (
        integrated_results["baseline"]["feasibility"]
        == "FEASIBLE"
        and
        integrated_results["baseline"]["objective_value"]
        == 4.0
        and
        abs(
            integrated_results["baseline"]["mad"]
            - 0.6666666666666666
        )
        < 0.000001
    )

    availability_valid = (
        integrated_results[
            "availability_restricted"
        ]["feasibility"]
        == "FEASIBLE"
        and
        integrated_results[
            "availability_restricted"
        ]["objective_value"]
        == 16.0
        and
        abs(
            integrated_results[
                "availability_restricted"
            ]["mad"]
            - 2.6666666666666665
        )
        < 0.000001
    )

    qualification_valid = (
        integrated_results[
            "qualification_restricted"
        ]["feasibility"]
        == "INFEASIBLE"
        and
        integrated_results[
            "qualification_restricted"
        ]["schedule_entries"]
        == 0
        and
        integrated_results[
            "qualification_restricted"
        ]["mad"]
        is None
    )

    print("========================================")
    print("VALIDATION")
    print("========================================")

    if baseline_valid:
        print(
            "[PASS] Baseline results validated."
        )
    else:
        print(
            "[FAIL] Baseline results are inconsistent."
        )

    if availability_valid:
        print(
            "[PASS] Availability-restricted results validated."
        )
    else:
        print(
            "[FAIL] Availability-restricted results are inconsistent."
        )

    if qualification_valid:
        print(
            "[PASS] Qualification-restricted results validated."
        )
    else:
        print(
            "[FAIL] Qualification-restricted results are inconsistent."
        )

    if (
        baseline_valid
        and availability_valid
        and qualification_valid
    ):
        print()
        print(
            "[PASS] Sprint 3.5 experimental integration "
            "completed successfully."
        )
    else:
        print()
        print(
            "[FAIL] Sprint 3.5 validation failed."
        )

    print()
    print("========================================")
    print("SPRINT 3.5 TEST COMPLETE")
    print("========================================")