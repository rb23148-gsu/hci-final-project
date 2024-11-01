from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, BooleanField, StringField, validators
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
from forms import LoginForm, CreateAccountForm, CourseForm
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
    # The login will still be processed in the login route.
    form = LoginForm()
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():

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
            # Catches the result of the last query as a tuple.
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

            # Redirect to the dashboard
            return redirect(url_for('dashboard'))

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
    
#Emmanuel importing Courses into Database
@app.route('/import-courses', methods=['GET', 'POST'])
def import_courses():
    form = CourseForm()

    
    connection = None
    cursor = None

    try:
        # Connection
        connection = connect_to_database()
        cursor = connection.cursor()

        # Getting uni names
        cursor.execute("SELECT university_id, university_name FROM Universities")
        universities = cursor.fetchall()
        form.university.choices = [(uni[0], uni[1]) for uni in universities]

        if form.validate_on_submit():
            course_name = form.course_name.data
            course_code = form.course_code.data
            university_id = form.university.data

            # If valid, insert course data into database
            query = "INSERT INTO Courses (course_name, course_code, university_id) VALUES (%s, %s, %s)"
            cursor.execute(query, (course_name, course_code, university_id))
            connection.commit()

            flash("Course imported successfully.")
            return redirect(url_for('import_courses'))

    except Exception as e:
        flash("There was an error importing the course.")
        print(f"Error importing course: {e}")

    finally:
        # Closing cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('import_courses.html', form=form)
    
@app.route('/dashboard')
def dashboard():
    # For now, just render the dashboard to show we can go there after logging in
    # We still need to get users logged in and session data going.
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
