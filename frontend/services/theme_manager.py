#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Frontend Service: Theme Manager
Zentralisierte Theme-Verwaltung für Light/Dark Mode und Farben

Features:
- Singleton Pattern für globalen Zugriff
- Theme-Switching (Light ↔ Dark)
- Observer Pattern für UI-Updates
- Dependency Injection freundlich
- Keine zirkulären Imports

Version: 1.0.0
"""

import logging
from typing import Dict, Callable, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ThemeType(Enum):
    """Verfügbare Themes"""
    LIGHT = 'light'
    DARK = 'dark'


class ThemeManager:
    """
    Zentrale Theme-Verwaltung nach Singleton-Pattern
    
    Features:
    - get_colors() für aktuelles Farbschema
    - set_theme() für Theme-Wechsel
    - toggle_theme() für Light ↔ Dark
    - Observer Pattern für automatische UI-Updates
    
    Example:
        theme_mgr = ThemeManager.get_instance()
        colors = theme_mgr.get_colors()
        theme_mgr.register_listener(my_update_callback)
        theme_mgr.toggle_theme()  # Triggert alle Callbacks
    """
    
    _instance: Optional['ThemeManager'] = None
    
    # ✨ Theme-Definitionen (aus veritas_app.py extrahiert)
    COLORS_LIGHT = {
        # Primary Colors
        'primary': '#2E86AB',
        'success': '#28A745',
        'warning': '#F18F01',
        'danger': '#C73E1D',
        'secondary': '#6C757D',
        'light': '#F8F9FA',
        'dark': '#343A40',
        
        # Background Colors
        'bg_main': '#FFFFFF',
        'bg_secondary': '#F7F7F7',
        'chat_bg': '#FFFFFF',
        'input_bg': '#F7F7F7',
        'bubble_user': '#E3F2FD',
        'bubble_assistant': '#FFFFFF',
        'bubble_system': '#F5F5F5',
        'user_bubble_bg': '#E3F2FD',
        'assistant_bubble_bg': '#FFFFFF',
        'metadata_bg': '#F5F5F5',  # ✨ Für MetadataCompactWrapper
        'metadata_text': '#616161',  # ✨ Text-Farbe für Metadata
        'metadata_collapsed': '#9E9E9E',  # ✨ Text-Farbe wenn collapsed
        
        # Text Colors
        'text_primary': '#212121',
        'text_secondary': '#616161',
        'text_disabled': '#9E9E9E',
        'text_user': '#1E3A5F',
        'user_text': '#1E3A5F',  # ✨ Alias
        'text_assistant': '#212121',
        'assistant_text': '#212121',  # ✨ Alias
        'timestamp': '#78909C',  # ✨ Timestamp-Farbe
        
        # Border Colors
        'border_main': '#E0E0E0',
        'border_light': '#EEEEEE',
        'border_user_bubble': '#BBDEFB',
        'border_assistant': '#E0E0E0',
        'metadata_border': '#E0E0E0',  # ✨ Border für Metadata-Wrapper
        
        # Quality Enhancement Colors
        'quality_high': '#4CAF50',
        'quality_medium': '#FF9800',
        'quality_low': '#F44336',
        'quality_bg': '#F8FFF8',
        'sources_bg': '#F0F8FF',
        'suggestions_bg': '#FFFAF0',
        
        # Feedback Colors
        'feedback_positive': '#4CAF50',
        'feedback_negative': '#F44336',
        'feedback_idle': '#BDBDBD',
    }
    
    COLORS_DARK = {
        # Primary Colors
        'primary': '#4A9ECC',
        'success': '#4CAF50',
        'warning': '#FFA726',
        'danger': '#EF5350',
        'secondary': '#9E9E9E',
        'light': '#424242',
        'dark': '#E0E0E0',
        
        # Background Colors
        'bg_main': '#1E1E1E',
        'bg_secondary': '#2C2C2C',
        'chat_bg': '#1E1E1E',
        'input_bg': '#2C2C2C',
        'bubble_user': '#1E3A5F',
        'bubble_assistant': '#2C2C2C',
        'bubble_system': '#373737',
        'user_bubble_bg': '#1E3A5F',
        'assistant_bubble_bg': '#2C2C2C',
        'metadata_bg': '#2C2C2C',  # ✨ Für MetadataCompactWrapper
        'metadata_text': '#B0B0B0',  # ✨ Text-Farbe für Metadata (Dark Mode)
        'metadata_collapsed': '#757575',  # ✨ Text-Farbe wenn collapsed (Dark Mode)
        
        # Text Colors
        'text_primary': '#E0E0E0',
        'text_secondary': '#B0B0B0',
        'text_disabled': '#757575',
        'text_user': '#E3F2FD',
        'user_text': '#E3F2FD',  # ✨ Alias
        'text_assistant': '#E0E0E0',
        'assistant_text': '#E0E0E0',  # ✨ Alias
        'timestamp': '#90A4AE',  # ✨ Timestamp-Farbe
        
        # Border Colors
        'border_main': '#424242',
        'border_light': '#373737',
        'border_user_bubble': '#2C5282',
        'border_assistant': '#424242',
        'metadata_border': '#424242',  # ✨ Border für Metadata-Wrapper
        
        # Quality Enhancement Colors
        'quality_high': '#66BB6A',
        'quality_medium': '#FFA726',
        'quality_low': '#EF5350',
        'quality_bg': '#1F2A1F',
        'sources_bg': '#1A2332',
        'suggestions_bg': '#2A251A',
        
        # Feedback Colors
        'feedback_positive': '#66BB6A',
        'feedback_negative': '#EF5350',
        'feedback_idle': '#757575',
    }
    
    def __init__(self):
        """Initialisiere ThemeManager (privat - use get_instance())"""
        self.current_theme = ThemeType.LIGHT
        self.listeners: List[Callable[[Dict[str, str]], None]] = []
        logger.info(f"✅ ThemeManager initialisiert: {self.current_theme.value}")
    
    @classmethod
    def get_instance(cls) -> 'ThemeManager':
        """
        Singleton Instance (Thread-safe)
        
        Returns:
            ThemeManager: Globale Instanz
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_colors(self) -> Dict[str, str]:
        """
        Gibt aktuelles Farbschema zurück
        
        Returns:
            Dict mit allen Farben für aktuelles Theme
        """
        if self.current_theme == ThemeType.DARK:
            return self.COLORS_DARK.copy()
        return self.COLORS_LIGHT.copy()
    
    def get_theme(self) -> ThemeType:
        """Gibt aktuelles Theme zurück"""
        return self.current_theme
    
    def set_theme(self, theme: ThemeType):
        """
        Setzt Theme und benachrichtigt Listener
        
        Args:
            theme: LIGHT oder DARK
        """
        if theme == self.current_theme:
            return  # Kein Wechsel nötig
        
        old_theme = self.current_theme
        self.current_theme = theme
        
        logger.info(f"🎨 Theme gewechselt: {old_theme.value} → {theme.value}")
        
        # Benachrichtige alle registrierten Listener
        colors = self.get_colors()
        for listener in self.listeners:
            try:
                listener(colors)
            except Exception as e:
                logger.error(f"❌ Fehler in Theme-Listener: {e}")
    
    def toggle_theme(self):
        """Wechselt zwischen Light und Dark Mode"""
        new_theme = ThemeType.DARK if self.current_theme == ThemeType.LIGHT else ThemeType.LIGHT
        self.set_theme(new_theme)
    
    def register_listener(self, callback: Callable[[Dict[str, str]], None]):
        """
        Registriere Callback für Theme-Änderungen
        
        Args:
            callback: Funktion die bei Theme-Wechsel aufgerufen wird
                     Signatur: callback(colors: Dict[str, str])
        
        Example:
            def update_ui(colors):
                window.config(bg=colors['bg_main'])
            
            theme_mgr.register_listener(update_ui)
        """
        if callback not in self.listeners:
            self.listeners.append(callback)
            logger.debug(f"✅ Theme-Listener registriert: {callback.__name__}")
    
    def unregister_listener(self, callback: Callable[[Dict[str, str]], None]):
        """Entfernt registrierten Listener"""
        if callback in self.listeners:
            self.listeners.remove(callback)
            logger.debug(f"🗑️ Theme-Listener entfernt: {callback.__name__}")
    
    def inject_colors_into_module(self, module_set_colors_func: Callable[[Dict[str, str]], None]):
        """
        Injiziert Farben in UI-Module (für Rückwärtskompatibilität)
        
        Args:
            module_set_colors_func: set_colors() Funktion des Ziel-Moduls
        
        Example:
            from ui.veritas_ui_chat_bubbles import set_colors
            theme_mgr.inject_colors_into_module(set_colors)
        """
        try:
            colors = self.get_colors()
            module_set_colors_func(colors)
            logger.debug(f"✅ Theme-Farben in Modul injiziert")
        except Exception as e:
            logger.error(f"❌ Fehler beim Injizieren der Theme-Farben: {e}")


# ✨ Convenience-Funktion für globalen Zugriff
def get_theme_manager() -> ThemeManager:
    """
    Globaler Zugriff auf ThemeManager-Instanz
    
    Returns:
        ThemeManager: Singleton-Instanz
    """
    return ThemeManager.get_instance()


# ✨ Convenience-Funktion für direkten Farb-Zugriff
def get_colors() -> Dict[str, str]:
    """
    Direkter Zugriff auf aktuelles Farbschema
    
    Returns:
        Dict mit allen Farben
    """
    return ThemeManager.get_instance().get_colors()
