import pymysql

connection = 

def parse_course_line(line):
    parts = line.split(" - ")
    course_code = parts[0]
    course_description = parts[1].split("(")[0].strip()
    subject_code, course_number = course_code.split()
    return subject_code, course_number, course_description

def insert_course_to_db(cursor, course_code, course_id, course_name):    
    sql = "INSERT INTO Courses (subject_code, subject_name, course_number, university_id) VALUES (%s, %s, %s, 1)"
    cursor.execute(sql, (course_code, course_name, course_id))

def upload_courses(file_path):
    with connection.cursor() as cursor:
        with open(file_path, "r") as file:
            for line in file:
                if line.strip():
                    subject_code, course_id, course_name = parse_course_line(line)
                    insert_course_to_db(cursor, subject_code, course_id, course_name)
        connection.commit()

file_path = "courses.txt"
upload_courses(file_path)

connection.close()
