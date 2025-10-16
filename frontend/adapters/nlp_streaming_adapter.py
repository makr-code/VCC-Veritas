"""
VERITAS NLP Foundation - Tkinter Frontend Adapter
=================================================

Adapter to integrate NLP streaming with existing Tkinter frontend.

Connects the new NLP pipeline (Phase 1-3) with the existing
veritas_app.py tkinter interface for seamless integration.

Features:
- Thread-safe tkinter updates
- Progress display in existing UI
- Real-time status updates
- Session management
- Backward compatible with existing frontend

Usage in veritas_app.py:
    from frontend.adapters.nlp_streaming_adapter import NLPStreamingAdapter
    
    # Initialize adapter
    adapter = NLPStreamingAdapter(
        text_widget=self.chat_display,
        status_label=self.status_label
    )
    
    # Process query with streaming
    adapter.process_query_with_streaming("Bauantrag für Stuttgart")

Created: 2025-10-14
"""

import tkinter as tk
from tkinter import ttk
import threading
import queue
import logging
import sys
import os
from typing import Optional, Callable, Dict, Any
from datetime import datetime

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import NLP services
try:
    from backend.services.nlp_service import NLPService
    from backend.services.process_builder import ProcessBuilder
    from backend.services.process_executor import ProcessExecutor
    from backend.models.streaming_progress import ProgressCallback, ProgressEvent
    NLP_AVAILABLE = True
except ImportError as e:
    NLP_AVAILABLE = False
    logging.warning(f"⚠️ NLP services not available: {e}")


logger = logging.getLogger(__name__)


