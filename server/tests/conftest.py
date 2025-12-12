"""
Test configuration for pytest.

This file ensures the 'app' package is importable in all test files.
"""
import os
import sys

# Add the server directory to sys.path so 'app' module can be imported
SERVER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SERVER_ROOT not in sys.path:
    sys.path.insert(0, SERVER_ROOT)
