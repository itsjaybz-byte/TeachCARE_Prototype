import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT,
)

from pulp import (
    LpBinary,
    LpMinimize,
    LpProblem,
    LpStatus,
    LpVariable,
    PULP_CBC_CMD,
    lpSum,
    value,
)

from app import create_app

from models import (
    Teacher,
    CurriculumRequirement,
    SchedulePeriod,
    TeacherAvailability,
)

from services.optimizer import (
    teacher_is_qualified,
    teacher_is_level_eligible,
    TARGET_HOURS,
)


def build_candidates(
    teachers,
    requirements,
    periods,
    availability,
):
    candidates = []

    for req in requirements:
        for teacher in teachers:

            if not teacher_is_qualified(
                teacher,
                req.subject,
            ):
                continue

            if not teacher_is_level_eligible(
                teacher,
                req.section,
            ):
                continue

            for period in periods:

                if not availability.get(
                    (teacher.id, period.id),
                    False,
                ):
                    continue

                candidates.append(
                    (
                        teacher.id,
                        req.id,
                        period.id,
                    )
                )

    return candidates


def build_model(
    teachers,
    requirements,
    periods,
    candidates,
    optimize_workload,
):
    model = LpProblem(
        "TeachCARE_Controlled_Comparison",
        LpMinimize,
    )

    x = {
        key: LpVariable(
            f"x_t{key[0]}_r{key[1]}_p{key[2]}",
            cat=LpBinary,
        )
        for key in candidates
    }

    workload = {
        teacher.id: LpVariable(
            f"workload_t{teacher.id}",
            lowBound=0,
        )
        for teacher in teachers
    }

    deviation = {
        teacher.id: LpVariable(
            f"deviation_t{teacher.id}",
            lowBound=0,
        )
        for teacher in teachers
    }

    # =========================================================
    # HARD CONSTRAINT 1 — CURRICULUM COVERAGE
    # =========================================================

    for req in requirements:

        vars_for_req = [
            x[(tid, rid, pid)]
            for tid, rid, pid in candidates
            if rid == req.id
        ]

        model += (
            lpSum(vars_for_req)
            == req.required_periods
        )

    # =========================================================
    # HARD CONSTRAINT 2 — TEACHER CONFLICT
    # =========================================================

    for teacher in teachers:

        for period in periods:

            vars_for_slot = [
                x[(tid, rid, pid)]
                for tid, rid, pid in candidates
                if tid == teacher.id
                and pid == period.id
            ]

            model += (
                lpSum(vars_for_slot) <= 1
            )

    # =========================================================
    # HARD CONSTRAINT 3 — SECTION CONFLICT
    # =========================================================

    section_ids = sorted(
        {
            req.section_id
            for req in requirements
        }
    )

    for section_id in section_ids:

        for period in periods:

            vars_for_slot = [
                x[(tid, rid, pid)]
                for tid, rid, pid in candidates
                for req in requirements
                if rid == req.id
                and req.section_id == section_id
                and pid == period.id
            ]

            model += (
                lpSum(vars_for_slot) <= 1
            )

    # =========================================================
    # WORKLOAD EQUATIONS
    # =========================================================

    for teacher in teachers:

        teacher_vars = [
            x[key]
            for key in x
            if key[0] == teacher.id
        ]

        model += (
            workload[teacher.id]
            == lpSum(teacher_vars)
        )

        model += (
            deviation[teacher.id]
            >= workload[teacher.id]
            - TARGET_HOURS
        )

        model += (
            deviation[teacher.id]
            >= TARGET_HOURS
            - workload[teacher.id]
        )

    # =========================================================
    # OBJECTIVE
    # =========================================================

    if optimize_workload:
        model += lpSum(
            deviation.values()
        )
    else:
        model += 0

    return model, x, workload


