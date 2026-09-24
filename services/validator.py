from collections import Counter

from models import (
    ScheduleEntry,
    CurriculumRequirement,
    Teacher,
    TeacherAvailability,
)

from services.optimizer import (
    teacher_is_qualified,
    teacher_meets_educational_attainment,
    teacher_is_level_eligible,
)

from services.workload import (
    calculate_workload_report,
)


def validate_schedule():

    entries = ScheduleEntry.query.all()

    requirements = CurriculumRequirement.query.all()

    errors = []
    warnings = []


    # =========================================================
    # CURRICULUM COVERAGE
    # =========================================================

    actual = Counter(
        (e.section_id, e.subject_id)
        for e in entries
    )

    for req in requirements:

        count = actual[
            (req.section_id, req.subject_id)
        ]

        if count != req.required_periods:

            errors.append(
                f"Curriculum coverage error: "
                f"section {req.section.name}, "
                f"subject {req.subject.name}: "
                f"required {req.required_periods}, "
                f"found {count}."
            )


    # =========================================================
    # TEACHER QUALIFICATION AND LEVEL ELIGIBILITY
    # =========================================================

    for e in entries:

        if not teacher_is_qualified(
            e.teacher,
            e.subject,
        ):

            errors.append(
                f"Qualification violation: "
                f"{e.teacher.name} is not qualified "
                f"for {e.subject.name}."
            )


        if not teacher_meets_educational_attainment(
            e.teacher,
            e.subject,
        ):

            errors.append(
                f"Educational-attainment violation: "
                f"{e.teacher.name} does not meet the "
                f"minimum educational attainment required "
                f"for {e.subject.name}."
            )


        if not teacher_is_level_eligible(
            e.teacher,
            e.section,
        ):

            errors.append(
                f"Educational-level eligibility violation: "
                f"{e.teacher.name} is not eligible "
                f"for {e.section.educational_level}."
            )


    # =========================================================
    # TEACHER SCHEDULE CONFLICTS
    # =========================================================

    teacher_slots = {}

    for e in entries:

        key = (
            e.teacher_id,
            e.period_id,
        )

        if key in teacher_slots:

            other = teacher_slots[key]

            errors.append(
                f"Teacher schedule conflict: "
                f"{e.teacher.name} is assigned to "
                f"{other.section.name} and "
                f"{e.section.name} during "
                f"{e.schedule_period.day} "
                f"{e.schedule_period.period}."
            )

        else:

            teacher_slots[key] = e


    # =========================================================
    # SECTION SCHEDULE CONFLICTS
    # =========================================================

    section_slots = {}

    for e in entries:

        key = (
            e.section_id,
            e.period_id,
        )

        if key in section_slots:

            other = section_slots[key]

            errors.append(
                f"Section schedule conflict: "
                f"{e.section.name} has "
                f"{other.subject.name} and "
                f"{e.subject.name} during "
                f"{e.schedule_period.day} "
                f"{e.schedule_period.period}."
            )

        else:

            section_slots[key] = e

        # =========================================================
    # TEACHER AVAILABILITY
    # =========================================================
    #
    # Independently verify that every generated schedule entry
    # uses a teacher-period combination marked as available.
    #
    # Missing availability records are treated as unavailable,
    # matching the optimizer's scheduling rule.
    # =========================================================

    availability_records = TeacherAvailability.query.all()

    availability = {
        (
            record.teacher_id,
            record.period_id,
        ): record.available
        for record in availability_records
    }

    for e in entries:

        is_available = availability.get(
            (
                e.teacher_id,
                e.period_id,
            ),
            False,
        )

        if not is_available:

            errors.append(
                f"Teacher availability violation: "
                f"{e.teacher.name} is assigned to "
                f"{e.section.name} during "
                f"{e.schedule_period.day} "
                f"{e.schedule_period.period}, "
                f"but the teacher is unavailable."
            )


    # =========================================================
    # WORKLOAD ASSESSMENT
    # =========================================================

    report = calculate_workload_report()
    


    # =========================================================
    # WORKLOAD OBSERVATIONS
    # =========================================================
    #
    # Workload imbalance is treated as an assessment/observation,
    # not as a hard scheduling violation.
    #
    # Therefore it does NOT make result["valid"] false.
    # =========================================================

    for teacher in report["teachers"]:

        if teacher["status"] == "YELLOW":

            warnings.append(
                f"{teacher['name']}: "
                f"{teacher['workload']} contact periods "
                f"(deviation of "
                f"{teacher['absolute_deviation']} "
                f"from target)."
            )

        elif teacher["status"] == "RED":

            warnings.append(
                f"{teacher['name']}: "
                f"{teacher['workload']} contact periods "
                f"(significantly unbalanced; "
                f"deviation of "
                f"{teacher['absolute_deviation']} "
                f"from target)."
            )


    # =========================================================
    # WORKLOAD MAPPING
    # =========================================================

    workload = {
        teacher["teacher_id"]: teacher["workload"]
        for teacher in report["teachers"]
    }


    # =========================================================
    # VALIDATION RESULT
    # =========================================================

    return {
        "valid": len(errors) == 0,

        "errors": errors,

        "warnings": warnings,

        "workload": workload,

        "report": report,
    }