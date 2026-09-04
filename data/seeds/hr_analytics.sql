-- ============================================================
-- hr_analytics.db seed — SmartSQLQuery T-1.10
-- ============================================================

PRAGMA foreign_keys = ON;

-- ── Departments ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    dept_id   INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    location  TEXT
);

INSERT INTO departments (dept_id, name, location) VALUES
  (1, 'Engineering',     'Block A'),
  (2, 'Sales',           'Block B'),
  (3, 'HR',              'Block C'),
  (4, 'Finance',         'Block D'),
  (5, 'Marketing',       'Block B'),
  (6, 'IT',              'Block A'),
  (7, 'Operations',      'Block E');

-- ── Employees ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    employee_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    dept_id       INTEGER NOT NULL,
    job_title     TEXT NOT NULL,
    hire_date     TEXT NOT NULL,
    status        TEXT CHECK(status IN ('active','terminated','on_leave')) DEFAULT 'active',
    manager_id    INTEGER,  -- self-referential FK
    FOREIGN KEY (dept_id)    REFERENCES departments(dept_id),
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
);

INSERT INTO employees (employee_id, name, email, dept_id, job_title, hire_date, status, manager_id) VALUES
  (1,  'Rahul Mehta',     'rahul@corp.com',    1, 'VP Engineering',    '2018-03-01', 'active',     NULL),
  (2,  'Sunita Rao',      'sunita@corp.com',   2, 'VP Sales',          '2019-06-15', 'active',     NULL),
  (3,  'Arjun Nair',      'arjun@corp.com',    1, 'Senior Engineer',   '2020-01-10', 'active',     1),
  (4,  'Priti Shah',      'priti@corp.com',    3, 'HR Manager',        '2017-09-20', 'active',     NULL),
  (5,  'Deepak Verma',    'deepak@corp.com',   4, 'Finance Manager',   '2019-11-05', 'active',     NULL),
  (6,  'Anjali Gupta',    'anjali@corp.com',   5, 'Marketing Lead',    '2021-02-28', 'active',     NULL),
  (7,  'Kiran Pillai',    'kiran@corp.com',    6, 'IT Manager',        '2018-07-12', 'active',     NULL),
  (8,  'Meera Krishnan',  'meera@corp.com',    1, 'Junior Engineer',   '2023-05-01', 'active',     3),
  (9,  'Sanjay Joshi',    'sanjay@corp.com',   2, 'Sales Executive',   '2022-03-15', 'active',     2),
  (10, 'Tanvi Desai',     'tanvi@corp.com',    1, 'Senior Engineer',   '2021-09-01', 'active',     1),
  (11, 'Uday Bhat',       'uday@corp.com',     4, 'Accountant',        '2022-01-10', 'active',     5),
  (12, 'Veena Thomas',    'veena@corp.com',    3, 'HR Executive',      '2023-02-20', 'active',     4),
  (13, 'Wasim Khan',      'wasim@corp.com',    7, 'Operations Lead',   '2020-08-15', 'active',     NULL),
  (14, 'Xerxes Irani',    'xerxes@corp.com',   6, 'System Admin',      '2021-04-10', 'active',     7),
  (15, 'Yamini Reddy',    'yamini@corp.com',   5, 'Marketing Analyst', '2022-07-01', 'terminated', 6),
  (16, 'Zara Sheikh',     'zara@corp.com',     1, 'Junior Engineer',   '2024-01-15', 'active',     3),
  (17, 'Arun Kumar',      'arun@corp.com',     2, 'Sales Manager',     '2020-05-20', 'active',     2),
  (18, 'Bhumi Patel',     'bhumi@corp.com',    7, 'Operations Analyst','2023-03-01', 'active',     13),
  (19, 'Chetan Mishra',   'chetan@corp.com',   4, 'Senior Accountant', '2019-12-01', 'on_leave',   5),
  (20, 'Diya Choudhary',  'diya@corp.com',     6, 'IT Analyst',        '2022-09-05', 'active',     7);

