#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS UI Icons Module
Zentrales Icon-Management für konsistente Emoji-Icons im Frontend
"""

import logging
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class IconCategory(Enum):
    """Icon-Kategorien für bessere Organisation"""

    CHAT = "chat"
    SOURCES = "sources"
    METADATA = "metadata"
    AGENTS = "agents"
    ACTIONS = "actions"
    STATUS = "status"
    FILES = "files"
    NAVIGATION = "navigation"


class VeritasIcons:
    """
    Zentrale Icon-Verwaltung für VERITAS Frontend

    Features:
    - Konsistente Emoji-Icons über alle UI-Komponenten
    - Kategorisierte Icon-Struktur
    - Fallback-Icons für fehlende Kategorien
    - Theme-Support (Hell/Dunkel)
    """

    # === CHAT ICONS ===
    CHAT_ICONS = {
        "user": "👤",
        "assistant": "🤖",
        "system": "ℹ️",
        "error": "❌",
        "warning": "⚠️",
        "success": "✅",
        "thinking": "💭",
        "typing": "✍️",
    }

    # === SOURCE ICONS ===
    SOURCE_ICONS = {
        "sources": "📚",
        "document": "📄",
        "pdf": "📕",
        "web": "🌐",
        "database": "💾",
        "file": "📁",
        "link": "🔗",
        "search": "🔍",
        "reference": "📖",
    }

    # === METADATA ICONS ===
    METADATA_ICONS = {
        "confidence": "🎯",
        "count": "🔢",
        "duration": "⏱️",
        "timestamp": "🕐",
        "version": "🔖",
        "tag": "🏷️",
        "category": "📂",
        "priority": "⭐",
    }

    # === AGENT ICONS ===
    AGENT_ICONS = {
        "agents": "🤖",
        "orchestrator": "🎭",
        "worker": "⚙️",
        "analyzer": "🔬",
        "processor": "⚡",
        "validator": "✓",
        "summarizer": "📝",
    }

    # === ACTION ICONS ===
    ACTION_ICONS = {
        "send": "📤",
        "receive": "📥",
        "upload": "📤",
        "download": "📥",
        "copy": "📋",
        "paste": "📄",
        "delete": "🗑️",
        "edit": "✏️",
        "save": "💾",
        "load": "📂",
        "refresh": "🔄",
        "settings": "⚙️",
        "info": "ℹ️",
        "close": "❌",
        "new": "➕",
        "menu": "☰",
    }

    # === STATUS ICONS ===
    STATUS_ICONS = {
        "ready": "🟢",
        "busy": "🟡",
        "error": "🔴",
        "offline": "⚫",
        "loading": "⏳",
        "complete": "✅",
        "pending": "⏸️",
        "running": "▶️",
    }

    # === FILE TYPE ICONS ===
    FILE_ICONS = {
        # Documents
        "pdf": "📕",
        "docx": "📘",
        "doc": "📘",
        "txt": "📄",
        "md": "📝",
        "rtf": "📃",
        # Web & Markup
        "html": "🌐",
        "htm": "🌐",
        "xml": "📋",
        # ✨ Feature #13: Erweiterte Data-Formate
        "json": "📊",
        "yaml": "📊",
        "yml": "�",
        "csv": "📈",
        "tsv": "📈",
        "xls": "📊",
        "xlsx": "📊",
        "sql": "🗄️",
        "db": "🗄️",
        "sqlite": "🗄️",
        # ✨ Feature #13: Code-Dateien
        "py": "🐍",
        "js": "📜",
        "ts": "📜",
        "java": "☕",
        "cpp": "⚙️",
        "c": "⚙️",
        "cs": "🔷",
        "php": "🐘",
        "rb": "💎",
        "go": "🐹",
        "rs": "🦀",
        # ✨ Feature #13: Media-Dateien
        "image": "🖼️",
        "jpg": "🖼️",
        "jpeg": "🖼️",
        "png": "🖼️",
        "gif": "🖼️",
        "svg": "🎨",
        "bmp": "🖼️",
        "webp": "🖼️",
        "video": "🎬",
        "mp4": "🎬",
        "avi": "🎬",
        "mkv": "🎬",
        "mov": "🎬",
        "wmv": "🎬",
        "flv": "🎬",
        "webm": "�",
        "audio": "🎵",
        "mp3": "🎵",
        "wav": "🎵",
        "flac": "🎵",
        "aac": "🎵",
        "ogg": "🎵",
        "m4a": "🎵",
        "wma": "🎵",
        # ✨ Feature #13: Archive-Formate
        "zip": "📦",
        "rar": "📦",
        "tar": "📦",
        "gz": "📦",
        "7z": "📦",
        "bz2": "📦",
        # Default
        "unknown": "📄",
    }

    # === NAVIGATION ICONS ===
    NAVIGATION_ICONS = {
        "home": "🏠",
        "back": "◀️",
        "forward": "▶️",
        "up": "⬆️",
        "down": "⬇️",
        "expand": "🔽",
        "collapse": "🔼",
        "next": "➡️",
        "previous": "⬅️",
    }

    # === CONFIDENCE LEVEL ICONS ===
    CONFIDENCE_ICONS = {
        "high": "🟢",  # > 0.8
        "medium": "🟡",  # 0.5 - 0.8
        "low": "🔴",  # < 0.5
        "unknown": "⚪",
    }

    # === SPECIAL ICONS ===
    SPECIAL_ICONS = {
        "veritas": "💬",
        "rag": "🔍",
        "vpb": "📊",
        "suggestion": "💡",
        "feedback": "👍",
        "quote": "💬",
        "code": "💻",
        "list": "📋",
        "bullet": "•",
        "checkmark": "✓",
        "cross": "✗",
    }

    @classmethod
    def get(cls, category: str, name: str, fallback: str = "•") -> str:
        """
        Holt Icon aus Kategorie

        Args:
            category: Icon-Kategorie (chat, sources, metadata, etc.)
            name: Icon-Name innerhalb der Kategorie
            fallback: Fallback-Icon wenn nicht gefunden

        Returns:
            Emoji-Icon String

        Example:
            >>> VeritasIcons.get('chat', 'user')
            '👤'
            >>> VeritasIcons.get('sources', 'pdf')
            '📕'
        """
        category_map = {
            "chat": cls.CHAT_ICONS,
            "sources": cls.SOURCE_ICONS,
            "metadata": cls.METADATA_ICONS,
            "agents": cls.AGENT_ICONS,
            "actions": cls.ACTION_ICONS,
            "status": cls.STATUS_ICONS,
            "files": cls.FILE_ICONS,
            "navigation": cls.NAVIGATION_ICONS,
            "confidence": cls.CONFIDENCE_ICONS,
            "special": cls.SPECIAL_ICONS,
        }

        category_dict = category_map.get(category.lower())
        if not category_dict:
            logger.debug(f"Unbekannte Icon-Kategorie: {category}")
            return fallback

        return category_dict.get(name.lower(), fallback)

    @classmethod
    def chat(cls, name: str, fallback: str = "💬") -> str:
        """Shortcut für Chat-Icons"""
        return cls.get("chat", name, fallback)

    @classmethod
    def source(cls, name: str, fallback: str = "📄") -> str:
        """Shortcut für Source-Icons"""
        return cls.get("sources", name, fallback)

    @classmethod
    def metadata(cls, name: str, fallback: str = "🏷️") -> str:
        """Shortcut für Metadata-Icons"""
        return cls.get("metadata", name, fallback)

    @classmethod
    def agent(cls, name: str, fallback: str = "🤖") -> str:
        """Shortcut für Agent-Icons"""
        return cls.get("agents", name, fallback)

    @classmethod
    def action(cls, name: str, fallback: str = "⚙️") -> str:
        """Shortcut für Action-Icons"""
        return cls.get("actions", name, fallback)

    @classmethod
    def status(cls, name: str, fallback: str = "⚪") -> str:
        """Shortcut für Status-Icons"""
        return cls.get("status", name, fallback)

    @classmethod
    def file(cls, extension: str, fallback: str = "📄") -> str:
        """
        Holt Icon basierend auf Datei-Extension

        Args:
            extension: Datei-Endung (mit oder ohne Punkt)
            fallback: Fallback-Icon

        Returns:
            Datei-Typ-Icon

        Example:
            >>> VeritasIcons.file('.pdf')
            '📕'
            >>> VeritasIcons.file('docx')
            '📘'
        """
        # Entferne Punkt falls vorhanden
        ext = extension.lower().lstrip(".")
        return cls.get("files", ext, fallback)

    @classmethod
    def confidence(cls, score: float) -> str:
        """
        Holt Icon basierend auf Confidence-Score

        Args:
            score: Confidence-Score (0.0 - 1.0)

        Returns:
            Confidence-Icon (🟢/🟡/🔴)

        Example:
            >>> VeritasIcons.confidence(0.9)
            '🟢'
            >>> VeritasIcons.confidence(0.6)
            '🟡'
        """
        if score >= 0.8:
            return cls.CONFIDENCE_ICONS["high"]
        elif score >= 0.5:
            return cls.CONFIDENCE_ICONS["medium"]
        else:
            return cls.CONFIDENCE_ICONS["low"]

    @classmethod
    def get_all_icons(cls) -> Dict[str, Dict[str, str]]:
        """
        Gibt alle verfügbaren Icons als Dictionary zurück

        Returns:
            Dict mit allen Icon-Kategorien und ihren Icons
        """
        return {
            "chat": cls.CHAT_ICONS,
            "sources": cls.SOURCE_ICONS,
            "metadata": cls.METADATA_ICONS,
            "agents": cls.AGENT_ICONS,
            "actions": cls.ACTION_ICONS,
            "status": cls.STATUS_ICONS,
            "files": cls.FILE_ICONS,
            "navigation": cls.NAVIGATION_ICONS,
            "confidence": cls.CONFIDENCE_ICONS,
            "special": cls.SPECIAL_ICONS,
        }

    @classmethod
    def get_category_icons(cls, category: str) -> Dict[str, str]:
        """
        Gibt alle Icons einer Kategorie zurück

        Args:
            category: Kategorie-Name

        Returns:
            Dict mit Icon-Namen und Emojis
        """
        all_icons = cls.get_all_icons()
        return all_icons.get(category.lower(), {})


# === ICON UTILITIES ===


def format_with_icon(text: str, icon_category: str, icon_name: str, spacing: int = 1) -> str:
    """
    Formatiert Text mit Icon

    Args:
        text: Text-Inhalt
        icon_category: Icon-Kategorie
        icon_name: Icon-Name
        spacing: Anzahl Leerzeichen zwischen Icon und Text

    Returns:
        Formatierter String "Icon Text"

    Example:
        >>> format_with_icon("Verwendete Quellen:", "sources", "sources")
        '📚 Verwendete Quellen:'
    """
    icon = VeritasIcons.get(icon_category, icon_name)
    space = " " * spacing
    return f"{icon}{space}{text}"


def get_file_icon(filename: str) -> str:
    """
    Ermittelt Icon basierend auf Dateinamen

    Args:
        filename: Dateiname (mit Extension)

    Returns:
        Datei-Icon

    Example:
        >>> get_file_icon("document.pdf")
        '📕'
        >>> get_file_icon("readme.md")
        '📝'
    """
    import os

    _, ext = os.path.splitext(filename)
    return VeritasIcons.file(ext)


def get_source_icon(source_text: str) -> str:
    """
    Ermittelt Icon basierend auf Quellen-Text

    Args:
        source_text: Quellen-String (URL, Dateiname, etc.)

    Returns:
        Source-Icon

    Example:
        >>> get_source_icon("https://example.com")
        '🌐'
        >>> get_source_icon("document.pdf")
        '📕'
    """
    source_lower = source_text.lower()

    # Web-URLs
    if source_lower.startswith(("http://", "https://", "www.")):
        return VeritasIcons.source("web")

    # Datei-Extensions
    if ".pdf" in source_lower:
        return VeritasIcons.source("pdf")
    elif any(ext in source_lower for ext in [".doc", ".docx"]):
        return VeritasIcons.file("docx")
    elif ".txt" in source_lower:
        return VeritasIcons.file("txt")
    elif ".md" in source_lower:
        return VeritasIcons.file("md")

    # Datenbank-Quellen
    elif "database" in source_lower or "db" in source_lower:
        return VeritasIcons.source("database")

    # Default: Dokument
    else:
        return VeritasIcons.source("document")


# === ICON TESTING ===

if __name__ == "__main__":
    """Test-Suite für Icon-System"""

    print("=== VERITAS Icon System Test ===\n")

    # Test alle Kategorien
    print("📋 Verfügbare Icon-Kategorien:")
    all_icons = VeritasIcons.get_all_icons()
    for category, icons in all_icons.items():
        print(f"\n{category.upper()} ({len(icons)} Icons):")
        for name, icon in list(icons.items())[:5]:  # Zeige erste 5
            print(f"  {icon} {name}")
        if len(icons) > 5:
            print(f"  ... und {len(icons) - 5} weitere")

    # Test Shortcuts
    print("\n\n🎯 Shortcut Tests:")
    print(f"Chat User: {VeritasIcons.chat('user')}")
    print(f"Source PDF: {VeritasIcons.source('pdf')}")
    print(f"Metadata Confidence: {VeritasIcons.metadata('confidence')}")
    print(f"Action Save: {VeritasIcons.action('save')}")

    # Test Confidence Levels
    print("\n\n🎯 Confidence-Score Tests:")
    for score in [0.95, 0.75, 0.45, 0.2]:
        icon = VeritasIcons.confidence(score)
        print(f"Score {score:.2f}: {icon}")

    # Test File Icons
    print("\n\n📁 File Icon Tests:")
    test_files = ["document.pdf", "report.docx", "notes.txt", "readme.md", "data.json"]
    for filename in test_files:
        icon = get_file_icon(filename)
        print(f"{icon} {filename}")

    # Test Source Icons
    print("\n\n🔗 Source Icon Tests:")
    test_sources = ["https://example.com/page", "document.pdf", "database_entry_123", "report.docx", "unknown_source"]
    for source in test_sources:
        icon = get_source_icon(source)
        print(f"{icon} {source}")

    # Test Formatierung
    print("\n\n✨ Format Tests:")
    print(format_with_icon("Verwendete Quellen:", "sources", "sources"))
    print(format_with_icon("Agent-Analysen:", "agents", "agents"))
    print(format_with_icon("Metadaten:", "metadata", "tag"))

    print("\n\n✅ Icon System Tests abgeschlossen!")
