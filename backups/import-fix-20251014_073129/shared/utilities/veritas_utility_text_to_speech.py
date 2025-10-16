"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "veritas_utility_text_to_speech"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...9tK+Wg=="  # Gekuerzt fuer Sicherheit
module_organization_key = "5b17b22ef9076bfe3f13ed8ab5ceb46341bc72b77c40ff86afa037f6acdb3da8"
module_file_key = "55c5fbe1e1415b34fbaf0be6f88fef32e4879b3ffa5bd09bdbf6a709696976c6"
module_version = "1.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
"""
Text-to-Speech Modul für Veritas Chat
Bietet eine einfache Schnittstelle für die Sprachausgabe von KI-Antworten.
"""

import pyttsx3
import threading
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TextToSpeechManager:
    """
    Verwaltet Text-to-Speech Funktionalität für die Veritas Chat-Anwendung.
    Verwendet pyttsx3 für plattformübergreifende TTS-Unterstützung.
    """
    
    def __init__(self):
        self.engine: Optional[pyttsx3.Engine] = None
        self.is_speaking = False
        self.is_available = False
        self._initialize_engine()
    
    def _initialize_engine(self):
        """
        Initialisiert die TTS-Engine.
        """
        try:
            self.engine = pyttsx3.init()
            self.is_available = True
            
            # Standardeinstellungen
            self._set_default_properties()
            
            logger.info("Text-to-Speech Engine erfolgreich initialisiert")
            
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren der TTS-Engine: {e}")
            self.is_available = False
    
    def _set_default_properties(self):
        """
        Setzt Standardeigenschaften für die TTS-Engine.
        """
        if not self.engine:
            return
            
        try:
            # Geschwindigkeit (Wörter pro Minute)
            self.engine.setProperty('rate', 180)
            
            # Lautstärke (0.0 bis 1.0)
            self.engine.setProperty('volume', 0.8)
            
            # Versuche deutsche Stimme zu finden
            voices = self.engine.getProperty('voices')
            german_voice = None
            
            for voice in voices:
                if 'german' in voice.name.lower() or 'deutsch' in voice.name.lower():
                    german_voice = voice.id
                    break
                elif 'de' in voice.id.lower():
                    german_voice = voice.id
                    break
            
            if german_voice:
                self.engine.setProperty('voice', german_voice)
                logger.info(f"Deutsche Stimme gefunden und gesetzt: {german_voice}")
            else:
                logger.info("Keine deutsche Stimme gefunden, verwende Standardstimme")
                
        except Exception as e:
            logger.warning(f"Fehler beim Setzen der TTS-Eigenschaften: {e}")
    
    def speak_text(self, text: str, interrupt_current: bool = True) -> bool:
        """
        Spricht den gegebenen Text aus.
        
        Args:
            text: Der zu sprechende Text
            interrupt_current: Ob aktuelle Sprachausgabe unterbrochen werden soll
            
        Returns:
            bool: True wenn erfolgreich gestartet, False bei Fehler
        """
        if not self.is_available or not self.engine:
            logger.warning("TTS-Engine nicht verfügbar")
            return False
        
        if not text or not text.strip():
            logger.warning("Leerer Text für TTS übergeben")
            return False
        
        try:
            # Aktuell laufende Sprachausgabe stoppen
            if interrupt_current and self.is_speaking:
                self.stop_speaking()
            
            # Text bereinigen für bessere Aussprache
            cleaned_text = self._clean_text_for_speech(text)
            
            # Sprachausgabe in separatem Thread starten
            speech_thread = threading.Thread(
                target=self._speak_in_thread,
                args=(cleaned_text,),
                daemon=True
            )
            speech_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Starten der Sprachausgabe: {e}")
            return False
    
    def _speak_in_thread(self, text: str):
        """
        Führt die Sprachausgabe in einem separaten Thread aus.
        
        Args:
            text: Der zu sprechende Text
        """
        try:
            self.is_speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
            
        except Exception as e:
            logger.error(f"Fehler während der Sprachausgabe: {e}")
            
        finally:
            self.is_speaking = False
    
    def stop_speaking(self):
        """
        Stoppt die aktuelle Sprachausgabe.
        """
        if not self.engine:
            return
            
        try:
            self.engine.stop()
            self.is_speaking = False
            logger.debug("Sprachausgabe gestoppt")
            
        except Exception as e:
            logger.error(f"Fehler beim Stoppen der Sprachausgabe: {e}")
    
    def _clean_text_for_speech(self, text: str) -> str:
        """
        Bereinigt Text für bessere TTS-Aussprache.
        
        Args:
            text: Ursprünglicher Text
            
        Returns:
            str: Bereinigter Text
        """
        # Entferne Markdown-Formatierung
        import re
        
        # Entferne Code-Blöcke
        text = re.sub(r'```[\s\S]*?```', '[Code-Block]', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Entferne Markdown-Links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Entferne Markdown-Formatierung
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'_{2}(.*?)_{2}', r'\1', text)  # Underline
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
        
        # Entferne überschüssige Leerzeichen und Zeilenumbrüche
        text = re.sub(r'\n+', '. ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Kürze sehr lange Texte
        max_length = 1000  # Maximale Zeichenanzahl
        if len(text) > max_length:
            text = text[:max_length] + "... [Text gekürzt]"
        
        return text.strip()
    
    def get_available_voices(self) -> list:
        """
        Gibt eine Liste verfügbarer Stimmen zurück.
        
        Returns:
            list: Liste der verfügbaren Stimmen
        """
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'age': getattr(voice, 'age', 'Unknown'),
                    'gender': getattr(voice, 'gender', 'Unknown'),
                    'languages': getattr(voice, 'languages', ['Unknown'])
                }
                voice_list.append(voice_info)
            
            return voice_list
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Stimmen: {e}")
            return []
    
    def set_voice_properties(self, rate: Optional[int] = None, 
                           volume: Optional[float] = None,
                           voice_id: Optional[str] = None) -> bool:
        """
        Setzt TTS-Eigenschaften.
        
        Args:
            rate: Sprechgeschwindigkeit (100-300 WPM)
            volume: Lautstärke (0.0-1.0)
            voice_id: ID der zu verwendenden Stimme
            
        Returns:
            bool: True wenn erfolgreich gesetzt
        """
        if not self.engine:
            return False
        
        try:
            if rate is not None:
                # Validiere und setze Geschwindigkeit
                rate = max(100, min(300, rate))
                self.engine.setProperty('rate', rate)
            
            if volume is not None:
                # Validiere und setze Lautstärke
                volume = max(0.0, min(1.0, volume))
                self.engine.setProperty('volume', volume)
            
            if voice_id is not None:
                # Prüfe ob Stimme existiert
                voices = self.engine.getProperty('voices')
                voice_exists = any(voice.id == voice_id for voice in voices)
                
                if voice_exists:
                    self.engine.setProperty('voice', voice_id)
                else:
                    logger.warning(f"Stimme mit ID '{voice_id}' nicht gefunden")
                    return False
            
            logger.info("TTS-Eigenschaften erfolgreich aktualisiert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Setzen der TTS-Eigenschaften: {e}")
            return False
    
    def get_current_properties(self) -> Dict[str, Any]:
        """
        Gibt aktuelle TTS-Eigenschaften zurück.
        
        Returns:
            dict: Aktuelle Eigenschaften
        """
        if not self.engine:
            return {}
        
        try:
            properties = {
                'rate': self.engine.getProperty('rate'),
                'volume': self.engine.getProperty('volume'),
                'voice': self.engine.getProperty('voice'),
                'is_speaking': self.is_speaking,
                'is_available': self.is_available
            }
            return properties
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der TTS-Eigenschaften: {e}")
            return {}

# Globale TTS-Manager-Instanz
_tts_manager = None

def get_tts_manager() -> TextToSpeechManager:
    """
    Gibt die globale TTS-Manager-Instanz zurück (Singleton).
    
    Returns:
        TextToSpeechManager: Die TTS-Manager-Instanz
    """
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TextToSpeechManager()
    return _tts_manager

# Convenience-Funktionen
def speak_text(text: str, interrupt_current: bool = True) -> bool:
    """
    Convenience-Funktion für Sprachausgabe.
    
    Args:
        text: Der zu sprechende Text
        interrupt_current: Ob aktuelle Sprachausgabe unterbrochen werden soll
        
    Returns:
        bool: True wenn erfolgreich gestartet
    """
    return get_tts_manager().speak_text(text, interrupt_current)

def stop_speech():
    """
    Convenience-Funktion zum Stoppen der Sprachausgabe.
    """
    get_tts_manager().stop_speaking()

def is_tts_available() -> bool:
    """
    Prüft ob TTS verfügbar ist.
    
    Returns:
        bool: True wenn TTS verfügbar
    """
    return get_tts_manager().is_available
