# Async Upload Processing Setup

## Overview
The upload system now uses **Celery + Redis** for asynchronous background processing. This means:
- Upload endpoint returns instantly (HTTP 202 Accepted)
- File processing happens in the background
- Client can check progress with status endpoint
- No more freezing UI while processing!

## Architecture

```
┌─────────────────────────────────────────────────┐
│            USER/CLIENT                          │
└────────────────┬────────────────────────────────┘
                 │
                 ├─ POST /uploads (file)
                 │ Response: {"task_id": "abc123", "status": "processing"}
                 │ HTTP 202 Accepted ✅ (instant)
                 │
                 └─ GET /upload-status/abc123 (polling)
                    Response: {"status": "processing", "percentage": 45}
                    
┌─────────────────────────────────────────────────┐
│            FLASK API                            │
│ - Validates request                             │
│ - Queues task to Redis                          │
│ - Returns task_id immediately                   │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  REDIS QUEUE   │
        │  (Message Bus) │
        └────────┬────────┘
                 │
        ┌────────▼──────────────────────┐
        │  CELERY WORKER(s)            │
        │  - process_upload_document   │
        │  - Extract text (MinerU)     │
        │  - Chunk text                │
        │  - Generate embeddings       │
        │  - Save to database          │
        │  Updates task state with %   │
        └──────────────────────────────┘
```

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install & run Redis** (if not already running):

   **Windows (WSL or Docker):**
   ```bash
   # Option A: Using Docker
   docker run -d -p 6379:6379 redis:alpine
   
   # Option B: Using WSL
   wsl -u root
   apt-get install redis-server
   redis-server
   ```

   **Linux:**
   ```bash
   sudo apt-get install redis-server
   redis-server
   ```

   **macOS:**
   ```bash
   brew install redis
   redis-server
   ```

3. **Verify Redis is running:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

## Running the System

### Terminal 1: Flask API
```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac

# Run Flask app
python main.py
# API running at http://localhost:5000
```

### Terminal 2: Celery Worker
```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows
source venv/bin/activate      # Linux/Mac

# Run Celery worker
python celery_worker.py

# Or use celery command directly:
celery -A app.celery_app worker --loglevel=info --pool=solo
```

### Terminal 3 (Optional): Flower - Task Monitoring Dashboard
```bash
# Install flower (optional, for monitoring)
pip install flower

# Run Flower
celery -A app.celery_app flower --port=5555
# Dashboard at http://localhost:5555
```

## API Usage

### Upload File (Instant Response)
```bash
curl -X POST http://localhost:5000/uploads \
  -F "file=@document.pdf" \
  -F "course_id=101" \
  -F "course_name=Python Basics" \
  -F "module_id=mod_001" \
  -F "tenant_id=tenant_001"

# Response (HTTP 202):
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "message": "File upload queued for processing. Check status with /upload-status/{task_id}"
  },
  "message": "Upload queued successfully"
}
```

### Check Upload Status
```bash
curl http://localhost:5000/upload-status/550e8400-e29b-41d4-a716-446655440000

# Response (while processing):
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "current": 5,
    "total": 8,
    "percentage": 62,
    "status_message": "Generating embeddings..."
  },
  "message": "Task status retrieved"
}

# Response (completed):
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "percentage": 100,
    "result": {
      "status": "completed",
      "course_id": "101",
      "module_id": "mod_123",
      "num_chunks": 45,
      "full_text_length": 23456
    }
  },
  "message": "Task status retrieved"
}
```

## Frontend Implementation Example

```javascript
// Upload file and get task_id
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('course_id', '101');
formData.append('course_name', 'Python Basics');
formData.append('module_id', 'mod_001');
formData.append('tenant_id', 'tenant_001');

const response = await fetch('/uploads', {
  method: 'POST',
  body: formData
});

const result = await response.json();
const taskId = result.data.task_id;

// Poll for status
const pollStatus = setInterval(async () => {
  const statusResponse = await fetch(`/upload-status/${taskId}`);
  const statusResult = await statusResponse.json();
  
  const data = statusResult.data;
  console.log(`Progress: ${data.percentage}% - ${data.status_message}`);
  
  // Update UI with progress bar
  document.getElementById('progress').style.width = `${data.percentage}%`;
  
  if (data.status === 'completed') {
    clearInterval(pollStatus);
    console.log('Upload complete!', data.result);
    // Redirect or show success
  } else if (data.status === 'failed') {
    clearInterval(pollStatus);
    console.error('Upload failed!', data.error);
  }
}, 2000); // Check every 2 seconds
```

## Performance Improvement

**Before (Synchronous):**
- Upload response: **10-17 minutes** ⏳
- User frozen during entire process
- Poor UX

**After (Asynchronous):**
- Upload response: **< 1 second** ✅
- Background processing: 10-17 minutes
- User can continue browsing
- Real-time progress updates

## Monitoring & Debugging

### Check Celery Tasks
```bash
# Using Flower (Web UI)
celery -A app.celery_app flower

# Or CLI
celery -A app.celery_app inspect active
celery -A app.celery_app inspect reserved
celery -A app.celery_app inspect stats
```

### Check Redis
```bash
redis-cli

# Common commands:
> KEYS *                    # List all keys
> TTL key_name             # Check expiration
> DEL key_name             # Delete key
> FLUSHDB                  # Clear all data
> INFO stats               # Redis stats
```

### Logs
- Flask logs: Terminal 1
- Celery logs: Terminal 2
- Check `extracted_texts/` folder for processing output

## Troubleshooting

### Redis Connection Error
```
Error: ConnectionError("Error 111 connecting to localhost:6379")
```
**Solution:** Make sure Redis is running (`redis-server`)

### Celery Worker Not Processing Tasks
1. Check if worker is running: `celery -A app.celery_app inspect active`
2. Restart worker: Kill and run `python celery_worker.py` again
3. Check Redis: `redis-cli ping`

### Task Takes Too Long
- Check file size (large PDFs take longer)
- Check MinerU API status
- Check Groq API rate limits
- Monitor with Flower: http://localhost:5555

### Windows Issues
- Use `--pool=solo` flag (already configured in celery_worker.py)
- Make sure Redis is accessible (Docker recommended)

## Configuration Tweaks

Edit `app/celery_app.py` to adjust:
- **Concurrency:** `--concurrency=2` (number of parallel workers)
- **Task timeout:** `task_time_limit=30*60` (30 minutes)
- **Result expiry:** `result_expires=3600` (1 hour)

## Production Deployment

For production, use:
```bash
# Gunicorn for Flask
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

# Celery with better pool
celery -A app.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --pool=prefork \
  --time-limit=1800
```

