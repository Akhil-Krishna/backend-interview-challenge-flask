from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    completed = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)  # Keep as 'deleted' for your current implementation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sync_status = db.Column(db.String, default='synced')  # 'pending', 'synced', 'error'
    server_id = db.Column(db.String)  # For client-server ID mapping
    last_synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "deleted": self.deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "sync_status": self.sync_status,
            "server_id": self.server_id,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None
        }

class SyncQueue(db.Model):
    __tablename__ = "sync_queue"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.String, nullable=False)
    operation = db.Column(db.String, nullable=False)  # 'create', 'update', 'delete'
    task_data = db.Column(db.Text)  # JSON string of task data
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    status = db.Column(db.String, default='pending')  # 'pending', 'synced', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_attempted_at = db.Column(db.DateTime)

    def as_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "operation": self.operation,
            "task_data": self.task_data,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_attempted_at": self.last_attempted_at.isoformat() if self.last_attempted_at else None
        }