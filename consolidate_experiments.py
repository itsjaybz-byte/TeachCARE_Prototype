import json
from pathlib import Path


BASELINE_FILE = Path("experiment_results.json")
EXPERIMENT_2_FILE = Path("experiment_2_results.json")
EXPERIMENT_3_FILE = Path("experiment_3_results.json")

OUTPUT_FILE = Path("research_experiment_results.json")


def load_result(filename):
    if not filename.exists():
        raise FileNotFoundError(
            f"Required experiment result not found: {filename}"
        )

    with filename.open("r", encoding="utf-8") as file:
        return json.load(file)


baseline = load_result(BASELINE_FILE)
experiment_2 = load_result(EXPERIMENT_2_FILE)
experiment_3 = load_result(EXPERIMENT_3_FILE)


baseline_objective = baseline.get("objective_value")


def objective_change(result):
    objective = result.get("objective_value")

    if (
        baseline_objective is None
        or objective is None
    ):
        return None

    return objective - baseline_objective


def classify_status(result):
    status = result.get("solver_status")

    if status == "OPTIMAL":
        return "FEASIBLE"

    if status == "INFEASIBLE":
        return "INFEASIBLE"

    return "UNKNOWN"


experiments = [
    {
        "experiment_id": "EXP-01",
        "name": "Baseline Feasible Scenario",
        "scenario": baseline.get("scenario"),
        "solver_status": baseline.get("solver_status"),
        "feasibility": classify_status(baseline),
        "schedule_entries": baseline.get("schedule_entries"),
        "objective_value": baseline.get("objective_value"),
        "objective_change_from_baseline": 0,
        "message": baseline.get("message"),
    },

    {
        "experiment_id": "EXP-02",
        "name": "Availability-Restricted Scenario",
        "scenario": experiment_2.get("scenario"),
        "solver_status": experiment_2.get("solver_status"),
        "feasibility": classify_status(experiment_2),
        "schedule_entries": experiment_2.get("schedule_entries"),
        "objective_value": experiment_2.get("objective_value"),
        "objective_change_from_baseline": objective_change(
            experiment_2
        ),
        "restricted_teacher": experiment_2.get(
            "restricted_teacher"
        ),
        "restricted_teacher_name": experiment_2.get(
            "restricted_teacher_name"
        ),
        "message": experiment_2.get("message"),
    },

    {
        "experiment_id": "EXP-03",
        "name": "Qualification-Restricted Scenario",
        "scenario": experiment_3.get("scenario"),
        "solver_status": experiment_3.get("solver_status"),
        "feasibility": classify_status(experiment_3),
        "schedule_entries": experiment_3.get("schedule_entries"),
        "objective_value": experiment_3.get("objective_value"),
        "objective_change_from_baseline": objective_change(
            experiment_3
        ),
        "restricted_teacher": experiment_3.get(
            "restricted_teacher"
        ),
        "restricted_teacher_name": experiment_3.get(
            "restricted_teacher_name"
        ),
        "removed_qualification": experiment_3.get(
            "removed_qualification"
        ),
        "message": experiment_3.get("message"),
    },
]


consolidated_results = {
    "project": "TeachCARE Prototype",
    "purpose": (
        "Initial experimental dataset for evaluating "
        "teacher workload scheduling under controlled "
        "constraint changes."
    ),
    "baseline_objective_value": baseline_objective,
    "experiments": experiments,
}


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        consolidated_results,
        file,
        indent=4,
    )


print()
print("========================================")
print("SPRINT 2.13 - RESULTS CONSOLIDATION")
print("========================================")
print()

for experiment in experiments:

    print(
        f"{experiment['experiment_id']}: "
        f"{experiment['name']}"
    )

    print(
        f"  Feasibility:       "
        f"{experiment['feasibility']}"
    )

    print(
        f"  Solver status:     "
        f"{experiment['solver_status']}"
    )

    print(
        f"  Schedule entries:  "
        f"{experiment['schedule_entries']}"
    )

    print(
        f"  Objective value:   "
        f"{experiment['objective_value']}"
    )

    print(
        f"  Change from base:  "
        f"{experiment['objective_change_from_baseline']}"
    )

    print()


print("========================================")
print("SUMMARY")
print("========================================")

print(
    f"Baseline objective: "
    f"{baseline_objective}"
)

print(
    f"Results saved to:   "
    f"{OUTPUT_FILE}"
)

print()
print("[PASS] Experiments 1-3 consolidated.")
print("[OK] Initial research dataset preserved.")
print()