"""
InputManager - Input Field Management for VERITAS
=================================================

Manages the chat input field including:
- Placeholder text (show/hide on focus)
- Focus event handling
- Text retrieval and validation
- Keyboard shortcuts (Ctrl+Enter)
- Input change tracking

Part of the VERITAS frontend modularization (Phase 4).

Author: VERITAS Development Team
Created: 2025-10-18
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class InputManager:
    """
    Manages the chat input field and its interactions.
    
    Responsibilities:
    - Placeholder text management
    - Focus event handling
    - Text retrieval and validation
    - Keyboard shortcuts
    - Input state tracking
    
    Design Pattern: Manager Pattern with Event Callbacks
    """
    
    def __init__(
        self,
        input_text: tk.Text,
        placeholder_text: str = "Ihre Frage hier eingeben... (Ctrl+Enter zum Senden)",
        on_submit_callback: Optional[Callable[[], None]] = None,
        on_text_changed_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the InputManager.
        
        Args:
            input_text: The Tkinter Text widget to manage
            placeholder_text: Text to show when input is empty
            on_submit_callback: Function to call on Ctrl+Enter
            on_text_changed_callback: Function to call when text changes
        """
        self.input_text = input_text
        self.placeholder_text = placeholder_text
        self.on_submit_callback = on_submit_callback
        self.on_text_changed_callback = on_text_changed_callback
        
        # State tracking
        self.placeholder_active = False
        self._last_text = ""
        
        # Bind events
        self._bind_events()
        
        # Show initial placeholder
        self.show_placeholder()
        
        logger.info("✅ InputManager initialisiert")
    
    def _bind_events(self):
        """Bind all input events"""
        # Focus events
        self.input_text.bind("<FocusIn>", lambda e: self.on_focus_in())
        self.input_text.bind("<FocusOut>", lambda e: self.on_focus_out())
        
        # Keyboard shortcuts
        self.input_text.bind("<Control-Return>", lambda e: self._on_ctrl_enter())
        self.input_text.bind("<Control-KP_Enter>", lambda e: self._on_ctrl_enter())  # Numpad
        
        # Text change tracking
        self.input_text.bind("<KeyRelease>", lambda e: self._on_text_changed())
    
    def show_placeholder(self):
        """Show placeholder text in the input field"""
        if self.placeholder_active:
            return  # Already showing
        
        current_text = self.input_text.get("1.0", tk.END).strip()
        if current_text:
            return  # Don't show placeholder if text exists
        
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", self.placeholder_text)
        self.input_text.config(foreground='#999999')
        self.placeholder_active = True
    
    def hide_placeholder(self):
        """Hide placeholder text (called on focus)"""
        if not self.placeholder_active:
            return  # Already hidden
        
        self.input_text.delete("1.0", tk.END)
        self.input_text.config(foreground='#000000')
        self.placeholder_active = False
    
    def on_focus_in(self):
        """Handle focus gain event"""
        if self.placeholder_active:
            self.hide_placeholder()
    
    def on_focus_out(self):
        """Handle focus loss event"""
        current_text = self.input_text.get("1.0", tk.END).strip()
        if not current_text:
            self.show_placeholder()
    
    def get_input_text(self) -> str:
        """
        Get the current input text (without placeholder).
        
        Returns:
            The user's input text, or empty string if placeholder is active
        """
        if self.placeholder_active:
            return ""
        
        text = self.input_text.get("1.0", tk.END).strip()
        return text
    
    def set_input_text(self, text: str):
        """
        Set the input text programmatically.
        
        Args:
            text: The text to set
        """
        self.input_text.delete("1.0", tk.END)
        if text:
            self.input_text.insert("1.0", text)
            self.input_text.config(foreground='#000000')
            self.placeholder_active = False
        else:
            self.show_placeholder()
    
    def clear_input(self):
        """Clear the input field and show placeholder"""
        self.input_text.delete("1.0", tk.END)
        self.show_placeholder()
    
    def focus(self):
        """Set focus to the input field"""
        self.input_text.focus_set()
    
    def _on_ctrl_enter(self):
        """Handle Ctrl+Enter keyboard shortcut"""
        if self.on_submit_callback:
            try:
                self.on_submit_callback()
            except Exception as e:
                logger.error(f"Fehler beim Submit-Callback: {e}")
        return "break"  # Prevent default behavior
    
    def _on_text_changed(self):
        """Handle text change event"""
        if self.placeholder_active:
            return  # Ignore changes when placeholder is active
        
        current_text = self.get_input_text()
        
        # Only call callback if text actually changed
        if current_text != self._last_text:
            self._last_text = current_text
            
            if self.on_text_changed_callback:
                try:
                    self.on_text_changed_callback(current_text)
                except Exception as e:
                    logger.error(f"Fehler beim Text-Changed-Callback: {e}")
    
    def is_empty(self) -> bool:
        """Check if input is empty (ignoring placeholder)"""
        return len(self.get_input_text()) == 0
    
    def get_character_count(self) -> int:
        """Get the number of characters in the input (excluding placeholder)"""
        return len(self.get_input_text())
    
    def get_word_count(self) -> int:
        """Get the number of words in the input (excluding placeholder)"""
        text = self.get_input_text()
        if not text:
            return 0
        return len(text.split())


def create_input_manager(
    input_text: tk.Text,
    placeholder_text: str = "Ihre Frage hier eingeben... (Ctrl+Enter zum Senden)",
    on_submit_callback: Optional[Callable[[], None]] = None,
    on_text_changed_callback: Optional[Callable[[str], None]] = None
) -> InputManager:
    """
    Factory function to create an InputManager.
    
    Args:
        input_text: The Tkinter Text widget to manage
        placeholder_text: Text to show when input is empty
        on_submit_callback: Function to call on Ctrl+Enter
        on_text_changed_callback: Function to call when text changes
    
    Returns:
        Configured InputManager instance
    
    Example:
        >>> input_manager = create_input_manager(
        ...     input_text=self.input_text,
        ...     on_submit_callback=self.send_chat_message
        ... )
    """
    return InputManager(
        input_text=input_text,
        placeholder_text=placeholder_text,
        on_submit_callback=on_submit_callback,
        on_text_changed_callback=on_text_changed_callback
    )
