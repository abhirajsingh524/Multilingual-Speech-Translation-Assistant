#!/usr/bin/env python3
"""
Test speech-to-text translation workflow
"""
import sys

print("=" * 60)
print("Testing Speech Translation Workflow")
print("=" * 60)

# Test 1: Import translator module
print("\n1. Testing translator module import...")
try:
    from models.translator import translate_text
    print("   ✓ Translator imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import translator: {e}")
    sys.exit(1)

# Test 2: Test simple translation (without loading NLLB)
print("\n2. Testing Marian translation (en -> hi)...")
try:
    # This should use Marian model, not NLLB
    result = translate_text("Hello world", "en", "hi")
    print(f"   ✓ Translation successful: '{result}'")
except Exception as e:
    print(f"   ❌ Translation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Import speech_to_text
print("\n3. Testing speech_to_text module import...")
try:
    from models.speech_to_text import speech_to_text
    print("   ✓ Speech-to-text module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import speech_to_text: {e}")
    sys.exit(1)

# Test 4: Check Whisper model
print("\n4. Checking Whisper model...")
try:
    from models.speech_to_text import model as whisper_model
    print(f"   ✓ Whisper model loaded: {type(whisper_model)}")
except Exception as e:
    print(f"   ❌ Whisper model error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All speech translation tests passed!")
print("=" * 60)
print("\nThe speech model should now work correctly.")
print("Try uploading an audio file and selecting 'Speech Model'.")
