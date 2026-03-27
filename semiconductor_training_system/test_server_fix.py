#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Start the game server with fixed HTML"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from interface.first_person_interface import _start_server, _write_viewer_html, _STATIC

print("[Starting] Regenerating HTML with fixes...")
_write_viewer_html(_STATIC)
print("[OK] HTML regenerated")

print("[Starting] Server startup...")
try:
    port = _start_server(str(_STATIC))
    print(f"[OK] Server running at http://127.0.0.1:{port}/")
    print()
    print("Open browser and test the loading bar!")
    print("Press Ctrl+C to stop")
    print()
    
    # Keep running
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[OK] Server stopped")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
