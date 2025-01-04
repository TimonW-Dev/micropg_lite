-- Create the database
CREATE DATABASE exampledatabase;

-- !IMPORTANT! You have to switch to the new database which just was created
-- In PGAdmin4 you have to refresh the left tab, then select the new database and open the query tool

-- Create Table for testing
CREATE TABLE customers (
  id INT PRIMARY KEY,
  firstName VARCHAR(50),
  lastName VARCHAR(50),
  email VARCHAR(100)
);

-- Insert data for testing
INSERT INTO customers (id, firstName, lastName, email)
VALUES
(1, 'John', 'Doe', 'john.doe@example.com'),
(2, 'Jane', 'Smith', 'jane.smith@example.com'),
(3, 'Mike', 'Johnson', 'mike.johnson@example.com'),
(4, 'Emily', 'Brown', 'emily.brown@example.com');