from app import create_app
from services.workload import (
    calculate_teacher_workloads,
    calculate_absolute_deviations,
    calculate_mad,
    calculate_workload_report,
)


app = create_app()


with app.app_context():

    print()
    print("========================================")
    print("SPRINT 3.1 - WORKLOAD AND MAD TEST")
    print("========================================")
    print()

    # ---------------------------------------------------------
    # TEST 1 - WORKLOAD CALCULATION
    # ---------------------------------------------------------

    print("TEST 1: Teacher Workloads")
    print("----------------------------------------")

    workloads = calculate_teacher_workloads()

    if workloads:
        print("[PASS] Teacher workloads were calculated.")

        for teacher_id, workload in workloads.items():
            print(
                f"Teacher ID {teacher_id}: "
                f"{workload} periods"
            )

    else:
        print("[FAIL] No teacher workloads were calculated.")

    print()

    # ---------------------------------------------------------
    # TEST 2 - ABSOLUTE DEVIATIONS
    # ---------------------------------------------------------

    print("TEST 2: Absolute Deviations")
    print("----------------------------------------")

    deviations = calculate_absolute_deviations(
        workloads,
        target=6,
    )

    if deviations:
        print("[PASS] Absolute deviations were calculated.")

        for teacher_id, deviation in deviations.items():
            print(
                f"Teacher ID {teacher_id}: "
                f"deviation = {deviation}"
            )

    else:
        print("[FAIL] No deviations were calculated.")

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

    print(f"Target workload: 6")
    print(f"MAD:             {mad}")

    if mad >= 0:
        print("[PASS] MAD was calculated successfully.")

    else:
        print("[FAIL] MAD calculation produced an invalid value.")

    print()

    # ---------------------------------------------------------
    # TEST 4 - COMPLETE REPORT
    # ---------------------------------------------------------

    print("TEST 4: Complete Workload Report")
    print("----------------------------------------")

    report = calculate_workload_report(
        target=6,
    )

    print(
        f"Target workload: "
        f"{report['target']}"
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

    print()

    print(
        f"Overall MAD: "
        f"{report['mad']}"
    )

    print()

    if (
        "teachers" in report
        and "mad" in report
    ):
        print(
            "[PASS] Complete workload report "
            "was generated."
        )
    else:
        print(
            "[FAIL] Workload report is incomplete."
        )

    print()

    print("========================================")
    print("SPRINT 3.1 TEST COMPLETE")
    print("========================================")