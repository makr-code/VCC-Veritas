"""
Typing Indicator - "KI arbeitet..." Animation für VERITAS
==========================================================

Material Design Typing Indicator mit pulsierenden Punkten.
Zeigt an, dass die KI gerade eine Antwort generiert.

Features:
- Pulsierende Dot-Animation
- Material Design Styling
- Smooth Ein-/Ausblenden
- Integrierbar in Chat-Display

Part of the VERITAS frontend components.

Author: VERITAS Development Team
Created: 2025-10-18
"""

import tkinter as tk
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TypingIndicator:
    """
    Typing Indicator für Chat-UI.
    
    Zeigt animierte "..." Punkte an um zu signalisieren dass die KI arbeitet.
    
    Design Pattern: Component Pattern mit Animation
    """
    
    def __init__(
        self,
        text_widget: tk.Text,
        bg_color: str = "#F5F5F5",
        fg_color: str = "#757575",
        dot_color: str = "#2196F3",
        animation_speed: int = 500
    ):
        """
        Initialize the TypingIndicator.
        
        Args:
            text_widget: Tkinter Text widget to display indicator in
            bg_color: Background color (Material Design Grey 100)
            fg_color: Foreground color (Material Design Grey 600)
            dot_color: Dot animation color (Material Design Blue 500)
            animation_speed: Animation speed in milliseconds
        """
        self.text_widget = text_widget
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.dot_color = dot_color
        self.animation_speed = animation_speed
        
        # State
        self.is_visible = False
        self.indicator_mark: Optional[str] = None
        self.animation_job: Optional[str] = None
        self.dot_count = 0
        
        logger.debug("✅ TypingIndicator initialisiert")
    
    def show(self):
        """Show typing indicator with animation"""
        if self.is_visible:
            return  # Already visible
        
        self.is_visible = True
        
        # Create unique mark
        import time
        self.indicator_mark = f"typing_indicator_{int(time.time() * 1000)}"
        
        # Insert indicator
        self._insert_indicator()
        
        # Start animation
        self._animate()
        
        logger.debug("👀 Typing indicator shown")
    
    def hide(self):
        """Hide typing indicator"""
        if not self.is_visible:
            return  # Already hidden
        
        self.is_visible = False
        
        # Stop animation
        if self.animation_job:
            try:
                self.text_widget.after_cancel(self.animation_job)
            except:
                pass
            self.animation_job = None
        
        # Remove indicator from text widget
        if self.indicator_mark:
            try:
                # Find and delete indicator
                start_index = self.text_widget.search(
                    "🤖 KI arbeitet",
                    "1.0",
                    tk.END
                )
                if start_index:
                    # Calculate end index
                    line_end = self.text_widget.index(f"{start_index} lineend")
                    self.text_widget.delete(start_index, f"{line_end}+1c")
            except Exception as e:
                logger.error(f"Fehler beim Entfernen des Typing Indicators: {e}")
        
        self.indicator_mark = None
        self.dot_count = 0
        
        logger.debug("👋 Typing indicator hidden")
    
    def _insert_indicator(self):
        """Insert typing indicator into text widget"""
        try:
            # Insert at end
            self.text_widget.insert(tk.END, "\n")
            
            # Create indicator frame (simulated with text)
            indicator_text = "🤖 KI arbeitet"
            dots_text = "."
            
            # Insert indicator
            insert_index = self.text_widget.index(tk.END)
            self.text_widget.insert(tk.END, indicator_text)
            self.text_widget.insert(tk.END, dots_text, "typing_dots")
            self.text_widget.insert(tk.END, "\n")
            
            # Configure tag for dots
            self.text_widget.tag_config(
                "typing_dots",
                foreground=self.dot_color,
                font=("Segoe UI", 10, "bold")
            )
            
            # Configure tag for indicator
            line_num = insert_index.split('.')[0]
            self.text_widget.tag_add("typing_indicator", f"{line_num}.0", f"{line_num}.end")
            self.text_widget.tag_config(
                "typing_indicator",
                background=self.bg_color,
                foreground=self.fg_color,
                font=("Segoe UI", 10),
                spacing1=5,
                spacing3=5,
                lmargin1=10,
                lmargin2=10,
                rmargin=10
            )
            
            # Scroll to end
            self.text_widget.see(tk.END)
            
        except Exception as e:
            logger.error(f"Fehler beim Einfügen des Typing Indicators: {e}")
    
    def _animate(self):
        """Animate the dots (...) to show activity"""
        if not self.is_visible:
            return
        
        try:
            # Find the typing indicator
            start_index = self.text_widget.search(
                "🤖 KI arbeitet",
                "1.0",
                tk.END
            )
            
            if not start_index:
                return
            
            # Calculate dots position
            dots_start = self.text_widget.search(
                ".",
                start_index,
                f"{start_index} lineend"
            )
            
            if dots_start:
                # Calculate dots range
                line_num = dots_start.split('.')[0]
                dots_end = self.text_widget.index(f"{line_num}.end")
                
                # Delete existing dots
                self.text_widget.delete(dots_start, dots_end)
                
                # Update dot count (cycle 0-3)
                self.dot_count = (self.dot_count + 1) % 4
                
                # Insert new dots
                new_dots = "." * self.dot_count if self.dot_count > 0 else " "
                self.text_widget.insert(dots_start, new_dots, "typing_dots")
            
            # Schedule next animation frame
            self.animation_job = self.text_widget.after(
                self.animation_speed,
                self._animate
            )
            
        except Exception as e:
            logger.error(f"Fehler bei Dot-Animation: {e}")
    
    def is_active(self) -> bool:
        """Check if typing indicator is currently visible"""
        return self.is_visible


def create_typing_indicator(
    text_widget: tk.Text,
    bg_color: str = "#F5F5F5",
    fg_color: str = "#757575",
    dot_color: str = "#2196F3",
    animation_speed: int = 500
) -> TypingIndicator:
    """
    Factory function to create a TypingIndicator.
    
    Args:
        text_widget: Tkinter Text widget to display indicator in
        bg_color: Background color (Material Design Grey 100)
        fg_color: Foreground color (Material Design Grey 600)
        dot_color: Dot animation color (Material Design Blue 500)
        animation_speed: Animation speed in milliseconds
    
    Returns:
        Configured TypingIndicator instance
    
    Example:
        >>> indicator = create_typing_indicator(self.chat_text)
        >>> indicator.show()  # Show "KI arbeitet..."
        >>> # ... wait for response ...
        >>> indicator.hide()  # Hide indicator
    """
    return TypingIndicator(
        text_widget=text_widget,
        bg_color=bg_color,
        fg_color=fg_color,
        dot_color=dot_color,
        animation_speed=animation_speed
    )
