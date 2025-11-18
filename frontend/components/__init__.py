#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Frontend Components Package
Wiederverwendbare UI-Komponenten

Components:
- ErrorHandler: Error display and retry management
- InputManager: Input field management with placeholders
- ScrollManager: Scroll behavior and scroll-to-top button
- FileAttachmentManager: File upload and attachment management
- SettingsManager: LLM parameter presets and settings
"""

from .answer_toolbar import AnswerToolbar, create_answer_toolbar
from .error_handler import ErrorData, ErrorHandler, ErrorType, create_error_handler
from .file_attachment_manager import FileAttachmentManager, create_file_attachment_manager
from .input_manager import InputManager, create_input_manager
from .scroll_manager import ScrollManager, create_scroll_manager
from .settings_manager import SettingsManager, create_settings_manager
from .typing_indicator import TypingIndicator, create_typing_indicator

__all__ = [
    "ErrorHandler",
    "ErrorType",
    "ErrorData",
    "create_error_handler",
    "InputManager",
    "create_input_manager",
    "ScrollManager",
    "create_scroll_manager",
    "FileAttachmentManager",
    "create_file_attachment_manager",
    "SettingsManager",
    "create_settings_manager",
    "TypingIndicator",
    "create_typing_indicator",
    "AnswerToolbar",
    "create_answer_toolbar",
]
