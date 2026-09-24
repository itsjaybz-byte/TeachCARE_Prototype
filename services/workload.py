from models import Teacher, ScheduleEntry


TARGET_WORKLOAD = 6


def calculate_teacher_workloads():
    """
    Calculate the current workload of every teacher.

    Workload is defined as the number of schedule entries
    assigned to the teacher.
    """

    teachers = Teacher.query.order_by(
        Teacher.id
    ).all()

    workloads = {}

    for teacher in teachers:
        workload = ScheduleEntry.query.filter_by(
            teacher_id=teacher.id
        ).count()

        workloads[teacher.id] = workload

    return workloads


def calculate_absolute_deviations(
    workloads,
    target=TARGET_WORKLOAD,
):
    """
    Calculate each teacher's absolute deviation
    from the target workload.

    D_t = |W_t - T|
    """

    deviations = {}

    for teacher_id, workload in workloads.items():
        deviations[teacher_id] = abs(
            workload - target
        )

    return deviations


def calculate_mad(
    workloads,
    target=TARGET_WORKLOAD,
):
    """
    Calculate Mean Absolute Deviation (MAD).

    MAD = (1 / N) * sum(|W_t - T|)

    Lower MAD indicates a more balanced workload
    distribution relative to the target.
    """

    if not workloads:
        return 0.0

    deviations = calculate_absolute_deviations(
        workloads,
        target,
    )

    return sum(
        deviations.values()
    ) / len(deviations)


def classify_workload(
    workload,
    target=TARGET_WORKLOAD,
):
    """
    Classify workload according to absolute deviation
    from the target.

    GREEN:
        Exact target workload.

    YELLOW:
        Deviation of 1 to 2 periods.

    RED:
        Deviation greater than 2 periods.
    """

    deviation = abs(
        workload - target
    )

    if deviation == 0:
        return "GREEN"

    if deviation <= 2:
        return "YELLOW"

    return "RED"


def calculate_workload_statistics(
    workloads,
):
    """
    Calculate summary workload statistics.
    """

    if not workloads:
        return {
            "teacher_count": 0,
            "total_workload": 0,
            "minimum_workload": 0,
            "maximum_workload": 0,
            "average_workload": 0.0,
        }

    workload_values = list(
        workloads.values()
    )

    return {
        "teacher_count": len(
            workload_values
        ),

        "total_workload": sum(
            workload_values
        ),

        "minimum_workload": min(
            workload_values
        ),

        "maximum_workload": max(
            workload_values
        ),

        "average_workload": (
            sum(workload_values)
            / len(workload_values)
        ),
    }


def calculate_workload_report(
    target=TARGET_WORKLOAD,
):
    """
    Generate a complete workload report.

    Returns:

        {
            "target": ...,
            "teachers": [...],
            "mad": ...,
            "teacher_count": ...,
            "total_workload": ...,
            "minimum_workload": ...,
            "maximum_workload": ...,
            "average_workload": ...
        }
    """

    workloads = calculate_teacher_workloads()

    deviations = calculate_absolute_deviations(
        workloads,
        target,
    )

    teachers = Teacher.query.order_by(
        Teacher.id
    ).all()

    teacher_results = []

    for teacher in teachers:

        workload = workloads.get(
            teacher.id,
            0,
        )

        deviation = deviations.get(
            teacher.id,
            0,
        )

        status = classify_workload(
            workload,
            target,
        )

        teacher_results.append(
            {
                "teacher_id": teacher.id,
                "employee_id": teacher.employee_id,
                "name": teacher.name,
                "workload": workload,
                "target": target,
                "absolute_deviation": deviation,
                "status": status,
            }
        )

    mad = calculate_mad(
        workloads,
        target,
    )

    statistics = calculate_workload_statistics(
        workloads
    )

    return {
        "target": target,
        "teachers": teacher_results,
        "mad": mad,

        "teacher_count": statistics[
            "teacher_count"
        ],

        "total_workload": statistics[
            "total_workload"
        ],

        "minimum_workload": statistics[
            "minimum_workload"
        ],

        "maximum_workload": statistics[
            "maximum_workload"
        ],

        "average_workload": statistics[
            "average_workload"
        ],
    }