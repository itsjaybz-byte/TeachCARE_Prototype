import time

from app import create_app
from extensions import db
from services.optimizer import generate_schedule


app = create_app()

with app.app_context():

    print("=" * 60)
    print("TEACHCARE - COMPUTATIONAL RUNTIME TEST")
    print("=" * 60)

    # =========================================================
    # WARM-UP RUN
    # =========================================================

    print("\nWarm-up run...")
    generate_schedule(db)

    # =========================================================
    # RUNTIME MEASUREMENTS
    # =========================================================

    runtimes = []

    print("\nStarting runtime measurements...")

    for i in range(5):

        start_time = time.perf_counter()

        result = generate_schedule(db)

        end_time = time.perf_counter()

        runtime = end_time - start_time
        runtimes.append(runtime)

        print(f"\nRun {i + 1}")
        print(f"Solver status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Objective value: {result.get('objective_value')}")
        print(f"Runtime: {runtime:.6f} seconds")

    # =========================================================
    # RUNTIME STATISTICS
    # =========================================================

    average_runtime = sum(runtimes) / len(runtimes)
    minimum_runtime = min(runtimes)
    maximum_runtime = max(runtimes)

    # =========================================================
    # SUMMARY
    # =========================================================

    print("\n" + "=" * 60)
    print("RUNTIME SUMMARY")
    print("=" * 60)

    print(f"Runs: {len(runtimes)}")
    print(f"Average runtime: {average_runtime:.6f} seconds")
    print(f"Minimum runtime: {minimum_runtime:.6f} seconds")
    print(f"Maximum runtime: {maximum_runtime:.6f} seconds")

    print("=" * 60)