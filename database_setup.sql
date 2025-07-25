-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS task_manager;

-- Use the database
USE task_manager;

-- Create the tasks table with appropriate data types and constraints
CREATE TABLE IF NOT EXISTS tasks (
    task_id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,
    priority_level ENUM('Low', 'Medium', 'High') NOT NULL,
    status ENUM('Pending', 'In Progress', 'Completed') NOT NULL,
    creation_timestamp DATETIME NOT NULL
);

-- Optional: Create an index for faster filtering
CREATE INDEX idx_due_date ON tasks(due_date);
CREATE INDEX idx_priority ON tasks(priority_level);
CREATE INDEX idx_status ON tasks(status);

