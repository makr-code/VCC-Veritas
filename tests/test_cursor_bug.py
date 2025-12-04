#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test für Cursor-Bug"""

import tkinter as tk

root = tk.Tk()
root.withdraw()

# Test 1: Label mit cursor im Constructor (sollte FEHLEN)
try:
    label1 = tk.Label(root, text="Test 1", cursor="hand2")
    print("✅ Test 1: Label mit cursor im Constructor - FUNKTIONIERT")
except Exception as e:
    print(f"❌ Test 1 FEHLER: {e}")

# Test 2: Label mit cursor via config (sollte funktionieren)
try:
    label2 = tk.Label(root, text="Test 2")
    label2.config(cursor="hand2")
    print("✅ Test 2: Label mit cursor via config - FUNKTIONIERT")
except Exception as e:
    print(f"❌ Test 2 FEHLER: {e}")

# Test 3: Button mit cursor (sollte funktionieren)
try:
    btn = tk.Button(root, text="Test 3", cursor="hand2")
    print("✅ Test 3: Button mit cursor - FUNKTIONIERT")
except Exception as e:
    print(f"❌ Test 3 FEHLER: {e}")

root.destroy()
print("\n=== ALLE TESTS ABGESCHLOSSEN ===")
