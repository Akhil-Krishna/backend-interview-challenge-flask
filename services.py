from models import db, Task, SyncQueue
from datetime import datetime
import json
import os

BATCH_SIZE = int(os.getenv('SYNC_BATCH_SIZE', 50))

def create_task(data):
    task = Task(**data)
    db.session.add(task)
    db.session.commit()
    
    # Add to sync queue if this is a client operation
    if not data.get('skip_sync_queue', False):
        add_to_sync_queue(task.id, 'create', task.as_dict())
    
    return task

def get_tasks():
    return Task.query.filter_by(deleted=False).all()

def get_task_by_id(task_id):
    return Task.query.get(task_id)

def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        return None
    
    for key, value in data.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    task.updated_at = datetime.utcnow()
    task.sync_status = 'pending'
    db.session.commit()
    
    # Add to sync queue if this is a client operation
    if not data.get('skip_sync_queue', False):
        add_to_sync_queue(task.id, 'update', task.as_dict())
    
    return task

def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return None
    
    task.deleted = True
    task.updated_at = datetime.utcnow()
    task.sync_status = 'pending'
    db.session.commit()
    
    # Add to sync queue
    add_to_sync_queue(task.id, 'delete', task.as_dict())
    
    return task

def add_to_sync_queue(task_id, operation, task_data):
    """Add operation to sync queue"""
    queue_item = SyncQueue(
        task_id=task_id,
        operation=operation,
        task_data=json.dumps(task_data)
    )
    db.session.add(queue_item)
    db.session.commit()
    return queue_item

def get_pending_sync_items(limit=None):
    """Get pending sync queue items"""
    query = SyncQueue.query.filter(
        SyncQueue.status == 'pending',
        SyncQueue.retry_count < SyncQueue.max_retries
    ).order_by(SyncQueue.created_at)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()

def mark_sync_item_completed(sync_item_id):
    """Mark sync queue item as completed"""
    item = SyncQueue.query.get(sync_item_id)
    if item:
        item.status = 'synced'
        item.last_attempted_at = datetime.utcnow()
        db.session.commit()

def mark_sync_item_failed(sync_item_id):
    """Mark sync queue item as failed and increment retry count"""
    item = SyncQueue.query.get(sync_item_id)
    if item:
        item.retry_count += 1
        item.last_attempted_at = datetime.utcnow()
        
        if item.retry_count >= item.max_retries:
            item.status = 'failed'
        
        db.session.commit()

def apply_from_client(operation, client_data):
    """Apply sync operation (create/update/delete) with LWW conflict resolution"""
    task_id = client_data.get("id")
    
    # Parse client timestamp
    try:
        client_updated_at = datetime.fromisoformat(client_data["updated_at"].replace('Z', '+00:00'))
    except (KeyError, ValueError):
        client_updated_at = datetime.utcnow()
    
    server_task = Task.query.get(task_id) if task_id else None

    if operation == "create":
        if server_task:
            return {"status": "exists", "server_id": server_task.id, "resolved_data": server_task.as_dict()}
        
        # Ensure we don't add to sync queue for server-originated operations
        client_data['skip_sync_queue'] = True
        task = create_task(client_data)
        task.sync_status = 'synced'
        task.last_synced_at = datetime.utcnow()
        db.session.commit()
        
        return {"status": "success", "server_id": task.id, "resolved_data": task.as_dict()}

    elif operation == "update":
        if not server_task:
            return {"status": "not_found"}
        
        # Last-write-wins conflict resolution
        if client_updated_at > server_task.updated_at:
            # Client wins - apply the update
            client_data['skip_sync_queue'] = True
            updated_task = update_task(task_id, client_data)
            updated_task.sync_status = 'synced'
            updated_task.last_synced_at = datetime.utcnow()
            db.session.commit()
            
            return {"status": "success", "server_id": task_id, "resolved_data": updated_task.as_dict()}
        else:
            # Server wins - return server data
            return {"status": "conflict", "server_id": task_id, "resolved_data": server_task.as_dict()}

    elif operation == "delete":
        if not server_task:
            return {"status": "not_found"}
        
        # Last-write-wins conflict resolution
        if client_updated_at > server_task.updated_at:
            # Client wins - apply the delete
            deleted_task = delete_task(task_id)
            deleted_task.sync_status = 'synced'
            deleted_task.last_synced_at = datetime.utcnow()
            db.session.commit()
            
            return {"status": "success", "server_id": task_id}
        else:
            # Server wins - return server data
            return {"status": "conflict", "server_id": task_id, "resolved_data": server_task.as_dict()}

    return {"status": "error", "message": "Invalid operation"}

def process_sync_queue():
    """Process pending sync queue items in batches"""
    pending_items = get_pending_sync_items(BATCH_SIZE)
    results = []
    
    for item in pending_items:
        try:
            task_data = json.loads(item.task_data)
            result = apply_from_client(item.operation, task_data)
            
            if result.get('status') in ['success', 'exists']:
                mark_sync_item_completed(item.id)
            else:
                mark_sync_item_failed(item.id)
            
            results.append({
                "sync_item_id": item.id,
                "task_id": item.task_id,
                "operation": item.operation,
                **result
            })
            
        except Exception as e:
            mark_sync_item_failed(item.id)
            results.append({
                "sync_item_id": item.id,
                "task_id": item.task_id,
                "operation": item.operation,
                "status": "error",
                "message": str(e)
            })
    
    return results

def get_sync_status():
    """Get current sync queue status"""
    pending_count = SyncQueue.query.filter_by(status='pending').count()
    failed_count = SyncQueue.query.filter_by(status='failed').count()
    synced_count = SyncQueue.query.filter_by(status='synced').count()
    
    return {
        "pending": pending_count,
        "failed": failed_count,
        "synced": synced_count,
        "total": pending_count + failed_count + synced_count
    }