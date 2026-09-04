-- ============================================================
-- university.db seed — SmartSQLQuery T-1.08
-- Run via: python scripts/seed_all.py
-- ============================================================

PRAGMA foreign_keys = ON;

-- ── Departments ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    dept_id   INTEGER PRIMARY KEY,
    code      TEXT NOT NULL UNIQUE,   -- e.g. 'CSE', 'MATH'
    name      TEXT NOT NULL,          -- e.g. 'Computer Science and Engineering'
    building  TEXT,
    budget    REAL DEFAULT 0.0
);

INSERT INTO departments (dept_id, code, name, building, budget) VALUES
  (1, 'CSE',  'Computer Science and Engineering', 'Tech Block A', 1500000.00),
  (2, 'MATH', 'Mathematics',                       'Science Wing',  900000.00),
  (3, 'PHY',  'Physics',                           'Science Wing',  750000.00),
  (4, 'MBA',  'Business Administration',            'Commerce Hall',1200000.00),
  (5, 'EEE',  'Electrical and Electronics',         'Tech Block B',  980000.00);

-- ── Instructors ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS instructors (
    instructor_id INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    dept_id       INTEGER NOT NULL,
    rank          TEXT CHECK(rank IN ('Assistant','Associate','Professor')) DEFAULT 'Assistant',
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO instructors (instructor_id, name, email, dept_id, rank) VALUES
  (1, 'Dr. Ananya Rao',     'a.rao@univ.edu',      1, 'Professor'),
  (2, 'Prof. Ravi Sharma',  'r.sharma@univ.edu',   1, 'Associate'),
  (3, 'Dr. Meena Pillai',   'm.pillai@univ.edu',   2, 'Professor'),
  (4, 'Dr. Suresh Kumar',   's.kumar@univ.edu',    3, 'Assistant'),
  (5, 'Prof. Nita Joshi',   'n.joshi@univ.edu',    4, 'Associate'),
  (6, 'Dr. Farhan Ahmed',   'f.ahmed@univ.edu',    5, 'Professor');

-- ── Students ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    student_id  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    dept_id     INTEGER NOT NULL,
    gpa         REAL DEFAULT 0.0,     -- 0.0 – 4.0 scale
    year        INTEGER DEFAULT 1,    -- 1=Freshman … 4=Senior
    status      TEXT CHECK(status IN ('active','inactive','graduated')) DEFAULT 'active',
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO students (student_id, name, email, dept_id, gpa, year, status) VALUES
  (1,  'Alice Thomas',     'alice@univ.edu',   1, 3.92, 3, 'active'),
  (2,  'Bob Menon',        'bob@univ.edu',     1, 2.85, 2, 'active'),
  (3,  'Chitra Nair',      'chitra@univ.edu',  2, 3.75, 4, 'active'),
  (4,  'Dev Patel',        'dev@univ.edu',     1, 3.50, 1, 'active'),
  (5,  'Eva Singh',        'eva@univ.edu',     3, 3.20, 2, 'active'),
  (6,  'Frank D Souza',    'frank@univ.edu',   4, 2.60, 3, 'active'),
  (7,  'Gita Reddy',       'gita@univ.edu',    1, 3.88, 4, 'active'),
  (8,  'Hari Krishnan',    'hari@univ.edu',    2, 3.10, 1, 'active'),
  (9,  'Isha Desai',       'isha@univ.edu',    5, 2.95, 2, 'active'),
  (10, 'Jay Kapoor',       'jay@univ.edu',     4, 3.45, 3, 'active'),
  (11, 'Kavya Iyer',       'kavya@univ.edu',   1, 3.91, 4, 'active'),
  (12, 'Liam Fernandez',   'liam@univ.edu',    3, 2.40, 2, 'active'),
  (13, 'Mia George',       'mia@univ.edu',     2, 3.60, 3, 'active'),
  (14, 'Nikhil Bose',      'nikhil@univ.edu',  5, 3.30, 1, 'active'),
  (15, 'Olivia Chatterjee','olivia@univ.edu',  1, 2.75, 4, 'inactive'),
  (16, 'Priya Saxena',     'priya@univ.edu',   4, 3.80, 2, 'active'),
  (17, 'Qasim Shaikh',     'qasim@univ.edu',   1, 3.55, 3, 'active'),
  (18, 'Ritika Verma',     'ritika@univ.edu',  2, 2.90, 4, 'graduated'),
  (19, 'Sonu Mishra',      'sonu@univ.edu',    1, 3.20, 1, 'active'),
  (20, 'Tanya Malhotra',   'tanya@univ.edu',   5, 3.65, 3, 'active');

-- ── Courses ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS courses (
    course_id   INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,  -- e.g. 'CS101'
    title       TEXT NOT NULL,
    dept_id     INTEGER NOT NULL,
    credits     INTEGER DEFAULT 3,
    instructor_id INTEGER,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
);

INSERT INTO courses (course_id, code, title, dept_id, credits, instructor_id) VALUES
  (1,  'CS101', 'Intro to Programming',        1, 3, 1),
  (2,  'CS201', 'Data Structures',             1, 4, 2),
  (3,  'CS301', 'Database Systems',            1, 3, 1),
  (4,  'CS401', 'Machine Learning',            1, 4, 2),
  (5,  'MA101', 'Calculus I',                  2, 4, 3),
  (6,  'MA201', 'Linear Algebra',              2, 3, 3),
  (7,  'PH101', 'Classical Mechanics',         3, 4, 4),
  (8,  'PH201', 'Quantum Physics',             3, 3, 4),
  (9,  'MB101', 'Principles of Management',    4, 3, 5),
  (10, 'EE101', 'Circuit Theory',              5, 4, 6),
  (11, 'CS302', 'Computer Networks',           1, 3, 1),
  (12, 'MA301', 'Probability & Statistics',    2, 3, 3);

-- ── Enrollments ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY,
    student_id    INTEGER NOT NULL,
    course_id     INTEGER NOT NULL,
    semester      TEXT NOT NULL,   -- e.g. '2024-Fall'
    UNIQUE (student_id, course_id, semester),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)
);

