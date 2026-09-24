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

from models import (
    Teacher,
    CurriculumRequirement,
    SchedulePeriod,
    ScheduleEntry,
    TeacherAvailability,
)


TARGET_HOURS = 6


def teacher_is_qualified(teacher, subject):
    required = subject.required_qualification.name.strip().lower()

    if teacher.major.strip().lower() == required:
        return True

    return any(
        q.name.strip().lower() == required
        for q in teacher.qualifications
    )


def teacher_meets_educational_attainment(teacher, subject):
    """
    Determine whether the teacher's educational attainment
    satisfies the minimum attainment required by the subject.

    The controlled prototype uses Bachelor's Degree as the
    minimum educational-attainment requirement.
    """

    required = (
        subject.minimum_educational_attainment
        .strip()
        .lower()
    )

    attainment = (
        teacher.educational_attainment
        .strip()
        .lower()
    )

    attainment_rank = {
        "high school": 1,
        "associate degree": 2,
        "bachelor's degree": 3,
        "master's degree": 4,
        "doctorate": 5,
    }

    teacher_rank = attainment_rank.get(
        attainment,
        0,
    )

    required_rank = attainment_rank.get(
        required,
        0,
    )

    return (
        teacher_rank >= required_rank
        and teacher_rank > 0
        and required_rank > 0
    )


def teacher_is_level_eligible(teacher, section):
    if section.educational_level == "JHS":
        return teacher.jhs_eligible

    if section.educational_level == "SHS":
        return teacher.shs_eligible

    return False


