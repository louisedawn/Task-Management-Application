# Task Management Application 
# By Louise Dawn F. Santos

A python command-line task manager with MySQL database integration.


## Features
- Add new tasks with title, description, due date, and priority
- List all tasks with filtering options
- Update task details
- Mark tasks as completed
- Delete tasks
- Persistent storage in MySQL database


## Requirements
- Python 3.8+
- MySQL Server
- PyMySQL library


## Setup Instructions

### 1. Install Requirements
- **Python**: [Download Python](https://www.python.org/downloads/)
- **MySQL**: [Download MySQL Community Server](https://dev.mysql.com/downloads/mysql/)

### 2. Set Up MySQL
1. Start MySQL server
2. Run the database setup script in cmd/bash:
   ```bash
   mysql -u root -p < database_setup.sql

### 3. Complete the setup
3. In terminal install requirements
   ```bash
      pip install -r requirements.txt

4. Run the application:
   ```bash
      python task_manager.py
