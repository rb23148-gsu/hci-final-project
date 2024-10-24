-- GroupLoop initial MySQL setup file
-- 10/24/2024

CREATE DATABASE grouploop_db;
USE grouploop_db;

CREATE TABLE Universities (
    university_id INT AUTO_INCREMENT PRIMARY KEY,
    university_name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    university_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (university_id) REFERENCES Universities(university_id)
);



CREATE TABLE Courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_code VARCHAR(10) NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    course_number VARCHAR(10) NOT NULL,
    university_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (subject_code, course_number, university_id),
    -- Prevents multiple enrollments in a course.
    FOREIGN KEY (university_id) REFERENCES Universities(university_id)
    
);

CREATE TABLE Sections (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    section_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (section_code, course_id),
    -- Prevents multiple creations of the same course/section combo.
    FOREIGN KEY (course_id) REFERENCES Courses(course_id)
);

CREATE TABLE Enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    section_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, section_id),
    -- Prevents multiple enrollments to one section of a course.
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (section_id) REFERENCES Sections(section_id)
);

CREATE TABLE User_Groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
	group_name VARCHAR(255) NOT NULL,
    group_description VARCHAR(255),
    section_id INT NOT NULL,
    availability VARCHAR(255),
    preferred_meeting_link VARCHAR(255),
    invite_code VARCHAR(10) UNIQUE,
    creator_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (section_id) REFERENCES Sections(section_id),
    FOREIGN KEY (creator_id) REFERENCES Users(user_id)
);

CREATE TABLE Group_Membership (
    group_membership_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT,
    user_id INT,
    is_group_leader BOOLEAN DEFAULT FALSE,
    availability VARCHAR(255),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES User_Groups(group_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT,
    user_id INT,
    availability VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, group_id),
    -- Permits only one availability per user per group.
    FOREIGN KEY (group_id) REFERENCES User_Groups(group_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Group_Post (
    post_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT,
    user_id INT,
    post_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES User_Groups(group_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Post_Comment (
    comment_id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT,
    user_id INT,
    comment_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES Group_Post(post_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

SHOW tables;
