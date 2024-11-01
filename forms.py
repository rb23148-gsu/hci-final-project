from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Regexp, Email, EqualTo

### LOGIN FORM ###

# Defining our login form for easy form handling with WTForms.
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

### CREATE ACCOUNT FORM ###

# The class entry form has to be duplicated up to a max of 6 enrolled classes.
# So we create a subform to be included in the main registration form.
class ClassEntryForm(FlaskForm):
    # Use this when we have a table set up with all subject codes, course numbers, and course names.
    # subject_code = SelectField('Subject Code', choices=[], validators=[DataRequired()])
    section_code = StringField('Section Code')

class CreateAccountForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    username = StringField('Username')
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    password = PasswordField('Password', validators=[DataRequired()])
    match_password = PasswordField('Match Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    university = SelectField('University', choices=[], validators=[DataRequired()])
    classes = FieldList(FormField(ClassEntryForm), min_entries=1, max_entries=6)
    create_account = SubmitField('Create Account')

# ADDING COURSE FORM - Emmanuel
from wtforms import Form, StringField, SelectField, validators

    # course_number = SelectField('Course Number', choices=[], validators=[DataRequired()])
    # section_code = StringField('Section Code', validators=[DataRequired()])
    subject_code = StringField('Subject Code')
    course_number = StringField('Course Number')
    section_code = StringField('Section Code')

class CreateAccountForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    username = StringField('Username')
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    password = PasswordField('Password', validators=[DataRequired()])
    match_password = PasswordField('Match Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    university = SelectField('University', choices=[], validators=[DataRequired()])
    classes = FieldList(FormField(ClassEntryForm), min_entries=1, max_entries=6)
    create_account = SubmitField('Create Account')

# ADDING COURSE FORM - Emmanuel


class CourseForm(Form):
    course_name = StringField('Course Name', [validators.Length(min=1, max=100)])
    course_code = StringField('Course Code', [validators.Length(min=1, max=10)])
    university = SelectField('University', coerce=int)

