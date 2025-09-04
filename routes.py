from flask import Blueprint, request, jsonify
from services import (
    create_task, get_tasks, get_task_by_id, update_task, delete_task, 
    apply_from_client, process_sync_queue, get_sync_status
)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")
sync_bp = Blueprint("sync", __name__, url_prefix="/api/sync")

# Task Routes
@tasks_bp.route("", methods=["POST"])
def create():
    """Create a new task"""
    data = request.json
    
    # Basic validation
    if not data or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400
    
    try:
        task = create_task(data)
        return jsonify(task.as_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tasks_bp.route("", methods=["GET"])
def list_tasks():
    """Get all non-deleted tasks"""
    try:
        tasks = get_tasks()
        return jsonify([t.as_dict() for t in tasks])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tasks_bp.route("/<task_id>", methods=["GET"])
def get_task(task_id):
    """Get a specific task by ID"""
    try:
        task = get_task_by_id(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        
        if task.deleted:
            return jsonify({"error": "Task has been deleted"}), 404
        
        return jsonify(task.as_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tasks_bp.route("/<task_id>", methods=["PUT"])
def update(task_id):
    """Update an existing task (full update)"""
    data = request.json
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    try:
        task = update_task(task_id, data)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task.as_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tasks_bp.route("/<task_id>", methods=["PATCH"])
def patch_update(task_id):
    """Partially update an existing task"""
    data = request.json
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    try:
        task = update_task(task_id, data)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task.as_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tasks_bp.route("/<task_id>", methods=["DELETE"])
def delete(task_id):
    """Soft delete a task"""
    try:
        task = delete_task(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"status": "deleted", "task": task.as_dict()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Sync Routes
@sync_bp.route("/batch", methods=["POST"])
def batch_sync():
    """Handle batch sync operations from client"""
    try:
        body = request.json
        
        if not body or 'items' not in body:
            return jsonify({"error": "Items array is required"}), 400
        
        results = []
        for item in body.get("items", []):
            # Validate item structure
            if not all(k in item for k in ['operation', 'data']):
                results.append({
                    "client_id": item.get("client_id"),
                    "status": "error",
                    "message": "Missing required fields: operation, data"
                })
                continue
            
            try:
                res = apply_from_client(item["operation"], item["data"])
                results.append({
                    "client_id": item.get("client_id"),
                    **res
                })
            except Exception as e:
                results.append({
                    "client_id": item.get("client_id"),
                    "status": "error",
                    "message": str(e)
                })
        
        return jsonify({"processed_items": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sync_bp.route("/trigger", methods=["POST"])
def trigger_sync():
    """Manually trigger sync queue processing"""
    try:
        results = process_sync_queue()
        return jsonify({
            "status": "completed",
            "processed_count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sync_bp.route("/status", methods=["GET"])
def sync_status():
    """Get current sync queue status"""
    try:
        status = get_sync_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sync_bp.route("/queue", methods=["GET"])
def get_queue():
    """Get pending sync queue items (for debugging)"""
    try:
        from services import get_pending_sync_items
        items = get_pending_sync_items(50)  # Limit to 50 for performance
        return jsonify([item.as_dict() for item in items])
    except Exception as e:
        return jsonify({"error": str(e)}), 500