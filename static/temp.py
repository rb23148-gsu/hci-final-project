
# @app.route('/edit-classes', methods=['GET', 'POST'])
# def edit_classes():

#     # Send the user to the login page if they try to visit this page while not logged in.
#     if 'user' not in session:
#         return redirect(url_for('login'))
    
#     if request.method == 'POST':
#         print(f"Form data: {request.form}")
    
#     # Get user id from session
#     user_id = session['user']
#     # Still need to add this data to the session data.
#     university_id = session.get('university_id')
#     # Call the form for use in the page.
#     form = ClassEntryForm()

#     try:
#         # Connect to db
#         connection = connect_to_database()
#         cursor = connection.cursor()

#         # Check the db for the user's existing course/section combos so we can populate the edit-classes form.
#         # Include some spicy joins to get all the relevant data across the tables.
#         cursor.execute("""SELECT c.subject_code, c.course_number, s.section_code FROM Sections s 
#                     JOIN Courses c ON s.course_id = c.course_id 
#                     JOIN Enrollments e ON s.section_id = e.section_id WHERE e.user_id = %s""", (user_id,))
        
#         existing_classes = cursor.fetchall()

#         # If classes exist, start with a blank slate then populate them with db info.

#         # form.classes.entries = []

#         classes_data = [{"subject_code": subject_code, "course_number": course_number, "section_code": section_code}
#             for subject_code, course_number, section_code in existing_classes]
#         #print(f'Classes data is: {classes_data}')

#         # Ajax is causing tons of problems with the form submission for some reason I can't figure out.
#         # Trying to load all subject codes and course numbers then filter.
#         cursor.execute("SELECT DISTINCT subject_code, course_number FROM Courses WHERE university_id = %s", (university_id,))
#         all_courses = cursor.fetchall()

#         courses_dict = {}
#         for subject_code, course_number in all_courses:
#             if subject_code not in courses_dict:
#                 courses_dict[subject_code] = []
#             courses_dict[subject_code].append(course_number)

#         #print(f'Courses dict: {courses_dict}')

#         # Old code for populating dynamic list.
#         # for subject_code, course_number, section_code in existing_classes:
#         #     print(f'Subject Code is: {subject_code}')
#         #     print(f'Course Number is: {course_number}')
#         #     print(f'Section Code is: {section_code}')
#         #     entry = ClassEntryForm(
#         #         subject_code=subject_code,
#         #         course_number=course_number,
#         #         section_code=section_code,
#         #     )
#         #     form.classes.append_entry(entry)
        
#         # Check if the request is an AJAX request for subject codes
#         if request.args.get('action') == 'load_subject_codes':
#             # Get data from the request.
#             university_id = request.args.get('university_id', type=int)
#             # Debugging print
#             # print(f"AJAX request for subject codes: university_id={university_id}")

#             # Get subject codes from the db.
#             cursor.execute("SELECT DISTINCT subject_code FROM Courses WHERE university_id = %s", (university_id,))
#             subject_codes = [code[0] for code in cursor.fetchall()]
#             # Enables dynamic updates.
#             # for entry in form.classes.entries:
#             #     entry.subject_code.choices  = [(code, code) for code in subject_codes]
#             # Make sure we got something back.
#             print("Subject Codes Retrieved:", subject_codes)

#             # Assuming everything worked, send it to populate the field.
#             return jsonify(subject_codes=subject_codes)

#         # Check if the request is an AJAX request for course numbers
#         if request.args.get('action') == 'load_course_numbers':
#             # Get data from the request.
#             subject_code = request.args.get('subject_code')
#             # Debug because getting this to work sucked.
#             # print(f"AJAX request for course numbers: university_id={university_id}, subject_code={subject_code}")
#             # Get course numbers from the db.
#             cursor.execute("SELECT course_number FROM Courses WHERE university_id = %s AND subject_code = %s", (university_id, subject_code))
#             course_numbers = [num[0] for num in cursor.fetchall()]
#             # Print course numbers to make sure it worked.
#             # print("Course Numbers Retrieved:", course_numbers)

#             # Send course numbers that exist for the subject code.
#             return jsonify(course_numbers=course_numbers)
        
