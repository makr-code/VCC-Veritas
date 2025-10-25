"""
Minimales Test-Skript um Tkinter mainloop zu testen
"""
import tkinter as tk
import sys

print("=" * 60)
print("TKINTER MINIMAL TEST")
print("=" * 60)

try:
    print("1. Creating Tk root window...")
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("400x300")
    
    print("2. Adding label...")
    label = tk.Label(root, text="Tkinter Test - Fenster sollte sichtbar bleiben", font=("Arial", 14))
    label.pack(pady=50)
    
    print("3. Adding button...")
    button = tk.Button(root, text="Schließen", command=root.quit)
    button.pack()
    
    print("4. Starting mainloop()...")
    print("   (Fenster sollte jetzt erscheinen und offen bleiben)")
    root.mainloop()
    
    print("5. Mainloop exited (Fenster wurde geschlossen)")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ Test completed")
