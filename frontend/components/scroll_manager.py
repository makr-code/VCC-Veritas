"""
ScrollManager - Scroll Management for VERITAS Chat Window
==========================================================

Manages scrolling behavior in the chat window including:
- Scroll-to-top button (Material Design)
- Auto-scroll detection
- Smooth scrolling
- Scroll position tracking

Part of the VERITAS frontend modularization (Phase 4).

Author: VERITAS Development Team
Created: 2025-10-18
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ScrollManager:
    """
    Manages scrolling behavior in the chat window.
    
    Responsibilities:
    - Show/hide scroll-to-top button
    - Auto-scroll management
    - Smooth scrolling
    - Scroll position tracking
    
    Design Pattern: Manager Pattern with UI Components
    """
    
    def __init__(
        self,
        chat_text: tk.Text,
        parent_frame: tk.Frame,
        auto_scroll_threshold: float = 0.95,
        button_bg: str = "#0078D4",
        button_fg: str = "#FFFFFF"
    ):
        """
        Initialize the ScrollManager.
        
        Args:
            chat_text: The Tkinter Text widget to manage scrolling for
            parent_frame: Parent frame to place the scroll-to-top button in
            auto_scroll_threshold: Scroll position threshold for auto-scroll (0.0-1.0)
            button_bg: Background color for scroll-to-top button
            button_fg: Foreground color for scroll-to-top button
        """
        self.chat_text = chat_text
        self.parent_frame = parent_frame
        self.auto_scroll_threshold = auto_scroll_threshold
        self.button_bg = button_bg
        self.button_fg = button_fg
        
        # State tracking
        self.scroll_to_top_button: Optional[tk.Button] = None
        self.at_bottom = True
        
        # Create UI components
        self._create_scroll_to_top_button()
        
        # Bind scroll events
        self.chat_text.bind("<Configure>", lambda e: self._on_chat_scroll())
        
        logger.info("✅ ScrollManager initialisiert")
    
    def _create_scroll_to_top_button(self):
        """Create the scroll-to-top button (Material Design)"""
        try:
            # Create button with Material Design styling
            self.scroll_to_top_button = tk.Button(
                self.parent_frame,
                text="⬆",
                command=self.scroll_to_top,
                bg=self.button_bg,
                fg=self.button_fg,
                font=('Segoe UI', 14, 'bold'),
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                width=3,
                height=1
            )
            
            # Material Design shadow effect
            self.scroll_to_top_button.config(
                highlightthickness=2,
                highlightbackground="#004578",
                highlightcolor="#004578"
            )
            
            # Position: Bottom-right corner (initially hidden)
            self.scroll_to_top_button.place_forget()
            
            # Hover effects
            self.scroll_to_top_button.bind("<Enter>", lambda e: self._on_button_enter())
            self.scroll_to_top_button.bind("<Leave>", lambda e: self._on_button_leave())
            
            logger.debug("Scroll-to-top Button erstellt")
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Scroll-Buttons: {e}")
    
    def _on_button_enter(self):
        """Handle button hover enter"""
        if self.scroll_to_top_button:
            self.scroll_to_top_button.config(bg="#005A9E")  # Darker blue
    
    def _on_button_leave(self):
        """Handle button hover leave"""
        if self.scroll_to_top_button:
            self.scroll_to_top_button.config(bg=self.button_bg)
    
    def _on_chat_scroll(self):
        """Handle chat scroll event"""
        try:
            # Get current scroll position
            yview = self.chat_text.yview()
            bottom_pos = yview[1]  # Bottom of visible area (0.0-1.0)
            
            # Update state
            self.at_bottom = bottom_pos >= self.auto_scroll_threshold
            
            # Show/hide scroll-to-top button
            if bottom_pos < 0.85:  # Show button when scrolled up
                self._show_scroll_button()
            else:
                self._hide_scroll_button()
            
        except Exception as e:
            logger.error(f"Fehler bei Scroll-Event-Behandlung: {e}")
    
    def _show_scroll_button(self):
        """Show the scroll-to-top button"""
        if self.scroll_to_top_button and not self.scroll_to_top_button.winfo_ismapped():
            try:
                # Position: Bottom-right corner with padding
                self.scroll_to_top_button.place(relx=0.95, rely=0.90, anchor=tk.SE)
            except Exception as e:
                logger.error(f"Fehler beim Anzeigen des Scroll-Buttons: {e}")
    
    def _hide_scroll_button(self):
        """Hide the scroll-to-top button"""
        if self.scroll_to_top_button and self.scroll_to_top_button.winfo_ismapped():
            try:
                self.scroll_to_top_button.place_forget()
            except Exception as e:
                logger.error(f"Fehler beim Verstecken des Scroll-Buttons: {e}")
    
    def scroll_to_top(self):
        """Scroll to the top of the chat (smooth)"""
        try:
            self.chat_text.yview_moveto(0.0)
            self.at_bottom = False
            logger.debug("Nach oben gescrollt")
        except Exception as e:
            logger.error(f"Fehler beim Scrollen nach oben: {e}")
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the chat (smooth)"""
        try:
            self.chat_text.yview_moveto(1.0)
            self.at_bottom = True
            logger.debug("Nach unten gescrollt")
        except Exception as e:
            logger.error(f"Fehler beim Scrollen nach unten: {e}")
    
    def auto_scroll_if_at_bottom(self):
        """Auto-scroll to bottom if user is already at bottom"""
        if self.at_bottom:
            self.scroll_to_bottom()
    
    def get_scroll_position(self) -> tuple:
        """Get current scroll position (top, bottom)"""
        return self.chat_text.yview()
    
    def set_scroll_position(self, position: float):
        """
        Set scroll position.
        
        Args:
            position: Scroll position (0.0 = top, 1.0 = bottom)
        """
        try:
            self.chat_text.yview_moveto(position)
            self.at_bottom = position >= self.auto_scroll_threshold
        except Exception as e:
            logger.error(f"Fehler beim Setzen der Scroll-Position: {e}")


def create_scroll_manager(
    chat_text: tk.Text,
    parent_frame: tk.Frame,
    auto_scroll_threshold: float = 0.95,
    button_bg: str = "#0078D4",
    button_fg: str = "#FFFFFF"
) -> ScrollManager:
    """
    Factory function to create a ScrollManager.
    
    Args:
        chat_text: The Tkinter Text widget to manage scrolling for
        parent_frame: Parent frame to place the scroll-to-top button in
        auto_scroll_threshold: Scroll position threshold for auto-scroll (0.0-1.0)
        button_bg: Background color for scroll-to-top button
        button_fg: Foreground color for scroll-to-top button
    
    Returns:
        Configured ScrollManager instance
    
    Example:
        >>> scroll_manager = create_scroll_manager(
        ...     chat_text=self.chat_text,
        ...     parent_frame=self.main_frame
        ... )
    """
    return ScrollManager(
        chat_text=chat_text,
        parent_frame=parent_frame,
        auto_scroll_threshold=auto_scroll_threshold,
        button_bg=button_bg,
        button_fg=button_fg
    )