#         # Do this once the form is submitted.
#         if form.validate_on_submit():
#             #print(f'Printing form: {form}')
#             #print(f'Printing form class entries: {form.classes.entries}')

#             subject_code = form.subject_code.data
#             course_number = form.course_number.data
#             section_code = form.section_code.data

#             # Multiple forms version - Iterate over class_entry data from multiple classes to get all entries.
#             # for class_entry in form.classes.entries:
#             #     # If the fields are empty, ignore the entry.
#             #     print("Iterating over forms.")
#             #     subject_code = class_entry.subject_code.data
#             #     course_number = class_entry.course_number.data
#             #     section_code = class_entry.section_code.data
#             #     print(f'Subject code: {subject_code}')
#             #     print(f'Course number: : {course_number}')
#             #     print(f'Section code: {section_code}')


#             # See if the course exists (it should, but just in case someone decides to tamper with data or something weird happens.)
#             cursor.execute("SELECT course_id FROM Courses WHERE subject_code = %s AND course_number = %s AND university_id = %s", (subject_code, course_number, university_id))
#             course = cursor.fetchone()
#             #print(f'Checking if course exists: {course}')

#             # If the course doesn't exist, show an error and refresh the page.
#             if not course:
#                 flash("This course does not exist! Contact us with your your error.", "error")
#                 #print('Error block: Course does not exist.')

#                 return redirect(url_for('edit_classes'))
            
#             course_id = course[0]

#             # Check section data to see if combo already exists for the class/section.
#             # We are relying on the user to get the section data correct.
#             cursor.execute("SELECT section_id FROM Sections WHERE course_id = %s AND section_code = %s", (course_id, section_code))
#             section = cursor.fetchone()
#             #print('Checking if section exists.')

            
#             # If the section/course combo exists, skip putting it in the db, otherwise add it.
#             if not section:
#                 print(f'Section doesn\'t exist. Inserting section into database. {course_id}{section_code}')
#                 cursor.execute("INSERT INTO Sections (course_id, section_code) VALUES (%s, %s)", (course_id, section_code))
#                 connection.commit()
#                 section_id = cursor.lastrowid
#             else:
#                 # If the section/course combo already exists, get the section id.
#                 section_id = section[0]
#                 print(f'Section/course combo exists. section id is {section_id}')


#             # Next, the Enrollments table needs to be used to tie the user to the course/section combos.
#             # We check first to see if the enrollment exists.
#             print('Checking if enrollment exists.')

#             cursor.execute("SELECT * FROM Enrollments WHERE user_id = %s AND section_id = %s", (user_id, section_id))
#             enrollment = cursor.fetchone()
#             #print(f'Checking if enrollment exists: {enrollment}')


#             # If the enrollment doesn't exist, add it.
#             if not enrollment:
#                 print(f'Enrollment doesn\'t exist. Inserting into database {user_id}{section_id}')
#                 cursor.execute("INSERT INTO Enrollments (user_id, section_id) VALUES (%s, %s)", (user_id, section_id))
#                 connection.commit()

#             flash("Classes successfully updated!")
#             print("Classes successfully updated!")

#             # Redirect to edit classes page.
#             return redirect(url_for('dashboard'))
    
#     except Exception as e:
#         flash("There was an error editing classes.")
#         print(f"Error editing classes: {e}")
#         connection.rollback()

#     finally:
#         # Close cursor and connection
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()
#     return render_template('edit-classes.html', form=form, university_id=university_id, classes_data=classes_data, courses_dict=courses_dict)
#     # return render_template('edit-classes.html', form=form, university_id=university_id, classes_data=classes_data)


# @app.route('/edit-classes', methods=['GET', 'POST'])
# def edit_classes():
#     if 'user' not in session:
#         return redirect(url_for('login'))

#     user_id = session['user']
#     university_id = session.get('university_id')
    
#     form = ClassEntryForm()

#     try:
#         connection = connect_to_database()
#         cursor = connection.cursor()

#         cursor.execute("""SELECT c.subject_code, c.course_number, s.section_code FROM Sections s 
#                     JOIN Courses c ON s.course_id = c.course_id 
#                     JOIN Enrollments e ON s.section_id = e.section_id WHERE e.user_id = %s""", (user_id,))
        
#         existing_classes = cursor.fetchall()

