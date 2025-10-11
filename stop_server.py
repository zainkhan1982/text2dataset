"""
Script to stop the Text2Dataset server
"""

import os
import signal
import sys

def stop_server():
    """Stop the FastAPI server"""
    try:
        # This is a simple script to remind users how to stop the server
        print("To stop the Text2Dataset server:")
        print("1. Go to the terminal where the server is running")
        print("2. Press Ctrl+C to stop the server")
        print("")
        print("If you started the server in the background, you can:")
        print("1. Find the process: netstat -ano | findstr :8000 (Windows)")
        print("2. Kill the process: taskkill /PID <process_id> /F (Windows)")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    stop_server()