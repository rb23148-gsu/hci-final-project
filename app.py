from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, BooleanField, StringField, validators
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
from forms import LoginForm, CreateAccountForm, CourseForm, AddClassesForm
import re
import os
import pymysql

load_dotenv()
SQL_USER = os.environ.get('gl_username')
SQL_PASSWORD = os.environ.get('gl_sql_password')
SQL_HOST = os.environ.get('gl_sql_host')
SQL_DB = 'grouploop_db'

app = Flask(__name__)
app.secret_key = os.urandom(24)

# PyMySQL documentation.https://pymysql.readthedocs.io/en/latest/
# This is a personal preference, allows to use written SQL commands using the cursor versus creating an object of SQLAlchemy.
# Can switch and learn the other if needed but for now going to use this. 

### BEGIN FUNCTION DEFINITIONS ### 
def connect_to_database():
    return pymysql.connect(host=SQL_HOST, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DB)


### BEGIN ROUTE DEFINITIONS ###
# Set up default route when visiting the site including the login form
@app.route('/')
def index():
    # Create form object to be passed to the page.
    # Send user to the login page when they visit the app.
    # The login will be processed in the login route.
    form = LoginForm()
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Don't let the user visit the login page if they're already logged in.
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    # Create form object to be passed to the page.
    form = LoginForm()
    
    # WTForms checks some basic validation.
    # Additional validation required. 
    if form.validate_on_submit():
        # Connect to db and prepare cursor for query
        connection = connect_to_database()
        cursor = connection.cursor()

        try:
            # Get input data from the form submission.
            input = form.email.data
            raw_password = form.password.data

            # Formulate db query and get the result.
            # Hashed password version
            # This method grabs the password from the provided email or username and checks it later.
            query = "SELECT user_id, password FROM Users WHERE email = %s OR username = %s"
            cursor.execute(query, (input, input))
            # Gets the result of the last query as a tuple.
            user = cursor.fetchone()

            # Hashed password version
            # Start session data and send the user to the dashboard if the login was successful.
            if user and check_password_hash(user[1], raw_password):
                session['user'] = user[0]
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password')

        except Exception as e:
            flash('An error occurred during login.')
            print(f"Error during login: {e}")

        # Close cursor and connection
        finally:
            cursor.close()
            connection.close()
    
    # Render main page and pass the form object to it.
    return render_template('login.html', form=form)


@app.route('/create-account', methods=['GET', 'POST'])
def create_account():

    # Don't let user visit this page if they're already logged in.
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    # Create form object to pass to the page.
    form = CreateAccountForm()

    # Define these so they are in scope for the finally block to close connections.
    connection = None
    cursor = None

    try:
        # Connect to db and prepare cursor for query
        connection = connect_to_database()
        cursor = connection.cursor()

        # Get university names data to populate field.
        cursor.execute("SELECT university_id, university_name FROM Universities")
        universities = cursor.fetchall()
        # WTForms wants a list of tuples. In this case, we are returning both id and name.
        form.university.choices = [(uni[0], uni[1]) for uni in universities]

        if form.validate_on_submit():
            # Get input data from the form submission.
            email = form.email.data
            username = form.username.data
            first_name = form.first_name.data
            last_name = form.last_name.data
            raw_password = form.password.data
            university = form.university.data

            # Hash the password before storing it!
            hashed_password = generate_password_hash(raw_password)

            # Insert the data into the db after validation.
            query = "INSERT INTO Users (username, first_name, last_name, email, password, university_id) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (username, first_name, last_name, email, hashed_password, university))
            connection.commit()

            # Get the user id so we can use it in the session
            session_query = "SELECT user_id FROM Users WHERE email = %s"
            cursor.execute(session_query, (email,))
            user = cursor.fetchone()
            session['user'] = user[0]

            # Assuming everything else went well, redirect to edit classes page.
            return redirect(url_for('edit_classes', university_id=university))

    except Exception as e:
        flash("There was an error creating the account.")
        print(f"Error creating account: {e}")
         
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('create-account.html', form=form)


