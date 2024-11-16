from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from datetime import datetime
from forms import LoginForm, CreateAccountForm, CourseForm, AddClassesForm, ClassEntryForm, CreateGroupForm, PostForm, CommentForm, EditGroupForm, GroupForm
import os, pymysql, random, string, ast

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

            if 'pending_invite' in session:
                redirect(url_for('invite', invite_code=session['pending_invite']))

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

    # Get user id from session
    user_id = session['user']
    university_id = session.get('university_id')
    
    # Call the form for use in the page.
    form = ClassEntryForm()

    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        # Check the db for the user's existing course/section combos so we can populate the edit-classes form.
        cursor.execute("""SELECT c.subject_code, c.course_number, c.subject_name, s.section_code, e.enrollment_id FROM Sections s 
                       JOIN Courses c ON s.course_id = c.course_id   
                       JOIN Enrollments e ON s.section_id = e.section_id     
                       WHERE e.user_id = %s""", (user_id,))
        existing_classes = cursor.fetchall()

        # If classes exist, start with a blank slate then populate them with db info.
        classes_data = [{"subject_code": subject_code, "course_number": course_number, "subject_name": subject_name, "section_code": section_code, "enrollment_id": enrollment_id}
                for subject_code, course_number, subject_name, section_code, enrollment_id in existing_classes]

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

            return redirect(url_for('edit_classes'))

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

@app.route('/delete-course/<int:enrollment_id>', methods=['POST'])
def delete_course(enrollment_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    connection = connect_to_database()
    cursor = connection.cursor()
    try:
        # Find section id first
        cursor.execute("SELECT section_id FROM Enrollments WHERE enrollment_id = %s", (enrollment_id,))
        section_row = cursor.fetchone()
        section_id = section_row[0]

        # Deleting the student's enrollments records
        cursor.execute("DELETE FROM Enrollments WHERE enrollment_id = %s", (enrollment_id,))
        connection.commit()

        # Checking to see if any students remain in a section. If not, delete the section.
        cursor.execute("SELECT COUNT(*) FROM Enrollments WHERE section_id = %s", (section_id,))
        enrollment_count_query = cursor.fetchone()
        enrollment_count = enrollment_count_query[0]

        if enrollment_count == 0:
            cursor.execute("DELETE FROM Sections WHERE section_id = %s", (section_id,))
            connection.commit()

        flash("Course successfully deleted!")

    except Exception as e:
        connection.rollback()
        flash("There was an error deleting the course.")
        print(f"Error deleting course: {e}")
        connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('edit_classes'))