INSERT INTO enrollments (enrollment_id, student_id, course_id, semester) VALUES
  (1,  1,  1,  '2024-Fall'),
  (2,  1,  2,  '2024-Fall'),
  (3,  1,  3,  '2024-Fall'),
  (4,  2,  1,  '2024-Fall'),
  (5,  2,  5,  '2024-Fall'),
  (6,  3,  5,  '2024-Fall'),
  (7,  3,  6,  '2024-Fall'),
  (8,  4,  1,  '2024-Fall'),
  (9,  4,  2,  '2024-Fall'),
  (10, 5,  7,  '2024-Fall'),
  (11, 6,  9,  '2024-Fall'),
  (12, 7,  2,  '2024-Fall'),
  (13, 7,  3,  '2024-Fall'),
  (14, 7,  4,  '2024-Fall'),
  (15, 8,  5,  '2024-Fall'),
  (16, 9,  10, '2024-Fall'),
  (17, 10, 9,  '2024-Fall'),
  (18, 11, 1,  '2024-Fall'),
  (19, 11, 2,  '2024-Fall'),
  (20, 11, 4,  '2024-Fall'),
  (21, 13, 6,  '2024-Fall'),
  (22, 14, 10, '2024-Fall'),
  (23, 16, 9,  '2024-Fall'),
  (24, 17, 3,  '2024-Fall'),
  (25, 19, 1,  '2024-Fall'),
  (26, 20, 10, '2024-Fall'),
  (27, 1,  11, '2025-Spring'),
  (28, 7,  11, '2025-Spring'),
  (29, 4,  12, '2025-Spring'),
  (30, 8,  12, '2025-Spring');

-- ── Grades ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grades (
    grade_id      INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL UNIQUE,
    score         REAL NOT NULL,   -- 0–100
    letter_grade  TEXT,            -- 'A','B','C','D','F'
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
);

INSERT INTO grades (grade_id, enrollment_id, score, letter_grade) VALUES
  (1,  1,  91.5, 'A'),
  (2,  2,  88.0, 'A'),
  (3,  3,  85.5, 'A'),
  (4,  4,  72.0, 'B'),
  (5,  5,  68.0, 'C'),
  (6,  6,  92.0, 'A'),
  (7,  7,  87.5, 'A'),
  (8,  8,  79.0, 'B'),
  (9,  9,  83.0, 'B'),
  (10, 10, 70.0, 'B'),
  (11, 11, 55.0, 'D'),
  (12, 12, 94.0, 'A'),
  (13, 13, 89.0, 'A'),
  (14, 14, 91.0, 'A'),
  (15, 15, 76.0, 'B'),
  (16, 16, 66.0, 'C'),
  (17, 17, 60.0, 'C'),
  (18, 18, 95.0, 'A'),
  (19, 19, 90.0, 'A'),
  (20, 20, 87.0, 'A'),
  (21, 21, 82.0, 'B'),
  (22, 22, 73.0, 'B'),
  (23, 23, 78.0, 'B'),
  (24, 24, 81.0, 'B'),
  (25, 25, 62.0, 'C'),
  (26, 26, 84.0, 'B'),
  (27, 27, 88.0, 'A'),
  (28, 28, 90.0, 'A'),
  (29, 29, 77.0, 'B'),
  (30, 30, 69.0, 'C');