@app.route('/edit-classes', methods=['GET', 'POST'])
def edit_classes():

    # Send the user to the login page if they try to visit this page while not logged in.
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Check if the request is an AJAX request for subject codes
    if request.args.get('action') == 'load_subject_codes':
        # Get data from the request.
        university_id = request.args.get('university_id', type=int)
        # Debugging print
        print(f"AJAX request for subject codes: university_id={university_id}")

        # Connect to db and get subject codes
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT subject_code FROM Courses WHERE university_id = %s", (university_id,))
        subject_codes = [code[0] for code in cursor.fetchall()]
        cursor.close()
        connection.close()
        # Make sure we got something back.
        print("Subject Codes Retrieved:", subject_codes)
        # Assuming everything worked, send it to populate the field.
        return jsonify(subject_codes=subject_codes)

    # Check if the request is an AJAX request for course numbers
    if request.args.get('action') == 'load_course_numbers':
        # Get data from the request.
        university_id = request.args.get('university_id', type=int)
        subject_code = request.args.get('subject_code')
        # Debug because getting this to work sucked.
        print(f"AJAX request for course numbers: university_id={university_id}, subject_code={subject_code}")

        # Connect to db and get course numbers.
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute("SELECT course_number FROM Courses WHERE university_id = %s AND subject_code = %s", (university_id, subject_code))
        course_numbers = [num[0] for num in cursor.fetchall()]
        cursor.close()
        connection.close()
        # Print course numbers to make sure it worked.
        print("Course Numbers Retrieved:", course_numbers)
        # Send course numbers that exist for the subject code.
        return jsonify(course_numbers=course_numbers)
    
    # Do this once the form is submitted.
    # if form.validate_on_submit():
        # Get input data from the form submission. Use a for loop.
        # Section data will go into the Sections table to register that the section and course combo exists. Querying groups will use this data.
        # We are relying on the user to get the section data correct.
        # If the section/course combo exists, skip putting it in the db.
        # Next, the Enrollments table needs to be used to tie the user to the course/section combos.
        # Once this is done, we can redirect to the dashboard.
        # Did I miss anything?

        # This worked for an earlier version before AJAX, but a lot has changed. I haven't tested it yet.
        # # Iterate over class_entry data from multiple classes to get all entries.
        # for class_entry in form.classes:
        #     subject_code = class_entry.subject_code.data
        #     course_number = class_entry.course_number.data
        #     section_code = class_entry.section_code.data

        # Redirect to edit classes page.
        return redirect(url_for('dashboard'))

    # Regular page load or form submission
    form = AddClassesForm()
    university_id = request.args.get('university_id', type=int)
    return render_template('edit-classes.html', form=form, university_id=university_id)

# Rob - The course data is in its own file. Unless we're going to manually input 
# the courses in through the website, this isn't needed, but you could probably repurpose some of it
# to use it with the pdf/txt file. 
#Emmanuel importing Courses into Database
# @app.route('/import-courses', methods=['GET', 'POST'])
# def import_courses():
#     form = CourseForm()

    
#     connection = None
#     cursor = None

#     try:
#         # Connection
#         connection = connect_to_database()
#         cursor = connection.cursor()

#         # Getting uni names
#         # cursor.execute("SELECT university_id, university_name FROM Universities")
#         # universities = cursor.fetchall()
#         # form.university.choices = [(uni[0], uni[1]) for uni in universities]

#         if form.validate_on_submit():
#             course_name = form.course_name.data
#             course_code = form.course_code.data
#             university_id = form.university.data

#             # If valid, insert course data into database
#             query = "INSERT INTO Courses (course_name, course_code, university_id) VALUES (%s, %s, %s)"
#             cursor.execute(query, (course_name, course_code, university_id))
#             connection.commit()

#             flash("Course imported successfully.")
#             return redirect(url_for('import_courses'))

#     except Exception as e:
#         flash("There was an error importing the course.")
#         print(f"Error importing course: {e}")

#     finally:
#         # Closing cursor and connection
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()

#     return render_template('import_courses.html', form=form)
    
@app.route('/dashboard')
def dashboard():
    # For now, just render the dashboard to show we can go there after logging in
    return render_template('dashboard.html')

@app.route('/logout', methods=['POST'])
def logout():
        # Clear session to log out the user and send them to the login.
        session.clear()
        flash('You have been logged out!')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