class NLPStreamingAdapter:
    """
    Adapter to integrate NLP streaming with Tkinter frontend.
    
    Provides thread-safe updates to Tkinter widgets during
    NLP process execution with real-time progress.
    
    Features:
    - Thread-safe UI updates (via queue)
    - Progress bar integration
    - Status label updates
    - Text widget streaming
    - Session management
    
    Example:
        >>> adapter = NLPStreamingAdapter(
        ...     text_widget=chat_display,
        ...     status_label=status_label,
        ...     progress_bar=progress_bar
        ... )
        >>> adapter.process_query_with_streaming("Query here")
    """
    
    def __init__(
        self,
        text_widget: Optional[tk.Text] = None,
        status_label: Optional[tk.Label] = None,
        progress_bar: Optional[ttk.Progressbar] = None,
        root: Optional[tk.Tk] = None
    ):
        """
        Initialize NLP streaming adapter.
        
        Args:
            text_widget: Tkinter Text widget for output
            status_label: Label for status updates
            progress_bar: Progressbar for visual progress
            root: Root Tkinter window (for thread-safe updates)
        """
        self.text_widget = text_widget
        self.status_label = status_label
        self.progress_bar = progress_bar
        self.root = root
        
        # Message queue for thread-safe UI updates
        self.message_queue = queue.Queue()
        
        # NLP services
        self.nlp_service = None
        self.process_builder = None
        self.process_executor = None
        
        # Session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_counter = 0
        
        # Initialize NLP services
        self._initialize_services()
        
        # Start UI update loop
        if self.root:
            self._start_ui_update_loop()
        
        logger.info("NLPStreamingAdapter initialized")
    
    def _initialize_services(self):
        """Initialize NLP services."""
        if not NLP_AVAILABLE:
            logger.warning("⚠️ NLP services not available")
            return
        
        try:
            self.nlp_service = NLPService()
            self.process_builder = ProcessBuilder(self.nlp_service)
            self.process_executor = ProcessExecutor(max_workers=4, use_agents=True)
            logger.info("✅ NLP services initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize NLP services: {e}")
    
    def _start_ui_update_loop(self):
        """Start UI update loop (checks queue every 100ms)."""
        def update_loop():
            try:
                # Process all queued messages
                while True:
                    message = self.message_queue.get_nowait()
                    self._process_ui_message(message)
            except queue.Empty:
                pass
            
            # Schedule next update
            if self.root:
                self.root.after(100, update_loop)
        
        # Start loop
        if self.root:
            self.root.after(100, update_loop)
    
    def _process_ui_message(self, message: Dict[str, Any]):
        """Process UI update message (runs in main thread)."""
        msg_type = message.get("type")
        
        if msg_type == "text":
            # Update text widget
            if self.text_widget:
                text = message.get("text", "")
                tags = message.get("tags", None)
                self.text_widget.insert(tk.END, text, tags)
                self.text_widget.see(tk.END)
        
        elif msg_type == "status":
            # Update status label
            if self.status_label:
                status = message.get("status", "")
                self.status_label.config(text=status)
        
        elif msg_type == "progress":
            # Update progress bar
            if self.progress_bar:
                percentage = message.get("percentage", 0)
                self.progress_bar['value'] = percentage
    
    def _queue_ui_update(self, message: Dict[str, Any]):
        """Queue UI update (thread-safe)."""
        self.message_queue.put(message)
    
    def process_query_with_streaming(
        self,
        query: str,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> str:
        """
        Process query with streaming progress updates.
        
        Args:
            query: User query
            on_complete: Callback when complete (receives result dict)
            on_error: Callback on error (receives error message)
            
        Returns:
            Session ID
        """
        # Create session
        self.session_counter += 1
        session_id = f"session_{self.session_counter}_{int(datetime.now().timestamp())}"
        
        # Store session info
        self.active_sessions[session_id] = {
            "query": query,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        
        # Display query in UI
        self._queue_ui_update({
            "type": "text",
            "text": f"\n{'='*80}\n",
            "tags": "separator"
        })
        self._queue_ui_update({
            "type": "text",
            "text": f"🔍 Query: {query}\n",
            "tags": "query"
        })
        self._queue_ui_update({
            "type": "text",
            "text": f"{'='*80}\n\n",
            "tags": "separator"
        })
        
        # Update status
        self._queue_ui_update({
            "type": "status",
            "status": f"Processing: {query[:50]}..."
        })
        
        # Process in background thread
        def process_thread():
            try:
                # Create progress callback
                callback = ProgressCallback()
                callback.add_handler(self._on_progress_event)
                
                # Build process tree
                self._queue_ui_update({
                    "type": "text",
                    "text": "📊 Building process tree...\n",
                    "tags": "info"
                })
                
                tree = self.process_builder.build_process_tree(query)
                
                self._queue_ui_update({
                    "type": "text",
                    "text": f"   ✅ {len(tree.steps)} steps planned\n\n",
                    "tags": "success"
                })
                
                # Execute with streaming
                self._queue_ui_update({
                    "type": "text",
                    "text": "🚀 Executing process...\n\n",
                    "tags": "info"
                })
                
                result = self.process_executor.execute_process(tree, progress_callback=callback)
                
                # Display result
                self._display_result(result, session_id)
                
                # Update session
                self.active_sessions[session_id]["status"] = "completed"
                self.active_sessions[session_id]["result"] = result
                
                # Update status
                self._queue_ui_update({
                    "type": "status",
                    "status": "Ready"
                })
                
                # Call completion callback
                if on_complete:
                    on_complete(result)
                
            except Exception as e:
                logger.error(f"Error processing query: {e}", exc_info=True)
                
                # Display error
                self._queue_ui_update({
                    "type": "text",
                    "text": f"\n❌ Error: {str(e)}\n\n",
                    "tags": "error"
                })
                
                # Update session
                self.active_sessions[session_id]["status"] = "failed"
                self.active_sessions[session_id]["error"] = str(e)
                
                # Update status
                self._queue_ui_update({
                    "type": "status",
                    "status": "Error occurred"
                })
                
                # Call error callback
                if on_error:
                    on_error(str(e))
        
        # Start processing thread
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
        
        return session_id
    
    def _on_progress_event(self, event: ProgressEvent):
        """Handle progress event (called from worker thread)."""
        event_type = event.event_type.value
        
        if event_type == "plan_started":
            self._queue_ui_update({
                "type": "progress",
                "percentage": 0
            })
        
        elif event_type == "step_started":
            # Display step start
            self._queue_ui_update({
                "type": "text",
                "text": f"▶️  Step {event.current_step}/{event.total_steps}: {event.step_name}\n",
                "tags": "step"
            })
        
        elif event_type == "step_progress":
            # Update progress bar
            self._queue_ui_update({
                "type": "progress",
                "percentage": event.percentage
            })
            
            # Display progress message
            if event.message:
                self._queue_ui_update({
                    "type": "text",
                    "text": f"   ⏳ {event.percentage:.0f}%: {event.message}\n",
                    "tags": "progress"
                })
        
        elif event_type == "step_completed":
            # Display step completion
            self._queue_ui_update({
                "type": "text",
                "text": f"✅ Step {event.current_step}/{event.total_steps}: {event.step_name} ({event.execution_time:.3f}s)\n",
                "tags": "success"
            })
            
            # Update progress
            self._queue_ui_update({
                "type": "progress",
                "percentage": event.percentage
            })
        
        elif event_type == "step_failed":
            # Display error
            self._queue_ui_update({
                "type": "text",
                "text": f"❌ Step {event.current_step}/{event.total_steps} failed: {event.error}\n",
                "tags": "error"
            })
        
        elif event_type == "plan_completed":
            # Display completion
            self._queue_ui_update({
                "type": "text",
                "text": f"\n🎉 {event.message}\n",
                "tags": "success"
            })
            
            # Reset progress bar
            self._queue_ui_update({
                "type": "progress",
                "percentage": 100
            })
    
    def _display_result(self, result: Dict[str, Any], session_id: str):
        """Display execution result."""
        self._queue_ui_update({
            "type": "text",
            "text": f"\n{'─'*80}\n",
            "tags": "separator"
        })
        
        self._queue_ui_update({
            "type": "text",
            "text": "📊 Execution Summary:\n",
            "tags": "header"
        })
        
        # Display statistics
        stats = [
            f"   Success: {result['success']}",
            f"   Execution time: {result['execution_time']:.3f}s",
            f"   Steps completed: {result['steps_completed']}",
            f"   Steps failed: {result['steps_failed']}"
        ]
        
        for stat in stats:
            self._queue_ui_update({
                "type": "text",
                "text": f"{stat}\n",
                "tags": "info"
            })
        
        # Display final result data
        if result.get('data'):
            self._queue_ui_update({
                "type": "text",
                "text": "\n📋 Result Data:\n",
                "tags": "header"
            })
            
            for key, value in result['data'].items():
                self._queue_ui_update({
                    "type": "text",
                    "text": f"   {key}: {value}\n",
                    "tags": "result"
                })
        
        self._queue_ui_update({
            "type": "text",
            "text": f"{'─'*80}\n\n",
            "tags": "separator"
        })
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a session."""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions."""
        return self.active_sessions


# Test code (standalone)
if __name__ == "__main__":
    print("=" * 80)
    print("NLP STREAMING ADAPTER - STANDALONE TEST")
    print("=" * 80)
    
    # Create test window
    root = tk.Tk()
    root.title("NLP Streaming Adapter Test")
    root.geometry("800x600")
    
    # Create UI widgets
    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Status label
    status_label = ttk.Label(frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
    status_label.pack(fill=tk.X, pady=(0, 5))
    
    # Progress bar
    progress_bar = ttk.Progressbar(frame, mode='determinate', maximum=100)
    progress_bar.pack(fill=tk.X, pady=(0, 5))
    
    # Text widget
    text_widget = tk.Text(frame, wrap=tk.WORD, height=20)
    text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(text_widget)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=text_widget.yview)
    
    # Configure tags
    text_widget.tag_configure("query", foreground="blue", font=("Arial", 10, "bold"))
    text_widget.tag_configure("info", foreground="black")
    text_widget.tag_configure("success", foreground="green")
    text_widget.tag_configure("error", foreground="red")
    text_widget.tag_configure("header", font=("Arial", 10, "bold"))
    
    # Query input
    input_frame = ttk.Frame(frame)
    input_frame.pack(fill=tk.X)
    
    query_var = tk.StringVar(value="Bauantrag für Stuttgart")
    query_entry = ttk.Entry(input_frame, textvariable=query_var)
    query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    
    # Create adapter
    adapter = NLPStreamingAdapter(
        text_widget=text_widget,
        status_label=status_label,
        progress_bar=progress_bar,
        root=root
    )
    
    def on_send():
        query = query_var.get()
        if query:
            adapter.process_query_with_streaming(query)
    
    send_button = ttk.Button(input_frame, text="Send Query", command=on_send)
    send_button.pack(side=tk.RIGHT)
    
    # Info label
    info_label = ttk.Label(frame, text="Enter a query and click 'Send Query' to test NLP streaming",
                           foreground="gray")
    info_label.pack(pady=(5, 0))
    
    print("\n✅ Test window created")
    print("   Enter a query and click 'Send Query' to test streaming")
    print("\n" + "=" * 80)
    
    # Start GUI
    root.mainloop()
