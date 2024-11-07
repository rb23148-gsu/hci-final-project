from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, BooleanField, StringField, validators
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
from forms import LoginForm, CreateAccountForm, CourseForm, AddClassesForm, ClassEntryForm
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
app.config['WTF_CSRF_SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)

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
                # Set the user id
                session['user'] = user[0]

                # Get the university id for this user and store it in the session.
                cursor.execute("SELECT university_id FROM Users WHERE user_id = %s", (user[0]))
                session['university_id'] = cursor.fetchone()

                # Send the user to the dashboard.
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

            query = "SELECT COUNT(*) FROM Users WHERE username = %s"
            cursor.execute(query, (username,))
            if cursor.fetchone()[0] > 0:
                flash("The username is already taken. Please choose a different one.")
                return render_template('create-account.html', form=form)
            
            query = "SELECT COUNT(*) FROM Users WHERE email = %s"
            cursor.execute(query, (email,))
            if cursor.fetchone()[0] > 0:
                flash("The email is already taken. Please choose a different one or login.")
                return render_template('create-account.html', form=form)

            # Insert the data into the db after validation.
            query = "INSERT INTO Users (username, first_name, last_name, email, password, university_id) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (username, first_name, last_name, email, hashed_password, university))
            connection.commit()

            # Get the user id so we can use it in the session
            session_query = "SELECT user_id, university_id FROM Users WHERE email = %s"
            cursor.execute(session_query, (email,))
            user = cursor.fetchone()
            session['user'] = user[0]
            session['university_id'] = user[1]

            # Assuming everything else went well, redirect to edit classes page.
            return redirect(url_for('edit_classes', university_id=university))

    except Exception as e:
        flash("There was an error creating the account.")
        print(f"Error creating account: {e}")
        connection.rollback()
         
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('create-account.html', form=form)


@app.route('/suggest-username', methods=['POST'])
def suggest_username():
    email = request.form.get('email', '')
    if email and '@' in email:
        username = email.split('@')[0]
        return jsonify({'username': username})
    return jsonify({'username': ''})

@app.route('/edit-classes', methods=['GET', 'POST'])
def edit_classes():
    # Send the user to the login page if they try to visit this page while not logged in.
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
         print(f"Form data: {request.form}")

    # Get user id from session
    user_id = session['user']
    university_id = session.get('university_id')
    
    # Call the form for use in the page.
    form = ClassEntryForm()

    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        # Check the db for the user's existing course/section combos so we can populate the edit-classes form.
        cursor.execute("""SELECT c.subject_code, c.course_number, c.subject_name, s.section_code FROM Sections s JOIN Courses c ON s.course_id = c.course_id JOIN Enrollments e ON s.section_id = e.section_id WHERE e.user_id = %s""", (user_id,))
        existing_classes = cursor.fetchall()

        # If classes exist, start with a blank slate then populate them with db info.
        classes_data = [{"subject_code": subject_code, "course_number": course_number, "subject_name": subject_name, "section_code": section_code}
            for subject_code, course_number, subject_name, section_code in existing_classes]

        cursor.execute("SELECT DISTINCT subject_code, course_number FROM Courses WHERE university_id = %s", (university_id,))
        all_courses = cursor.fetchall()

        courses_dict = {}
        for subject_code, course_number in all_courses:
            courses_dict.setdefault(subject_code, []).append(course_number)

        cursor.execute("SELECT DISTINCT subject_code FROM Courses WHERE university_id = %s", (university_id,))
        subject_codes = [code[0] for code in cursor.fetchall()]
        form.subject_code.choices = [(code, code) for code in subject_codes]

        # Check if the request is an AJAX request for subject codes
        if request.args.get('action') == 'load_subject_codes':
            university_id = request.args.get('university_id', type=int)

            cursor.execute("SELECT DISTINCT subject_code FROM Courses WHERE university_id = %s", (university_id,))
            subject_codes = [code[0] for code in cursor.fetchall()]

            return jsonify(subject_codes=subject_codes)

        # Check if the request is an AJAX request for course numbers
        if request.args.get('action') == 'load_course_numbers':
            subject_code = request.args.get('subject_code')
            university_id = request.args.get('university_id')

            cursor.execute("SELECT course_number, subject_name FROM Courses WHERE university_id = %s AND subject_code = %s", (university_id, subject_code))
            courses = cursor.fetchall()

            course_data = [{'course_number': course[0], 'subject_name': course[1]} for course in courses]

            return jsonify(course_data=course_data)
        
        query = ("Select Count(*) from Enrollments where user_id = %s")
        cursor.execute(query, (user_id,))
        num_classes = cursor.fetchone()[0]
        if num_classes >= 6:
            flash("You cannot have more than 6 classes!", "error")
            disable_submit = True
            return render_template('edit-classes.html', form=form, classes_data=classes_data, university_id=university_id, disable_submit=disable_submit)

        if form.validate_on_submit():
            subject_code = form.subject_code.data
            course_number = form.course_number.data
            section_code = form.section_code.data

            # See if the course exists (it should, but just in case someone decides to tamper with data or something weird happens.)
            cursor.execute("SELECT course_id FROM Courses WHERE subject_code = %s AND course_number = %s AND university_id = %s", (subject_code, course_number, university_id))
            course = cursor.fetchone()

            # If the course doesn't exist, show an error and refresh the page.
            if not course:
                flash("This course does not exist! Contact us with your error.", "error")
                return redirect(url_for('edit_classes'))

            course_id = course[0]

            # Check section data to see if combo already exists for the class/section.
            # We are relying on the user to get the section data correct.
            cursor.execute("SELECT section_id FROM Sections WHERE course_id = %s AND section_code = %s", (course_id, section_code))
            section = cursor.fetchone()

            # If the section/course combo exists, skip putting it in the db, otherwise add it.
            if not section:
                print(f'Section doesn\'t exist. Inserting section into database. {course_id} {section_code}')
                cursor.execute("INSERT INTO Sections (course_id, section_code) VALUES (%s, %s)", (course_id, section_code))
                connection.commit()
                section_id = cursor.lastrowid
            else:
                section_id = section[0]
                print(f'Section/course combo exists. section id is {section_id}')

            # Next, the Enrollments table needs to be used to tie the user to the course/section combos.
            # We check first to see if the enrollment exists.
            cursor.execute("SELECT * FROM Enrollments WHERE user_id = %s AND section_id = %s", (user_id, section_id))
            enrollment = cursor.fetchone()

            # If the enrollment doesn't exist, add it.
            if not enrollment:
                print(f'Enrollment doesn\'t exist. Inserting into database {user_id} {section_id}')
                cursor.execute("INSERT INTO Enrollments (user_id, section_id) VALUES (%s, %s)", (user_id, section_id))
                connection.commit()

            flash("Classes successfully updated!")
            print("Classes successfully updated!")

            return redirect(url_for('dashboard'))

    except Exception as e:
        flash("There was an error editing classes.")
        print(f"Error editing classes: {e}")
        connection.rollback()

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('edit-classes.html', form=form, university_id=university_id, classes_data=classes_data, courses_dict=courses_dict)

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
