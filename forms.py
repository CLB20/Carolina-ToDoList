from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length

# Configure Forms


class RegisterForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8)])
    name = StringField(label="Name", validators=[DataRequired(), Length(min=3)])
    submit = SubmitField(label="Register")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label="Sign in")


class ListForm(FlaskForm):
    list_name = StringField(label="", render_kw={"placeholder": "New List"}, validators=[DataRequired()])
    submit = SubmitField(label="Create List")


class TaskForm(FlaskForm):
    task = StringField(label="", render_kw={"placeholder": "New Task"}, validators=[DataRequired()])
    submit = SubmitField(label="Add")



