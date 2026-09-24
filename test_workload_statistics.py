from app import create_app

from services.workload import (
    calculate_teacher_workloads,
    calculate_absolute_deviations,
    calculate_mad,
    calculate_workload_statistics,
    calculate_workload_report,
)


app = create_app()


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 3.4 - WORKLOAD STATISTICS TEST")
    print("========================================")
    print()

    # ---------------------------------------------------------
    # TEST 1 - WORKLOADS
    # ---------------------------------------------------------

    print("TEST 1: Teacher Workloads")
    print("----------------------------------------")

    workloads = calculate_teacher_workloads()

    if workloads:
        print(
            "[PASS] Teacher workloads were calculated."
        )

        for teacher_id, workload in workloads.items():
            print(
                f"Teacher ID {teacher_id}: "
                f"{workload} periods"
            )
    else:
        print(
            "[FAIL] No workloads were calculated."
        )

    print()

    # ---------------------------------------------------------
    # TEST 2 - DEVIATIONS
    # ---------------------------------------------------------

    print("TEST 2: Absolute Deviations")
    print("----------------------------------------")

    deviations = calculate_absolute_deviations(
        workloads,
        target=6,
    )

    print(
        f"Total absolute deviation: "
        f"{sum(deviations.values())}"
    )

    if deviations:
        print(
            "[PASS] Absolute deviations were calculated."
        )
    else:
        print(
            "[FAIL] Absolute deviations were not calculated."
        )

    print()

    # ---------------------------------------------------------
    # TEST 3 - MAD
    # ---------------------------------------------------------

    print("TEST 3: Mean Absolute Deviation")
    print("----------------------------------------")

    mad = calculate_mad(
        workloads,
        target=6,
    )

    print(
        f"Target workload: 6"
    )

    print(
        f"MAD:             {mad}"
    )

    if mad >= 0:
        print(
            "[PASS] MAD was calculated successfully."
        )
    else:
        print(
            "[FAIL] MAD calculation is invalid."
        )

    print()

    # ---------------------------------------------------------
    # TEST 4 - SUMMARY STATISTICS
    # ---------------------------------------------------------

    print("TEST 4: Workload Statistics")
    print("----------------------------------------")

    statistics = calculate_workload_statistics(
        workloads
    )

    print(
        f"Teacher count:       "
        f"{statistics['teacher_count']}"
    )

    print(
        f"Total workload:      "
        f"{statistics['total_workload']}"
    )

    print(
        f"Minimum workload:    "
        f"{statistics['minimum_workload']}"
    )

    print(
        f"Maximum workload:    "
        f"{statistics['maximum_workload']}"
    )

    print(
        f"Average workload:    "
        f"{statistics['average_workload']}"
    )

    expected_total = 40
    expected_minimum = 6
    expected_maximum = 8

    statistics_passed = (
        statistics["total_workload"]
        == expected_total
        and
        statistics["minimum_workload"]
        == expected_minimum
        and
        statistics["maximum_workload"]
        == expected_maximum
    )

    if statistics_passed:
        print(
            "[PASS] Workload statistics match "
            "the expected baseline values."
        )
    else:
        print(
            "[FAIL] Workload statistics do not "
            "match the expected baseline values."
        )

    print()

    # ---------------------------------------------------------
    # TEST 5 - COMPLETE REPORT
    # ---------------------------------------------------------

    print("TEST 5: Complete Workload Report")
    print("----------------------------------------")

    report = calculate_workload_report(
        target=6
    )

    print(
        f"Target workload:     "
        f"{report['target']}"
    )

    print(
        f"Teacher count:       "
        f"{report['teacher_count']}"
    )

    print(
        f"Total workload:      "
        f"{report['total_workload']}"
    )

    print(
        f"Minimum workload:    "
        f"{report['minimum_workload']}"
    )

    print(
        f"Maximum workload:    "
        f"{report['maximum_workload']}"
    )

    print(
        f"Average workload:    "
        f"{report['average_workload']}"
    )

    print(
        f"MAD:                 "
        f"{report['mad']}"
    )

    print()

    for teacher in report["teachers"]:

        print(
            f"{teacher['employee_id']} - "
            f"{teacher['name']}"
        )

        print(
            f"  Workload:           "
            f"{teacher['workload']}"
        )

        print(
            f"  Target:             "
            f"{teacher['target']}"
        )

        print(
            f"  Absolute deviation: "
            f"{teacher['absolute_deviation']}"
        )

        print(
            f"  Status:             "
            f"{teacher['status']}"
        )

    print()

    if (
        "teachers" in report
        and "mad" in report
        and "minimum_workload" in report
        and "maximum_workload" in report
        and "average_workload" in report
    ):
        print(
            "[PASS] Complete workload report "
            "contains all required statistics."
        )
    else:
        print(
            "[FAIL] Complete workload report "
            "is incomplete."
        )

    print()

    print("========================================")
    print("SPRINT 3.4 TEST COMPLETE")
    print("========================================")