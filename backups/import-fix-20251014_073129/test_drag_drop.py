#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Drag & Drop Test Suite
Visual test for file drop functionality
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from pathlib import Path

# Add project root to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Import DragDropHandler
from frontend.ui.veritas_ui_drag_drop import DragDropHandler

class DragDropTestApp:
    """Test application for Drag & Drop"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VERITAS Drag & Drop Test")
        self.root.geometry("800x600")
        
        # Dropped files list
        self.dropped_files = []
        
        # Setup UI
        self._setup_ui()
        
        # Setup Drag & Drop
        self._setup_drag_drop()
    
    def _setup_ui(self):
        """Setup test UI"""
        # Title
        title = tk.Label(
            self.root,
            text="🖱️ VERITAS Drag & Drop Test",
            font=('Segoe UI', 16, 'bold'),
            pady=10
        )
        title.pack()
        
        # Instructions
        instructions = tk.Label(
            self.root,
            text="📂 Drag & Drop Dateien hier her (max 10, max 50 MB pro Datei)",
            font=('Segoe UI', 10),
            fg='#666'
        )
        instructions.pack()
        
        # Drop Zone (Text Widget)
        drop_frame = tk.Frame(self.root, relief='sunken', bd=2)
        drop_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.drop_zone = tk.Text(
            drop_frame,
            font=('Consolas', 10),
            bg='#F5F5F5',
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.drop_zone.pack(fill=tk.BOTH, expand=True)
        
        # Initial message
        self.drop_zone.insert('1.0', """
📋 Drop Zone bereit!

Unterstützte Formate:
• Dokumente: .pdf, .docx, .doc, .txt, .md, .rtf, .odt
• Bilder: .png, .jpg, .jpeg, .gif, .bmp, .webp
• Daten: .csv, .xlsx, .xls, .json, .xml, .yaml, .yml
• Code: .py, .js, .ts, .java, .cpp, .c, .h, .cs, .go, .rs, .sql

Validierung:
✅ Max 10 Dateien gleichzeitig
✅ Max 50 MB pro Datei
✅ Duplikat-Erkennung (SHA256)
✅ Automatische Typ-Prüfung

Drag & Drop aktiviert - Warte auf Dateien...
""".strip())
        
        self.drop_zone.config(state='disabled')  # Read-only
        
        # Info Panel
        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.info_label = tk.Label(
            self.info_frame,
            text="Keine Dateien gedroppt",
            font=('Segoe UI', 9),
            fg='#666',
            anchor='w'
        )
        self.info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Clear Button
        self.clear_btn = tk.Button(
            self.info_frame,
            text="❌ Clear",
            command=self._clear_files,
            font=('Segoe UI', 9)
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # Show Formats Button
        self.formats_btn = tk.Button(
            self.info_frame,
            text="📋 Zeige alle Formate",
            command=self._show_formats,
            font=('Segoe UI', 9)
        )
        self.formats_btn.pack(side=tk.RIGHT, padx=5)
    
    def _setup_drag_drop(self):
        """Setup Drag & Drop Handler"""
        try:
            self.dnd_handler = DragDropHandler(
                target_widget=self.drop_zone,
                on_files_dropped=self._on_files_dropped
            )
            print("✅ DragDropHandler erfolgreich initialisiert")
        except Exception as e:
            print(f"❌ Fehler beim Setup: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_files_dropped(self, files):
        """Callback: Files wurden gedroppt"""
        print(f"\n📂 {len(files)} Datei(en) gedroppt:")
        
        # Add to list
        self.dropped_files.extend(files)
        
        # Update display
        self._update_display(files)
        
        # Update info
        total_count = len(self.dropped_files)
        total_mb = sum(f['size_mb'] for f in self.dropped_files)
        self.info_label.config(
            text=f"✅ {total_count} Datei(en) ({total_mb:.2f} MB total)"
        )
    
    def _update_display(self, new_files):
        """Update drop zone with file info"""
        self.drop_zone.config(state='normal')
        
        # Add separator
        self.drop_zone.insert(tk.END, "\n" + "="*60 + "\n")
        self.drop_zone.insert(tk.END, f"📦 Drop #{len(self.dropped_files) // len(new_files)}\n")
        self.drop_zone.insert(tk.END, "="*60 + "\n\n")
        
        # Add files
        for i, file in enumerate(new_files, 1):
            # File header
            self.drop_zone.insert(
                tk.END,
                f"📎 Datei {i}/{len(new_files)}: {file['name']}\n",
                'file_header'
            )
            
            # Details
            self.drop_zone.insert(
                tk.END,
                f"   📏 Größe: {file['size_mb']:.2f} MB ({file['size']:,} Bytes)\n"
            )
            self.drop_zone.insert(
                tk.END,
                f"   📄 Typ: {file['mime_type']}\n"
            )
            self.drop_zone.insert(
                tk.END,
                f"   🔗 Pfad: {file['path']}\n"
            )
            self.drop_zone.insert(
                tk.END,
                f"   🔐 Hash: {file['hash'][:16]}...\n"
            )
            self.drop_zone.insert(tk.END, "\n")
            
            # Print to console
            print(f"  {i}. {file['name']} ({file['size_mb']:.2f} MB)")
        
        self.drop_zone.config(state='disabled')
        
        # Scroll to bottom
        self.drop_zone.see(tk.END)
    
    def _clear_files(self):
        """Clear dropped files"""
        self.dropped_files.clear()
        self.dnd_handler.reset_uploaded_hashes()
        
        # Clear display
        self.drop_zone.config(state='normal')
        self.drop_zone.delete('1.0', tk.END)
        self.drop_zone.insert('1.0', "✅ Cleared! Warte auf neue Dateien...\n")
        self.drop_zone.config(state='disabled')
        
        # Reset info
        self.info_label.config(text="Keine Dateien gedroppt")
        
        print("\n🗑️ Dropped files cleared")
    
    def _show_formats(self):
        """Show all supported formats"""
        formats_str = self.dnd_handler.get_supported_formats_string()
        
        # Show in popup
        popup = tk.Toplevel(self.root)
        popup.title("Unterstützte Formate")
        popup.geometry("500x400")
        
        text = tk.Text(popup, font=('Consolas', 9), wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert('1.0', formats_str)
        text.config(state='disabled')
        
        close_btn = tk.Button(
            popup,
            text="Schließen",
            command=popup.destroy,
            font=('Segoe UI', 9)
        )
        close_btn.pack(pady=5)
    
    def run(self):
        """Run test app"""
        print("\n" + "="*60)
        print("🧪 VERITAS Drag & Drop Test Suite")
        print("="*60)
        print("\n📋 Instruktionen:")
        print("1. Drag & Drop Dateien in das Text-Widget")
        print("2. Beobachte grüne Border beim Hover")
        print("3. Check validierte Dateien in der Liste")
        print("4. Test verschiedene Formate und Szenarien:")
        print("   - Single file")
        print("   - Multiple files (max 10)")
        print("   - Large file (>50 MB) → sollte rejected werden")
        print("   - Unsupported format (.exe) → sollte rejected werden")
        print("   - Duplicate file → sollte rejected werden")
        print("\n✅ Test-App läuft - Fenster öffnet sich...")
        print("="*60 + "\n")
        
        self.root.mainloop()

if __name__ == "__main__":
    app = DragDropTestApp()
    app.run()
