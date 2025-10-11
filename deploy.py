"""
Deployment script for Text2Dataset application
"""

import subprocess
import sys
import os

def deploy_local():
    """Deploy the application locally"""
    print("Starting Text2Dataset application...")
    print("Application will be available at http://localhost:8002")
    
    try:
        # Change to the application directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Run the application
        subprocess.run([sys.executable, "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running the application: {e}")
    except KeyboardInterrupt:
        print("\nApplication stopped by user")

def deploy_online():
    """Instructions for deploying online"""
    print("""
To deploy Text2Dataset online, you have several options:

1. Railway.app (Recommended for free deployment):
   - Go to https://railway.app/
   - Create an account
   - Create a new project
   - Connect your GitHub repository or upload your code
   - Set environment variables:
     * MONGODB_URI=mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/
   - Add a requirements.txt file with all dependencies
   - Set the start command to: python app.py

2. Heroku:
   - Install Heroku CLI
   - Create a new Heroku app
   - Set environment variables:
     * MONGODB_URI=mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/
   - Deploy using git push heroku main

3. Render:
   - Go to https://render.com/
   - Create a new Web Service
   - Connect your GitHub repository
   - Set environment variables:
     * MONGODB_URI=mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/
   - Set the build command: pip install -r requirements.txt
   - Set the start command: python app.py

Environment variables needed:
- MONGODB_URI: Your MongoDB Atlas connection string
""")

if __name__ == "__main__":
    print("Text2Dataset Deployment Options")
    print("=" * 40)
    print("1. Run locally")
    print("2. View online deployment instructions")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        deploy_local()
    elif choice == "2":
        deploy_online()
    else:
        print("Invalid choice. Please run the script again and select 1 or 2.")