-- ── Salaries ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS salaries (
    salary_id   INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    amount      REAL NOT NULL,
    effective   TEXT NOT NULL,   -- ISO 8601 date
    currency    TEXT DEFAULT 'INR',
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

INSERT INTO salaries (salary_id, employee_id, amount, effective) VALUES
  (1,  1,  2500000, '2023-01-01'),
  (2,  2,  2200000, '2023-01-01'),
  (3,  3,  1200000, '2023-01-01'),
  (4,  4,   900000, '2023-01-01'),
  (5,  5,  1100000, '2023-01-01'),
  (6,  6,   850000, '2023-01-01'),
  (7,  7,   950000, '2023-01-01'),
  (8,  8,   650000, '2023-01-01'),
  (9,  9,   700000, '2023-01-01'),
  (10, 10, 1250000, '2023-01-01'),
  (11, 11,  750000, '2023-01-01'),
  (12, 12,  600000, '2023-01-01'),
  (13, 13,  980000, '2023-01-01'),
  (14, 14,  720000, '2023-01-01'),
  (15, 15,  780000, '2023-01-01'),
  (16, 16,  580000, '2024-01-15'),
  (17, 17, 1050000, '2023-01-01'),
  (18, 18,  630000, '2023-03-01'),
  (19, 19,  890000, '2023-01-01'),
  (20, 20,  710000, '2022-09-05');

-- ── PerformanceReviews ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS performance_reviews (
    review_id   INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    review_date TEXT NOT NULL,
    score       REAL NOT NULL,     -- 1.0 – 5.0
    rating      TEXT CHECK(rating IN ('Outstanding','Exceeds','Meets','Below','Unsatisfactory')),
    reviewer_id INTEGER,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (reviewer_id) REFERENCES employees(employee_id)
);

INSERT INTO performance_reviews (review_id, employee_id, review_date, score, rating, reviewer_id) VALUES
  (1,  3,  '2024-01-15', 4.5, 'Outstanding',  1),
  (2,  8,  '2024-01-15', 3.2, 'Meets',         3),
  (3,  9,  '2024-01-20', 4.0, 'Exceeds',       2),
  (4,  10, '2024-01-15', 4.7, 'Outstanding',   1),
  (5,  11, '2024-01-22', 3.5, 'Meets',          5),
  (6,  12, '2024-01-25', 3.8, 'Meets',          4),
  (7,  14, '2024-01-18', 4.2, 'Exceeds',        7),
  (8,  15, '2024-01-19', 2.5, 'Below',          6),
  (9,  16, '2024-06-01', 3.0, 'Meets',          3),
  (10, 17, '2024-01-20', 4.6, 'Outstanding',    2),
  (11, 18, '2024-01-25', 3.3, 'Meets',         13),
  (12, 19, '2024-01-22', 4.1, 'Exceeds',        5),
  (13, 20, '2024-01-18', 3.9, 'Meets',          7),
  (14, 6,  '2024-01-23', 4.3, 'Exceeds',       NULL),
  (15, 13, '2024-01-24', 4.0, 'Exceeds',       NULL);

-- ── Projects ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    project_id  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    dept_id     INTEGER NOT NULL,
    start_date  TEXT NOT NULL,
    end_date    TEXT,
    status      TEXT CHECK(status IN ('active','completed','on_hold')) DEFAULT 'active',
    budget      REAL DEFAULT 0.0,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO projects (project_id, name, dept_id, start_date, end_date, status, budget) VALUES
  (1, 'Cloud Migration',       1, '2024-01-01', NULL,         'active',    5000000),
  (2, 'CRM Overhaul',          2, '2023-06-01', '2024-03-31', 'completed', 2000000),
  (3, 'HR Digital Transform',  3, '2024-02-01', NULL,         'active',    1500000),
  (4, 'Financial Audit 2024',  4, '2024-04-01', '2024-09-30', 'completed',  800000),
  (5, 'Brand Refresh',         5, '2023-11-01', '2024-05-31', 'completed', 1200000),
  (6, 'ERP Upgrade',           6, '2024-03-01', NULL,         'active',    3500000),
  (7, 'Supply Chain Optimize', 7, '2024-01-15', NULL,         'on_hold',   2200000);

-- ── Project Assignments ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_assignments (
    assignment_id INTEGER PRIMARY KEY,
    project_id    INTEGER NOT NULL,
    employee_id   INTEGER NOT NULL,
    role          TEXT,
    UNIQUE (project_id, employee_id),
    FOREIGN KEY (project_id)  REFERENCES projects(project_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

INSERT INTO project_assignments (assignment_id, project_id, employee_id, role) VALUES
  (1,  1, 1,  'Sponsor'),
  (2,  1, 3,  'Lead Engineer'),
  (3,  1, 10, 'Engineer'),
  (4,  1, 8,  'Tester'),
  (5,  2, 2,  'Owner'),
  (6,  2, 9,  'Analyst'),
  (7,  2, 17, 'Manager'),
  (8,  3, 4,  'Owner'),
  (9,  3, 12, 'Coordinator'),
  (10, 4, 5,  'Owner'),
  (11, 4, 11, 'Analyst'),
  (12, 4, 19, 'Reviewer'),
  (13, 5, 6,  'Owner'),
  (14, 5, 15, 'Analyst'),
  (15, 6, 7,  'Owner'),
  (16, 6, 14, 'Lead Admin'),
  (17, 6, 20, 'Analyst'),
  (18, 7, 13, 'Owner'),
  (19, 7, 18, 'Analyst');
