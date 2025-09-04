# Task Sync API - Backend Interview Challenge

A robust task management API with offline synchronization capabilities, built with Flask and PostgreSQL. This project demonstrates offline-first architecture, conflict resolution, and RESTful API design.

## 🌟 Live Demo

**API Base URL:** `https://your-app-name.up.railway.app`

**Health Check:** [https://your-app-name.up.railway.app/health](https://your-app-name.up.railway.app/health)

## 📋 Features

- ✅ **Complete CRUD Operations** - Create, read, update, delete tasks
- ✅ **Offline-First Architecture** - Sync queue for offline operations
- ✅ **Conflict Resolution** - Last-write-wins strategy with timestamps
- ✅ **Batch Sync Operations** - Efficient bulk synchronization
- ✅ **Soft Delete** - Tasks are marked as deleted, not permanently removed
- ✅ **Production Ready** - Deployed with PostgreSQL and proper error handling
- ✅ **Health Monitoring** - Built-in health checks and status endpoints

## 🏗️ Architecture Overview

### Sync Strategy
This API implements an **offline-first architecture** where:

1. **Local Operations**: All CRUD operations work offline and are queued for sync
2. **Sync Queue**: Operations are stored in a queue with retry mechanisms
3. **Conflict Resolution**: Uses Last-Write-Wins (LWW) based on `updated_at` timestamps
4. **Batch Processing**: Sync operations are processed in configurable batches

### Key Design Decisions

- **Soft Deletes**: Tasks are marked as `deleted=True` instead of being removed
- **UUID Primary Keys**: Prevents ID conflicts during sync operations  
- **Timestamp-based Conflicts**: Simple and predictable conflict resolution
- **Separate Sync Queue**: Decouples sync logic from main task operations
- **Idempotent Operations**: Safe to retry sync operations multiple times

## 🚀 API Endpoints

### Task Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks` | Get all active tasks |
| `GET` | `/api/tasks/:id` | Get specific task |
| `POST` | `/api/tasks` | Create new task |
| `PUT` | `/api/tasks/:id` | Update entire task |
| `PATCH` | `/api/tasks/:id` | Partially update task |
| `DELETE` | `/api/tasks/:id` | Soft delete task |

### Sync Operations  

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sync/batch` | Process batch sync operations |
| `POST` | `/api/sync/trigger` | Manually trigger sync queue |
| `GET` | `/api/sync/status` | Get sync queue status |
| `GET` | `/api/sync/queue` | View pending sync items |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check with DB status |
| `GET` | `/` | API information |

## 📊 Data Models

### Task Model
```json
{
  "id": "uuid-string",
  "title": "string (required)",
  "description": "string (optional)",
  "completed": "boolean",
  "deleted": "boolean",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime", 
  "sync_status": "pending|synced|error",
  "server_id": "string (for client mapping)",
  "last_synced_at": "ISO datetime"
}
```

### Sync Queue Model
```json
{
  "id": "integer",
  "task_id": "string",
  "operation": "create|update|delete",
  "task_data": "JSON string",
  "retry_count": "integer",
  "max_retries": "integer (default: 3)",
  "status": "pending|synced|failed",
  "created_at": "ISO datetime",
  "last_attempted_at": "ISO datetime"
}
```

## 🔧 Local Development

### Prerequisites
- Python 3.8+
- pip or pipenv

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/task-sync-api.git
cd task-sync-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run development server
python app.py
```

### Environment Variables
```bash
FLASK_ENV=development
DATABASE_URL=sqlite:///database.db  # PostgreSQL URL for production
SYNC_BATCH_SIZE=50
PORT=5000
```

## 🧪 API Usage Examples

### Create a Task
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive README and API docs",
    "completed": false
  }'
```

### Update a Task
```bash
curl -X PUT http://localhost:5000/api/tasks/your-task-id \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated task title",
    "completed": true
  }'
