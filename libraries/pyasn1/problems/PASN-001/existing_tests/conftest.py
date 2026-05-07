"""
conftest.py — Ensure pyasn1 is imported from /workspace/lib (evaluation mode)
or from the virtual environment (local testing).
"""
import sys
import os

# If running under the eval harness, /workspace/lib is prepended at runtime.
# This conftest has no additional logic; pytest collection handles it.