def generate_schedule(db):
    teachers = Teacher.query.order_by(Teacher.id).all()

    requirements = (
        CurriculumRequirement.query
        .order_by(CurriculumRequirement.id)
        .all()
    )

    periods = (
        SchedulePeriod.query
        .order_by(SchedulePeriod.sequence)
        .all()
    )

    if not teachers or not requirements or not periods:
        # -----------------------------------------------------
        # No scheduling data exists.
        #
        # Remove any previously generated schedule so that
        # stale records cannot be mistaken for the current
        # result.
        # -----------------------------------------------------

        ScheduleEntry.query.delete()
        db.session.commit()

        return {
            "status": "INFEASIBLE",
            "message": (
                "Teachers, curriculum requirements, "
                "and periods are required."
            ),
        }

    # ---------------------------------------------------------
    # Teacher availability lookup
    # ---------------------------------------------------------
    #
    # Maps:
    #
    # (teacher_id, period_id) -> True / False
    #
    # This allows the optimizer to quickly determine whether
    # a teacher can be assigned during a particular period.
    # ---------------------------------------------------------

    availability_records = TeacherAvailability.query.all()

    availability = {
        (record.teacher_id, record.period_id): record.available
        for record in availability_records
    }

    # ---------------------------------------------------------
    # Candidate assignment generation
    # ---------------------------------------------------------

    candidates = []

    for req in requirements:
        for teacher in teachers:

            # Teacher must be qualified for the subject.
            if not teacher_is_qualified(teacher, req.subject):
                continue

            # Teacher must satisfy the minimum educational
            # attainment required for the subject.
            if not teacher_meets_educational_attainment(
                teacher,
                req.subject,
            ):
                continue

            # Teacher must be eligible for the section's
            # educational level.
            if not teacher_is_level_eligible(
                teacher,
                req.section,
            ):
                continue

            for period in periods:

                # Teacher must be available during this period.
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

    if not candidates:
        # -----------------------------------------------------
        # No valid teacher-subject-section-period combination
        # exists.
        #
        # Clear the previous generated schedule because the
        # current scenario is infeasible.
        # -----------------------------------------------------

        ScheduleEntry.query.delete()
        db.session.commit()

        return {
            "status": "INFEASIBLE",
            "message": (
                "No teacher-subject-section-period "
                "assignments satisfy qualification, "
                "eligibility, and availability rules."
            ),
        }

    model = LpProblem(
        "TeachCARE_Workload_Management",
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
        t.id: LpVariable(
            f"workload_t{t.id}",
            lowBound=0,
        )
        for t in teachers
    }

    deviation = {
        t.id: LpVariable(
            f"deviation_t{t.id}",
            lowBound=0,
        )
        for t in teachers
    }

    # ---------------------------------------------------------
    # Curriculum coverage
    # ---------------------------------------------------------
    #
    # Each curriculum requirement must receive exactly the
    # number of periods specified by required_periods.
    # ---------------------------------------------------------

    for req in requirements:

        vars_for_req = [
            x[(tid, req.id, pid)]
            for tid, rid, pid in candidates
            if rid == req.id
        ]

        model += (
            lpSum(vars_for_req) == req.required_periods,
            f"coverage_req_{req.id}",
        )

    # ---------------------------------------------------------
    # Teacher conflict
    # ---------------------------------------------------------
    #
    # A teacher cannot teach two classes during the same
    # scheduling period.
    # ---------------------------------------------------------

    for teacher in teachers:
        for period in periods:

            vars_for_slot = [
                x[(tid, rid, pid)]
                for tid, rid, pid in candidates
                if tid == teacher.id
                and pid == period.id
            ]

            model += (
                lpSum(vars_for_slot) <= 1,
                f"teacher_conflict_t{teacher.id}_p{period.id}",
            )

    # ---------------------------------------------------------
    # Section conflict
    # ---------------------------------------------------------
    #
    # A section cannot receive two subjects during the same
    # scheduling period.
    # ---------------------------------------------------------

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
                lpSum(vars_for_slot) <= 1,
                f"section_conflict_s{section_id}_p{period.id}",
            )

    # ---------------------------------------------------------
    # Workload equation and absolute deviation
    # ---------------------------------------------------------
    #
    # Target workload = 6 hours/periods.
    # ---------------------------------------------------------

    for teacher in teachers:

        teacher_vars = [
            x[key]
            for key in x
            if key[0] == teacher.id
        ]

        model += (
            workload[teacher.id] == lpSum(teacher_vars),
            f"workload_t{teacher.id}",
        )

        model += (
            deviation[teacher.id]
            >= workload[teacher.id] - TARGET_HOURS
        )

        model += (
            deviation[teacher.id]
            >= TARGET_HOURS - workload[teacher.id]
        )

    # ---------------------------------------------------------
    # Objective
    # ---------------------------------------------------------
    #
    # Minimize total absolute workload deviation.
    # ---------------------------------------------------------

    model += (
        lpSum(deviation.values()),
        "minimize_total_workload_deviation",
    )

    model.solve(
        PULP_CBC_CMD(msg=False)
    )

    status = LpStatus.get(
        model.status,
        "Unknown",
    )

    # ---------------------------------------------------------
    # Infeasible / unsuccessful solver result
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # If the current scenario is infeasible, delete any
    # previously generated ScheduleEntry records.
    #
    # This prevents stale schedules from being displayed or
    # counted as though they belonged to the current scenario.
    # ---------------------------------------------------------

    if status != "Optimal":

        ScheduleEntry.query.delete()
        db.session.commit()

        return {
            "status": "INFEASIBLE",
            "message": (
                "No optimal feasible schedule was found. "
                f"Solver status: {status}."
            ),
        }

    # ---------------------------------------------------------
    # Replace previous generated schedule
    # ---------------------------------------------------------
    #
    # The current model is optimal, so it is safe to replace
    # the previous generated schedule with the new one.
    # ---------------------------------------------------------

    ScheduleEntry.query.delete()
    db.session.commit()

    created = []

    for (
        teacher_id,
        req_id,
        period_id,
    ), variable in x.items():

        if value(variable) == 1:

            req = db.session.get(
                CurriculumRequirement,
                req_id,
            )

            entry = ScheduleEntry(
                teacher_id=teacher_id,
                subject_id=req.subject_id,
                section_id=req.section_id,
                period_id=period_id,
            )

            db.session.add(entry)
            created.append(entry)

    db.session.commit()

    return {
        "status": "OPTIMAL",
        "message": (
            f"Generated {len(created)} schedule entries."
        ),
        "objective_value": value(model.objective),
    }