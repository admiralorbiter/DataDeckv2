from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange

from models.session import Module
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
        choices=[(mod.value, mod.display_name) for mod in Module],
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
