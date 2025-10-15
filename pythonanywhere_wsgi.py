"""
WSGI configuration for Text2Dataset on PythonAnywhere
"""

# This file is used by PythonAnywhere to serve your FastAPI application
# Make sure to update the path below to match your actual project location

import sys
import os

# Add your project directory to the sys.path
# Update this path to match your actual project location
project_home = '/home/Zainkhanza/text/text2dataset'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Change to the project directory
os.chdir(project_home)

# Import your FastAPI app
from app import app as application

# PythonAnywhere will use the 'application' variable to serve your app
# The app variable should be your FastAPI instance