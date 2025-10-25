#!/usr/bin/env python3
"""
Token Budget Visualizer - Zeigt Budget-Progression grafisch
============================================================
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Verwaltungsrecht-Beispiel
steps = ['Initial\n(Intent Only)', 'After RAG\n(+12 Chunks)', 'After Agents\n(+5 Agents)']
budgets = [1020, 2886, 4000]
colors = ['#3498db', '#e74c3c', '#2ecc71']

# Figure erstellen
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Dynamic Token Budget System - Verwaltungsrecht-Beispiel', fontsize=16, fontweight='bold')

# Plot 1: Budget Progression
bars = ax1.bar(steps, budgets, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
ax1.set_ylabel('Token Budget', fontsize=12, fontweight='bold')
ax1.set_title('Budget Progression durch Pipeline', fontsize=14)
ax1.set_ylim(0, 4500)
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Werte auf Bars anzeigen
for i, (bar, budget) in enumerate(zip(bars, budgets)):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 100,
             f'{budget:,} tokens',
             ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    if i > 0:
        delta = budget - budgets[i-1]
        ax1.text(bar.get_x() + bar.get_width()/2., height/2,
                 f'+{delta:,}\n(+{(delta/budgets[i-1]*100):.0f}%)',
                 ha='center', va='center', fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Plot 2: Budget Breakdown
categories = ['Base\n600', 'Complexity\n×0.85', 'Chunks\n+600', 'Sources\n×1.30', 'Agents\n×1.75', 'Intent\n×2.0']
contributions = [600, 510, 600, 330, 750, 1210]  # Approximiert für Visualisierung
colors2 = ['#95a5a6', '#3498db', '#e67e22', '#9b59b6', '#e74c3c', '#2ecc71']

wedges, texts, autotexts = ax2.pie(contributions, labels=categories, autopct='%1.0f%%',
                                     colors=colors2, startangle=90,
                                     wedgeprops=dict(edgecolor='white', linewidth=2))

ax2.set_title('Budget Breakdown (Final: 4000 tokens)', fontsize=14)

# Text formatting
for text in texts:
    text.set_fontsize(10)
    text.set_fontweight('bold')

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(9)
    autotext.set_fontweight('bold')

plt.tight_layout()
plt.savefig('c:/VCC/veritas/docs/token_budget_visualization.png', dpi=300, bbox_inches='tight')
print("✅ Visualization saved: docs/token_budget_visualization.png")
plt.show()
