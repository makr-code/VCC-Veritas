"""
UDS3 Warnings Suppressor (Optional)
Unterdrückt nicht-kritische UDS3 Import-Warnings
"""

import warnings
import logging

# Unterdrücke UDS3 Warnings
warnings.filterwarnings('ignore', message='.*not available for PolyglotQuery')
warnings.filterwarnings('ignore', message='.*Operations module not available')
warnings.filterwarnings('ignore', message='.*Filter module not available')

# UDS3 Logger auf ERROR setzen (statt WARNING)
logging.getLogger('uds3').setLevel(logging.ERROR)

print("✅ UDS3 Warnings unterdrückt")
