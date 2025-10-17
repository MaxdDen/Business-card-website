#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.
"""
try:
    import jwt
    print("✓ JWT import successful")
except ImportError as e:
    print(f"✗ JWT import failed: {e}")

try:
    from passlib.context import CryptContext
    print("✓ Passlib import successful")
except ImportError as e:
    print(f"✗ Passlib import failed: {e}")

try:
    from fastapi import FastAPI
    print("✓ FastAPI import successful")
except ImportError as e:
    print(f"✗ FastAPI import failed: {e}")

try:
    from app.database.db import ensure_database_initialized
    print("✓ Database module import successful")
except ImportError as e:
    print(f"✗ Database module import failed: {e}")

try:
    from app.auth.security import create_access_token
    print("✓ Auth security import successful")
except ImportError as e:
    print(f"✗ Auth security import failed: {e}")

print("All imports tested.")
