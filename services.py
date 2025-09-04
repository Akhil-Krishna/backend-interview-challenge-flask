from models import db, Task
from datetime import datetime

def create_task(data):
    task = Task(**data)
    db.session.add(task)
    db.session.commit()
    return task

def get_tasks():
    return Task.query.filter_by(deleted=False).all()

def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        return None
    for key, value in data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    db.session.commit()
    return task

def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return None
    task.deleted = True
    task.updated_at = datetime.utcnow()
    db.session.commit()
    return task

def apply_from_client(operation, client_data):
    """Apply sync operation (create/update/delete) with LWW conflict resolution"""
    task_id = client_data.get("id")
    client_updated_at = datetime.fromisoformat(client_data["updated_at"])
    server_task = Task.query.get(task_id) if task_id else None

    if operation == "create":
        if server_task:
            return {"status": "exists", "server_id": server_task.id, "resolved_data": server_task.as_dict()}
        task = create_task(client_data)
        return {"status": "success", "server_id": task.id, "resolved_data": task.as_dict()}

    elif operation == "update":
        if not server_task:
            return {"status": "not_found"}
        if client_updated_at > server_task.updated_at:
            update_task(task_id, client_data)
            return {"status": "success", "server_id": task_id, "resolved_data": server_task.as_dict()}
        return {"status": "conflict", "server_id": task_id, "resolved_data": server_task.as_dict()}

    elif operation == "delete":
        if not server_task:
            return {"status": "not_found"}
        if client_updated_at > server_task.updated_at:
            delete_task(task_id)
            return {"status": "success", "server_id": task_id}
        return {"status": "conflict", "server_id": task_id, "resolved_data": server_task.as_dict()}

    return {"status": "error"}
