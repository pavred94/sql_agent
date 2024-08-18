--- DB GENERATION

CREATE DATABASE student_data OWNER postgres;

--- TABLE GENERATION

CREATE TABLE students (
    student_id INT PRIMARY KEY,     -- Manually assigned unique student ID
    name VARCHAR(100) NOT NULL,     -- Student's name
    university_year INT NOT NULL    -- University year (e.g., 1, 2, 3, 4)
);


CREATE TABLE grades_and_subjects (
    id SERIAL PRIMARY KEY,         -- Auto-incrementing ID
    student_id INT NOT NULL,       -- Foreign key to students.student_id
    subject VARCHAR(100) NOT NULL, -- Name of the subject
    grade DECIMAL(5, 2) NOT NULL,  -- Numeric grade (e.g., 85.50, 92.00)
    CONSTRAINT fk_student          -- Foreign key constraint
        FOREIGN KEY (student_id) REFERENCES students(student_id) 
        ON DELETE CASCADE          -- Automatically delete grades if student is deleted
);

--- SAMPLE DATA

INSERT INTO students (student_id, name, university_year)
VALUES
    (1232, 'Alice Smith', 1),
    (6767, 'Bob Johnson', 2),
    (9873, 'Charlie Brown', 3),
    (1508, 'Diana Prince', 4);

INSERT INTO grades_and_subjects (student_id, subject, grade)
VALUES
    -- Grades for Alice Smith (student_id = 1232)
    (1232, 'Mathematics', 100.00),
    (1232, 'Physics', 87.00),
    (1232, 'Computer Science', 92.00),

    -- Grades for Bob Johnson (student_id = 6767)
    (6767, 'Mathematics', 78.00),
    (6767, 'Biology', 91.00),
    (6767, 'Chemistry', 84.00),

    -- Grades for Charlie Brown (student_id = 9873)
    (9873, 'History', 65.00),
    (9873, 'Mathematics', 72.00),
    (9873, 'English', 80.00),

    -- Grades for Diana Prince (student_id = 1508)
    (1508, 'Art', 98.00),
    (1508, 'History', 89.00),
    (1508, 'Mathematics', 77.00);

--- Example JOIN

SELECT 
    s.student_id,
    s.name AS student_name,
    s.university_year,
    g.subject,
    g.grade
FROM 
    students s
LEFT JOIN 
    grades_and_subjects g
ON 
    s.student_id = g.student_id
ORDER BY 
    s.student_id, g.subject;
