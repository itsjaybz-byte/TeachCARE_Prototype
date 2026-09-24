import json


INPUT_FILE = "research_workload_results.json"
OUTPUT_FILE = "research_comparative_analysis.json"


def percentage_change(baseline, scenario):
    if baseline is None or scenario is None:
        return None

    if baseline == 0:
        return None

    return (
        (scenario - baseline)
        / baseline
    ) * 100


def calculate_range(minimum, maximum):
    if minimum is None or maximum is None:
        return None

    return maximum - minimum


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8",
) as file:
    results = json.load(file)


baseline = results["baseline"]

availability = results[
    "availability_restricted"
]

qualification = results[
    "qualification_restricted"
]

baseline_objective = baseline[
    "objective_value"
]

availability_objective = availability[
    "objective_value"
]

baseline_mad = baseline[
    "mad"
]

availability_mad = availability[
    "mad"
]


# ============================================================
# COMPARATIVE METRICS
# ============================================================

objective_change = (
    availability_objective
    - baseline_objective
)

objective_percentage = percentage_change(
    baseline_objective,
    availability_objective,
)

mad_change = (
    availability_mad
    - baseline_mad
)

mad_percentage = percentage_change(
    baseline_mad,
    availability_mad,
)


baseline_workload = results[
    "current_baseline_workload"
]

baseline_range = calculate_range(
    baseline_workload[
        "minimum_workload"
    ],
    baseline_workload[
        "maximum_workload"
    ],
)


# ============================================================
# INTERPRETATIONS
# ============================================================

baseline_interpretation = (
    "The baseline scenario produced a feasible "
    "schedule with relatively balanced teacher "
    "workloads around the six-period target."
)

availability_interpretation = (
    "Restricting teacher availability preserved "
    "feasibility but increased workload imbalance. "
    "The optimizer compensated for reduced scheduling "
    "flexibility by assigning a less balanced workload "
    "distribution."
)

qualification_interpretation = (
    "Removing the critical English qualification "
    "made the scheduling problem infeasible. "
    "Because no valid schedule exists, workload "
    "balance metrics are not applicable to this scenario."
)


# ============================================================
# BUILD RESEARCH ANALYSIS
# ============================================================

analysis = {

    "study": "TeachCARE",

    "analysis": (
        "Sprint 3.6 - Experimental Interpretation "
        "and Comparative Analysis"
    ),

    "baseline": {

        "feasibility": baseline[
            "feasibility"
        ],

        "objective_value": baseline_objective,

        "mad": baseline_mad,

        "workload_range": baseline_range,

        "interpretation":
            baseline_interpretation,
    },

    "availability_restricted": {

        "feasibility": availability[
            "feasibility"
        ],

        "objective_value":
            availability_objective,

        "mad":
            availability_mad,

        "objective_change":
            objective_change,

        "objective_percentage_change":
            objective_percentage,

        "mad_change":
            mad_change,

        "mad_percentage_change":
            mad_percentage,

        "interpretation":
            availability_interpretation,
    },

    "qualification_restricted": {

        "feasibility": qualification[
            "feasibility"
        ],

        "objective_value":
            qualification[
                "objective_value"
            ],

        "mad":
            qualification[
                "mad"
            ],

        "interpretation":
            qualification_interpretation,
    },

    "comparative_findings": {

        "availability_restriction":

            "Availability restriction increased "
            "the optimization objective from "
            "4.0 to 16.0 and increased MAD from "
            "0.6667 to 2.6667 while maintaining "
            "feasibility.",

        "qualification_restriction":

            "Qualification restriction eliminated "
            "feasibility because the required English "
            "instruction could no longer be assigned "
            "to a qualified teacher.",

        "overall":

            "The experiments demonstrate that the "
            "framework responds differently to "
            "different scheduling constraints. "
            "Availability constraints can reduce "
            "workload balance while preserving a "
            "feasible solution, whereas a critical "
            "qualification constraint can make the "
            "problem infeasible."
    },
}


# ============================================================
# DISPLAY
# ============================================================

print()
print("========================================")
print("SPRINT 3.6 - COMPARATIVE ANALYSIS")
print("========================================")
print()

print("BASELINE")
print("----------------------------------------")

print(
    f"Objective value:   "
    f"{baseline_objective}"
)

print(
    f"MAD:               "
    f"{baseline_mad}"
)

print(
    f"Workload range:    "
    f"{baseline_range}"
)

print()

print("AVAILABILITY-RESTRICTED")
print("----------------------------------------")

print(
    f"Objective value:   "
    f"{availability_objective}"
)

print(
    f"Objective change:  "
    f"{objective_change}"
)

print(
    f"Objective change %: "
    f"{objective_percentage:.2f}%"
)

print(
    f"MAD:               "
    f"{availability_mad}"
)

print(
    f"MAD change:        "
    f"{mad_change}"
)

print(
    f"MAD change %:      "
    f"{mad_percentage:.2f}%"
)

print()

print("QUALIFICATION-RESTRICTED")
print("----------------------------------------")

print(
    f"Feasibility:       "
    f"{qualification['feasibility']}"
)

print(
    f"Objective value:   "
    f"{qualification['objective_value']}"
)

print(
    f"MAD:               "
    f"{qualification['mad']}"
)

print()

print("========================================")
print("RESEARCH FINDINGS")
print("========================================")

print(
    analysis[
        "comparative_findings"
    ]["availability_restriction"]
)

print()

print(
    analysis[
        "comparative_findings"
    ]["qualification_restriction"]
)

print()

print(
    analysis[
        "comparative_findings"
    ]["overall"]
)

print()

# ============================================================
# SAVE RESULTS
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        analysis,
        file,
        indent=4,
    )

print(
    f"[OK] Comparative analysis saved to: "
    f"{OUTPUT_FILE}"
)

# ============================================================
# VALIDATION
# ============================================================

validation_passed = (
    baseline_mad is not None
    and availability_mad is not None
    and qualification[
        "mad"
    ] is None
    and abs(
        mad_change - 2.0
    ) < 0.000001
    and abs(
        mad_percentage - 300.0
    ) < 0.000001
    and qualification[
        "feasibility"
    ] == "INFEASIBLE"
)

print()

if validation_passed:
    print(
        "[PASS] Comparative analysis "
        "validated successfully."
    )
else:
    print(
        "[FAIL] Comparative analysis "
        "validation failed."
    )

print()
print("========================================")
print("SPRINT 3.6 TEST COMPLETE")
print("========================================")