def solve_scenario(
    teachers,
    requirements,
    periods,
    candidates,
    optimize_workload,
):

    model, x, workload = build_model(
        teachers,
        requirements,
        periods,
        candidates,
        optimize_workload,
    )

    model.solve(
        PULP_CBC_CMD(msg=False)
    )

    status = LpStatus.get(
        model.status,
        "Unknown",
    )

    if status != "Optimal":
        return {
            "status": status,
        }

    workloads = {
        teacher.id: int(
            round(
                value(
                    workload[teacher.id]
                )
            )
        )
        for teacher in teachers
    }

    deviations = {
        teacher.id: abs(
            workloads[teacher.id]
            - TARGET_HOURS
        )
        for teacher in teachers
    }

    total_deviation = sum(
        deviations.values()
    )

    mad = (
        total_deviation
        / len(teachers)
        if teachers
        else 0
    )

    return {
        "status": status,
        "workloads": workloads,
        "deviations": deviations,
        "total_deviation": total_deviation,
        "mad": mad,
        "objective": value(
            model.objective
        ),
    }


def print_scenario(
    title,
    result,
    teachers,
):

    print()
    print("=" * 65)
    print(title)
    print("=" * 65)

    print(
        "Solver status:",
        result["status"],
    )

    if result["status"] != "Optimal":
        return

    print(
        "Total absolute deviation:",
        result["total_deviation"],
    )

    print(
        "MAD:",
        round(result["mad"], 4),
    )

    print()

    print(
        f"{'Teacher':25}"
        f"{'Workload':>10}"
        f"{'Deviation':>12}"
    )

    print("-" * 50)

    for teacher in teachers:

        print(
            f"{teacher.name:25}"
            f"{result['workloads'][teacher.id]:>10}"
            f"{result['deviations'][teacher.id]:>12}"
        )


def main():

    app = create_app()

    with app.app_context():

        teachers = (
            Teacher.query
            .order_by(Teacher.id)
            .all()
        )

        requirements = (
            CurriculumRequirement.query
            .order_by(
                CurriculumRequirement.id
            )
            .all()
        )

        periods = (
            SchedulePeriod.query
            .order_by(
                SchedulePeriod.sequence
            )
            .all()
        )

        availability_records = (
            TeacherAvailability.query
            .all()
        )

        availability = {
            (
                record.teacher_id,
                record.period_id,
            ): record.available
            for record in availability_records
        }

        candidates = build_candidates(
            teachers,
            requirements,
            periods,
            availability,
        )

        print()
        print(
            "TEACHCARE CONTROLLED "
            "OPTIMIZATION EXPERIMENT"
        )
        print("=" * 65)

        print(
            "Teachers:",
            len(teachers),
        )

        print(
            "Curriculum requirements:",
            len(requirements),
        )

        print(
            "Scheduling periods:",
            len(periods),
        )

        print(
            "Candidate assignments:",
            len(candidates),
        )

        feasible = solve_scenario(
            teachers,
            requirements,
            periods,
            candidates,
            optimize_workload=False,
        )

        optimized = solve_scenario(
            teachers,
            requirements,
            periods,
            candidates,
            optimize_workload=True,
        )

        print_scenario(
            "SCENARIO A — FEASIBILITY ONLY",
            feasible,
            teachers,
        )

        print_scenario(
            "SCENARIO B — WORKLOAD OPTIMIZED",
            optimized,
            teachers,
        )

        if (
            feasible["status"] == "Optimal"
            and optimized["status"] == "Optimal"
        ):

            improvement = (
                feasible["total_deviation"]
                - optimized["total_deviation"]
            )

            print()
            print("=" * 65)
            print("CONTROLLED COMPARISON")
            print("=" * 65)

            print(
                "Feasibility-only total deviation:",
                feasible["total_deviation"],
            )

            print(
                "Optimized total deviation:",
                optimized["total_deviation"],
            )

            print(
                "Feasibility-only MAD:",
                round(
                    feasible["mad"],
                    4,
                ),
            )

            print(
                "Optimized MAD:",
                round(
                    optimized["mad"],
                    4,
                ),
            )

            print(
                "Improvement in total deviation:",
                improvement,
            )

            if improvement > 0:

                print(
                    "RESULT: Workload optimization "
                    "improved the workload distribution."
                )

            elif improvement == 0:

                print(
                    "RESULT: Both scenarios have "
                    "the same workload deviation."
                )

            else:

                print(
                    "RESULT: Unexpected result — "
                    "inspect the experiment."
                )


if __name__ == "__main__":
    main()
