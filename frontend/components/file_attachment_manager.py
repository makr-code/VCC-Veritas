"""
FileAttachmentManager - File Attachment Management for VERITAS
==============================================================

Manages file attachments in the chat interface including:
- File upload dialog
- Attachment display (buttons with preview)
- Attachment removal
- File metadata tracking

Part of the VERITAS frontend modularization (Phase 4).

Author: VERITAS Development Team
Created: 2025-10-18
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Optional, Callable
import os
import logging

logger = logging.getLogger(__name__)


class FileAttachmentManager:
    """
    Manages file attachments in the chat interface.
    
    Responsibilities:
    - File upload dialog
    - Attachment display and tracking
    - Attachment removal
    - File validation
    
    Design Pattern: Manager Pattern with UI Components
    """
    
    def __init__(
        self,
        attachments_display: tk.Frame,
        supported_filetypes: Optional[List[tuple]] = None,
        max_file_size_mb: int = 10,
        on_attachment_added: Optional[Callable[[str], None]] = None,
        on_attachment_removed: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the FileAttachmentManager.
        
        Args:
            attachments_display: Frame to display attachment buttons
            supported_filetypes: List of (description, extension) tuples
            max_file_size_mb: Maximum file size in megabytes
            on_attachment_added: Callback when file is added
            on_attachment_removed: Callback when file is removed
        """
        self.attachments_display = attachments_display
        self.max_file_size_mb = max_file_size_mb
        self.on_attachment_added = on_attachment_added
        self.on_attachment_removed = on_attachment_removed
        
        # Default supported file types
        self.supported_filetypes = supported_filetypes or [
            ("PDF-Dateien", "*.pdf"),
            ("Word-Dokumente", "*.docx *.doc"),
            ("Text-Dateien", "*.txt"),
            ("Markdown-Dateien", "*.md"),
            ("Alle Dateien", "*.*")
        ]
        
        # State tracking
        self.uploaded_files: List[str] = []
        self.attachment_buttons: Dict[str, ttk.Button] = {}
        
        logger.info("✅ FileAttachmentManager initialisiert")
    
    def upload_file(self):
        """Open file upload dialog and add attachment"""
        try:
            filename = filedialog.askopenfilename(
                title="Datei für Kontext auswählen",
                filetypes=self.supported_filetypes
            )
            
            if not filename:
                return  # User cancelled
            
            # Validate file
            if not self._validate_file(filename):
                return
            
            # Add to uploaded files
            self.uploaded_files.append(filename)
            
            # Create attachment button
            file_name = os.path.basename(filename)
            self._add_attachment_button(file_name, filename)
            
            # Callback
            if self.on_attachment_added:
                try:
                    self.on_attachment_added(filename)
                except Exception as e:
                    logger.error(f"Fehler beim Attachment-Added-Callback: {e}")
            
            logger.info(f"Datei für Upload ausgewählt: {file_name}")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Datei konnte nicht geladen werden: {e}")
            logger.error(f"Datei-Upload Fehler: {e}")
    
    def _validate_file(self, file_path: str) -> bool:
        """
        Validate file (size, existence).
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                messagebox.showerror("Fehler", "Datei existiert nicht.")
                return False
            
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                messagebox.showerror(
                    "Fehler",
                    f"Datei zu groß ({file_size_mb:.1f} MB).\n"
                    f"Maximum: {self.max_file_size_mb} MB"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Datei-Validierung: {e}")
            messagebox.showerror("Fehler", f"Datei-Validierung fehlgeschlagen: {e}")
            return False
    
    def _add_attachment_button(self, file_name: str, file_path: str):
        """
        Add a button for an attached file.
        
        Args:
            file_name: Display name of the file
            file_path: Full path to the file
        """
        try:
            # Truncate long file names
            display_name = file_name if len(file_name) <= 20 else file_name[:17] + "..."
            
            # Create button
            file_button = ttk.Button(
                self.attachments_display,
                text=f"📄 {display_name} ❌",
                command=lambda: self.remove_attachment(file_path),
                width=25
            )
            file_button.pack(side=tk.LEFT, padx=(0, 5))
            
            # Store button reference
            self.attachment_buttons[file_path] = file_button
            
            logger.debug(f"Attachment-Button erstellt: {display_name}")
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Attachment-Buttons: {e}")
    
    def remove_attachment(self, file_path: str):
        """
        Remove an attached file.
        
        Args:
            file_path: Path to the file to remove
        """
        try:
            # Remove from uploaded files list
            if file_path in self.uploaded_files:
                self.uploaded_files.remove(file_path)
            
            # Destroy button
            if file_path in self.attachment_buttons:
                self.attachment_buttons[file_path].destroy()
                del self.attachment_buttons[file_path]
            
            # Callback
            if self.on_attachment_removed:
                try:
                    self.on_attachment_removed(file_path)
                except Exception as e:
                    logger.error(f"Fehler beim Attachment-Removed-Callback: {e}")
            
            logger.info(f"Datei-Anhang entfernt: {os.path.basename(file_path)}")
            
        except Exception as e:
            logger.error(f"Fehler beim Entfernen des Anhangs: {e}")
    
    def clear_all_attachments(self):
        """Remove all attachments"""
        try:
            # Copy list to avoid modification during iteration
            files_to_remove = list(self.uploaded_files)
            
            for file_path in files_to_remove:
                self.remove_attachment(file_path)
            
            logger.info("Alle Anhänge entfernt")
            
        except Exception as e:
            logger.error(f"Fehler beim Löschen aller Anhänge: {e}")
    
    def get_uploaded_files(self) -> List[str]:
        """Get list of uploaded file paths"""
        return list(self.uploaded_files)
    
    def has_attachments(self) -> bool:
        """Check if there are any attachments"""
        return len(self.uploaded_files) > 0
    
    def get_attachment_count(self) -> int:
        """Get number of attachments"""
        return len(self.uploaded_files)
    
    def get_attachment_metadata(self) -> List[Dict[str, any]]:
        """
        Get metadata for all attachments.
        
        Returns:
            List of dictionaries with file metadata
        """
        metadata = []
        for file_path in self.uploaded_files:
            try:
                metadata.append({
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'size_bytes': os.path.getsize(file_path),
                    'size_mb': os.path.getsize(file_path) / (1024 * 1024),
                    'extension': os.path.splitext(file_path)[1]
                })
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Metadaten für {file_path}: {e}")
        
        return metadata


def create_file_attachment_manager(
    attachments_display: tk.Frame,
    supported_filetypes: Optional[List[tuple]] = None,
    max_file_size_mb: int = 10,
    on_attachment_added: Optional[Callable[[str], None]] = None,
    on_attachment_removed: Optional[Callable[[str], None]] = None
) -> FileAttachmentManager:
    """
    Factory function to create a FileAttachmentManager.
    
    Args:
        attachments_display: Frame to display attachment buttons
        supported_filetypes: List of (description, extension) tuples
        max_file_size_mb: Maximum file size in megabytes
        on_attachment_added: Callback when file is added
        on_attachment_removed: Callback when file is removed
    
    Returns:
        Configured FileAttachmentManager instance
    
    Example:
        >>> file_manager = create_file_attachment_manager(
        ...     attachments_display=self.attachments_frame,
        ...     max_file_size_mb=10,
        ...     on_attachment_added=lambda path: logger.info(f"Added: {path}")
        ... )
    """
    return FileAttachmentManager(
        attachments_display=attachments_display,
        supported_filetypes=supported_filetypes,
        max_file_size_mb=max_file_size_mb,
        on_attachment_added=on_attachment_added,
        on_attachment_removed=on_attachment_removed
    )
