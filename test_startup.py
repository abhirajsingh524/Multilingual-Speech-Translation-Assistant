#!/usr/bin/env python3
"""
Quick startup test for app.py
"""
import sys
import time

start_time = time.time()

try:
    print("Testing app startup...")
    from app import app
    
    elapsed = time.time() - start_time
    print(f"✓ App imported successfully in {elapsed:.2f} seconds")
    print(f"✓ Flask app created: {app.name}")
    print(f"✓ Upload folder: {app.config.get('UPLOAD_FOLDER')}")
    print(f"✓ Output folder: {app.config.get('OUTPUT_FOLDER')}")
    
    # Check if routes are registered
    print(f"✓ Registered blueprints: {list(app.blueprints.keys())}")
    
    print("\n✅ All checks passed! App is ready to run.")
    sys.exit(0)
    
except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n❌ Error after {elapsed:.2f} seconds:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
