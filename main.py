from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# Pydantic models for data validation (Stage 3 & 4)
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

# Stage 2: In-memory list (pre-filled with 3 example tasks)
tasks_db = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Read book", "done": True},
    {"id": 3, "title": "Complete assignment", "done": False}
]
task_id_counter = 4

# Stage 1: Root and health endpoints
@app.get("/")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Stage 2: Read all tasks
@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks_db

# Stage 2: Read a single task by ID
@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    # Return a 404 error if the task ID does not exist
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# Stage 3: Create a new task (POST)
@app.post("/tasks", status_code=status.HTTP_201_CREATED, response_model=Task)
def create_task(task: TaskCreate):
    # Validation: Ensure the title is not missing or empty
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    global task_id_counter
    new_task = {"id": task_id_counter, "title": task.title, "done": task.done}
    tasks_db.append(new_task)
    task_id_counter += 1
    return new_task

# Stage 4: Update an existing task (PUT)
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks_db:
        if task["id"] == task_id:
            # Update title if provided, ensuring it is not empty
            if task_update.title is not None:
                if task_update.title.strip() == "":
                    raise HTTPException(status_code=400, detail="Title cannot be empty")
                task["title"] = task_update.title
            
            # Update completion status if provided
            if task_update.done is not None:
                task["done"] = task_update.done
            return task
    
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# Stage 4: Delete a task (DELETE)
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            del tasks_db[i]
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")