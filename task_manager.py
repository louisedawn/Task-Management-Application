import uuid
from datetime import datetime
import pymysql
from typing import List, Dict, Optional, Union
from enum import Enum
import config  # Import database configuration from config.py

class PriorityLevel(Enum):
    """Enum representing task priority levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class TaskStatus(Enum):
    """Enum representing task status options"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

class Task:
    """Class representing a single task with all required attributes"""
    def __init__(
        self,
        title: str,
        description: str,
        due_date: str,
        priority_level: PriorityLevel,
        status: TaskStatus = TaskStatus.PENDING,
        task_id: Optional[str] = None,
        creation_timestamp: Optional[str] = None
    ):
        """
        Initialize a Task object
        
        Args:
            title: Task title
            description: Task description
            due_date: Due date in YYYY-MM-DD format
            priority_level: Priority level (Low, Medium, High)
            status: Task status (default: Pending)
            task_id: Unique task ID (auto-generated if not provided)
            creation_timestamp: Creation timestamp (auto-generated if not provided)
        """
        # Generate unique ID if not provided
        self.task_id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority_level = priority_level
        self.status = status
        # Set creation timestamp to current time if not provided
        self.creation_timestamp = creation_timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Union[str, None]]:
        """Convert task object to dictionary for database storage"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "priority_level": self.priority_level.value,
            "status": self.status.value,
            "creation_timestamp": self.creation_timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, None]]) -> 'Task':
        """
        Create Task object from dictionary (typically from database)
        
        Args:
            data: Dictionary containing task attributes
            
        Returns:
            Task object
        """
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            due_date=data["due_date"],
            priority_level=PriorityLevel(data["priority_level"]),
            status=TaskStatus(data["status"]),
            creation_timestamp=data["creation_timestamp"]
        )

class DatabaseManager:
    """Class for managing database connections and queries"""
    def __init__(self, host: str, user: str, password: str, database: str):
        """
        Initialize database connection
        
        Args:
            host: Database host
            user: Database user
            password: Database password
            database: Database name
        """
        try:
            self.connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.Error as e:
            raise ConnectionError(f"Database connection failed: {str(e)}")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute a SQL query that doesn't return results (INSERT, UPDATE, DELETE)

        Returns:
            Number of affected rows
        """
        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.execute(query, params or ())
                self.connection.commit()
                return affected_rows  # Always return an integer
        except pymysql.Error as e:
            self.connection.rollback()
            raise RuntimeError(f"Query execution failed: {str(e)}")


    def fetch_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Execute a SQL query that returns results (SELECT)
        
        Args:
            query: SQL query string
            params: Parameters for the query
            
        Returns:
            List of result dictionaries
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except pymysql.Error as e:
            raise RuntimeError(f"Fetch query failed: {str(e)}")

    def close(self) -> None:
        """Close the database connection"""
        try:
            if self.connection:
                self.connection.close()
        except pymysql.Error as e:
            print(f"Error closing connection: {str(e)}")

class TaskManager:
    """Class for managing task-related operations"""
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize TaskManager with database connection
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def add_task(self, task: Task) -> None:
        """Add a new task to the database"""
        query = """
        INSERT INTO tasks (task_id, title, description, due_date, priority_level, status, creation_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.db_manager.execute_query(query, (
            task.task_id,
            task.title,
            task.description,
            task.due_date,
            task.priority_level.value,
            task.status.value,
            task.creation_timestamp
        ))

    def get_all_tasks(self, filters: Optional[Dict] = None) -> List[Task]:
        """
        Retrieve tasks from database with optional filters
        
        Args:
            filters: Dictionary of filter criteria (due_date, priority_level, status)
            
        Returns:
            List of Task objects
        """
        base_query = "SELECT * FROM tasks"
        params = []
        
        # Build WHERE clause based on filters
        if filters:
            conditions = []
            for key, value in filters.items():
                if key == "due_date":
                    conditions.append(f"due_date = %s")
                    params.append(value)
                elif key == "priority_level":
                    conditions.append(f"priority_level = %s")
                    params.append(value)
                elif key == "status":
                    conditions.append(f"status = %s")
                    params.append(value)
            
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
        
        # Execute query and convert results to Task objects
        tasks_data = self.db_manager.fetch_query(base_query, tuple(params)) if params else self.db_manager.fetch_query(base_query)
        return [Task.from_dict(task) for task in tasks_data]

    def update_task(self, task_id: str, updates: Dict) -> bool:
        """Update task attributes"""
        if not updates:
            return False

        set_clauses = []
        params = []

        for key, value in updates.items():
            if key == "priority_level":
                set_clauses.append("priority_level = %s")
                params.append(value.value if isinstance(value, PriorityLevel) else value)
            elif key == "status":
                set_clauses.append("status = %s")
                params.append(value.value if isinstance(value, TaskStatus) else value)
            else:
                set_clauses.append(f"{key} = %s")
                params.append(value)

        params.append(task_id)

        query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = %s"
        affected = self.db_manager.execute_query(query, tuple(params))
        return affected > 0


    def delete_task(self, task_id: str) -> bool:
        """Delete a task from the database"""
        query = "DELETE FROM tasks WHERE task_id = %s"
        affected = self.db_manager.execute_query(query, (task_id,))
        return affected > 0

    def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed"""
        return self.update_task(task_id, {"status": TaskStatus.COMPLETED})

