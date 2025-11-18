"""
Explicit package marker for `shared` to avoid duplicate-module detection by mypy

Adding this file makes `shared` a regular package (not a namespace package)
which helps static tools map file paths consistently to module names.

This file is intentionally empty (keeps runtime semantics unchanged).
"""
