import time

from app import create_app
from extensions import db

from models import (
    Teacher,
    Qualification,
    Section,
    Subject,
    CurriculumRequirement,
    SchedulePeriod,
    TeacherAvailability,
    ScheduleEntry,
)

from services.optimizer import generate_schedule


app = create_app()


# ============================================================
# SPRINT 2.11
# CONTROLLED SCALABILITY TEST CONFIGURATIONS
# ============================================================

SCENARIOS = [
    {
        "name": "Scale 1 - Small",
        "teachers": 10,
        "sections": 5,
        "subjects": 5,
        "periods": 15,
    },
    {
        "name": "Scale 2 - Medium",
        "teachers": 20,
        "sections": 8,
        "subjects": 6,
        "periods": 15,
    },
    {
        "name": "Scale 3 - Large",
        "teachers": 30,
        "sections": 12,
        "subjects": 7,
        "periods": 15,
    },
    {
        "name": "Scale 4 - Very Large",
        "teachers": 40,
        "sections": 16,
        "subjects": 8,
        "periods": 15,
    },
]


# Maximum amount of time allowed for one optimization run.
SOLVER_TIME_LIMIT = 30


# ============================================================
# CREATE CONTROLLED TEST DATASET
# ============================================================

def create_scenario(
    teacher_count,
    section_count,
    subject_count,
    period_count,
):

    # Clear the SQLAlchemy session before rebuilding
    # the database.
    db.session.remove()

    db.drop_all()
    db.create_all()

    # --------------------------------------------------------
    # QUALIFICATIONS
    # --------------------------------------------------------

    qualifications = []

    for i in range(subject_count):

        qualification = Qualification(
            name=f"Qualification {i + 1}"
        )

        qualifications.append(qualification)
        db.session.add(qualification)

    db.session.commit()

    # --------------------------------------------------------
    # TEACHERS
    # --------------------------------------------------------

    teachers = []

    for i in range(teacher_count):

        qualification = qualifications[i % subject_count]

        teacher = Teacher(
            employee_id=f"SC-T{i + 1:03d}",
            name=f"Scalability Teacher {i + 1}",
            major=qualification.name,
            educational_attainment="Bachelor's Degree",
            jhs_eligible=True,
            shs_eligible=True,
            qualifications=[qualification],
        )

        teachers.append(teacher)
        db.session.add(teacher)

    # --------------------------------------------------------
    # SECTIONS
    # --------------------------------------------------------

    sections = []

    for i in range(section_count):

        section = Section(
            name=f"SC-Section-{i + 1}",
            grade_level="Grade 7",
            educational_level="JHS",
        )

        sections.append(section)
        db.session.add(section)

    # --------------------------------------------------------
    # SUBJECTS
    # --------------------------------------------------------

    subjects = []

    for i in range(subject_count):

        subject = Subject(
            name=f"Subject {i + 1}",
            required_qualification=qualifications[i],
        )

        subjects.append(subject)
        db.session.add(subject)

    db.session.commit()

    # --------------------------------------------------------
    # SCHEDULE PERIODS
    # --------------------------------------------------------

    periods = []

    for i in range(period_count):

        day_number = (i // 3) + 1
        period_number = (i % 3) + 1

        schedule_period = SchedulePeriod(
            day=f"Day {day_number}",
            period=f"Period {period_number}",
            sequence=i + 1,
        )

        periods.append(schedule_period)
        db.session.add(schedule_period)

    db.session.commit()

    # --------------------------------------------------------
    # TEACHER AVAILABILITY
    # --------------------------------------------------------

    for teacher in teachers:

        for period in periods:

            db.session.add(
                TeacherAvailability(
                    teacher_id=teacher.id,
                    period_id=period.id,
                    available=True,
                )
            )

    db.session.commit()

    # --------------------------------------------------------
    # CURRICULUM REQUIREMENTS
    # --------------------------------------------------------

    for section in sections:

        for subject in subjects:

            db.session.add(
                CurriculumRequirement(
                    section_id=section.id,
                    subject_id=subject.id,
                    required_periods=2,
                )
            )

    db.session.commit()


# ============================================================
# CALCULATE MODEL SIZE
# ============================================================

def calculate_model_size():

    teachers = Teacher.query.all()
    requirements = CurriculumRequirement.query.all()
    periods = SchedulePeriod.query.all()

    candidate_count = 0

    for requirement in requirements:

        required_qualification = (
            requirement.subject
            .required_qualification
            .name
        )

        for teacher in teachers:

            if teacher.major == required_qualification:

                candidate_count += len(periods)

    # Binary assignment variables
    assignment_variables = candidate_count

    # Workload variables
    workload_variables = len(teachers)

    # Deviation variables
    deviation_variables = len(teachers)

    decision_variables = (
        assignment_variables
        + workload_variables
        + deviation_variables
    )

    # --------------------------------------------------------
    # CONSTRAINT COUNT
    # --------------------------------------------------------

    # One curriculum coverage constraint per requirement.
    curriculum_constraints = len(requirements)

    # One teacher-conflict constraint per teacher-period.
    teacher_conflict_constraints = (
        len(teachers) * len(periods)
    )

    # One section-conflict constraint per section-period.
    section_count = len(
        {
            requirement.section_id
            for requirement in requirements
        }
    )

    section_conflict_constraints = (
        section_count * len(periods)
    )

    # One workload equation per teacher.
    workload_constraints = len(teachers)

    # Two absolute-deviation constraints per teacher.
    deviation_constraints = len(teachers) * 2

    total_constraints = (
        curriculum_constraints
        + teacher_conflict_constraints
        + section_conflict_constraints
        + workload_constraints
        + deviation_constraints
    )

    return {
        "candidate_assignments": candidate_count,
        "decision_variables": decision_variables,
        "constraints": total_constraints,
    }


# ============================================================
# CALCULATE WORKLOAD AND MAD
# ============================================================

def calculate_workload_statistics():

    TARGET_HOURS = 6

    teachers = Teacher.query.all()

    workloads = []

    for teacher in teachers:

        workload = ScheduleEntry.query.filter_by(
            teacher_id=teacher.id
        ).count()

        workloads.append(workload)

    if not workloads:

        return {
            "min_workload": 0,
            "max_workload": 0,
            "average_workload": 0,
            "mad": 0,
        }

    average_workload = (
        sum(workloads) / len(workloads)
    )

    mad = (
        sum(
            abs(workload - TARGET_HOURS)
            for workload in workloads
        )
        / len(workloads)
    )

    return {
        "min_workload": min(workloads),
        "max_workload": max(workloads),
        "average_workload": average_workload,
        "mad": mad,
    }


# ============================================================
# RUN SCALABILITY EXPERIMENT
# ============================================================

with app.app_context():

    print()
    print("========================================")
    print("SPRINT 2.11 - SCALABILITY TEST")
    print("========================================")
    print()

    print(
        f"Solver time limit per scenario: "
        f"{SOLVER_TIME_LIMIT} seconds"
    )

    print()

    results = []

    for scenario in SCENARIOS:

        print("----------------------------------------")
        print(scenario["name"])
        print("----------------------------------------")

        print(
            f"Teachers:  {scenario['teachers']}"
        )

        print(
            f"Sections:  {scenario['sections']}"
        )

        print(
            f"Subjects:  {scenario['subjects']}"
        )

        print(
            f"Periods:   {scenario['periods']}"
        )

        # ----------------------------------------------------
        # CREATE DATASET
        # ----------------------------------------------------

        create_scenario(
            teacher_count=scenario["teachers"],
            section_count=scenario["sections"],
            subject_count=scenario["subjects"],
            period_count=scenario["periods"],
        )

        # ----------------------------------------------------
        # MODEL SIZE
        # ----------------------------------------------------

        model_size = calculate_model_size()

        # ----------------------------------------------------
        # RUN OPTIMIZER
        # ----------------------------------------------------

        print()
        print("Running optimizer...")

        start_time = time.perf_counter()

        result = generate_schedule(db)

        end_time = time.perf_counter()

        elapsed_time = (
            end_time - start_time
        )

        # ----------------------------------------------------
        # WORKLOAD STATISTICS
        # ----------------------------------------------------

        workload_stats = (
            calculate_workload_statistics()
        )

        # ----------------------------------------------------
        # DATABASE COUNTS
        # ----------------------------------------------------

        requirement_count = (
            CurriculumRequirement.query.count()
        )

        availability_count = (
            TeacherAvailability.query.count()
        )

        schedule_entry_count = (
            ScheduleEntry.query.count()
        )

        # ----------------------------------------------------
        # RESULT STATUS
        # ----------------------------------------------------

        solver_status = result.get("status")

        if elapsed_time >= SOLVER_TIME_LIMIT:

            recorded_status = "TIME_LIMIT"

        else:

            recorded_status = solver_status

        # ----------------------------------------------------
        # STORE RESULTS
        # ----------------------------------------------------

        results.append(
            {
                "name": scenario["name"],
                "teachers": scenario["teachers"],
                "sections": scenario["sections"],
                "subjects": scenario["subjects"],
                "periods": scenario["periods"],
                "requirements": requirement_count,
                "availability": availability_count,
                "candidate_assignments": (
                    model_size["candidate_assignments"]
                ),
                "decision_variables": (
                    model_size["decision_variables"]
                ),
                "constraints": (
                    model_size["constraints"]
                ),
                "solver_status": recorded_status,
                "schedule_entries": schedule_entry_count,
                "execution_time": elapsed_time,
                "min_workload": (
                    workload_stats["min_workload"]
                ),
                "max_workload": (
                    workload_stats["max_workload"]
                ),
                "average_workload": (
                    workload_stats["average_workload"]
                ),
                "mad": workload_stats["mad"],
            }
        )

        # ----------------------------------------------------
        # DISPLAY RESULTS
        # ----------------------------------------------------

        print()
        print(
            f"Requirements:          "
            f"{requirement_count}"
        )

        print(
            f"Availability records:  "
            f"{availability_count}"
        )

        print(
            f"Candidate assignments: "
            f"{model_size['candidate_assignments']}"
        )

        print(
            f"Decision variables:    "
            f"{model_size['decision_variables']}"
        )

        print(
            f"Constraints:           "
            f"{model_size['constraints']}"
        )

        print(
            f"Solver status:         "
            f"{recorded_status}"
        )

        print(
            f"Schedule entries:      "
            f"{schedule_entry_count}"
        )

        print(
            f"Execution time:        "
            f"{elapsed_time:.4f} seconds"
        )

        print(
            f"Minimum workload:      "
            f"{workload_stats['min_workload']:.2f}"
        )

        print(
            f"Maximum workload:      "
            f"{workload_stats['max_workload']:.2f}"
        )

        print(
            f"Average workload:      "
            f"{workload_stats['average_workload']:.2f}"
        )

        print(
            f"MAD from target:       "
            f"{workload_stats['mad']:.4f}"
        )

        print()

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("========================================")
    print("SCALABILITY EXPERIMENT SUMMARY")
    print("========================================")
    print()

    print(
        "Scale | Teachers | Sections | Subjects | "
        "Requirements | Variables | Constraints | "
        "Runtime | Status | MAD"
    )

    print("-" * 115)

    for result in results:

        print(
            f"{result['name']} | "
            f"{result['teachers']} | "
            f"{result['sections']} | "
            f"{result['subjects']} | "
            f"{result['requirements']} | "
            f"{result['decision_variables']} | "
            f"{result['constraints']} | "
            f"{result['execution_time']:.4f}s | "
            f"{result['solver_status']} | "
            f"{result['mad']:.4f}"
        )

    print()

    print("========================================")
    print("SPRINT 2.11 EXPERIMENT COMPLETE")
    print("========================================")