class TaskManagerCLI:
    """Command-line interface for task management application"""
    def __init__(self, task_manager: TaskManager):
        """
        Initialize CLI with TaskManager
        
        Args:
            task_manager: TaskManager instance
        """
        self.task_manager = task_manager

    def display_menu(self) -> None:
        """Display the main menu options"""
        print("\nTask Management Application")
        print("1. Add a new task")
        print("2. List all tasks")
        print("3. Update a task")
        print("4. Mark a task as completed")
        print("5. Delete a task")
        print("6. Exit")

    def add_task(self) -> None:
        """Handle adding a new task"""
        print("\nAdd a New Task")
        title = input("Title: ").strip()
        if not title:
            print("Error: Title cannot be empty!")
            return
            
        description = input("Description: ").strip()
        due_date = input("Due Date (YYYY-MM-DD): ").strip()
        
        # Validate date format
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return
        
        print("Priority Level:")
        for i, level in enumerate(PriorityLevel, 1):
            print(f"{i}. {level.value}")
        priority_choice = input("Select priority (1-3): ").strip()
        
        try:
            priority_level = list(PriorityLevel)[int(priority_choice) - 1]
        except (ValueError, IndexError):
            print("Invalid priority selection. Using 'Medium' as default.")
            priority_level = PriorityLevel.MEDIUM
        
        # Create and add task
        task = Task(title, description, due_date, priority_level)
        self.task_manager.add_task(task)
        print("Task added successfully!")

    def list_tasks(self) -> None:
        """List tasks with optional filtering"""
        print("\nFilter Options:")
        print("1. No filter/Display All Tasks")
        print("2. Filter by due date")
        print("3. Filter by priority")
        print("4. Filter by status")
        filter_choice = input("Select filter option (1-4): ").strip()
        
        filters = {}
        if filter_choice == "2":
            due_date = input("Enter due date to filter (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
                filters["due_date"] = due_date
            except ValueError:
                print("Invalid date format. No date filter applied.")
        elif filter_choice == "3":
            print("Priority Levels:")
            for i, level in enumerate(PriorityLevel, 1):
                print(f"{i}. {level.value}")
            priority_choice = input("Select priority to filter (1-3): ").strip()
            try:
                priority_level = list(PriorityLevel)[int(priority_choice) - 1]
                filters["priority_level"] = priority_level.value
            except (ValueError, IndexError):
                print("Invalid priority selection. No priority filter applied.")
        elif filter_choice == "4":
            print("Status Options:")
            for i, status in enumerate(TaskStatus, 1):
                print(f"{i}. {status.value}")
            status_choice = input("Select status to filter (1-3): ").strip()
            try:
                status = list(TaskStatus)[int(status_choice) - 1]
                filters["status"] = status.value
            except (ValueError, IndexError):
                print("Invalid status selection. No status filter applied.")
        
        # Retrieve and display tasks
        try:
            tasks = self.task_manager.get_all_tasks(filters)
        except Exception as e:
            print(f"Error retrieving tasks: {str(e)}")
            return
        
        if not tasks:
            print("No tasks found.")
            return
        
        print("\nTasks:")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. ID: {task.task_id}")
            print(f"   Title: {task.title}")
            print(f"   Description: {task.description}")
            print(f"   Due Date: {task.due_date}")
            print(f"   Priority: {task.priority_level.value}")
            print(f"   Status: {task.status.value}")
            print(f"   Created: {task.creation_timestamp}")
            print("-" * 40)

    def update_task(self) -> None:
        """Update an existing task"""
        task_id = input("Enter task ID to update: ").strip()
        if not task_id:
            print("Error: Task ID cannot be empty!")
            return
        
        try:
            success = self.task_manager.mark_task_completed(task_id)
            if success:
                print("✅ Task marked as completed!")
            else:
                print("⚠️ No task found with that ID. Nothing was updated.")
        except Exception as e:
            print(f"Error marking task as completed: {str(e)}")
        
        print("\nSelect field to update:")
        print("1. Title")
        print("2. Description")
        print("3. Due Date")
        print("4. Priority Level")
        print("5. Status")
        field_choice = input("Select field (1-5): ").strip()
        
        updates = {}
        if field_choice == "1":
            new_title = input("New title: ").strip()
            if not new_title:
                print("Error: Title cannot be empty!")
                return
            updates["title"] = new_title
        elif field_choice == "2":
            updates["description"] = input("New description: ").strip()
        elif field_choice == "3":
            new_date = input("New due date (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(new_date, "%Y-%m-%d")
                updates["due_date"] = new_date
            except ValueError:
                print("Invalid date format. Update cancelled.")
                return
        elif field_choice == "4":
            print("Priority Levels:")
            for i, level in enumerate(PriorityLevel, 1):
                print(f"{i}. {level.value}")
            priority_choice = input("Select new priority (1-3): ").strip()
            try:
                updates["priority_level"] = list(PriorityLevel)[int(priority_choice) - 1]
            except (ValueError, IndexError):
                print("Invalid priority selection. Update cancelled.")
                return
        elif field_choice == "5":
            print("Status Options:")
            for i, status in enumerate(TaskStatus, 1):
                print(f"{i}. {status.value}")
            status_choice = input("Select new status (1-3): ").strip()
            try:
                updates["status"] = list(TaskStatus)[int(status_choice) - 1]
            except (ValueError, IndexError):
                print("Invalid status selection. Update cancelled.")
                return
        else:
            print("Invalid field selection. Update cancelled.")
            return
        
        # Perform update
        try:
            success = self.task_manager.update_task(task_id, updates)
            if success:
                print("✅ Task updated successfully!")
            else:
                print("⚠️ No task found with that ID. Update failed.")
        except Exception as e:
            print(f"Error updating task: {str(e)}")

    def mark_task_completed(self) -> None:
        """Mark a task as completed"""
        task_id = input("Enter task ID to mark as completed: ").strip()
        if not task_id:
            print("Error: Task ID cannot be empty!")
            return
            
        try:
            success = self.task_manager.mark_task_completed(task_id)
            if success:
                print("✅ Task marked as completed!")
            else:
                print("⚠️ No task found with that ID. Nothing was updated.")
        except Exception as e:
            print(f"Error marking task as completed: {str(e)}")

    def delete_task(self) -> None:
        """Delete a task"""
        task_id = input("Enter task ID to delete: ").strip()
        if not task_id:
            print("Error: Task ID cannot be empty!")
            return

        try:
            success = self.task_manager.delete_task(task_id)
            if success:
                print("✅ Task deleted successfully!")
            else:
                print("⚠️ No task found with that ID. Nothing was deleted.")
        except Exception as e:
            print(f"Error deleting task: {str(e)}")


    def run(self) -> None:
        """Main application loop"""
        while True:
            try:
                self.display_menu()
                choice = input("Select an option (1-6): ").strip()
                
                if choice == "1":
                    self.add_task()
                elif choice == "2":
                    self.list_tasks()
                elif choice == "3":
                    self.update_task()
                elif choice == "4":
                    self.mark_task_completed()
                elif choice == "5":
                    self.delete_task()
                elif choice == "6":
                    print("Exiting application. Goodbye!")
                    break
                else:
                    print("Invalid choice. Please select a number between 1 and 6.")
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")

def main():
    """Main function to start the application"""
    try:
        # Initialize database connection
        db_manager = DatabaseManager(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        
        # Initialize task manager and CLI
        task_manager = TaskManager(db_manager)
        cli = TaskManagerCLI(task_manager)
        
        # Start CLI
        cli.run()
    except Exception as e:
        print(f"Failed to initialize application: {str(e)}")
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    main()



####### Louise Dawn F. Santos - Task Management Application #######