```

### Batch Sync Operations
```bash
curl -X POST http://localhost:5000/api/sync/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "client_id": "client_1", 
        "operation": "create",
        "data": {
          "id": "offline-task-1",
          "title": "Offline created task",
          "updated_at": "2024-01-15T10:30:00Z"
        }
      },
      {
        "client_id": "client_2",
        "operation": "update", 
        "data": {
          "id": "existing-task-id",
          "title": "Updated offline",
          "completed": true,
          "updated_at": "2024-01-15T10:35:00Z"
        }
      }
    ]
  }'
```

### Check Sync Status
```bash
curl http://localhost:5000/api/sync/status
```

Response:
```json
{
  "pending": 0,
  "failed": 0, 
  "synced": 15,
  "total": 15
}
```

## 🔄 Sync Workflow

### Client-Side Flow
1. **Offline Operations**: Store operations in local sync queue
2. **Online Detection**: When internet is available, trigger batch sync
3. **Conflict Handling**: Accept server resolution for conflicts
4. **Status Updates**: Update local sync status based on server response

### Server-Side Processing
1. **Receive Batch**: Process array of sync operations
2. **Conflict Resolution**: Compare timestamps for LWW resolution
3. **Database Updates**: Apply winning changes to database
4. **Response**: Return status and resolved data for each operation

### Conflict Resolution Example
```
Client timestamp: 2024-01-15T10:35:00Z
Server timestamp: 2024-01-15T10:30:00Z
Result: Client wins (more recent)

Client timestamp: 2024-01-15T10:25:00Z  
Server timestamp: 2024-01-15T10:30:00Z
Result: Server wins (more recent)
```

## 🚀 Deployment

### Railway (Recommended)
1. Push code to GitHub
2. Connect Repository to Railway
3. Add PostgreSQL database service
4. Set environment variables
5. Deploy automatically on git push

### Production Environment Variables
```bash
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/db
SYNC_BATCH_SIZE=50
```

## 🔍 Testing

### Manual Testing Scenarios

**Basic CRUD:**
```bash
# Create task
POST /api/tasks → 201 Created

# Get all tasks  
GET /api/tasks → 200 OK

# Update task
PUT /api/tasks/:id → 200 OK

# Delete task
DELETE /api/tasks/:id → 200 OK
```

**Sync Testing:**
```bash
# Batch sync with conflicts
POST /api/sync/batch → 200 OK

# Check queue status
GET /api/sync/status → 200 OK

# Trigger manual sync
POST /api/sync/trigger → 200 OK
```

**Error Handling:**
```bash
# Invalid task ID
GET /api/tasks/invalid-id → 404 Not Found

# Missing required fields
POST /api/tasks {} → 400 Bad Request

# Database connection
GET /health → 200 OK (with DB status)
```

## 🛠️ Technology Stack

- **Backend Framework**: Flask 3.0.0
- **Database**: PostgreSQL (Production), SQLite (Development)  
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Deployment**: Railway.app with automatic PostgreSQL
- **Environment Management**: python-dotenv
- **Production Server**: Gunicorn

## 📈 Performance Considerations

- **Batch Size**: Configurable sync batch size (default: 50)
- **Database Indexing**: Proper indexes on frequently queried fields
- **Connection Pooling**: SQLAlchemy handles connection pooling
- **Error Recovery**: Retry mechanism with exponential backoff
- **Soft Deletes**: Prevents data loss and supports audit trails

## 🔐 Security Features

- **Input Validation**: Request validation for all endpoints
- **SQL Injection Prevention**: SQLAlchemy ORM parameterization
- **Error Handling**: Secure error messages without sensitive data
- **HTTPS**: Automatic HTTPS in production deployment

## 🐛 Known Limitations

1. **Single User**: Currently designed for single-user scenarios
2. **Simple Conflict Resolution**: Only supports Last-Write-Wins
3. **No Authentication**: No user authentication implemented
4. **Memory Sync Queue**: Sync queue stored in database (could use Redis for scale)

## 🔮 Future Enhancements

- [ ] Multi-user support with authentication
- [ ] More sophisticated conflict resolution strategies
- [ ] Real-time sync with WebSockets
- [ ] Task categories and tags
- [ ] Full-text search capabilities
- [ ] Task attachments and file uploads
- [ ] Sync progress tracking with percentages
- [ ] Offline indicator and sync status in responses



## 📄 License

This project was created as part of a technical interview challenge.

---

