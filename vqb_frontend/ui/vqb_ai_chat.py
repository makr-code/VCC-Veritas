"""
VQB UI Components - AI Chat Panel

OOP-based AI chat panel for VCC-Clara integration.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class VQBAIChatPanel:
    """
    VQB AI Chat Panel Component
    
    Provides chat interface with VCC-Clara AI assistant.
    """
    
    def __init__(self, parent: tk.Frame, controller):
        """
        Initialize AI chat panel
        
        Args:
            parent: Parent frame
            controller: Application controller
        """
        self.parent = parent
        self.controller = controller
        
        # Create chat panel frame
        self.chat_frame = ttk.LabelFrame(
            parent,
            text="🤖 VCC-Clara AI Assistent",
            height=200
        )
        self.chat_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=2, pady=2)
        self.chat_frame.pack_propagate(False)  # Maintain height
        
        # Build chat interface
        self._create_chat_interface()
        
        # Chat history
        self.chat_history = []
        
        logger.info("VQB AI Chat Panel initialized")
    
    def _create_chat_interface(self):
        """Create chat interface"""
        # Chat display area
        chat_display_frame = ttk.Frame(self.chat_frame)
        chat_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        chat_scroll = ttk.Scrollbar(chat_display_frame)
        chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Chat text widget
        self.chat_display = tk.Text(
            chat_display_frame,
            wrap=tk.WORD,
            yscrollcommand=chat_scroll.set,
            height=8,
            bg="#F0F8FF",  # Light blue background
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        chat_scroll.config(command=self.chat_display.yview)
        
        # Configure text tags for styling
        self.chat_display.tag_config("user", foreground="#0066CC", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("ai", foreground="#006600", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("system", foreground="#666666", font=("Arial", 9, "italic"))
        self.chat_display.tag_config("timestamp", foreground="#999999", font=("Arial", 8))
        
        # Input area
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Quick action buttons
        quick_actions_frame = ttk.Frame(input_frame)
        quick_actions_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(quick_actions_frame, text="Schnellaktionen:").pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            quick_actions_frame,
            text="📝 Zusammenfassen",
            command=self._quick_summarize,
            width=15
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_actions_frame,
            text="✅ Compliance",
            command=self._quick_compliance,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            quick_actions_frame,
            text="🔍 Ähnliche",
            command=self._quick_similar,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        # Chat input
        input_entry_frame = ttk.Frame(input_frame)
        input_entry_frame.pack(fill=tk.X)
        
        self.chat_input = ttk.Entry(input_entry_frame, font=("Arial", 10))
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.chat_input.bind("<Return>", lambda e: self._send_message())
        self.chat_input.bind("<Shift-Return>", lambda e: "break")  # Allow multiline with Shift+Enter
        
        ttk.Button(
            input_entry_frame,
            text="Senden",
            command=self._send_message,
            width=10
        ).pack(side=tk.LEFT)
        
        # Add welcome message
        self._add_system_message(
            "Willkommen beim VQB AI Assistenten! 👋\n"
            "Ich kann Ihnen helfen bei:\n"
            "• Dokumenten-Zusammenfassungen\n"
            "• Komplexen Recherchen\n"
            "• Compliance-Checks\n"
            "• Prozess-Analysen\n"
            "• Und vieles mehr!\n\n"
            "Stellen Sie mir eine Frage oder nutzen Sie die Schnellaktionen."
        )
    
    def _send_message(self):
        """Send user message to AI"""
        message = self.chat_input.get().strip()
        if not message:
            return
        
        # Clear input
        self.chat_input.delete(0, tk.END)
        
        # Add user message to display
        self._add_user_message(message)
        
        # Add to history
        self.chat_history.append({"role": "user", "content": message})
        
        # Send to controller for AI processing
        self.controller.process_ai_message(message, self._handle_ai_response)
    
    def _handle_ai_response(self, response: str):
        """Handle AI response"""
        self._add_ai_message(response)
        self.chat_history.append({"role": "assistant", "content": response})
    
    def _add_user_message(self, message: str):
        """Add user message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, "Sie: ", "user")
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _add_ai_message(self, message: str):
        """Add AI message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, "VCC-Clara: ", "ai")
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _add_system_message(self, message: str):
        """Add system message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        self.chat_display.insert(tk.END, "ℹ️ System: ", "system")
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _quick_summarize(self):
        """Quick action: Summarize current document"""
        self.chat_input.delete(0, tk.END)
        self.chat_input.insert(0, "Fasse das aktuell ausgewählte Dokument zusammen")
        self._send_message()
    
    def _quick_compliance(self):
        """Quick action: Run compliance check"""
        self.chat_input.delete(0, tk.END)
        self.chat_input.insert(0, "Führe einen Compliance-Check für den aktuellen Prozess durch")
        self._send_message()
    
    def _quick_similar(self):
        """Quick action: Find similar items"""
        self.chat_input.delete(0, tk.END)
        self.chat_input.insert(0, "Finde ähnliche Vorgänge zu dem aktuell ausgewählten")
        self._send_message()
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_history = []
        logger.info("Chat history cleared")
    
    def get_frame(self) -> ttk.LabelFrame:
        """Get chat frame"""
        return self.chat_frame
    
    def toggle_visibility(self):
        """Toggle chat panel visibility"""
        if self.chat_frame.winfo_viewable():
            self.chat_frame.pack_forget()
        else:
            self.chat_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=2, pady=2)
