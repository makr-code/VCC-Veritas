#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Module: Drag & Drop Handler
Ermöglicht File-Upload via Drag & Drop in Chat-Fenster
"""

import tkinter as tk
from tkinter import messagebox
import logging
import os
from pathlib import Path
from typing import List, Dict, Callable, Optional
import hashlib
import mimetypes

logger = logging.getLogger(__name__)

# Supported File Types (MIME-Types)
SUPPORTED_DOCUMENTS = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.rtf': 'application/rtf',
    '.odt': 'application/vnd.oasis.opendocument.text'
}

SUPPORTED_IMAGES = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.webp': 'image/webp'
}

SUPPORTED_DATA = {
    '.csv': 'text/csv',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.json': 'application/json',
    '.xml': 'text/xml',
    '.yaml': 'text/yaml',
    '.yml': 'text/yaml'
}

SUPPORTED_CODE = {
    '.py': 'text/x-python',
    '.js': 'text/javascript',
    '.ts': 'text/typescript',
    '.java': 'text/x-java',
    '.cpp': 'text/x-c++src',
    '.c': 'text/x-csrc',
    '.h': 'text/x-chdr',
    '.cs': 'text/x-csharp',
    '.go': 'text/x-go',
    '.rs': 'text/x-rust',
    '.sql': 'application/sql'
}

# Alle unterstützten Formate kombiniert
ALL_SUPPORTED_FORMATS = {
    **SUPPORTED_DOCUMENTS,
    **SUPPORTED_IMAGES,
    **SUPPORTED_DATA,
    **SUPPORTED_CODE
}

# Max File Size (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB in Bytes

# Max Files per Drop
MAX_FILES_PER_DROP = 10


class DragDropHandler:
    """
    Drag & Drop Handler für VERITAS Chat-Fenster
    
    Features:
    - Multi-file support (bis zu 10 Dateien)
    - Visual feedback (gestrichelte Border bei Hover)
    - File validation (Typ, Größe, Duplikate)
    - Progress tracking
    - Upload-Callbacks
    """
    
    def __init__(
        self,
        target_widget: tk.Widget,
        on_files_dropped: Callable[[List[Dict]], None],
        supported_formats: Optional[Dict[str, str]] = None,
        max_file_size: int = MAX_FILE_SIZE,
        max_files: int = MAX_FILES_PER_DROP
    ):
        """
        Initialisiert Drag & Drop Handler
        
        Args:
            target_widget: Tkinter Widget für Drop-Zone
            on_files_dropped: Callback bei erfolgreichen Drop (receives list of file dicts)
            supported_formats: Dict {'.ext': 'mime/type'} (default: ALL_SUPPORTED_FORMATS)
            max_file_size: Max Dateigröße in Bytes (default: 50 MB)
            max_files: Max Dateien pro Drop (default: 10)
        """
        self.target_widget = target_widget
        self.on_files_dropped = on_files_dropped
        self.supported_formats = supported_formats or ALL_SUPPORTED_FORMATS
        self.max_file_size = max_file_size
        self.max_files = max_files
        
        # State
        self._is_hovering = False
        self._uploaded_hashes = set()  # Duplikat-Erkennung
        self._original_border = None  # Original Border-Style
        
        # Setup DND
        self._setup_drag_drop()
        
        logger.info(f"✅ DragDropHandler initialisiert für {target_widget.winfo_class()}")
    
    def _setup_drag_drop(self):
        """Konfiguriert Drag & Drop Events"""
        try:
            # Windows: Tkinter DND2 Support
            self.target_widget.drop_target_register('DND_Files')
            self.target_widget.dnd_bind('<<DropEnter>>', self._on_drop_enter)
            self.target_widget.dnd_bind('<<DropLeave>>', self._on_drop_leave)
            self.target_widget.dnd_bind('<<Drop>>', self._on_drop)
            logger.info("✅ Native DND2 Support aktiviert")
        
        except (AttributeError, tk.TclError):
            # Fallback: Tkinter DND über tkinterdnd2
            try:
                from tkinterdnd2 import DND_FILES, TkinterDnD
                
                # Bind Events
                self.target_widget.drop_target_register(DND_FILES)
                self.target_widget.dnd_bind('<<DropEnter>>', self._on_drop_enter)
                self.target_widget.dnd_bind('<<DropLeave>>', self._on_drop_leave)
                self.target_widget.dnd_bind('<<Drop>>', self._on_drop)
                logger.info("✅ tkinterdnd2 Support aktiviert")
            
            except ImportError:
                # Fallback: Manual Binding (limitiert)
                logger.warning("⚠️ Kein DND-Support - verwende manuelle Bindings")
                self._setup_manual_dnd()
    
    def _setup_manual_dnd(self):
        """Manual DND Setup (limitiert, nur für Development)"""
        # Simpler Hover-Effekt ohne echtes DND
        self.target_widget.bind('<Enter>', self._on_drop_enter)
        self.target_widget.bind('<Leave>', self._on_drop_leave)
        
        # Info-Message
        logger.info("💡 Für volle DND-Unterstützung installiere: pip install tkinterdnd2")
    
    def _on_drop_enter(self, event):
        """Callback: Drag Enter (Hover-Start)"""
        if self._is_hovering:
            return
        
        self._is_hovering = True
        
        # Visual Feedback: Gestrichelte Border
        try:
            self._original_border = {
                'relief': self.target_widget.cget('relief'),
                'borderwidth': self.target_widget.cget('borderwidth'),
                'highlightbackground': self.target_widget.cget('highlightbackground'),
                'highlightthickness': self.target_widget.cget('highlightthickness')
            }
            
            self.target_widget.configure(
                relief='solid',
                borderwidth=2,
                highlightbackground='#4CAF50',  # Grün
                highlightthickness=2
            )
            
            logger.debug("✅ Drag Enter: Visual Feedback aktiviert")
        
        except tk.TclError as e:
            logger.debug(f"⚠️ Konnte Border nicht ändern: {e}")
    
    def _on_drop_leave(self, event):
        """Callback: Drag Leave (Hover-End)"""
        if not self._is_hovering:
            return
        
        self._is_hovering = False
        
        # Visual Feedback zurücksetzen
        if self._original_border:
            try:
                self.target_widget.configure(**self._original_border)
                logger.debug("✅ Drag Leave: Visual Feedback deaktiviert")
            except tk.TclError as e:
                logger.debug(f"⚠️ Konnte Border nicht zurücksetzen: {e}")
    
    def _on_drop(self, event):
        """Callback: Drop (Dateien gedroppt)"""
        # Reset Hover-State
        self._on_drop_leave(event)
        
        # Parse Dateien aus Event
        files = self._parse_drop_event(event)
        
        if not files:
            logger.warning("⚠️ Keine Dateien im Drop-Event gefunden")
            return
        
        logger.info(f"📂 {len(files)} Datei(en) gedroppt: {[f.name for f in files]}")
        
        # Validiere Dateien
        valid_files, errors = self._validate_files(files)
        
        # Zeige Fehler
        if errors:
            error_msg = "\n".join(errors[:5])  # Max 5 Fehler
            if len(errors) > 5:
                error_msg += f"\n... und {len(errors) - 5} weitere Fehler"
            
            messagebox.showwarning(
                "Ungültige Dateien",
                f"Folgende Dateien konnten nicht verarbeitet werden:\n\n{error_msg}"
            )
        
        # Verarbeite gültige Dateien
        if valid_files:
            file_dicts = self._create_file_dicts(valid_files)
            
            # Callback ausführen
            try:
                self.on_files_dropped(file_dicts)
                logger.info(f"✅ {len(valid_files)} Datei(en) erfolgreich verarbeitet")
            
            except Exception as e:
                logger.error(f"❌ Fehler beim Verarbeiten: {e}")
                messagebox.showerror(
                    "Verarbeitungsfehler",
                    f"Fehler beim Verarbeiten der Dateien:\n{str(e)}"
                )
    
    def _parse_drop_event(self, event) -> List[Path]:
        """
        Parsed Dateipfade aus Drop-Event
        
        Args:
            event: Tkinter Event
            
        Returns:
            Liste von Path-Objekten
        """
        files = []
        
        # Try event.data (tkinterdnd2)
        if hasattr(event, 'data'):
            data = event.data
            
            # Parsen: Windows-Format '{C:/path/file.txt} {C:/path/file2.txt}'
            if isinstance(data, str):
                # Split by braces
                import re
                file_paths = re.findall(r'\{([^}]+)\}', data)
                
                if not file_paths:
                    # Fallback: Split by whitespace
                    file_paths = data.split()
                
                for path_str in file_paths:
                    path_str = path_str.strip()
                    if path_str:
                        path = Path(path_str)
                        if path.exists():
                            files.append(path)
        
        # Try event.widget.selection_get() (Fallback)
        elif hasattr(event.widget, 'selection_get'):
            try:
                data = event.widget.selection_get()
                path = Path(data.strip())
                if path.exists():
                    files.append(path)
            except (tk.TclError, OSError):
                pass
        
        return files
    
    def _validate_files(self, files: List[Path]) -> tuple[List[Path], List[str]]:
        """
        Validiert Dateien
        
        Args:
            files: Liste von Path-Objekten
            
        Returns:
            (valid_files, error_messages)
        """
        valid_files = []
        errors = []
        
        # Max Files Check
        if len(files) > self.max_files:
            errors.append(f"⚠️ Zu viele Dateien ({len(files)}). Maximum: {self.max_files}")
            files = files[:self.max_files]
        
        for file_path in files:
            # Existenz-Check
            if not file_path.exists():
                errors.append(f"❌ {file_path.name}: Datei nicht gefunden")
                continue
            
            # Datei-Check (keine Ordner)
            if file_path.is_dir():
                errors.append(f"❌ {file_path.name}: Ordner werden nicht unterstützt")
                continue
            
            # Extension-Check
            extension = file_path.suffix.lower()
            if extension not in self.supported_formats:
                supported_exts = ', '.join(sorted(self.supported_formats.keys()))
                errors.append(f"❌ {file_path.name}: Nicht unterstützt. Erlaubt: {supported_exts}")
                continue
            
            # Size-Check
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                actual_mb = file_size / (1024 * 1024)
                errors.append(f"❌ {file_path.name}: Zu groß ({actual_mb:.1f} MB). Maximum: {max_mb:.0f} MB")
                continue
            
            # Duplikat-Check (Hash-basiert)
            file_hash = self._compute_file_hash(file_path)
            if file_hash in self._uploaded_hashes:
                errors.append(f"⚠️ {file_path.name}: Wurde bereits hochgeladen (Duplikat)")
                continue
            
            # Valid!
            valid_files.append(file_path)
            self._uploaded_hashes.add(file_hash)
        
        return valid_files, errors
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Berechnet SHA256-Hash einer Datei
        
        Args:
            file_path: Path zur Datei
            
        Returns:
            Hex-String des Hashes
        """
        hasher = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks (1 MB)
                for chunk in iter(lambda: f.read(1024 * 1024), b''):
                    hasher.update(chunk)
            
            return hasher.hexdigest()
        
        except Exception as e:
            logger.warning(f"⚠️ Konnte Hash nicht berechnen für {file_path.name}: {e}")
            # Fallback: Verwende Dateigröße + Name
            return f"{file_path.stat().st_size}_{file_path.name}"
    
    def _create_file_dicts(self, files: List[Path]) -> List[Dict]:
        """
        Erstellt File-Dictionaries für Callback
        
        Args:
            files: Liste von Path-Objekten
            
        Returns:
            Liste von Dicts mit {name, size, path, mime_type, extension}
        """
        file_dicts = []
        
        for file_path in files:
            file_size = file_path.stat().st_size
            extension = file_path.suffix.lower()
            mime_type = self.supported_formats.get(extension, 'application/octet-stream')
            
            file_dict = {
                'name': file_path.name,
                'size': file_size,
                'size_mb': file_size / (1024 * 1024),
                'path': str(file_path.absolute()),
                'mime_type': mime_type,
                'extension': extension,
                'hash': self._compute_file_hash(file_path)
            }
            
            file_dicts.append(file_dict)
        
        return file_dicts
    
    def reset_uploaded_hashes(self):
        """Reset Duplikat-Tracking (für neue Session)"""
        self._uploaded_hashes.clear()
        logger.info("✅ Uploaded Hashes zurückgesetzt")
    
    def get_supported_formats_list(self) -> List[str]:
        """Returns Liste aller unterstützten Dateiformate"""
        return sorted(self.supported_formats.keys())
    
    def get_supported_formats_string(self) -> str:
        """Returns String aller unterstützten Formate (für UI-Anzeige)"""
        docs = ', '.join(sorted(SUPPORTED_DOCUMENTS.keys()))
        images = ', '.join(sorted(SUPPORTED_IMAGES.keys()))
        data = ', '.join(sorted(SUPPORTED_DATA.keys()))
        code = ', '.join(sorted(SUPPORTED_CODE.keys()))
        
        return f"""
Unterstützte Formate:
• Dokumente: {docs}
• Bilder: {images}
• Daten: {data}
• Code: {code}
""".strip()
