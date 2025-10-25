"""
SettingsManager - LLM Parameter Settings Management for VERITAS
================================================================

Manages LLM parameter settings including:
- Parameter presets (Rechtsauskunft, Standard, Ausführlich, etc.)
- Temperature, max_tokens, top_p configuration
- Preset application and UI updates

Part of the VERITAS frontend modularization (Phase 4).

Author: VERITAS Development Team
Created: 2025-10-18
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    Manages LLM parameter settings and presets.
    
    Responsibilities:
    - Parameter preset definitions
    - Preset application
    - UI updates (temperature, tokens, top_p labels)
    - System message notifications
    
    Design Pattern: Manager Pattern with Preset Pattern
    """
    
    def __init__(
        self,
        temperature_var: tk.DoubleVar,
        max_tokens_var: tk.IntVar,
        top_p_var: tk.DoubleVar,
        temperature_label: Optional[ttk.Label] = None,
        tokens_label: Optional[ttk.Label] = None,
        topp_label: Optional[ttk.Label] = None,
        on_preset_applied: Optional[Callable[[str, float, int, float], None]] = None,
        add_system_message_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the SettingsManager.
        
        Args:
            temperature_var: Tkinter DoubleVar for temperature
            max_tokens_var: Tkinter IntVar for max_tokens
            top_p_var: Tkinter DoubleVar for top_p
            temperature_label: Label to update with temperature value
            tokens_label: Label to update with tokens info
            topp_label: Label to update with top_p value
            on_preset_applied: Callback when preset is applied
            add_system_message_callback: Callback to add system message to chat
        """
        self.temperature_var = temperature_var
        self.max_tokens_var = max_tokens_var
        self.top_p_var = top_p_var
        self.temperature_label = temperature_label
        self.tokens_label = tokens_label
        self.topp_label = topp_label
        self.on_preset_applied = on_preset_applied
        self.add_system_message_callback = add_system_message_callback
        
        # Define presets (optimized for Verwaltungsrecht/Administrative Law)
        self.presets = self._define_presets()
        
        logger.info("✅ SettingsManager initialisiert")
    
    def _define_presets(self) -> List[Tuple[str, float, int, float, str]]:
        """
        Define parameter presets.
        
        Returns:
            List of (label, temperature, max_tokens, top_p, tooltip) tuples
        """
        return [
            (
                "⚖️ Rechtsauskunft",
                0.3,
                800,
                0.7,
                "Präzise Rechtsauskunft\n\n"
                "Optimal für:\n"
                "• Gesetzestexte & Paragraphen\n"
                "• Konkrete Rechtsfragen\n"
                "• Behördliche Bescheide\n\n"
                "Temp: 0.3 | Tokens: 800 | Top-p: 0.7\n\n"
                "💡 Tipp: Für kurze, faktenbasierte Antworten"
            ),
            (
                "📘 Standard",
                0.6,
                1200,
                0.85,
                "Standard-Verwaltungsantwort\n\n"
                "Optimal für:\n"
                "• Typische Verwaltungsfragen\n"
                "• Verfahrensabläufe\n"
                "• Antragsberatung\n\n"
                "Temp: 0.6 | Tokens: 1200 | Top-p: 0.85\n\n"
                "💡 Tipp: IDEAL für Verwaltungsrecht"
            ),
            (
                "📄 Ausführlich",
                0.5,
                1800,
                0.8,
                "Ausführliche Rechtsanalyse\n\n"
                "Optimal für:\n"
                "• Komplexe Rechtsfragen\n"
                "• Mehrere Rechtsgebiete\n"
                "• Detaillierte Verfahrenserklärungen\n\n"
                "Temp: 0.5 | Tokens: 1800 | Top-p: 0.8\n\n"
                "💡 Tipp: Für umfassende Beratung"
            ),
            (
                "🎨 Bürgerfreundlich",
                0.7,
                1000,
                0.9,
                "Bürgerfreundliche Formulierung\n\n"
                "Optimal für:\n"
                "• Verständliche Erklärungen\n"
                "• Umformulierung von Amtsdeutsch\n"
                "• Mehrere Beispiele\n\n"
                "Temp: 0.7 | Tokens: 1000 | Top-p: 0.9\n\n"
                "💡 Tipp: Für Bürgerkommunikation"
            )
        ]
    
    def apply_preset(self, preset_name: str):
        """
        Apply a parameter preset by name.
        
        Args:
            preset_name: Name of the preset to apply (e.g., "⚖️ Rechtsauskunft")
        """
        # Find preset
        preset = None
        for p in self.presets:
            if p[0] == preset_name:
                preset = p
                break
        
        if not preset:
            logger.warning(f"Preset nicht gefunden: {preset_name}")
            return
        
        # Unpack preset
        label, temperature, max_tokens, top_p, _ = preset
        
        # Apply parameters
        self._apply_preset_values(label, temperature, max_tokens, top_p)
    
    def _apply_preset_values(self, preset_name: str, temperature: float, max_tokens: int, top_p: float):
        """
        Apply preset parameter values.
        
        Args:
            preset_name: Name of the preset
            temperature: Temperature value
            max_tokens: Max tokens value
            top_p: Top-p value
        """
        try:
            # Set parameter variables
            self.temperature_var.set(temperature)
            self.max_tokens_var.set(max_tokens)
            self.top_p_var.set(top_p)
            
            # Update UI labels
            self._update_temperature_label(temperature)
            self._update_topp_label(top_p)
            self._update_tokens_label()
            
            # System message
            preset_msg = f"🎛️ Preset angewandt: {preset_name} (Temp={temperature}, Tokens={max_tokens}, Top-p={top_p})"
            if self.add_system_message_callback:
                try:
                    self.add_system_message_callback(preset_msg)
                except Exception as e:
                    logger.error(f"Fehler beim Hinzufügen der System-Nachricht: {e}")
            else:
                logger.info(preset_msg)
            
            # Callback
            if self.on_preset_applied:
                try:
                    self.on_preset_applied(preset_name, temperature, max_tokens, top_p)
                except Exception as e:
                    logger.error(f"Fehler beim Preset-Applied-Callback: {e}")
            
            logger.info(f"Preset angewandt: {preset_name} | T={temperature}, Tokens={max_tokens}, p={top_p}")
            
        except Exception as e:
            logger.error(f"Fehler beim Anwenden des Presets '{preset_name}': {e}")
            if self.add_system_message_callback:
                try:
                    self.add_system_message_callback(f"❌ Fehler beim Anwenden des Presets: {e}")
                except:
                    pass
    
    def _update_temperature_label(self, value):
        """Update temperature label"""
        if self.temperature_label:
            try:
                temp_val = float(value)
                self.temperature_label.config(text=f"{temp_val:.2f}")
            except:
                pass
    
    def _update_topp_label(self, value):
        """Update top-p label"""
        if self.topp_label:
            try:
                topp_val = float(value)
                self.topp_label.config(text=f"{topp_val:.2f}")
            except:
                pass
    
    def _update_tokens_label(self):
        """Update tokens info label"""
        if self.tokens_label:
            try:
                tokens = self.max_tokens_var.get()
                # Estimate words (German: 1 token ≈ 0.75 words)
                estimated_words = int(tokens * 0.75)
                self.tokens_label.config(text=f"📝 ~{estimated_words} Wörter")
            except:
                pass
    
    def get_current_settings(self) -> Dict[str, any]:
        """
        Get current parameter settings.
        
        Returns:
            Dictionary with current parameter values
        """
        return {
            'temperature': self.temperature_var.get(),
            'max_tokens': self.max_tokens_var.get(),
            'top_p': self.top_p_var.get()
        }
    
    def get_presets(self) -> List[Tuple[str, float, int, float, str]]:
        """Get list of available presets"""
        return list(self.presets)
    
    def get_preset_names(self) -> List[str]:
        """Get list of preset names"""
        return [preset[0] for preset in self.presets]
    
    def create_preset_buttons(self, parent: tk.Frame, tooltip_callback: Optional[Callable] = None):
        """
        Create preset buttons in the given parent frame.
        
        Args:
            parent: Parent frame to create buttons in
            tooltip_callback: Optional callback for creating tooltips
        """
        try:
            preset_frame = ttk.Frame(parent)
            preset_frame.pack(fill=tk.X, padx=5, pady=3)
            
            # Label
            preset_label = ttk.Label(
                preset_frame,
                text="Presets:",
                font=('Segoe UI', 8, 'bold'),
                foreground='#555555'
            )
            preset_label.pack(side=tk.LEFT, padx=(0, 8))
            
            # Create buttons for each preset
            for label, temp, tokens, topp, tooltip_text in self.presets:
                btn = ttk.Button(
                    preset_frame,
                    text=label,
                    command=lambda t=temp, tk=tokens, p=topp, l=label: 
                        self._apply_preset_values(l, t, tk, p),
                    width=14
                )
                btn.pack(side=tk.LEFT, padx=2)
                
                # Add tooltip if callback provided
                if tooltip_callback:
                    try:
                        tooltip_callback(btn, tooltip_text)
                    except Exception as e:
                        logger.error(f"Fehler beim Erstellen des Tooltips: {e}")
            
            logger.debug("Preset-Buttons erstellt")
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Preset-Buttons: {e}")


def create_settings_manager(
    temperature_var: tk.DoubleVar,
    max_tokens_var: tk.IntVar,
    top_p_var: tk.DoubleVar,
    temperature_label: Optional[ttk.Label] = None,
    tokens_label: Optional[ttk.Label] = None,
    topp_label: Optional[ttk.Label] = None,
    on_preset_applied: Optional[Callable[[str, float, int, float], None]] = None,
    add_system_message_callback: Optional[Callable[[str], None]] = None
) -> SettingsManager:
    """
    Factory function to create a SettingsManager.
    
    Args:
        temperature_var: Tkinter DoubleVar for temperature
        max_tokens_var: Tkinter IntVar for max_tokens
        top_p_var: Tkinter DoubleVar for top_p
        temperature_label: Label to update with temperature value
        tokens_label: Label to update with tokens info
        topp_label: Label to update with top_p value
        on_preset_applied: Callback when preset is applied
        add_system_message_callback: Callback to add system message to chat
    
    Returns:
        Configured SettingsManager instance
    
    Example:
        >>> settings_manager = create_settings_manager(
        ...     temperature_var=self.temperature_var,
        ...     max_tokens_var=self.max_tokens_var,
        ...     top_p_var=self.top_p_var,
        ...     add_system_message_callback=self.add_system_message
        ... )
    """
    return SettingsManager(
        temperature_var=temperature_var,
        max_tokens_var=max_tokens_var,
        top_p_var=top_p_var,
        temperature_label=temperature_label,
        tokens_label=tokens_label,
        topp_label=topp_label,
        on_preset_applied=on_preset_applied,
        add_system_message_callback=add_system_message_callback
    )
