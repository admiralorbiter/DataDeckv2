from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange

from models.module import Module
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
    submit = SubmitField("Start Session")
    archive_and_create = SubmitField("Archive Existing & Start New")

    def __init__(self, *args, **kwargs):
        super(StartSessionForm, self).__init__(*args, **kwargs)
        # Populate module choices from database
        self.module.choices = Module.get_choices_for_form()


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
