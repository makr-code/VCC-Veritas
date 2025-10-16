# FRONTEND STREAMING INTEGRATION - Implementation Plan

**File:** `frontend/veritas_app.py`  
**Current Status:** Streaming Service imported but not used  
**Target:** Enable SSE Streaming in `_send_to_backend` method

---

## 🎯 Required Changes

### Change 1: Enable Streaming in _send_to_backend (Line 825)

**CURRENT (Line 797-900):**
```python
def _send_to_backend(self, message: str):
    # ... existing code ...
    request_payload = {
        "query": message,
        "session_id": self.session_id,
        "model": ...,
        "temperature": ...,
        "max_tokens": ...,
        "mode": mode_key,
        "enable_streaming": False  # ← CHANGE THIS!
    }
```

**NEW:**
```python
def _send_to_backend(self, message: str):
    # Check if streaming is available
    use_streaming = STREAMING_AVAILABLE and hasattr(self, 'streaming_service')
    
    # ... existing code ...
    request_payload = {
        "query": message,
        "session_id": self.session_id,
        "model": ...,
        "temperature": ...,
        "max_tokens": ...,
        "mode": mode_key,
        "enable_streaming": use_streaming  # ← DYNAMIC!
    }
    
    if use_streaming:
        # Use streaming endpoint
        result = self.streaming_service.start_streaming_query(
            query=message,
            session_id=self.session_id,
            enable_progress=True,
            enable_intermediate=True,
            enable_thinking=True
        )
        
        if result['success']:
            logger.info(f"✅ Streaming started: {result['stream_session_id']}")
            return  # Progress updates will come via streaming
        else:
            logger.warning(f"⚠️ Streaming failed, fallback to regular query")
            # Fall through to regular query
    
    # Regular non-streaming query
    api_response = requests.post(
        f"{API_BASE_URL}/v2/query",
        json=request_payload,
        timeout=60
    )
    # ... rest of existing code ...
```

---

### Change 2: Initialize Streaming Service in ChatWindowBase

**Location:** ChatWindowBase.__init__  
**Add after existing initialization:**

```python
class ChatWindowBase(ABC, StreamingUIMixin if STREAMING_AVAILABLE else object):
    def __init__(self, parent, ...):
        # ... existing code ...
        
        # Initialize Streaming Service if available
        if STREAMING_AVAILABLE:
            self.streaming_service = VeritasStreamingService(
                base_url=API_BASE_URL
            )
            self.streaming_service.set_queue(self.queue)  # Connect to ChatWindow queue
            self.streaming_service.set_thread_manager(self.thread_manager)
            
            # Setup streaming UI components
            self.setup_streaming_integration(self.window_id, self.thread_manager)
            
            logger.info("✅ Streaming Service initialized for ChatWindow")
        else:
            self.streaming_service = None
            logger.warning("⚠️ Streaming Service not available")
```

---

### Change 3: Handle Streaming Messages in Message Loop

**Location:** ChatWindowBase._check_queue  
**Add streaming message handling:**

```python
def _check_queue(self):
    """Prüft Queue auf neue Nachrichten"""
    try:
        while not self.queue.empty():
            msg = self.queue.get_nowait()
            
            # Handle streaming messages
            if STREAMING_AVAILABLE and hasattr(self, '_handle_streaming_message'):
                if msg.msg_type == MessageType.BACKEND_RESPONSE:
                    data = msg.data if hasattr(msg, 'data') else {}
                    if 'stream_type' in data:
                        self._handle_streaming_message(msg)
                        continue
            
            # ... existing message handling ...
            if msg.msg_type == MessageType.BACKEND_RESPONSE:
                # ... existing code ...
```

---

### Change 4: Add Progress Bar UI (Optional Enhancement)

**Location:** ChatWindowBase UI setup  
**Add streaming progress widgets:**

```python
# Add to UI setup
if STREAMING_AVAILABLE:
    self.streaming_frame = ttk.Frame(self.bottom_frame)
    self.streaming_frame.pack(fill="x", pady=2)
    
    self.streaming_label = ttk.Label(
        self.streaming_frame, 
        text="", 
        font=('Arial', 9)
    )
    self.streaming_label.pack(side="left", padx=5)
    
    self.progress_bar = ttk.Progressbar(
        self.streaming_frame,
        mode='determinate',
        length=300
    )
    self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
    
    self.cancel_button = ttk.Button(
        self.streaming_frame,
        text="❌ Cancel",
        command=self._cancel_streaming,
        state="disabled"
    )
    self.cancel_button.pack(side="right", padx=5)
    
    # Initially hidden
    self.streaming_frame.pack_forget()
```

---

## 📋 Implementation Steps

### Step 1: Add Streaming Service Initialization (5 min)
```python
# Find ChatWindowBase.__init__ (around line 500)
# Add streaming_service initialization after existing setup
```

### Step 2: Modify _send_to_backend (10 min)
```python
# Find _send_to_backend (line 797)
# Add streaming check and call streaming_service.start_streaming_query
```

### Step 3: Test Streaming (5 min)
```powershell
# Frontend should already be running (Job 5)
# Submit a query and watch for:
# - Progress updates in console
# - Response appears in chat
```

### Step 4: Add Progress Bar UI (15 min - OPTIONAL)
```python
# Add streaming_frame, progress_bar, cancel_button
# Update UI in _handle_streaming_message
```

---

## ✅ Expected Results

### Before Changes:
```
User: "Was ist KI?"
Frontend: [Sends to /v2/query, enable_streaming: false]
Backend: [Processes fully, returns complete response]
Frontend: [Shows response after 5-7 seconds]
```

### After Changes:
```
User: "Was ist KI?"
Frontend: [Sends to /v2/query/stream, enable_streaming: true]
Backend: [Returns session_id immediately]
Frontend: [Connects to /progress/{session_id}]
Backend: [Streams progress events]
Frontend: [Shows real-time updates:
  - "🚀 Streaming gestartet..."
  - "📊 20% - Agent Orchestration"
  - "🤖 40% - Document Retrieval"
  - "🧠 75% - LLM Reasoning: Analysiere..."
  - "✅ 100% - Verarbeitung abgeschlossen"
  - Final response displayed
]
```

---

## 🔧 Quick Test Command

```powershell
# Check if Frontend is receiving streaming:
Get-Job | Where-Object {$_.Id -eq 5} | Receive-Job -Keep | Select-String "streaming"
```

---

## 📝 Notes

1. **Backward Compatibility:** If streaming fails, code falls back to regular query
2. **Thread Safety:** StreamingService handles threading via existing ThreadManager
3. **UI Updates:** All UI updates go through existing queue system
4. **Cancel Support:** Streaming can be cancelled mid-flight

---

**Next Step:** Implement Change 1 + 2, test with existing running frontend!
