CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  firstName VARCHAR(50),
  lastName VARCHAR(50),
  email VARCHAR(100),
  birthDate DATE,
  specialNote TEXT,
  loyaltyPoints INT DEFAULT 0
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  price DECIMAL(10, 2),
  description TEXT,
  inStock BOOLEAN,
  categoryId INT,
  weight FLOAT
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customerId INT REFERENCES customers(id),
  orderDate TIMESTAMP,
  totalAmount DECIMAL(10, 2),
  status VARCHAR(20),
  shippingMethod VARCHAR(50)
);

-- Neue Tabellen
CREATE TABLE categories (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50),
  parentCategoryId INT REFERENCES categories(id)
);

CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  orderId INT REFERENCES orders(id),
  productId INT REFERENCES products(id),
  quantity INT,
  unitPrice DECIMAL(10, 2)
);

CREATE TABLE inventory (
  id SERIAL PRIMARY KEY,
  productId INT REFERENCES products(id),
  quantity INT,
  lastRestockDate DATE
);

-- Erweiterte Testdaten
INSERT INTO customers (firstName, lastName, email, birthDate, specialNote, loyaltyPoints)
VALUES
('John', 'Doe', 'john.doe@example.com', '1990-05-15', 'VIP customer*', 500),
('Jane', 'Smith', 'jane.smith@example.com', '1985-12-03', 'Prefers email\contact', 250),
('Mike', 'Johnson', 'mike.johnson@example.com', '1978-08-22', 'Allergic to nuts;', 100),
('Emily*', '%Brown', 'emily.brown@example.com', '1995-02-28', 'New customer: follow up!', 50),
('David', 'Wilson', 'david.wilson@example.com', '1982-07-10', 'Frequent buyer', 750),
('Sarah', 'Taylor', 'sarah.taylor@example.com', '1993-11-18', 'Prefers phone calls', 300),
('Robert', 'Anderson', 'robert.anderson@example.com', '1975-09-30', 'Corporate account', 1000),
('Lisa', 'Martinez', 'lisa.martinez@example.com', '1988-04-05', 'Eco-friendly products only', 450),
('Thomas', 'Garcia', 'thomas.garcia@example.com', '1992-01-20', 'Student discount applied', 200),
('Jennifer', 'Lopez', 'jennifer.lopez@example.com', '1980-06-12', 'Birthday in June', 600),
('Mich!?l#', 'Lee@LeeTestChar=?{}()', 'michael.lee@example.com', '1987-03-25', 'Tech enthusiast', 350),
('Emma-Hans', '0Clark$', 'emma.clark@example.com', '1998-08-08', 'First-time buyer', 25);

INSERT INTO categories (name, parentCategoryId)
VALUES
('Electronics', NULL),
('Computers', 1),
('Smartphones', 1),
('Audio', 1),
('Accessories', NULL),
('Books', NULL),
('Home & Kitchen', NULL);

INSERT INTO products (name, price, description, inStock, categoryId, weight)
VALUES
('Laptop Pro X', 1299.99, 'High-performance laptop with 16GB RAM', true, 2, 2.5),
('Smartphone Y', 699.99, 'Latest model with 5G and 128GB storage', true, 3, 0.2),
('Noise-Cancelling Headphones', 249.99, 'Over-ear headphones with 20h battery life', false, 4, 0.3),
('10" Tablet', 399.99, 'Full HD display, perfect for reading and browsing', true, 2, 0.5),
('Wireless Mouse', 39.99, 'Ergonomic design with long battery life', true, 5, 0.1),
('Smart Watch', 199.99, 'Fitness tracking and notifications', true, 3, 0.05),
('Bluetooth Speaker', 89.99, 'Waterproof with 360-degree sound', true, 4, 0.4),
('E-reader', 129.99, '6" display with backlight', true, 6, 0.17),
('Coffee Maker', 79.99, '12-cup programmable coffee maker', true, 7, 2.0),
('External Hard Drive', 89.99, '2TB storage capacity', true, 2, 0.3),
('Wireless Keyboard', 59.99, 'Slim design with numeric keypad', true, 5, 0.7),
('Smart Bulb Set', 49.99, 'Color changing, voice-controlled', true, 7, 0.2);

INSERT INTO inventory (productId, quantity, lastRestockDate)
VALUES
(1, 50, '2024-03-01'),
(2, 100, '2024-03-05'),
(3, 0, '2024-02-15'),
(4, 30, '2024-03-10'),
(5, 200, '2024-03-12'),
(6, 75, '2024-03-08'),
(7, 60, '2024-03-07'),
(8, 40, '2024-03-03'),
(9, 25, '2024-03-09'),
(10, 80, '2024-03-11'),
(11, 150, '2024-03-06'),
(12, 100, '2024-03-04');

INSERT INTO orders (customerId, orderDate, totalAmount, status, shippingMethod)
VALUES
(1, '2024-03-15 10:30:00', 1599.98, 'Completed', 'Express'),
(2, '2024-03-16 14:45:00', 699.99, 'Processing', 'Standard'),
(3, '2024-03-17 09:15:00', 549.98, 'Shipped', 'Express'),
(4, '2024-03-18 16:20:00', 999.99, 'Pending', 'Standard'),
(5, '2024-03-19 11:00:00', 289.98, 'Completed', 'Express'),
(1, '2024-03-20 13:30:00', 449.98, 'Shipped', 'Standard'),
(6, '2024-03-21 10:45:00', 199.99, 'Processing', 'Express'),
(7, '2024-03-22 15:20:00', 1399.97, 'Completed', 'Standard'),
(8, '2024-03-23 09:00:00', 129.99, 'Shipped', 'Standard'),
(9, '2024-03-24 14:10:00', 89.99, 'Pending', 'Express'),
(10, '2024-03-25 12:30:00', 299.98, 'Processing', 'Standard'),
(2, '2024-03-26 11:15:00', 139.98, 'Completed', 'Express'),
(3, '2024-03-27 16:45:00', 249.99, 'Shipped', 'Standard'),
(11, '2024-03-28 10:00:00', 1299.99, 'Pending', 'Express'),
(12, '2024-03-29 13:20:00', 79.99, 'Processing', 'Standard'),
(4, '2024-03-30 15:30:00', 189.98, 'Completed', 'Express');

INSERT INTO order_items (orderId, productId, quantity, unitPrice)
VALUES
(1, 1, 1, 1299.99),
(1, 5, 1, 39.99),
(2, 2, 1, 699.99),
(3, 4, 1, 399.99),
(3, 7, 1, 89.99),
(4, 1, 1, 1299.99),
(5, 6, 1, 199.99),
(5, 11, 1, 59.99),
(6, 8, 1, 129.99),
(6, 10, 1, 89.99),
(7, 6, 1, 199.99),
(8, 1, 1, 1299.99),
(8, 5, 1, 39.99),
(8, 11, 1, 59.99),
(9, 8, 1, 129.99),
(10, 7, 1, 89.99),
(11, 6, 1, 199.99),
(11, 12, 1, 49.99),
(12, 5, 1, 39.99),
(12, 11, 1, 59.99),
(13, 3, 1, 249.99),
(14, 1, 1, 1299.99),
(15, 9, 1, 79.99),
(16, 6, 1, 199.99),
(16, 10, 1, 89.99);