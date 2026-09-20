from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
import sqlite3

app = FastAPI()

# Pydantic models (Same as before)
class TaskCreate(BaseModel):
    title: str
    done: bool = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

class Task(BaseModel):
    id: int
    title: str
    done: bool

# Stage 0: Database connection helper
def get_db_connection():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row  # Returns rows as dictionaries
    return conn

# Stage 0: Initialize database and seed if empty
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL CHECK (done IN (0, 1))
        )
    ''')
    
    # Count rows to prevent duplicating seeded tasks on restart
    count = cursor.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    
    if count == 0:
        sample_tasks = [
            ("Buy milk", 0),
            ("Read book", 1),
            ("Complete assignment", 0)
        ]
        cursor.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", sample_tasks)
        conn.commit()
        
    conn.close()

# Run DB initialization when the app starts
init_db()


# Original Root and health endpoints
@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    return {"status": "ok"}


# Stage 1: Read all tasks
@app.get("/tasks", response_model=List[Task])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in tasks]

# Stage 1: Read a single task by ID
@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    conn = get_db_connection()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    return {"id": task["id"], "title": task["title"], "done": bool(task["done"])}


# Stage 2: Create a new task (POST)
@app.post("/tasks", status_code=status.HTTP_201_CREATED, response_model=Task)
def create_task(task: TaskCreate):
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Use parameterized query to insert data
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, int(task.done)))
    conn.commit()
    new_task_id = cursor.lastrowid
    conn.close()
    
    return {"id": new_task_id, "title": task.title, "done": task.done}


# Stage 3: Update an existing task (PUT)
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if task exists first
    task = cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Determine new values
    new_title = task["title"]
    new_done = task["done"]
    
    if task_update.title is not None:
        if task_update.title.strip() == "":
            conn.close()
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        new_title = task_update.title
        
    if task_update.done is not None:
        new_done = int(task_update.done)
        
    # Update row with parameterized query
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (new_title, new_done, task_id))
    conn.commit()
    conn.close()
    
    return {"id": task_id, "title": new_title, "done": bool(new_done)}


# Stage 3: Delete a task (DELETE)
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if task exists first
    task = cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
    # Delete row using parameterized query
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return