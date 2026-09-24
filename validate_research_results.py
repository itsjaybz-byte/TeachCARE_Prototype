import json


EXPERIMENT_FILE = "research_experiment_results.json"
WORKLOAD_FILE = "research_workload_results.json"
ANALYSIS_FILE = "research_comparative_analysis.json"


def load_json(filename):
    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


print()
print("========================================")
print("SPRINT 3.7 - RESEARCH RESULTS VALIDATION")
print("========================================")
print()


# ============================================================
# LOAD RESEARCH FILES
# ============================================================

try:
    experiment_results = load_json(
        EXPERIMENT_FILE
    )

    workload_results = load_json(
        WORKLOAD_FILE
    )

    analysis_results = load_json(
        ANALYSIS_FILE
    )

    print(
        "[PASS] All research result files were loaded."
    )

except FileNotFoundError as error:

    print(
        f"[FAIL] Required research file not found: "
        f"{error.filename}"
    )

    raise SystemExit(1)


# ============================================================
# EXTRACT RESULTS
# ============================================================

baseline = experiment_results["experiments"][0]
availability = experiment_results["experiments"][1]
qualification = experiment_results["experiments"][2]


baseline_workload = (
    workload_results[
        "baseline"
    ]
)

availability_workload = (
    workload_results[
        "availability_restricted"
    ]
)

qualification_workload = (
    workload_results[
        "qualification_restricted"
    ]
)


# ============================================================
# TEST 1 - EXPERIMENT COUNT
# ============================================================

print()
print("TEST 1: Experiment Count")
print("----------------------------------------")

experiment_count = len(
    experiment_results["experiments"]
)

print(
    f"Experiments found: {experiment_count}"
)

if experiment_count == 3:
    print(
        "[PASS] Three controlled experiments are present."
    )
else:
    print(
        "[FAIL] Expected exactly three experiments."
    )


# ============================================================
# TEST 2 - BASELINE CONSISTENCY
# ============================================================

print()
print("TEST 2: Baseline Consistency")
print("----------------------------------------")

baseline_objective_1 = baseline[
    "objective_value"
]

baseline_objective_2 = baseline_workload[
    "objective_value"
]

baseline_objective_3 = analysis_results[
    "baseline"
]["objective_value"]

baseline_mad_1 = baseline_workload[
    "mad"
]

baseline_mad_2 = analysis_results[
    "baseline"
]["mad"]

baseline_consistent = (
    baseline_objective_1
    == baseline_objective_2
    == baseline_objective_3
    and
    abs(
        baseline_mad_1
        - baseline_mad_2
    ) < 0.000001
)

print(
    f"Objective: {baseline_objective_1}"
)

print(
    f"MAD:       {baseline_mad_1}"
)

if baseline_consistent:
    print(
        "[PASS] Baseline results are consistent."
    )
else:
    print(
        "[FAIL] Baseline results are inconsistent."
    )


# ============================================================
# TEST 3 - OBJECTIVE/MAD RELATIONSHIP
# ============================================================

print()
print("TEST 3: Objective-MAD Relationship")
print("----------------------------------------")

teacher_count = workload_results[
    "current_baseline_workload"
]["teacher_count"]

expected_baseline_mad = (
    baseline_objective_1
    / teacher_count
)

expected_availability_mad = (
    availability[
        "objective_value"
    ]
    / teacher_count
)

actual_availability_mad = (
    availability_workload[
        "mad"
    ]
)

print(
    f"Teacher count:              "
    f"{teacher_count}"
)

print(
    f"Baseline objective:         "
    f"{baseline_objective_1}"
)

print(
    f"Expected baseline MAD:      "
    f"{expected_baseline_mad}"
)

print(
    f"Recorded baseline MAD:      "
    f"{baseline_mad_1}"
)

print()

print(
    f"Availability objective:     "
    f"{availability['objective_value']}"
)

print(
    f"Expected availability MAD:  "
    f"{expected_availability_mad}"
)

print(
    f"Recorded availability MAD:  "
    f"{actual_availability_mad}"
)

objective_mad_valid = (
    abs(
        expected_baseline_mad
        - baseline_mad_1
    ) < 0.000001
    and
    abs(
        expected_availability_mad
        - actual_availability_mad
    ) < 0.000001
)

if objective_mad_valid:
    print(
        "[PASS] Objective values are consistent "
        "with the reported MAD values."
    )