@app.route('/create-group/<int:section_id>', methods=['GET', 'POST'])
def create_group(section_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    connection = connect_to_database()
    cursor = connection.cursor()

    form = CreateGroupForm()

    try:
        user = session['user']

        cursor.execute("""
            SELECT c.subject_code, c.subject_name, c.course_number, s.section_code
            FROM Sections s
            JOIN Courses c ON s.course_id = c.course_id
            WHERE s.section_id = %s
        """, (section_id,))
        class_details = cursor.fetchone()

        # Check if the user is enrolled in the section
        cursor.execute("SELECT COUNT(*) FROM Enrollments WHERE user_id = %s AND section_id = %s", (user, section_id))
        enrollment_count = cursor.fetchone()[0]

        if enrollment_count == 0:
            flash("You must be enrolled in this section to create a group.")
            return redirect(url_for('dashboard'))

        invite_code = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
        cursor.execute("SELECT COUNT(*) FROM User_Groups WHERE invite_code = %s", (invite_code,))
        
        # Check if invite code already exists; regenerate if necessary
        while cursor.fetchone()[0] > 0:
            invite_code = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
            cursor.execute("SELECT COUNT(*) FROM User_Groups WHERE invite_code = %s", (invite_code,))

        #If user has already created a group for this class section, don't allow them to create another
        cursor.execute("Select Count(*) from User_Groups where creator_id = %s and section_id = %s", (user, section_id))
        if cursor.fetchone()[0] > 0:
            flash("You have already created a group for this class section.")
            return redirect(url_for('dashboard'))
        
        cursor.execute("SELECT group_id FROM User_Groups WHERE creator_id = %s AND section_id = %s", (user, section_id))
        existing_group = cursor.fetchone()

        if existing_group:
            flash("You already have a group for this section. Redirecting to edit page.")
            return redirect(url_for('edit_group', group_id=existing_group[0]))
        
        if request.method == 'POST' and form.validate_on_submit():
            group_name = form.group_name.data
            group_description = form.group_description.data
            meeting_link = form.meeting_link.data
            
            user_availability = {
                "Monday": (form.monday.selected.data, form.monday.start_time.data, form.monday.end_time.data),
                "Tuesday": (form.tuesday.selected.data, form.tuesday.start_time.data, form.tuesday.end_time.data),
                "Wednesday": (form.wednesday.selected.data, form.wednesday.start_time.data, form.wednesday.end_time.data),
                "Thursday": (form.thursday.selected.data, form.thursday.start_time.data, form.thursday.end_time.data),
                "Friday": (form.friday.selected.data, form.friday.start_time.data, form.friday.end_time.data),
                "Saturday": (form.saturday.selected.data, form.saturday.start_time.data, form.saturday.end_time.data),
                "Sunday": (form.sunday.selected.data, form.sunday.start_time.data, form.sunday.end_time.data),
            }

            cursor.execute("""INSERT INTO User_Groups (group_name, group_description, section_id, availability, preferred_meeting_link, invite_code, creator_id) 
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""", (group_name, group_description, section_id, str(user_availability), meeting_link, invite_code, user))
            connection.commit()

            group_id = cursor.lastrowid

            cursor.execute("INSERT INTO Group_Membership (group_id, user_id, is_group_leader, availability) VALUES (%s, %s, TRUE, %s)", (group_id, user, str(user_availability)))
            connection.commit()

            print("Group successfully created!")
            flash("Group successfully created!")

            return render_template('create-group.html', form=form, invite_code=invite_code, section_id=section_id, class_details=class_details)
        
    except Exception as e:
        connection.rollback()
        flash("There was an error creating the group.")
        print(f"Error creating group: {e}")
        connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return render_template('create-group.html', form=form, section_id=section_id, invite_code=invite_code, class_details=class_details)

@app.route('/edit-group/<int:group_id>', methods=['GET', 'POST'])
def edit_group(group_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    connection = connect_to_database()
    cursor = connection.cursor()
    form = EditGroupForm()

    try:
        user = session['user']

        # Fetch group details for the given group_id
        cursor.execute("SELECT group_name, group_description, availability FROM User_Groups WHERE group_id = %s", (group_id,))
        group = cursor.fetchone()

        cursor.execute("Select invite_code from User_Groups where group_id = %s", (group_id,))
        invite_code = cursor.fetchone()[0]

        cursor.execute("Select preferred_meeting_link from User_Groups where group_id = %s", (group_id,))
        meeting_link = cursor.fetchone()[0]

        if not group:
            flash("Group not found.")
            return redirect(url_for('dashboard'))

        group_name, group_description, user_availability_str = group

        # Convert the string representation of the dictionary back to a dictionary
        user_availability = ast.literal_eval(user_availability_str)

        # Pre-fill the form with existing group data
        if request.method == 'GET':
            form.group_name.data = group_name
            form.group_description.data = group_description

            # Populate availability fields with the existing data
            for day, (selected, start_time, end_time) in user_availability.items():
                if day == "Monday":
                    form.monday.selected.data = selected
                    form.monday.start_time.data = start_time
                    form.monday.end_time.data = end_time
                elif day == "Tuesday":
                    form.tuesday.selected.data = selected
                    form.tuesday.start_time.data = start_time
                    form.tuesday.end_time.data = end_time
                elif day == "Wednesday":
                    form.wednesday.selected.data = selected
                    form.wednesday.start_time.data = start_time
                    form.wednesday.end_time.data = end_time
                elif day == "Thursday":
                    form.thursday.selected.data = selected
                    form.thursday.start_time.data = start_time
                    form.thursday.end_time.data = end_time
                elif day == "Friday":
                    form.friday.selected.data = selected
                    form.friday.start_time.data = start_time
                    form.friday.end_time.data = end_time
                elif day == "Saturday":
                    form.saturday.selected.data = selected
                    form.saturday.start_time.data = start_time
                    form.saturday.end_time.data = end_time
                elif day == "Sunday":
                    form.sunday.selected.data = selected
                    form.sunday.start_time.data = start_time
                    form.sunday.end_time.data = end_time

        if request.method == 'POST' and form.validate_on_submit():
            new_group_name = form.group_name.data
            new_group_description = form.group_description.data
            new_meeting_link = form.meeting_link.data

            # Update availability from the form data
            user_availability = {
                "Monday": (form.monday.selected.data, form.monday.start_time.data, form.monday.end_time.data),
                "Tuesday": (form.tuesday.selected.data, form.tuesday.start_time.data, form.tuesday.end_time.data),
                "Wednesday": (form.wednesday.selected.data, form.wednesday.start_time.data, form.wednesday.end_time.data),
                "Thursday": (form.thursday.selected.data, form.thursday.start_time.data, form.thursday.end_time.data),
                "Friday": (form.friday.selected.data, form.friday.start_time.data, form.friday.end_time.data),
                "Saturday": (form.saturday.selected.data, form.saturday.start_time.data, form.saturday.end_time.data),
                "Sunday": (form.sunday.selected.data, form.sunday.start_time.data, form.sunday.end_time.data),
            }

            cursor.execute("""UPDATE User_Groups SET group_name = %s, group_description = %s, availability = %s, preferred_meeting_link = %s WHERE group_id = %s""", 
            (new_group_name, new_group_description, str(user_availability), new_meeting_link,group_id))
            connection.commit()

            flash("Group details updated successfully!")
            return redirect(url_for('dashboard'))
    
    except Exception as e:
        connection.rollback()
        flash("There was an error updating the group.")
        print(f"Error updating group: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('edit-group.html', form=form, meeting_link=meeting_link, group_id=group_id, invite_code=invite_code)

@app.route('/invite/<string:invite_code>', methods=['GET', 'POST'])
def invite(invite_code):
    if 'user' not in session:
        session['pending_invite'] = invite_code
        return redirect(url_for('login'))
    
    user = session['user']

    if 'pending_invite' in session:
        invite_code = session.pop('pending_invite')

    try:
        connection = connect_to_database()
        cursor = connection.cursor()

        if request.method == 'GET':
            cursor.execute("Select Count(*) from User_Groups where invite_code = %s", (invite_code,))
            invite_exists = cursor.fetchall()

            if invite_exists[0][0] == 0:
                flash("Invalid invite code.")
                return redirect(url_for('dashboard'))

            if invite_exists[0][0] == 1:
                cursor.execute("Select group_id from User_Groups where invite_code = %s", (invite_code,))
                group_id = cursor.fetchone()[0]
                cursor.execute("Insert into Group_Membership (group_id, user_id, is_group_leader) VALUES (%s, %s, FALSE)", (group_id, user))
                connection.commit()

                return redirect(url_for('group_page', group_id=group_id))
        
    except Exception as e:
        connection.rollback()
        flash("There was an error joining the group.")
        print(f"Error joining group: {e}")
        connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']
    
    connection = connect_to_database()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # Get user's joined groups
    cursor.execute(""" 
        SELECT g.group_name, s.section_code, c.subject_name, g.group_id, g.invite_code, g.preferred_meeting_link
        FROM Group_Membership gm
        JOIN User_Groups g ON gm.group_id = g.group_id
        JOIN Sections s ON g.section_id = s.section_id
        JOIN Courses c ON s.course_id = c.course_id
        WHERE gm.user_id = %s
    """, (user_id,))
    user_groups = cursor.fetchall()

    # Get the most recent activity for each group
    for group in user_groups:
        group_id = group['group_id']
        
        # Get the most recent post activity
        cursor.execute("""
            SELECT MAX(p.created_at) AS last_activity
            FROM Group_Post p
            WHERE p.group_id = %s
        """, (group_id,))
        post_activity = cursor.fetchone()
        group['last_activity'] = post_activity['last_activity'] if post_activity['last_activity'] else None
        
        # Get the most recent comment activity
        cursor.execute("""
            SELECT MAX(c.created_at) AS last_activity
            FROM Post_Comment c
            JOIN Group_Post p ON c.post_id = p.post_id
            WHERE p.group_id = %s
        """, (group_id,))
        comment_activity = cursor.fetchone()
        comment_last_activity = comment_activity['last_activity'] if comment_activity['last_activity'] else None

        # Determine the most recent activity (between post and comment)
        if group['last_activity'] and comment_last_activity:
            group['last_activity'] = max(group['last_activity'], comment_last_activity)
        elif not group['last_activity']:
            group['last_activity'] = comment_last_activity

    # Get user's available groups based on enrollments.
    cursor.execute(""" 
        SELECT g.group_name, g.group_id, c.subject_name, s.section_code, e.section_id
        FROM Enrollments e
        JOIN Sections s ON e.section_id = s.section_id
        JOIN Courses c ON s.course_id = c.course_id
        LEFT JOIN User_Groups g ON g.section_id = s.section_id
        WHERE e.user_id = %s AND g.group_id IS NOT NULL 
        AND g.group_id NOT IN (
            SELECT gm.group_id
            FROM Group_Membership gm
            WHERE gm.user_id = %s)""", (user_id, user_id))
    available_groups = cursor.fetchall()

    # Get the user's enrollments, marking those with existing groups
    cursor.execute(""" 
    SELECT c.subject_name, s.section_code, e.section_id,
           EXISTS (
               SELECT 1 
               FROM Group_Membership gm
               JOIN User_Groups g ON gm.group_id = g.group_id
               WHERE gm.user_id = %s AND g.section_id = e.section_id
           ) AS has_group
    FROM Enrollments e
    JOIN Sections s ON e.section_id = s.section_id
    JOIN Courses c ON s.course_id = c.course_id
    WHERE e.user_id = %s
    """, (user_id, user_id))
    user_enrollments = cursor.fetchall()

    return render_template('dashboard.html', user_groups=user_groups, user_enrollments=user_enrollments, available_groups=available_groups)

@app.route('/join-request', methods=['POST'])
def join_request():
    return render_template('dashboard.html')

@app.route('/group-page/<int:group_id>', methods=['GET', 'POST'])
def group_page(group_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    post_form = PostForm()
    comment_form = CommentForm()
    form = GroupForm()
    connection = connect_to_database()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        # Fetch group details
        query = """
            SELECT 
                g.group_id, 
                g.group_name, 
                c.subject_name, 
                s.section_code, 
                g.availability AS group_availability, 
                a.availability AS user_availability, 
                g.creator_id, 
                g.preferred_meeting_link,
                s.section_id
            FROM User_Groups g
            JOIN Sections s ON g.section_id = s.section_id
            JOIN Courses c ON s.course_id = c.course_id
            LEFT JOIN Availability a ON g.group_id = a.group_id
            WHERE g.group_id = %s
        """
        cursor.execute(query, (group_id,))
        group_details = cursor.fetchone()

        if not group_details:
            flash("Group not found or you do not have access to it.")
            return redirect(url_for('dashboard'))
        
        group_availability = ast.literal_eval(group_details['group_availability']) if group_details['group_availability'] else {}
        user_availability = ast.literal_eval(group_details['user_availability']) if group_details['user_availability'] else {}

        # Format availability into readable lists
        def format_availability(availability):
            return [
                f"{day}: {times[1]} - {times[2]}" if times[0] else f"{day}: Not Available"
                for day, times in availability.items()
            ]

        formatted_group_availability = format_availability(group_availability)
        formatted_user_availability = format_availability(user_availability)

        # Fetch posts and their comments
        query = """
            SELECT p.post_id, p.post_title, p.post_content, p.created_at, u.username
            FROM Group_Post p
            JOIN Users u ON p.user_id = u.user_id
            WHERE p.group_id = %s
            ORDER BY p.created_at DESC
        """
        cursor.execute(query, (group_id,))
        posts = cursor.fetchall()

        for post in posts:
            query = """
                SELECT c.comment_content, c.created_at, u.username
                FROM Post_Comment c
                JOIN Users u ON c.user_id = u.user_id
                WHERE c.post_id = %s
                ORDER BY c.created_at ASC
            """
            cursor.execute(query, (post['post_id'],))
            post['comments'] = cursor.fetchall()

        query = """
            SELECT u.first_name, u.last_name
            FROM Group_Membership gm
            JOIN Users u ON gm.user_id = u.user_id
            WHERE gm.group_id = %s
        """
        cursor.execute(query, (group_id,))
        group_members = cursor.fetchall()

    except Exception as e:
        flash("An error occurred while fetching posts and comments.")
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    return render_template('group-page.html', user_id=user_id, group_details=group_details, posts=posts, post_form=post_form, comment_form=comment_form, form=form, formatted_group_availability=formatted_group_availability, group_members=group_members, formatted_user_availability=formatted_user_availability)

@app.route('/add-post/<int:group_id>', methods=['POST'])
def add_post(group_id):
    post_form = PostForm()
    if post_form.validate_on_submit():
        connection = connect_to_database()
        cursor = connection.cursor()
        try:
            query = """INSERT INTO Group_Post (group_id, user_id, post_title, post_content) VALUES (%s, %s, %s, %s)"""
            cursor.execute(query, (group_id, session['user'], post_form.post_title.data, post_form.post_content.data))
            connection.commit()
            flash("Post created successfully!")
        except Exception as e:
            flash("An error occurred while creating the post.")
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()
    return redirect(url_for('group_page', group_id=group_id))

@app.route('/add-comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        connection = connect_to_database()
        cursor = connection.cursor()
        try:
            query = """INSERT INTO Post_Comment (post_id, user_id, comment_content) VALUES (%s, %s, %s)"""
            cursor.execute(query, (post_id, session['user'], comment_form.comment_content.data))
            connection.commit()
            flash("Comment added successfully!")
        except Exception as e:
            flash("An error occurred while adding the comment.")
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()
    return redirect(request.referrer)

@app.route('/add-availability/<int:group_id>', methods=['POST'])
def add_availability(group_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    form = GroupForm()

    if form.validate_on_submit():
        connection = connect_to_database()
        cursor = connection.cursor()
        try:
            user_availability = {
                "Monday": (form.monday.selected.data, form.monday.start_time.data, form.monday.end_time.data),
                "Tuesday": (form.tuesday.selected.data, form.tuesday.start_time.data, form.tuesday.end_time.data),
                "Wednesday": (form.wednesday.selected.data, form.wednesday.start_time.data, form.wednesday.end_time.data),
                "Thursday": (form.thursday.selected.data, form.thursday.start_time.data, form.thursday.end_time.data),
                "Friday": (form.friday.selected.data, form.friday.start_time.data, form.friday.end_time.data),
                "Saturday": (form.saturday.selected.data, form.saturday.start_time.data, form.saturday.end_time.data),
                "Sunday": (form.sunday.selected.data, form.sunday.start_time.data, form.sunday.end_time.data),
            }

            # Check if availability already exists for this user and group
            query = "SELECT COUNT(*) FROM Availability WHERE group_id = %s AND user_id = %s"
            cursor.execute(query, (group_id, user_id))
            availability_exists = cursor.fetchone()[0] > 0

            if availability_exists:
                # If availability exists, update it
                query = "UPDATE Availability SET availability = %s WHERE group_id = %s AND user_id = %s"
                cursor.execute(query, (str(user_availability), group_id, user_id))
                flash("Availability updated successfully!")
            else:
                # If no availability exists, insert it
                query = "INSERT INTO Availability (group_id, user_id, availability) VALUES (%s, %s, %s)"
                cursor.execute(query, (group_id, user_id, str(user_availability)))
                flash("Availability added successfully!")

            connection.commit()
        except Exception as e:
            flash("An error occurred while adding the availability.")
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()
    return redirect(request.referrer)

# Main function to calculate best meeting time for the group
def get_best_meeting_time(group_availabilities):
    best_times = {}

    # Looping over each day of the week
    for day in group_availabilities:
        user_times = []
        
        # Collecting the availability  for a day from all users
        for availability in group_availabilities[day]:
            if availability[0]:  # If the user is available
                start_time = convert_time_to_datetime(availability[1])
                end_time = convert_time_to_datetime(availability[2])
                user_times.append((start_time, end_time))
        
        # If there are available times, find the overlap
        if user_times:
            overlaps = find_overlap(user_times)
            if overlaps:
                best_times[day] = overlaps

    # Return the best available times
    return best_times

@app.route('/logout', methods=['POST'])
def logout():
        # Clear session to log out the user and send them to the login.
        session.clear()
        flash('You have been logged out!')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
