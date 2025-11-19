"""
VQB Frontend - Base Observable Model

Implements Observer pattern for model updates.
"""

from typing import Callable, List, Any, Dict
from abc import ABC


class Observable(ABC):
    """
    Base class for observable models
    
    Implements the Observer pattern to notify views of model changes.
    """
    
    def __init__(self):
        """Initialize observable with empty observer list"""
        self._observers: List[Callable] = []
    
    def attach(self, observer: Callable):
        """
        Attach an observer callback
        
        Args:
            observer: Callback function to be called on updates
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer: Callable):
        """
        Detach an observer callback
        
        Args:
            observer: Callback function to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event: str, **kwargs):
        """
        Notify all observers of an event
        
        Args:
            event: Event type (e.g., "added", "updated", "deleted")
            **kwargs: Event-specific data
        """
        for observer in self._observers:
            try:
                observer(event=event, **kwargs)
            except Exception as e:
                # Log but don't stop other observers
                import logging
                logging.error(f"Error in observer: {e}", exc_info=True)
    
    def get_observer_count(self) -> int:
        """Get number of attached observers"""
        return len(self._observers)