#         classes_data = [{"subject_code": subject_code, "course_number": course_number, "section_code": section_code}
#             for subject_code, course_number, section_code in existing_classes]

#         cursor.execute("SELECT DISTINCT subject_code, course_number FROM Courses WHERE university_id = %s", (university_id,))
#         all_courses = cursor.fetchall()

#         courses_dict = {}
#         for subject_code, course_number in all_courses:
#             if subject_code not in courses_dict:
#                 courses_dict[subject_code] = []
#             courses_dict[subject_code].append(course_number)

#         cursor.execute("SELECT DISTINCT subject_code FROM Courses WHERE university_id = %s", (university_id,))
#         subject_codes = [code[0] for code in cursor.fetchall()]
#         form.subject_code.choices = [(code, code) for code in subject_codes]

#         if request.method == 'POST':
#             subject_code = form.subject_code.data
#             if subject_code:
#                 cursor.execute("SELECT course_number FROM Courses WHERE university_id = %s AND subject_code = %s", (university_id, subject_code))
#                 course_numbers = [num[0] for num in cursor.fetchall()]
#                 form.course_number.choices = [(num, num) for num in course_numbers]
            
#             if request.args.get('action') == 'load_subject_codes':
#                 university_id = request.args.get('university_id', type=int)

#                 cursor.execute("SELECT DISTINCT subject_code FROM Courses WHERE university_id = %s", (university_id,))
#                 subject_codes = [code[0] for code in cursor.fetchall()]

#                 print("Subject Codes Retrieved:", subject_codes)

#                 # Assuming everything worked, send it to populate the field.
#                 return jsonify(subject_codes=subject_codes)

#             if request.args.get('action') == 'load_course_numbers':
#                 subject_code = request.args.get('subject_code')
               
#                 cursor.execute("SELECT course_number FROM Courses WHERE university_id = %s AND subject_code = %s", (university_id, subject_code))
#                 course_numbers = [num[0] for num in cursor.fetchall()]
                
#                 return jsonify(course_numbers=course_numbers)

#             if form.validate_on_submit():
#                 subject_code = form.subject_code.data
#                 course_number = form.course_number.data
#                 section_code = form.section_code.data

#                 cursor.execute("SELECT course_id FROM Courses WHERE subject_code = %s AND course_number = %s AND university_id = %s", (subject_code, course_number, university_id))
#                 course = cursor.fetchone()

#                 # If the course doesn't exist, show an error and refresh the page.
#                 if not course:
#                     flash("This course does not exist! Contact us with your your error.", "error")

#                     return redirect(url_for('edit_classes'))
                
#                 course_id = course[0]

                
#                 cursor.execute("SELECT section_id FROM Sections WHERE course_id = %s AND section_code = %s", (course_id, section_code))
#                 section = cursor.fetchone()
                
#                 if not section:
#                     print(f'Section doesn\'t exist. Inserting section into database. {course_id}{section_code}')
#                     cursor.execute("INSERT INTO Sections (course_id, section_code) VALUES (%s, %s)", (course_id, section_code))
#                     connection.commit()
#                     section_id = cursor.lastrowid
#                 else:
#                     section_id = section[0]
#                     print(f'Section/course combo exists. section id is {section_id}')


#                 print('Checking if enrollment exists.')

#                 cursor.execute("SELECT * FROM Enrollments WHERE user_id = %s AND section_id = %s", (user_id, section_id))
#                 enrollment = cursor.fetchone()

#                 if not enrollment:
#                     print(f'Enrollment doesn\'t exist. Inserting into database {user_id}{section_id}')
#                     cursor.execute("INSERT INTO Enrollments (user_id, section_id) VALUES (%s, %s)", (user_id, section_id))
#                     connection.commit()

#                 flash("Classes successfully updated!")
#                 print("Classes successfully updated!")

#                 # Redirect to edit classes page.
#                 return redirect(url_for('dashboard'))
    
#     except Exception as e:
#         flash("There was an error editing classes.")
#         print(f"Error editing classes: {e}")
#         connection.rollback()

#     finally:
#         # Close cursor and connection
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()
#     return render_template('edit-classes.html', form=form, university_id=university_id, classes_data=classes_data, courses_dict=courses_dict)
