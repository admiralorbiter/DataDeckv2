from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional

from models import db
from models.district import District
from models.module import Module
from models.school import School
from models.user import User


class LoginForm(FlaskForm):
    username = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class ObserverLoginForm(FlaskForm):
    # Kept for backward compatibility with legacy route which now redirects
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class UserCreationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    role = SelectField(
        "Role",
        choices=[(role.value, role.value.title()) for role in User.Role],
        default="teacher",
    )
    submit = SubmitField("Create User")


class UserEditForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    password = PasswordField("Password")  # Optional for editing
    role = SelectField(
        "Role", choices=[(role.value, role.value.title()) for role in User.Role]
    )
    submit = SubmitField("Save Changes")


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Change Password")


class StartSessionForm(FlaskForm):
    name = StringField(
        "Session Name",
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g., Period 3 - Data Analysis"},
    )
    section = IntegerField(
        "Section/Period",
        validators=[
            DataRequired(),
            NumberRange(min=1, max=12, message="Section must be between 1 and 12"),
        ],
        render_kw={"placeholder": "e.g., 3"},
    )
    module = SelectField(
        "Module",
        validators=[DataRequired()],
        choices=[],  # Will be populated dynamically
        coerce=int,  # Convert string values to integers
    )
    character_set = SelectField(
        "Character Set",
        validators=[DataRequired()],
        choices=[
            ("animals", "Animals"),
            ("superheroes", "Superheroes"),
            ("fantasy", "Fantasy Characters"),
            ("space", "Space Explorers"),
        ],
        default="animals",
    )
    student_count = IntegerField(
        "Number of Students",
        validators=[
            DataRequired(),
            NumberRange(
                min=5, max=50, message="Student count must be between 5 and 50"
            ),
        ],
        default=20,
        render_kw={"placeholder": "e.g., 25"},
    )
    submit = SubmitField("Start Session")
    archive_and_create = SubmitField("Archive Existing & Start New")

    def __init__(self, *args, **kwargs):
        super(StartSessionForm, self).__init__(*args, **kwargs)
        # Populate module choices from database
        self.module.choices = Module.get_choices_for_form()


class StudentLoginForm(FlaskForm):
    district_id = SelectField("District", coerce=int, choices=[])
    school_id = SelectField("School", coerce=int, choices=[])
    pin = PasswordField(
        "6-digit password",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "000000",
            "inputmode": "numeric",
            "pattern": "[0-9]{6}",
            "maxlength": 6,
        },
    )
    submit = SubmitField("Login")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate districts
        districts = District.query.order_by(District.name).all()
        self.district_id.choices = [(0, "Select District")] + [
            (d.id, d.name) for d in districts
        ]
        # Initial schools (will be updated in route on selection)
        schools = School.query.order_by(School.name).all()
        self.school_id.choices = [(0, "Select School")] + [
            (s.id, s.name) for s in schools
        ]


class ModuleForm(FlaskForm):
    """Form for creating/editing curriculum modules."""

    name = StringField(
        "Module Name",
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g., Module 3 - Advanced Statistics"},
    )
    description = StringField(
        "Description",
        render_kw={"placeholder": "Brief description of the module content"},
    )
    sort_order = IntegerField(
        "Sort Order",
        validators=[NumberRange(min=0, message="Sort order must be 0 or greater")],
        default=0,
        render_kw={"placeholder": "0"},
    )
    is_active = SelectField(
        "Status",
        choices=[(True, "Active"), (False, "Inactive")],
        coerce=lambda x: x == "True",
        default=True,
    )
    submit = SubmitField("Save Module")


class SessionFilterForm(FlaskForm):
    """Form for filtering sessions by status, module, and date range."""

    status = SelectField(
        "Status",
        choices=[
            ("", "All Statuses"),
            ("active", "Active"),
            ("archived", "Archived"),
            ("paused", "Paused"),
        ],
        validators=[Optional()],
        default="",
    )

    module = SelectField(
        "Module",
        choices=[("", "All Modules")],  # Will be populated dynamically
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        default="",
    )

    date_from = DateField(
        "From Date", validators=[Optional()], render_kw={"placeholder": "Start date"}
    )

    date_to = DateField(
        "To Date", validators=[Optional()], render_kw={"placeholder": "End date"}
    )

    submit = SubmitField("Apply Filters")

    def populate_module_choices(self):
        """Populate module choices from database."""
        modules = Module.query.filter_by(is_active=True).order_by(Module.name).all()
        choices = [("", "All Modules")]
        choices.extend([(module.id, module.name) for module in modules])
        self.module.choices = choices


class MediaFilterForm(FlaskForm):
    """Form for filtering media within a session by tags and type."""

    media_type = SelectField(
        "Media Type",
        choices=[
            ("", "All Types"),
            ("image", "Images"),
            ("video", "Videos"),
        ],
        validators=[Optional()],
        default="",
    )

    graph_tag = SelectField(
        "Graph Tag",
        choices=[("", "All Graph Tags")],  # Will be populated dynamically
        validators=[Optional()],
        default="",
    )

    variable_tag = SelectField(
        "Variable Tag",
        choices=[("", "All Variable Tags")],  # Will be populated dynamically
        validators=[Optional()],
        default="",
    )

    is_graph = SelectField(
        "Graph Content",
        choices=[
            ("", "All Content"),
            ("true", "Graph Content Only"),
            ("false", "Non-Graph Content Only"),
        ],
        validators=[Optional()],
        default="",
    )

    posted_by = SelectField(
        "Posted By",
        choices=[
            ("", "All Authors"),
            ("students", "Students"),
            ("teacher", "Teacher"),
        ],
        validators=[Optional()],
        default="",
    )

    submit = SubmitField("Apply Filters")

    def populate_tag_choices(self, session_id):
        """Populate graph_tag and variable_tag choices from session media."""
        from models import Media

        # Get unique graph tags from this session's media
        graph_tags = (
            db.session.query(Media.graph_tag)
            .filter(
                Media.session_id == session_id,
                Media.graph_tag.isnot(None),
                Media.graph_tag != "",
            )
            .distinct()
            .all()
        )

        # Get unique variable tags from this session's media
        variable_tags = (
            db.session.query(Media.variable_tag)
            .filter(
                Media.session_id == session_id,
                Media.variable_tag.isnot(None),
                Media.variable_tag != "",
            )
            .distinct()
            .all()
        )

        # Update choices
        graph_choices = [("", "All Graph Tags")]
        graph_choices.extend([(tag[0], tag[0]) for tag in graph_tags])
        self.graph_tag.choices = graph_choices

        variable_choices = [("", "All Variable Tags")]
        variable_choices.extend([(tag[0], tag[0]) for tag in variable_tags])
        self.variable_tag.choices = variable_choices
