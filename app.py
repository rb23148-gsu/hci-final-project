from flask import Flask, render_template, request, redirect, url_for, session, flash
from wtforms import Form, BooleanField, StringField, validators
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
from forms import LoginForm
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
    return render_template('index.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    connection = connect_to_database()
    cursor = connection.cursor()

    # Create form object to be passed to the page.
    form = LoginForm()
    
    # WTForms checks if the submitted form was sent with a POST request and fields are not empty.
    # Additional validation required. 
    if form.validate_on_submit():
        # Insert additional validation/maybe session stuff here then redirect to dashboard if all is good.
        # flash("Logging in from the login route.") <-flash messages for debugging lol
        input = form.email.data
        password = form.password.data

        query = "SELECT user_id FROM Users WHERE (email = %s OR username = %s) AND password = %s"
        cursor.execute(query, (input, input, password,))
        user = cursor.fetchone()

        if user:
            session['user'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    # Render main page and pass the form object to it.
    return render_template('login.html', form=form)

@app.route('/create-account', methods=['GET'])
def create_account():
    return render_template('create-account.html')

@app.route('/dashboard')
def dashboard():
    # For now, just render the dashboard to show we can go there after logging in
    # We still need to get users logged in and session data going.
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)