from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from sqlalchemy.exc import IntegrityError

from config import Config
from extensions import db, migrate

from models import (
    Teacher,
    Qualification,
    CurriculumRequirement,
    ScheduleEntry,
    TeacherAvailability,
    SchedulePeriod,
    Section,
    Subject,
)

from services.optimizer import (
    generate_schedule,
    teacher_is_qualified,
    teacher_meets_educational_attainment,
    teacher_is_level_eligible,
)
from services.validator import validate_schedule
from services.workload import calculate_workload_report

def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # =========================================================
    # DASHBOARD
    # =========================================================

    @app.route("/")
    def index():

        return render_template(
            "index.html",

            teacher_count=Teacher.query.count(),

            section_count=Section.query.count(),

            subject_count=Subject.query.count(),

            requirement_count=(
                CurriculumRequirement.query.count()
            ),

            schedule_count=(
                ScheduleEntry.query.count()
            ),
        )

    # =========================================================
    # MANAGE DATA
    # =========================================================

    @app.route("/manage")
    def manage_data():

        return render_template(
            "manage.html"
        )

    # =========================================================
    # TEACHERS - LIST
    # =========================================================

    @app.route("/teachers")
    def teachers():

        return render_template(
            "teachers.html",
            teachers=(
                Teacher.query
                .order_by(Teacher.name)
                .all()
            ),
        )

    # =========================================================
    # TEACHERS - CREATE
    # =========================================================

    @app.route(
        "/teachers/new",
        methods=["GET", "POST"],
    )
    def create_teacher():

        qualifications = (
            Qualification.query
            .order_by(Qualification.name)
            .all()
        )

        if request.method == "POST":

            employee_id = (
                request.form.get(
                    "employee_id",
                    "",
                )
                .strip()
            )

            name = (
                request.form.get(
                    "name",
                    "",
                )
                .strip()
            )

            major = (
                request.form.get(
                    "major",
                    "",
                )
                .strip()
            )

            educational_attainment = (
                request.form.get(
                    "educational_attainment",
                    "",
                )
                .strip()
            )

            jhs_eligible = (
                request.form.get(
                    "jhs_eligible"
                )
                == "on"
            )

            shs_eligible = (
                request.form.get(
                    "shs_eligible"
                )
                == "on"
            )

            qualification_ids = (
                request.form.getlist(
                    "qualifications"
                )
            )

            # -------------------------------------------------
            # Basic validation
            # -------------------------------------------------

            errors = []

            if not employee_id:
                errors.append(
                    "Employee ID is required."
                )

            if not name:
                errors.append(
                    "Teacher name is required."
                )

            if not major:
                errors.append(
                    "Major / specialization is required."
                )

            if not educational_attainment:
                errors.append(
                    "Educational attainment is required."
                )

            if errors:

                for error in errors:
                    flash(
                        error,
                        "danger",
                    )

                return render_template(
                    "teacher_form.html",
                    teacher=None,
                    qualifications=qualifications,
                )

            # -------------------------------------------------
            # Build teacher
            # -------------------------------------------------

            teacher = Teacher(
                employee_id=employee_id,
                name=name,
                major=major,
                educational_attainment=(
                    educational_attainment
                ),
                jhs_eligible=jhs_eligible,
                shs_eligible=shs_eligible,
            )

            teacher.qualifications = (
                Qualification.query
                .filter(
                    Qualification.id.in_(
                        qualification_ids
                    )
                )
                .all()
                if qualification_ids
                else []
            )

            db.session.add(teacher)

            try:

                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "A teacher with that Employee ID "
                    "already exists.",
                    "danger",
                )

                return render_template(
                    "teacher_form.html",
                    teacher=teacher,
                    qualifications=qualifications,
                )

            flash(
                f"Teacher {teacher.name} was added successfully.",
                "success",
            )

            return redirect(
                url_for("teachers")
            )

        return render_template(
            "teacher_form.html",
            teacher=None,
            qualifications=qualifications,
        )

    # =========================================================
    # TEACHERS - EDIT
    # =========================================================

    @app.route(
        "/teachers/<int:teacher_id>/edit",
        methods=["GET", "POST"],
    )
    def edit_teacher(
        teacher_id,
    ):

        teacher = Teacher.query.get_or_404(
            teacher_id
        )

        qualifications = (
            Qualification.query
            .order_by(Qualification.name)
            .all()
        )

        if request.method == "POST":

            employee_id = (
                request.form.get(
                    "employee_id",
                    "",
                )
                .strip()
            )

            name = (
                request.form.get(
                    "name",
                    "",
                )
                .strip()
            )

            major = (
                request.form.get(
                    "major",
                    "",
                )
                .strip()
            )

            educational_attainment = (
                request.form.get(
                    "educational_attainment",
                    "",
                )
                .strip()
            )

            jhs_eligible = (
                request.form.get(
                    "jhs_eligible"
                )
                == "on"
            )

            shs_eligible = (
                request.form.get(
                    "shs_eligible"
                )
                == "on"
            )

            qualification_ids = (
                request.form.getlist(
                    "qualifications"
                )
            )

            # -------------------------------------------------
            # Basic validation
            # -------------------------------------------------

            errors = []

            if not employee_id:
                errors.append(
                    "Employee ID is required."
                )

            if not name:
                errors.append(
                    "Teacher name is required."
                )

            if not major:
                errors.append(
                    "Major / specialization is required."
                )

            if not educational_attainment:
                errors.append(
                    "Educational attainment is required."
                )

            if errors:

                for error in errors:
                    flash(
                        error,
                        "danger",
                    )

                return render_template(
                    "teacher_form.html",
                    teacher=teacher,
                    qualifications=qualifications,
                )

            # -------------------------------------------------
            # Update teacher
            # -------------------------------------------------

            teacher.employee_id = employee_id
            teacher.name = name
            teacher.major = major
            teacher.educational_attainment = (
                educational_attainment
            )
            teacher.jhs_eligible = jhs_eligible
            teacher.shs_eligible = shs_eligible

            teacher.qualifications = (
                Qualification.query
                .filter(
                    Qualification.id.in_(
                        qualification_ids
                    )
                )
                .all()
                if qualification_ids
                else []
            )

            try:

                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "Another teacher already uses "
                    "that Employee ID.",
                    "danger",
                )

                return render_template(
                    "teacher_form.html",
                    teacher=teacher,
                    qualifications=qualifications,
                )

            flash(
                f"Teacher {teacher.name} was updated successfully.",
                "success",
            )

            return redirect(
                url_for("teachers")
            )

        return render_template(
            "teacher_form.html",
            teacher=teacher,
            qualifications=qualifications,
        )

    # =========================================================
    # TEACHERS - DELETE
    # =========================================================

    @app.route(
        "/teachers/<int:teacher_id>/delete",
        methods=["POST"],
    )
    def delete_teacher(
        teacher_id,
    ):

        teacher = Teacher.query.get_or_404(
            teacher_id
        )

        teacher_name = teacher.name

        # -----------------------------------------------------
        # Remove generated schedule entries belonging to
        # this teacher.
        # -----------------------------------------------------

        ScheduleEntry.query.filter_by(
            teacher_id=teacher.id
        ).delete(
            synchronize_session=False
        )

        # -----------------------------------------------------
        # Remove availability records belonging to
        # this teacher.
        # -----------------------------------------------------

        TeacherAvailability.query.filter_by(
            teacher_id=teacher.id
        ).delete(
            synchronize_session=False
        )

        # -----------------------------------------------------
        # Clear qualification relationships.
        # -----------------------------------------------------

        teacher.qualifications = []

        db.session.delete(
            teacher
        )

        try:

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "The teacher could not be deleted because "
                "other database records still depend on it.",
                "danger",
            )

            return redirect(
                url_for("teachers")
            )

        flash(
            f"Teacher {teacher_name} was deleted.",
            "success",
        )

        return redirect(
            url_for("teachers")
        )

    # =========================================================
    # QUALIFICATIONS - LIST
    # =========================================================

    @app.route("/qualifications")
    def qualifications():

        qualification_records = (
            Qualification.query
            .order_by(Qualification.name)
            .all()
        )

        return render_template(
            "qualifications.html",
            qualifications=qualification_records,
        )

    # =========================================================
    # QUALIFICATIONS - CREATE
    # =========================================================

    @app.route(
        "/qualifications/new",
        methods=["GET", "POST"],
    )
    def create_qualification():

        if request.method == "POST":

            name = (
                request.form.get(
                    "name",
                    "",
                )
                .strip()
            )

            # -------------------------------------------------
            # Required field validation
            # -------------------------------------------------

            if not name:

                flash(
                    "Qualification name is required.",
                    "danger",
                )

                return render_template(
                    "qualification_form.html",
                    qualification=None,
                )

            # -------------------------------------------------
            # Duplicate validation
            # -------------------------------------------------

            existing = (
                Qualification.query
                .filter(
                    db.func.lower(
                        Qualification.name
                    ) == name.lower()
                )
                .first()
            )

            if existing:

                flash(
                    "A qualification with that name "
                    "already exists.",
                    "danger",
                )

                return render_template(
                    "qualification_form.html",
                    qualification=None,
                )

            qualification = Qualification(
                name=name
            )

            db.session.add(
                qualification
            )

            try:

                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "That qualification already exists.",
                    "danger",
                )

                return render_template(
                    "qualification_form.html",
                    qualification=None,
                )

            flash(
                f"Qualification '{name}' was added successfully.",
                "success",
            )

            return redirect(
                url_for("qualifications")
            )

        return render_template(
            "qualification_form.html",
            qualification=None,
        )

    # =========================================================
    # QUALIFICATIONS - EDIT
    # =========================================================

    @app.route(
        "/qualifications/<int:qualification_id>/edit",
        methods=["GET", "POST"],
    )
    def edit_qualification(
        qualification_id,
    ):

        qualification = (
            Qualification.query.get_or_404(
                qualification_id
            )
        )

        if request.method == "POST":

            name = (
                request.form.get(
                    "name",
                    "",
                )
                .strip()
            )

            # -------------------------------------------------
            # Required field validation
            # -------------------------------------------------

            if not name:

                flash(
                    "Qualification name is required.",
                    "danger",
                )

                return render_template(
                    "qualification_form.html",
                    qualification=qualification,
                )

            # -------------------------------------------------
            # Duplicate validation
            # -------------------------------------------------

            existing = (
                Qualification.query
                .filter(
                    db.func.lower(
                        Qualification.name
                    ) == name.lower(),
                    Qualification.id
                    != qualification.id,
                )
                .first()
            )

            if existing:

                flash(
                    "Another qualification already "
                    "uses that name.",
                    "danger",
                )

                return render_template(
                    "qualification_form.html",
                    qualification=qualification,
                )

            qualification.name = name

            try:

                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "That qualification name "
                    "already exists.",
                    "danger",
                )

                return render_template(
                    "qualification_form.html",
                    qualification=qualification,
                )

            flash(
                f"Qualification '{name}' was updated successfully.",
                "success",
            )

            return redirect(
                url_for("qualifications")
            )

        return render_template(
            "qualification_form.html",
            qualification=qualification,
        )

    # =========================================================
    # QUALIFICATIONS - DELETE
    # =========================================================

    @app.route(
        "/qualifications/<int:qualification_id>/delete",
        methods=["POST"],
    )
    def delete_qualification(
        qualification_id,
    ):

        qualification = (
            Qualification.query.get_or_404(
                qualification_id
            )
        )

        # -----------------------------------------------------
        # A qualification currently assigned to teachers
        # cannot be deleted.
        # -----------------------------------------------------

        teacher_count = len(
            qualification.teachers
        )

        # -----------------------------------------------------
        # A qualification required by a subject is a hard
        # scheduling dependency and cannot be deleted.
        # -----------------------------------------------------

        subject_count = len(
            qualification.subjects
        )

        if teacher_count > 0 or subject_count > 0:

            reasons = []

            if teacher_count > 0:

                reasons.append(
                    f"{teacher_count} teacher(s)"
                )

            if subject_count > 0:

                reasons.append(
                    f"{subject_count} subject(s)"
                )

            flash(
                "Cannot delete this qualification because "
                "it is currently used by "
                + " and ".join(reasons)
                + ".",
                "danger",
            )

            return redirect(
                url_for("qualifications")
            )

        qualification_name = (
            qualification.name
        )

        db.session.delete(
            qualification
        )

        try:

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "The qualification could not be deleted "
                "because it is still referenced by "
                "other records.",
                "danger",
            )

            return redirect(
                url_for("qualifications")
            )

        flash(
            f"Qualification '{qualification_name}' "
            "was deleted.",
            "success",
        )

        return redirect(
            url_for("qualifications")
        )

    # =========================================================
    # SECTIONS - LIST
    # =========================================================

    @app.route("/sections")
    def sections():

        section_records = (
            Section.query
            .order_by(
                Section.educational_level,
                Section.grade_level,
                Section.name,
            )
            .all()
        )

        return render_template(
            "sections.html",
            sections=section_records,
        )

    # =========================================================
    # SECTIONS - CREATE
    # =========================================================

    @app.route(
        "/sections/new",
        methods=["GET", "POST"],
    )
    def create_section():

        if request.method == "POST":

            name = (
                request.form.get(
                    "name",
                    "",
                )
                .strip()
            )

            grade_level = (
                request.form.get(
                    "grade_level",
                    "",
                )
                .strip()
            )

            educational_level = (
                request.form.get(
                    "educational_level",
                    "",
                )
                .strip()
                .upper()
            )

            strand = (
                request.form.get(
                    "strand",
                    "",
                )
                .strip()
            )

            errors = []

            if not name:
                errors.append(
                    "Section name is required."
                )

            if not grade_level:
                errors.append(
                    "Grade level is required."
                )

            if educational_level not in ("JHS", "SHS"):
                errors.append(
                    "Educational level must be JHS or SHS."
                )

            if educational_level == "JHS":
                strand = ""

            if errors:
                for error in errors:
                    flash(error, "danger")

                return render_template(
                    "section_form.html",
                    section=None,
                )

            existing = (
                Section.query
                .filter(
                    db.func.lower(
                        Section.name
                    ) == name.lower()
                )
                .first()
            )

            if existing:
                flash(
                    "A section with that name already exists.",
                    "danger",
                )

                return render_template(
                    "section_form.html",
                    section=None,
                )

            section = Section(
                name=name,
                grade_level=grade_level,
                educational_level=educational_level,
                strand=strand or None,
            )

            db.session.add(section)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

                flash(
                    "The section could not be added.",
                    "danger",
                )

                return render_template(
                    "section_form.html",
                    section=None,
                )

            flash(
                f"Section '{section.name}' was added successfully.",
                "success",
            )

            return redirect(
                url_for("sections")
            )

        return render_template(
            "section_form.html",
            section=None,
        )

    # =========================================================
    # SECTIONS - EDIT
    # =========================================================

    @app.route(
        "/sections/<int:section_id>/edit",
        methods=["GET", "POST"],
    )
    def edit_section(section_id):

        section = Section.query.get_or_404(
            section_id
        )

        if request.method == "POST":

            name = (
                request.form.get(
                    "name",
                    "",
                )
                .strip()
            )

            grade_level = (
                request.form.get(
                    "grade_level",
                    "",
                )
                .strip()
            )

            educational_level = (
                request.form.get(
                    "educational_level",
                    "",
                )
                .strip()
                .upper()
            )

            strand = (
                request.form.get(
                    "strand",
                    "",
                )
                .strip()
            )

            errors = []

            if not name:
                errors.append(
                    "Section name is required."
                )

            if not grade_level:
                errors.append(
                    "Grade level is required."
                )

            if educational_level not in ("JHS", "SHS"):
                errors.append(
                    "Educational level must be JHS or SHS."
                )

            if educational_level == "JHS":
                strand = ""

            if errors:
                for error in errors:
                    flash(error, "danger")

                return render_template(
                    "section_form.html",
                    section=section,
                )

            existing = (
                Section.query
                .filter(
                    db.func.lower(
                        Section.name
                    ) == name.lower(),
                    Section.id != section.id,
                )
                .first()
            )

            if existing:
                flash(
                    "Another section already uses that name.",
                    "danger",
                )

                return render_template(
                    "section_form.html",
                    section=section,
                )

            section.name = name
            section.grade_level = grade_level
            section.educational_level = educational_level
            section.strand = strand or None

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

                flash(
                    "The section could not be updated.",
                    "danger",
                )

                return render_template(
                    "section_form.html",
                    section=section,
                )

            flash(
                f"Section '{section.name}' was updated successfully.",
                "success",
            )

            return redirect(
                url_for("sections")
            )

        return render_template(
            "section_form.html",
            section=section,
        )

    # =========================================================
    # SECTIONS - DELETE
    # =========================================================

    @app.route(
        "/sections/<int:section_id>/delete",
        methods=["POST"],
    )
    def delete_section(section_id):

        section = Section.query.get_or_404(
            section_id
        )

        # Section deletion is protected because the Section
        # model cascades to curriculum requirements and
        # schedule entries.

        curriculum_count = len(
            section.curriculum_requirements
        )

        schedule_count = len(
            section.schedule_entries
        )

        if curriculum_count > 0 or schedule_count > 0:

            reasons = []

            if curriculum_count > 0:
                reasons.append(
                    f"{curriculum_count} curriculum requirement(s)"
                )

            if schedule_count > 0:
                reasons.append(
                    f"{schedule_count} schedule entr{'y' if schedule_count == 1 else 'ies'}"
                )

            flash(
                "Cannot delete this section because it is "
                "currently used by "
                + " and ".join(reasons)
                + ".",
                "danger",
            )

            return redirect(
                url_for("sections")
            )

        section_name = section.name

        db.session.delete(section)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

            flash(
                "The section could not be deleted because "
                "it is still referenced by other records.",
                "danger",
            )

            return redirect(
                url_for("sections")
            )

        flash(
            f"Section '{section_name}' was deleted.",
            "success",
        )

        return redirect(
            url_for("sections")
        )

    # =========================================================
    # SUBJECTS - LIST
    # =========================================================

    @app.route("/subjects")
    def subjects():

        subject_records = (
            Subject.query
            .order_by(Subject.name)
            .all()
        )

        return render_template(
            "subjects.html",
            subjects=subject_records,
        )

    # =========================================================
    # SUBJECTS - CREATE
    # =========================================================

    @app.route(
        "/subjects/new",
        methods=["GET", "POST"],
    )
    def create_subject():

        qualifications = (
            Qualification.query
            .order_by(Qualification.name)
            .all()
        )

        if request.method == "POST":

            name = (
                request.form.get(
                    "name",
                    "",
                )
                .strip()
            )

            qualification_id = (
                request.form.get(
                    "required_qualification_id",
                    "",
                )
                .strip()
            )

            errors = []

            if not name:
                errors.append(
                    "Subject name is required."
                )

            if not qualification_id:
                errors.append(
                    "A required qualification must be selected."
                )

            required_qualification = None

            if qualification_id:
                try:
                    required_qualification = (
                        Qualification.query.get(
                            int(qualification_id)
                        )
                    )
                except (TypeError, ValueError):
                    required_qualification = None

                if required_qualification is None:
                    errors.append(
                        "The selected qualification is invalid."
                    )

            if errors:

                for error in errors:
                    flash(error, "danger")

                return render_template(
                    "subject_form.html",
                    subject=None,
                    qualifications=qualifications,
                )

            existing = (
                Subject.query
                .filter(
                    db.func.lower(
                        Subject.name
                    ) == name.lower()
                )
                .first()
            )

            if existing:

                flash(
                    "A subject with that name already exists.",
                    "danger",
                )

                return render_template(
                    "subject_form.html",
                    subject=None,
                    qualifications=qualifications,
                )

            subject = Subject(
                name=name,
                required_qualification_id=(
                    required_qualification.id
                ),
            )

            db.session.add(subject)

            try:

                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "The subject could not be added.",
                    "danger",
                )

                return render_template(
                    "subject_form.html",
                    subject=None,
                    qualifications=qualifications,
                )

            flash(
                f"Subject '{subject.name}' was added successfully.",
                "success",
            )

            return redirect(
                url_for("subjects")
            )

        return render_template(
            "subject_form.html",
            subject=None,
            qualifications=qualifications,
        )

    # =========================================================
    # SUBJECTS - EDIT
    # =========================================================

    @app.route(
        "/subjects/<int:subject_id>/edit",
        methods=["GET", "POST"],
    )
    def edit_subject(subject_id):

        subject = Subject.query.get_or_404(
            subject_id
        )

        qualifications = (
            Qualification.query
            .order_by(Qualification.name)
            .all()
        )

        if request.method == "POST":

            name = (
                request.form.get(
                    "name",
                    "",
                )
                .strip()
            )

            qualification_id = (
                request.form.get(
                    "required_qualification_id",
                    "",
                )
                .strip()
            )

            errors = []

            if not name:
                errors.append(
                    "Subject name is required."
                )

            if not qualification_id:
                errors.append(
                    "A required qualification must be selected."
                )

            required_qualification = None

            if qualification_id:
                try:
                    required_qualification = (
                        Qualification.query.get(
                            int(qualification_id)
                        )
                    )
                except (TypeError, ValueError):
                    required_qualification = None

                if required_qualification is None:
                    errors.append(
                        "The selected qualification is invalid."
                    )

            if errors:

                for error in errors:
                    flash(error, "danger")

                return render_template(
                    "subject_form.html",
                    subject=subject,
                    qualifications=qualifications,
                )

            existing = (
                Subject.query
                .filter(
                    db.func.lower(
                        Subject.name
                    ) == name.lower(),
                    Subject.id != subject.id,
                )
                .first()
            )

            if existing:

                flash(
                    "Another subject already uses that name.",
                    "danger",
                )

                return render_template(
                    "subject_form.html",
                    subject=subject,
                    qualifications=qualifications,
                )

            subject.name = name
            subject.required_qualification_id = (
                required_qualification.id
            )

            try:

                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "The subject could not be updated.",
                    "danger",
                )

                return render_template(
                    "subject_form.html",
                    subject=subject,
                    qualifications=qualifications,
                )

            flash(
                f"Subject '{subject.name}' was updated successfully.",
                "success",
            )

            return redirect(
                url_for("subjects")
            )

        return render_template(
            "subject_form.html",
            subject=subject,
            qualifications=qualifications,
        )

    # =========================================================
    # SUBJECTS - DELETE
    # =========================================================

    @app.route(
        "/subjects/<int:subject_id>/delete",
        methods=["POST"],
    )
    def delete_subject(subject_id):

        subject = Subject.query.get_or_404(
            subject_id
        )

        curriculum_count = (
            CurriculumRequirement.query
            .filter_by(
                subject_id=subject.id
            )
            .count()
        )

        schedule_count = (
            ScheduleEntry.query
            .filter_by(
                subject_id=subject.id
            )
            .count()
        )

        if curriculum_count > 0 or schedule_count > 0:

            reasons = []

            if curriculum_count > 0:
                reasons.append(
                    f"{curriculum_count} curriculum requirement(s)"
                )

            if schedule_count > 0:
                reasons.append(
                    f"{schedule_count} schedule entr{'y' if schedule_count == 1 else 'ies'}"
                )

            flash(
                "Cannot delete this subject because it is "
                "currently used by "
                + " and ".join(reasons)
                + ".",
                "danger",
            )

            return redirect(
                url_for("subjects")
            )

        subject_name = subject.name

        db.session.delete(subject)

        try:

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "The subject could not be deleted because "
                "it is still referenced by other records.",
                "danger",
            )

            return redirect(
                url_for("subjects")
            )

        flash(
            f"Subject '{subject_name}' was deleted.",
            "success",
        )

        return redirect(
            url_for("subjects")
        )

    # =========================================================
    # TEACHER AVAILABILITY - LIST
    # =========================================================

    @app.route("/availability")
    def availability():

        availability_records = (
            TeacherAvailability.query
            .join(Teacher)
            .join(SchedulePeriod)
            .order_by(
                Teacher.id,
                SchedulePeriod.sequence,
            )
            .all()
        )

        return render_template(
            "availability.html",
            availability_records=availability_records,
        )

    # =========================================================
    # TEACHER AVAILABILITY - TOGGLE
    # =========================================================

    @app.route(
        "/availability/<int:availability_id>/toggle",
        methods=["POST"],
    )
    def toggle_availability(
        availability_id,
    ):

        availability_record = (
            TeacherAvailability.query.get_or_404(
                availability_id
            )
        )

        availability_record.available = (
            not availability_record.available
        )

        teacher_name = (
            availability_record.teacher.name
        )

        period_name = (
            f"{availability_record.schedule_period.day} "
            f"{availability_record.schedule_period.period}"
        )

        status = (
            "available"
            if availability_record.available
            else "unavailable"
        )

        try:

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "The teacher availability could not be updated.",
                "danger",
            )

            return redirect(
                url_for("availability")
            )

        flash(
            f"{teacher_name} is now {status} for {period_name}.",
            "success",
        )

        return redirect(
            url_for("availability")
        )

    # =========================================================
    # SCHEDULING PERIODS - LIST
    # =========================================================

    @app.route("/periods")
    def periods():

        period_records = (
            SchedulePeriod.query
            .order_by(
                SchedulePeriod.sequence
            )
            .all()
        )

        return render_template(
            "periods.html",
            periods=period_records,
        )

    # =========================================================
    # CURRICULUM
    # =========================================================

    @app.route("/curriculum")
    def curriculum():

        requirements = (
            CurriculumRequirement.query
            .order_by(
                CurriculumRequirement.section_id,
                CurriculumRequirement.subject_id,
            )
            .all()
        )

        return render_template(
            "curriculum.html",
            requirements=requirements,
        )

    # =========================================================
    # CURRICULUM - CREATE
    # =========================================================

    @app.route(
        "/curriculum/new",
        methods=["GET", "POST"],
    )
    def create_curriculum_requirement():

        sections = (
            Section.query
            .order_by(
                Section.educational_level,
                Section.grade_level,
                Section.name,
            )
            .all()
        )

        subjects = (
            Subject.query
            .order_by(Subject.name)
            .all()
        )

        if request.method == "POST":

            section_id = request.form.get(
                "section_id",
                type=int,
            )

            subject_id = request.form.get(
                "subject_id",
                type=int,
            )

            required_periods = request.form.get(
                "required_periods",
                type=int,
            )

            errors = []

            if section_id is None:
                errors.append(
                    "Section is required."
                )

            if subject_id is None:
                errors.append(
                    "Subject is required."
                )

            if required_periods is None:
                errors.append(
                    "Required periods is required."
                )
            elif required_periods <= 0:
                errors.append(
                    "Required periods must be a positive whole number."
                )

            section = (
                Section.query.get(section_id)
                if section_id is not None
                else None
            )

            if section_id is not None and section is None:
                errors.append(
                    "The selected section is invalid."
                )

            subject = (
                Subject.query.get(subject_id)
                if subject_id is not None
                else None
            )

            if subject_id is not None and subject is None:
                errors.append(
                    "The selected subject is invalid."
                )

            if errors:

                for error in errors:
                    flash(error, "danger")

                return render_template(
                    "curriculum_form.html",
                    sections=sections,
                    subjects=subjects,
                    requirement=None,
                )

            existing = (
                CurriculumRequirement.query
                .filter_by(
                    section_id=section.id,
                    subject_id=subject.id,
                )
                .first()
            )

            if existing:

                flash(
                    "A curriculum requirement for that section and subject already exists.",
                    "danger",
                )

                return render_template(
                    "curriculum_form.html",
                    sections=sections,
                    subjects=subjects,
                    requirement=None,
                )

            requirement = CurriculumRequirement(
                section_id=section.id,
                subject_id=subject.id,
                required_periods=required_periods,
            )

            db.session.add(requirement)

            try:
                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "A curriculum requirement for that section and subject already exists.",
                    "danger",
                )

                return render_template(
                    "curriculum_form.html",
                    sections=sections,
                    subjects=subjects,
                    requirement=None,
                )

            flash(
                "Curriculum requirement was added successfully.",
                "success",
            )

            return redirect(
                url_for("curriculum")
            )

        return render_template(
            "curriculum_form.html",
            sections=sections,
            subjects=subjects,
            requirement=None,
        )

    # =========================================================
    # CURRICULUM - EDIT
    # =========================================================

    @app.route(
        "/curriculum/<int:requirement_id>/edit",
        methods=["GET", "POST"],
    )
    def edit_curriculum_requirement(
        requirement_id,
    ):

        requirement = (
            CurriculumRequirement.query.get_or_404(
                requirement_id
            )
        )

        sections = (
            Section.query
            .order_by(
                Section.educational_level,
                Section.grade_level,
                Section.name,
            )
            .all()
        )

        subjects = (
            Subject.query
            .order_by(Subject.name)
            .all()
        )

        if request.method == "POST":

            section_id = request.form.get(
                "section_id",
                type=int,
            )

            subject_id = request.form.get(
                "subject_id",
                type=int,
            )

            required_periods = request.form.get(
                "required_periods",
                type=int,
            )

            errors = []

            if section_id is None:
                errors.append(
                    "Section is required."
                )

            if subject_id is None:
                errors.append(
                    "Subject is required."
                )

            if required_periods is None:
                errors.append(
                    "Required periods is required."
                )
            elif required_periods <= 0:
                errors.append(
                    "Required periods must be a positive whole number."
                )

            section = (
                Section.query.get(section_id)
                if section_id is not None
                else None
            )

            if section_id is not None and section is None:
                errors.append(
                    "The selected section is invalid."
                )

            subject = (
                Subject.query.get(subject_id)
                if subject_id is not None
                else None
            )

            if subject_id is not None and subject is None:
                errors.append(
                    "The selected subject is invalid."
                )

            if errors:

                for error in errors:
                    flash(error, "danger")

                return render_template(
                    "curriculum_form.html",
                    sections=sections,
                    subjects=subjects,
                    requirement=requirement,
                )

            existing = (
                CurriculumRequirement.query
                .filter(
                    CurriculumRequirement.section_id == section.id,
                    CurriculumRequirement.subject_id == subject.id,
                    CurriculumRequirement.id != requirement.id,
                )
                .first()
            )

            if existing:

                flash(
                    "A curriculum requirement for that section and subject already exists.",
                    "danger",
                )

                return render_template(
                    "curriculum_form.html",
                    sections=sections,
                    subjects=subjects,
                    requirement=requirement,
                )

            requirement.section_id = section.id
            requirement.subject_id = subject.id
            requirement.required_periods = required_periods

            try:
                db.session.commit()

            except IntegrityError:

                db.session.rollback()

                flash(
                    "The curriculum requirement could not be updated.",
                    "danger",
                )

                return render_template(
                    "curriculum_form.html",
                    sections=sections,
                    subjects=subjects,
                    requirement=requirement,
                )

            flash(
                "Curriculum requirement was updated successfully.",
                "success",
            )

            return redirect(
                url_for("curriculum")
            )

        return render_template(
            "curriculum_form.html",
            sections=sections,
            subjects=subjects,
            requirement=requirement,
        )

    # =========================================================
    # CURRICULUM - DELETE
    # =========================================================

    @app.route(
        "/curriculum/<int:requirement_id>/delete",
        methods=["POST"],
    )
    def delete_curriculum_requirement(
        requirement_id,
    ):

        requirement = (
            CurriculumRequirement.query.get_or_404(
                requirement_id
            )
        )

        # Do not remove a curriculum requirement that is already
        # represented by generated schedule entries for the same
        # section and subject.

        schedule_count = (
            ScheduleEntry.query
            .filter_by(
                section_id=requirement.section_id,
                subject_id=requirement.subject_id,
            )
            .count()
        )

        if schedule_count > 0:

            flash(
                "Cannot delete this curriculum requirement because it is "
                "currently used by "
                f"{schedule_count} schedule entr"
                + ("y." if schedule_count == 1 else "ies."),
                "danger",
            )

            return redirect(
                url_for("curriculum")
            )

        section_name = requirement.section.name
        subject_name = requirement.subject.name

        db.session.delete(requirement)

        try:
            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "The curriculum requirement could not be deleted because "
                "it is still referenced by other records.",
                "danger",
            )

            return redirect(
                url_for("curriculum")
            )

        flash(
            f"Curriculum requirement for {section_name} - "
            f"{subject_name} was deleted successfully.",
            "success",
        )

        return redirect(
            url_for("curriculum")
        )
        # =========================================================
    # ELIGIBILITY SCREENING SUMMARY
    # =========================================================

    def get_eligibility_summary():

        teachers = (
            Teacher.query
            .order_by(Teacher.id)
            .all()
        )

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

        total_possible = (
            len(teachers)
            * len(requirements)
            * len(periods)
        )

        qualification_pass = 0
        attainment_pass = 0
        level_pass = 0
        eligible_candidates = 0

        for requirement in requirements:

            for teacher in teachers:

                if not teacher_is_qualified(
                    teacher,
                    requirement.subject,
                ):
                    continue

                qualification_pass += len(periods)

                if not teacher_meets_educational_attainment(
                    teacher,
                    requirement.subject,
                ):
                    continue

                attainment_pass += len(periods)

                if not teacher_is_level_eligible(
                    teacher,
                    requirement.section,
                ):
                    continue

                level_pass += len(periods)

                for period in periods:

                    if availability.get(
                        (
                            teacher.id,
                            period.id,
                        ),
                        False,
                    ):

                        eligible_candidates += 1

        return {
            "teacher_count": len(teachers),
            "requirement_count": len(requirements),
            "period_count": len(periods),
            "total_possible": total_possible,
            "qualification_pass": qualification_pass,
            "attainment_pass": attainment_pass,
            "level_pass": level_pass,
            "eligible_candidates": eligible_candidates,
        }
        # =========================================================
    # GENERATE SCHEDULE
    # =========================================================

    @app.route(
        "/generate",
        methods=["GET", "POST"],
    )
    def generate():

        eligibility = get_eligibility_summary()

        if request.method == "POST":

            result = generate_schedule(db)

            if result["status"] == "OPTIMAL":

                flash(
                    result["message"],
                    "success",
                )

                return redirect(
                    url_for("schedule")
                )

            flash(
                result["message"],
                "danger",
            )

        return render_template(
            "generate.html",
            eligibility=eligibility,
        )

    # =========================================================
    # SCHEDULE
    # =========================================================

    @app.route("/schedule")
    def schedule():

        entries = (
            ScheduleEntry.query
            .order_by(
                ScheduleEntry.period_id,
                ScheduleEntry.section_id,
            )
            .all()
        )

        return render_template(
            "schedule.html",
            entries=entries,
        )

    # =========================================================
    # WORKLOAD
    # =========================================================

    @app.route("/workload")
    def workload():

        validation_result = validate_schedule()
        workload_report = calculate_workload_report()

        return render_template(
            "workload.html",
            validation=validation_result,
            report=workload_report,
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    @app.route("/validation")
    def validation():

        return render_template(
            "validation.html",
            result=validate_schedule(),
        )

    return app


app = create_app()


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        debug=True
    )