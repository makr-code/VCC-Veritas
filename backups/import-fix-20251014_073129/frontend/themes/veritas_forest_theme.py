"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "veritas_forest_theme"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...XaKTyA=="  # Gekuerzt fuer Sicherheit
module_organization_key = "6bd9ecffd1a79dfc5ec9961491d8348ba25a72c0d3be4d50a15243978f146371"
module_file_key = "4ee23e7af2cfd4d7cce3f1ae52a883c8d0497eaa7e8678b0200fda1e742023c9"
module_version = "1.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veritas Forest Theme Manager - Original Forest Theme Integration
https://github.com/rdbende/Forest-ttk-theme
"""

import tkinter as tk
from tkinter import ttk
import os
import logging

logger = logging.getLogger(__name__)

# Theme-Farben für Forest Theme (werden vom echten Theme überschrieben)
VERITAS_COLORS = {
    'bg': '#f0f0f0',
    'fg': '#2d2d2d', 
    'select_bg': '#4a7c7e',
    'select_fg': '#ffffff',
    'button_bg': '#e8e8e8',
    'button_fg': '#2d2d2d',
    'entry_bg': '#ffffff',
    'entry_fg': '#2d2d2d',
    'text_bg': '#ffffff',
    'text_fg': '#2d2d2d',
    'accent': '#4a7c7e',
    'success': '#28a745',
    'warning': '#ffc107',
    'error': '#dc3545',
    'info': '#17a2b8'
}

# Theme-Status verfolgen
_theme_initialized = False
_current_theme = None

def initialize_veritas_theme(root=None):
    """Initialisiert das Original Forest Theme."""
    global _theme_initialized, _current_theme
    
    try:
        # Prüfen ob Theme bereits initialisiert
        if _theme_initialized and _current_theme:
            logger.debug(f"Theme bereits initialisiert: {_current_theme}")
            return VERITAS_COLORS
        
        # Root-Widget ermitteln
        if root is None:
            # Versuche aktuelle Root zu finden
            root = tk._default_root
            if root is None:
                logger.warning("Kein Root-Widget gefunden - Theme kann nicht geladen werden")
                return VERITAS_COLORS
        
        # Für Toplevel-Fenster: Das master-Widget (Root) verwenden
        if hasattr(root, 'master') and root.master:
            root_widget = root.master
        else:
            # Das übergebene Widget oder das default root verwenden
            root_widget = root if isinstance(root, tk.Tk) else tk._default_root
            if root_widget is None:
                # Als letzter Ausweg: Ein neues temporäres Root erstellen
                root_widget = tk.Tk()
                root_widget.withdraw()  # Verstecken
        
        # Forest Theme-Dateien suchen
        current_dir = os.path.dirname(os.path.abspath(__file__))
        theme_files = {
            'light': os.path.join(current_dir, 'themes', 'forest-light.tcl'),
            'dark': os.path.join(current_dir, 'themes', 'forest-dark.tcl')
        }
        
        # Verfügbare Theme-Datei laden
        theme_loaded = False
        active_theme = None
        for theme_name, theme_path in theme_files.items():
            if os.path.exists(theme_path):
                try:
                    # Prüfen ob Theme bereits existiert
                    existing_themes = list(ttk.Style().theme_names())
                    theme_full_name = f'forest-{theme_name}'
                    
                    if theme_full_name not in existing_themes:
                        # Import the tcl file nur wenn noch nicht geladen
                        root_widget.tk.call('source', theme_path)
                    
                    # Set the theme with the theme_use method
                    style = ttk.Style()
                    style.theme_use(theme_full_name)
                    
                    # Zusätzliche Forest-spezifische Style-Konfigurationen
                    _configure_forest_styles(style, theme_name)
                    
                    logger.info(f"Forest-{theme_name} Theme erfolgreich geladen")
                    theme_loaded = True
                    active_theme = theme_name
                    _current_theme = theme_full_name
                    break
                    
                except Exception as e:
                    logger.warning(f"Fehler beim Laden von forest-{theme_name}: {e}")
                    continue
        
        if not theme_loaded:
            logger.warning("Forest Theme-Dateien nicht gefunden - verwende Fallback")
            # Fallback: Einfaches Theme
            style = ttk.Style()
            style.configure('TLabel', background=VERITAS_COLORS['bg'], foreground=VERITAS_COLORS['fg'])
            style.configure('TButton', background=VERITAS_COLORS['button_bg'], foreground=VERITAS_COLORS['button_fg'])
            style.configure('TEntry', fieldbackground=VERITAS_COLORS['entry_bg'], foreground=VERITAS_COLORS['entry_fg'])
            active_theme = 'fallback'
            _current_theme = 'fallback'
        
        # Theme-spezifische Konfigurationen anwenden
        if theme_loaded and active_theme:
            _apply_veritas_customizations(style, active_theme)
        
        _theme_initialized = True
        return VERITAS_COLORS
        
    except Exception as e:
        logger.error(f"Forest Theme-Initialisierung fehlgeschlagen: {e}")
        return VERITAS_COLORS

def _configure_forest_styles(style, theme_name):
    """Konfiguriert Forest-spezifische Styles für ttk-Widgets."""
    try:
        # Basis-Theme-Farben je nach theme_name
        if theme_name == 'dark':
            colors = {
                'bg': '#313131',
                'fg': '#ffffff', 
                'accent': '#217346',
                'select_bg': '#217346',
                'select_fg': '#ffffff'
            }
        else:  # light
            colors = {
                'bg': '#ffffff',
                'fg': '#000000',
                'accent': '#217346', 
                'select_bg': '#217346',
                'select_fg': '#ffffff'
            }
        
        # Zusätzliche Forest-spezifische Styles konfigurieren
        # Diese Styles sind spezifisch für das Forest Theme
        
        # Accent Button Style (bereits im Theme definiert)
        # Wir können hier zusätzliche Anpassungen vornehmen
        
        # Card Style für Frames (bereits im Theme definiert)
        # Wir können hier Padding und Border-Anpassungen machen
        
        # Toggle Button und Switch Styles (bereits im Theme definiert)
        
        logger.debug(f"Forest-{theme_name} spezifische Styles konfiguriert")
        
    except Exception as e:
        logger.error(f"Fehler beim Konfigurieren der Forest-Styles: {e}")

def _apply_veritas_customizations(style, theme_name):
    """Wendet Veritas-spezifische Anpassungen auf das Forest Theme an."""
    try:
        # Anpassungen für bessere Integration mit Veritas
        
        # Toolbar-Buttons verwenden Standard ttk.Button
        # Chat-Aktions-Buttons können Accent.TButton verwenden für Hervorhebung
        
        # Statusbar-Labels
        style.configure('Status.TLabel', 
                       font=('Segoe UI', 8),
                       anchor='w')
        
        # Success, Warning, Error Status-Styles
        if theme_name == 'dark':
            style.configure('Success.TLabel', foreground='#4caf50')
            style.configure('Warning.TLabel', foreground='#ff9800') 
            style.configure('Error.TLabel', foreground='#f44336')
            style.configure('Info.TLabel', foreground='#2196f3')
        else:
            style.configure('Success.TLabel', foreground='#2e7d32')
            style.configure('Warning.TLabel', foreground='#f57c00')
            style.configure('Error.TLabel', foreground='#c62828')
            style.configure('Info.TLabel', foreground='#1565c0')
        
        # Spezielle Veritas-Styles
        style.configure('Citation.TFrame', relief='solid', borderwidth=1)
        style.configure('RAG.TLabel', font=('Segoe UI', 8, 'italic'))
        
        logger.debug(f"Veritas-Anpassungen für {theme_name}-Theme angewandt")
        
    except Exception as e:
        logger.error(f"Fehler beim Anwenden der Veritas-Anpassungen: {e}")

def apply_forest_widget_style(widget, style_name=None):
    """Wendet Forest-spezifische Styles auf ein Widget an."""
    try:
        if not style_name:
            return
            
        # Mapping von Widget-Typen zu empfohlenen Forest-Styles
        forest_styles = {
            'accent_button': 'Accent.TButton',      # Für wichtige Aktions-Buttons
            'toggle_button': 'ToggleButton',        # Für Checkbuttons als Toggle
            'switch': 'Switch',                     # Für Checkbuttons als Switch
            'card': 'Card',                         # Für Frames als Cards
            'citation_frame': 'Card'                # Für Citation-Frames
        }
        
        forest_style = forest_styles.get(style_name)
        if forest_style and hasattr(widget, 'configure'):
            # Prüfen ob es ein ttk-Widget ist
            if hasattr(widget, 'configure') and 'style' in widget.configure():
                widget.configure(style=forest_style)
                logger.debug(f"Forest-Style '{forest_style}' auf Widget angewandt")
            else:
                logger.warning(f"Widget unterstützt keine ttk-Styles: {type(widget)}")
                
    except Exception as e:
        logger.error(f"Fehler beim Anwenden des Forest-Widget-Styles: {e}")

def apply_theme_to_widget(widget, theme_colors=None):
    """Wendet Theme auf ein Widget an."""
    try:
        if not theme_colors:
            theme_colors = VERITAS_COLORS
            
        if isinstance(widget, (tk.Tk, tk.Toplevel, tk.Frame)):
            widget.configure(bg=theme_colors.get('bg', '#f0f0f0'))
        elif isinstance(widget, tk.Label):
            widget.configure(bg=theme_colors.get('bg', '#f0f0f0'),
                           fg=theme_colors.get('fg', '#2d2d2d'))
        elif isinstance(widget, tk.Button):
            widget.configure(bg=theme_colors.get('button_bg', '#e8e8e8'),
                           fg=theme_colors.get('button_fg', '#2d2d2d'))
        elif isinstance(widget, tk.Entry):
            widget.configure(bg=theme_colors.get('entry_bg', '#ffffff'),
                           fg=theme_colors.get('entry_fg', '#2d2d2d'))
        elif isinstance(widget, tk.Text):
            widget.configure(bg=theme_colors.get('text_bg', '#ffffff'),
                           fg=theme_colors.get('text_fg', '#2d2d2d'))
            
    except Exception as e:
        logger.error(f"Theme-Anwendung fehlgeschlagen: {e}")

def configure_text_with_theme(text_widget, theme_colors=None):
    """Konfiguriert ein Text-Widget mit dem Theme."""
    try:
        if not theme_colors:
            theme_colors = VERITAS_COLORS
            
        if text_widget:
            text_widget.configure(
                bg=theme_colors.get('text_bg', '#ffffff'),
                fg=theme_colors.get('text_fg', '#2d2d2d'),
                insertbackground=theme_colors.get('fg', '#2d2d2d'),
                selectbackground=theme_colors.get('select_bg', '#4a7c7e'),
                selectforeground=theme_colors.get('select_fg', '#ffffff'),
                relief='flat',
                bd=1
            )
            
            logger.debug("Text-Widget mit Theme konfiguriert")
            
    except Exception as e:
        logger.error(f"Text-Widget Theme-Konfiguration fehlgeschlagen: {e}")

def get_theme_colors():
    """Gibt Theme-Farben zurück."""
    return VERITAS_COLORS.copy()

def get_color(color_name, fallback='#000000'):
    """Gibt eine spezifische Theme-Farbe zurück."""
    return VERITAS_COLORS.get(color_name, fallback)

def configure_toolbar_with_theme(toolbar_frame, theme_colors=None):
    """Konfiguriert eine Toolbar mit dem Forest Theme."""
    try:
        if not theme_colors:
            theme_colors = VERITAS_COLORS
            
        if toolbar_frame:
            # Toolbar-Frame selbst
            if hasattr(toolbar_frame, 'configure') and 'style' in str(toolbar_frame.configure()):
                # ttk.Frame - verwende Card-Style für bessere Optik
                try:
                    toolbar_frame.configure(style='Card')
                except:
                    pass
            
            # Alle Buttons in der Toolbar durchgehen
            for child in toolbar_frame.winfo_children():
                _apply_forest_style_to_widget(child)
                
    except Exception as e:
        logger.error(f"Toolbar Theme-Konfiguration fehlgeschlagen: {e}")

def configure_statusbar_with_theme(statusbar_frame, theme_colors=None):
    """Konfiguriert eine Statusbar mit dem Forest Theme."""
    try:
        if not theme_colors:
            theme_colors = VERITAS_COLORS
            
        if statusbar_frame:
            # Statusbar Labels durchgehen
            for child in statusbar_frame.winfo_children():
                if isinstance(child, ttk.Label):
                    # Status.TLabel Style anwenden falls verfügbar
                    try:
                        child.configure(style='Status.TLabel')
                    except:
                        pass
                        
    except Exception as e:
        logger.error(f"Statusbar Theme-Konfiguration fehlgeschlagen: {e}")

def _apply_forest_style_to_widget(widget):
    """Wendet automatisch passende Forest-Styles auf ein Widget an."""
    try:
        widget_class = widget.winfo_class()
        
        # Mapping von Widget-Klassen zu Forest-Styles
        style_mapping = {
            'TButton': None,          # Standard-Button - kein spezieller Style
            'TEntry': None,           # Standard-Entry - kein spezieller Style  
            'TLabel': None,           # Standard-Label - kein spezieller Style
            'TFrame': None,           # Standard-Frame - kein spezieller Style
            'Checkbutton': 'Switch',  # Checkbuttons als Switches
            'TCheckbutton': 'Switch', # ttk Checkbuttons als Switches
        }
        
        # Spezielle Behandlung für bestimmte Button-Texte (Accent-Buttons)
        if widget_class == 'TButton' and hasattr(widget, 'cget'):
            try:
                button_text = widget.cget('text')
                # API-Status und wichtige Action-Buttons als Accent
                if button_text in ['🟢', '🔴', '🟡'] or 'API' in str(button_text):
                    widget.configure(style='Accent.TButton')
                    return
            except:
                pass
        
        # Standard-Style anwenden falls vorhanden
        forest_style = style_mapping.get(widget_class)
        if forest_style and hasattr(widget, 'configure'):
            try:
                widget.configure(style=forest_style)
                logger.debug(f"Forest-Style '{forest_style}' auf {widget_class} angewandt")
            except Exception as style_error:
                logger.debug(f"Style '{forest_style}' für {widget_class} nicht verfügbar: {style_error}")
                
        # Rekursiv auf Child-Widgets anwenden
        try:
            for child in widget.winfo_children():
                _apply_forest_style_to_widget(child)
        except:
            pass
            
    except Exception as e:
        logger.debug(f"Fehler beim automatischen Style-Anwenden: {e}")

def apply_forest_styles_to_window(window):
    """Wendet Forest-Styles rekursiv auf alle Widgets eines Fensters an."""
    try:
        # Auf alle Child-Widgets anwenden
        for child in window.winfo_children():
            _apply_forest_style_to_widget(child)
            
        logger.info("Forest-Styles auf Fenster angewandt")
        
    except Exception as e:
        logger.error(f"Fehler beim Anwenden der Forest-Styles auf Fenster: {e}")

def get_forest_style_for_widget(widget_type, widget_context=None):
    """Gibt den empfohlenen Forest-Style für einen Widget-Typ zurück."""
    style_recommendations = {
        'important_button': 'Accent.TButton',
        'toggle_action': 'ToggleButton', 
        'switch': 'Switch',
        'card_frame': 'Card',
        'citation_frame': 'Card',
        'status_label': 'Status.TLabel',
        'success_label': 'Success.TLabel',
        'warning_label': 'Warning.TLabel', 
        'error_label': 'Error.TLabel',
        'info_label': 'Info.TLabel'
    }
    
    return style_recommendations.get(widget_type, None)

# Backwards compatibility functions
def apply_modern_theme():
    """Legacy-Funktion für Rückwärtskompatibilität."""
    return initialize_veritas_theme()

def configure_widget_theme(widget, widget_type='default'):
    """Legacy-Funktion für Rückwärtskompatibilität."""
    return apply_theme_to_widget(widget)