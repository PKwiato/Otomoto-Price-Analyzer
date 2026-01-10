import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    import main
    print("Successfully imported main")
except Exception as e:
    import traceback
    traceback.print_exc()
