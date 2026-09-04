-- ============================================================
-- ecommerce.db seed — SmartSQLQuery T-1.09
-- ============================================================

PRAGMA foreign_keys = ON;

-- ── Categories ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);

INSERT INTO categories (category_id, name, description) VALUES
  (1, 'Electronics',   'Gadgets, devices, and accessories'),
  (2, 'Clothing',      'Apparel for all ages'),
  (3, 'Books',         'Fiction, non-fiction, and educational'),
  (4, 'Home & Garden', 'Furniture, décor, and garden supplies'),
  (5, 'Sports',        'Equipment and sportswear'),
  (6, 'Toys',          'Children toys and games');

-- ── Products ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    price       REAL NOT NULL,
    stock       INTEGER DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

INSERT INTO products (product_id, name, category_id, price, stock) VALUES
  (1,  'Wireless Headphones',  1, 2999.00,  50),
  (2,  'Smartphone X12',       1, 45999.00,  20),
  (3,  'Laptop Pro 15',        1, 89999.00,  10),
  (4,  'USB-C Hub',            1,   999.00, 200),
  (5,  'Running Shoes',        5,  3499.00,  80),
  (6,  'Yoga Mat',             5,   799.00, 120),
  (7,  'Cricket Bat',          5,  1500.00,  40),
  (8,  'Men T-Shirt',          2,   499.00, 300),
  (9,  'Women Jeans',          2,  1299.00, 150),
  (10, 'Python Cookbook',      3,   599.00,  60),
  (11, 'Design Patterns',      3,   750.00,  35),
  (12, 'Garden Hose 10m',      4,   999.00,  25),
  (13, 'Wall Clock',           4,   399.00,  70),
  (14, 'LEGO City Set',        6,  2499.00,  45),
  (15, 'Puzzle 1000 pieces',   6,   350.00,  90);

-- ── Customers ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    city        TEXT,
    joined_date TEXT NOT NULL   -- ISO 8601 date string
);

INSERT INTO customers (customer_id, name, email, city, joined_date) VALUES
  (1,  'Amit Kumar',       'amit@mail.com',    'Mumbai',    '2022-01-15'),
  (2,  'Bhavna Rao',       'bhavna@mail.com',  'Bangalore', '2022-03-20'),
  (3,  'Carlos Mendes',    'carlos@mail.com',  'Pune',      '2022-06-10'),
  (4,  'Divya Sharma',     'divya@mail.com',   'Chennai',   '2022-07-05'),
  (5,  'Elena Fernandez',  'elena@mail.com',   'Hyderabad', '2022-09-18'),
  (6,  'Farhan Ali',       'farhan@mail.com',  'Delhi',     '2023-01-02'),
  (7,  'Geetha Pillai',    'geetha@mail.com',  'Kolkata',   '2023-02-14'),
  (8,  'Harsh Malhotra',   'harsh@mail.com',   'Mumbai',    '2023-04-22'),
  (9,  'Isha Patel',       'isha@mail.com',    'Surat',     '2023-06-30'),
  (10, 'Jyothi Reddy',     'jyothi@mail.com',  'Bangalore', '2023-08-11');

-- ── Orders ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date  TEXT NOT NULL,
    status      TEXT CHECK(status IN ('pending','shipped','delivered','cancelled','refunded'))
                    DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

INSERT INTO orders (order_id, customer_id, order_date, status) VALUES
  (1,  1, '2024-01-10', 'delivered'),
  (2,  1, '2024-03-05', 'delivered'),
  (3,  2, '2024-01-20', 'delivered'),
  (4,  3, '2024-02-14', 'shipped'),
  (5,  4, '2024-02-28', 'delivered'),
  (6,  5, '2024-03-15', 'refunded'),
  (7,  6, '2024-04-01', 'cancelled'),
  (8,  7, '2024-04-10', 'delivered'),
  (9,  8, '2024-05-05', 'delivered'),
  (10, 9, '2024-05-20', 'pending'),
  (11, 1, '2024-06-01', 'delivered'),
  (12, 2, '2024-06-15', 'shipped'),
  (13, 10,'2024-06-25', 'delivered'),
  (14, 3, '2024-07-04', 'delivered'),
  (15, 4, '2024-07-20', 'delivered');

-- ── OrderItems ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    item_id     INTEGER PRIMARY KEY,
    order_id    INTEGER NOT NULL,
    product_id  INTEGER NOT NULL,
    quantity    INTEGER NOT NULL DEFAULT 1,
    unit_price  REAL NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price) VALUES
  (1,  1,  1,  1,  2999.00),
  (2,  1,  4,  2,   999.00),
  (3,  2,  10, 1,   599.00),
  (4,  2,  11, 1,   750.00),
  (5,  3,  2,  1, 45999.00),
  (6,  4,  5,  1,  3499.00),
  (7,  4,  6,  1,   799.00),
  (8,  5,  8,  3,   499.00),
  (9,  5,  9,  1,  1299.00),
  (10, 6,  3,  1, 89999.00),
  (11, 7,  14, 1,  2499.00),
  (12, 8,  7,  2,  1500.00),
  (13, 9,  1,  1,  2999.00),
  (14, 9,  4,  1,   999.00),
  (15, 10, 15, 2,   350.00),
  (16, 11, 2,  1, 45999.00),
  (17, 12, 5,  2,  3499.00),
  (18, 13, 13, 1,   399.00),
  (19, 13, 12, 1,   999.00),
  (20, 14, 10, 2,   599.00),
  (21, 15, 8,  5,   499.00),
  (22, 15, 9,  2,  1299.00);

-- ── Payments ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    payment_id  INTEGER PRIMARY KEY,
    order_id    INTEGER NOT NULL UNIQUE,
    amount      REAL NOT NULL,
    method      TEXT CHECK(method IN ('card','upi','netbanking','cod')) DEFAULT 'card',
    paid_date   TEXT,
    status      TEXT CHECK(status IN ('paid','pending','refunded','failed')) DEFAULT 'pending',
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

INSERT INTO payments (payment_id, order_id, amount, method, paid_date, status) VALUES
  (1,  1,  4997.00,  'upi',        '2024-01-10', 'paid'),
  (2,  2,  1349.00,  'card',       '2024-03-05', 'paid'),
  (3,  3,  45999.00, 'netbanking', '2024-01-20', 'paid'),
  (4,  4,  4298.00,  'upi',        '2024-02-14', 'paid'),
  (5,  5,  2796.00,  'cod',        '2024-02-28', 'paid'),
  (6,  6,  89999.00, 'card',       '2024-03-15', 'refunded'),
  (7,  7,  2499.00,  'upi',        NULL,          'failed'),
  (8,  8,  3000.00,  'card',       '2024-04-10', 'paid'),
  (9,  9,  3998.00,  'upi',        '2024-05-05', 'paid'),
  (10, 10, 700.00,   'cod',        NULL,          'pending'),
  (11, 11, 45999.00, 'card',       '2024-06-01', 'paid'),
  (12, 12, 6998.00,  'upi',        '2024-06-16', 'paid'),
  (13, 13, 1398.00,  'netbanking', '2024-06-25', 'paid'),
  (14, 14, 1198.00,  'card',       '2024-07-04', 'paid'),
  (15, 15, 5043.00,  'upi',        '2024-07-20', 'paid');