else:
    print(
        "[FAIL] Objective/MAD relationship is inconsistent."
    )


# ============================================================
# TEST 4 - AVAILABILITY RESTRICTION
# ============================================================

print()
print("TEST 4: Availability-Restricted Results")
print("----------------------------------------")

availability_objective = availability[
    "objective_value"
]

availability_mad = availability_workload[
    "mad"
]

objective_change = (
    availability_objective
    - baseline_objective_1
)

mad_change = (
    availability_mad
    - baseline_mad_1
)

expected_objective_change = 12.0
expected_mad_change = 2.0

print(
    f"Objective change: "
    f"{objective_change}"
)

print(
    f"MAD change:       "
    f"{mad_change}"
)

availability_valid = (
    availability[
        "feasibility"
    ]
    == "FEASIBLE"
    and
    availability_objective
    == 16.0
    and
    abs(
        objective_change
        - expected_objective_change
    ) < 0.000001
    and
    abs(
        mad_change
        - expected_mad_change
    ) < 0.000001
)

if availability_valid:
    print(
        "[PASS] Availability-restricted results "
        "are internally consistent."
    )
else:
    print(
        "[FAIL] Availability-restricted results "
        "are inconsistent."
    )


# ============================================================
# TEST 5 - QUALIFICATION RESTRICTION
# ============================================================

print()
print("TEST 5: Qualification-Restricted Results")
print("----------------------------------------")

print(
    f"Feasibility:      "
    f"{qualification['feasibility']}"
)

print(
    f"Solver status:    "
    f"{qualification['solver_status']}"
)

print(
    f"Schedule entries: "
    f"{qualification['schedule_entries']}"
)

print(
    f"MAD:              "
    f"{qualification_workload['mad']}"
)

qualification_valid = (
    qualification[
        "feasibility"
    ]
    == "INFEASIBLE"
    and
    qualification[
        "solver_status"
    ]
    == "INFEASIBLE"
    and
    qualification[
        "schedule_entries"
    ]
    == 0
    and
    qualification_workload[
        "mad"
    ] is None
)

if qualification_valid:
    print(
        "[PASS] Qualification-restricted results "
        "correctly represent infeasibility."
    )
else:
    print(
        "[FAIL] Qualification-restricted results "
        "are inconsistent."
    )


# ============================================================
# TEST 6 - COMPARATIVE ANALYSIS
# ============================================================

print()
print("TEST 6: Comparative Analysis")
print("----------------------------------------")

reported_mad_change = analysis_results[
    "availability_restricted"
]["mad_change"]

reported_mad_percentage = analysis_results[
    "availability_restricted"
]["mad_percentage_change"]

expected_mad_percentage = (
    mad_change
    / baseline_mad_1
) * 100

print(
    f"Reported MAD change: "
    f"{reported_mad_change}"
)

print(
    f"Expected MAD change: "
    f"{mad_change}"
)

print(
    f"Reported MAD increase: "
    f"{reported_mad_percentage:.2f}%"
)

print(
    f"Expected MAD increase: "
    f"{expected_mad_percentage:.2f}%"
)

comparative_valid = (
    abs(
        reported_mad_change
        - mad_change
    ) < 0.000001
    and
    abs(
        reported_mad_percentage
        - expected_mad_percentage
    ) < 0.000001
)

if comparative_valid:
    print(
        "[PASS] Comparative analysis is mathematically consistent."
    )
else:
    print(
        "[FAIL] Comparative analysis contains inconsistent metrics."
    )


# ============================================================
# FINAL VALIDATION
# ============================================================

all_tests_passed = (
    experiment_count == 3
    and baseline_consistent
    and objective_mad_valid
    and availability_valid
    and qualification_valid
    and comparative_valid
)


print()
print("========================================")
print("FINAL VALIDATION")
print("========================================")

if all_tests_passed:

    print(
        "[PASS] All research results are internally consistent."
    )

    print(
        "[PASS] Baseline, availability, and qualification "
        "experiments are correctly represented."
    )

    print(
        "[PASS] Objective values and MAD calculations agree."
    )

    print(
        "[PASS] Feasible and infeasible scenarios are "
        "properly distinguished."
    )

    print()
    print(
        "Sprint 3.7 research-results validation PASSED."
    )

else:

    print(
        "[FAIL] One or more research validation checks failed."
    )


print()
print("========================================")
print("SPRINT 3.7 TEST COMPLETE")
print("========================================")