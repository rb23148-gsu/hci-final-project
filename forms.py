from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SubmitField, SelectField, FieldList, FormField, validators
from wtforms.validators import DataRequired, Optional, EqualTo

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
    # Variable names correspond to columns in Courses table.
    subject_code = SelectField('Subject Code', choices=[], validate_choice=False, validators=[DataRequired()])
    course_number = SelectField('Course Number', choices=[], validate_choice=False, validators=[DataRequired()])
    section_code = StringField('Section Code', validators=[DataRequired()])

# Form to create the account on create-account page.
class CreateAccountForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    username = StringField('Username')
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    password = PasswordField('Password', validators=[DataRequired()])
    match_password = PasswordField('Match Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    university = SelectField('University', choices=[], validators=[DataRequired()])
    create_account = SubmitField('Create Account')

# Form for the edit-classes page using the ClassEntryForm subform.
class AddClassesForm(FlaskForm):
    classes = FieldList(FormField(ClassEntryForm), min_entries=1, max_entries=6)
    add_classes = SubmitField('Add All Classes to Account')

# ADDING COURSE FORM - Emmanuel
class CourseForm(FlaskForm):
    course_name = StringField('Course Name', [validators.Length(min=1, max=100)])
    course_code = StringField('Course Code', [validators.Length(min=1, max=10)])
    university = SelectField('University', coerce=int)

class AvailabilityDayForm(FlaskForm):
    selected = BooleanField('Available')

    time_choices = [("", "Select Time")] + [
        (f"{hour_12}:{minute:02d} {am_pm}", f"{hour_12}:{minute:02d} {am_pm}")
        for hour in range(24)
        for minute in [0, 15, 30, 45]
        for am_pm in ['AM' if hour < 12 else 'PM']
        for hour_12 in [hour % 12 if hour % 12 != 0 else 12]
    ]
    
    start_time = SelectField('Start Time', choices=time_choices)
    end_time = SelectField('End Time', choices=time_choices)

#Form for the create-group page.
class CreateGroupForm(FlaskForm):
    group_name = StringField('Group Name', validators=[DataRequired()])
    group_description = StringField('Group Description', validators=[DataRequired()])
    monday = FormField(AvailabilityDayForm)
    tuesday = FormField(AvailabilityDayForm)
    wednesday = FormField(AvailabilityDayForm)
    thursday = FormField(AvailabilityDayForm)
    friday = FormField(AvailabilityDayForm)
    saturday = FormField(AvailabilityDayForm)
    sunday = FormField(AvailabilityDayForm)
    create_group = SubmitField('Create Group')