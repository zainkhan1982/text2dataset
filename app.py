from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import pandas as pd
import os
import tempfile
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import sqlite3

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Lazy load the processing modules
# from preprocess import clean_text, split_sentences
# from labeling_fast import label_entities_fast, convert_to_spacy_format as convert_fast_to_spacy
# from labeling_smart import label_entities_smart, convert_to_spacy_format as convert_smart_to_spacy
# from exporter import export_to_csv, export_to_json
from dataset_history import dataset_history
from community_datasets import community_datasets

# Security
security = HTTPBasic()
# Simple user storage (in production, use a proper database)
user_sessions = {}  # session_id -> username

# Helper functions for authentication
def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return hash_password(plain_password) == hashed_password

def create_session(username: str) -> str:
    """Create a new session for a user."""
    session_id = str(uuid.uuid4())
    user_sessions[session_id] = username
    return session_id

def get_current_user(request: Request) -> Optional[str]:
    """Get the current user from the session cookie."""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in user_sessions:
        return user_sessions[session_id]
    return None

def get_user_id(username: str) -> Optional[int]:
    """Get user ID from username."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_user_dataset(user_id: int, dataset_id: str, filename: str, mode: str, format_type: str, entity_count: int, file_path: str):
    """Add a dataset to a user's history."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_datasets (user_id, dataset_id, filename, mode, format_type, entity_count, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, dataset_id, filename, mode, format_type, entity_count, file_path))
    conn.commit()
    conn.close()

def get_user_datasets(user_id: int):
    """Get all datasets for a user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dataset_id, filename, mode, format_type, entity_count, timestamp, file_path
        FROM user_datasets
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', (user_id,))
    results = cursor.fetchall()
    conn.close()
    
    datasets = []
    for row in results:
        datasets.append({
            "id": row[0],
            "filename": row[1],
            "mode": row[2],
            "format": row[3],
            "entity_count": row[4],
            "timestamp": row[5],
            "file_path": row[6]
        })
    return datasets

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user against the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result and verify_password(password, result[0]):
        return True
    return False

def create_user(username: str, password: str) -> bool:
    """Create a new user in the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash) 
            VALUES (?, ?)
        ''', (username, password_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# Database setup
DB_NAME = "users.db"

def init_db():
    """Initialize the database with users and user_datasets tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user_datasets table for user-specific history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            dataset_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            mode TEXT NOT NULL,
            format_type TEXT NOT NULL,
            entity_count INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create a default admin user if it doesn't exist
    password_hash = hash_password("password")
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash) 
        VALUES (?, ?)
    ''', ("admin", password_hash))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

app = FastAPI()

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

templates = Jinja2Templates(directory="templates")

# Create outputs directory if it doesn't exist
os.makedirs("outputs", exist_ok=True)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check MongoDB connection
    try:
        mongo_status = "not configured"
        if hasattr(community_datasets, 'use_mongodb') and community_datasets.use_mongodb and community_datasets.client is not None:
            # Test MongoDB connection
            community_datasets.client.admin.command('ping')
            mongo_status = "connected"
        elif hasattr(dataset_history, 'use_mongodb') and dataset_history.use_mongodb and dataset_history.client is not None:
            # Test MongoDB connection
            dataset_history.client.admin.command('ping')
            mongo_status = "connected"
        else:
            mongo_status = "using file storage"
    except Exception as e:
        mongo_status = f"error: {str(e)}"
    
    return JSONResponse({
        "status": "healthy",
        "mongodb": mongo_status,
        "community_datasets_count": len(community_datasets.get_community_datasets()),
        "history_datasets_count": len(dataset_history.get_history())
    })

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Get current user
    current_user = get_current_user(request)
    
    # If user is not logged in, redirect to login page
    if not current_user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to access the application"
        })
    
    # Get recent datasets for display
    recent_datasets = dataset_history.get_recent_datasets(5)
    # Get popular community datasets
    popular_datasets = community_datasets.get_popular_datasets(3)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_datasets": recent_datasets,
        "popular_datasets": popular_datasets,
        "current_user": current_user
    })

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Display dataset history page - only for logged-in users"""
    # Check if user is logged in
    current_user = get_current_user(request)
    
    if not current_user:
        # Redirect to login page
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view history"
        })
    
    # Get user-specific history
    user_id = get_user_id(current_user)
    
    if user_id:
        user_datasets = get_user_datasets(user_id)
        # Sort by timestamp (newest first)
        user_datasets.sort(key=lambda x: x['timestamp'], reverse=True)
        return templates.TemplateResponse("history.html", {
            "request": request,
            "datasets": user_datasets,
            "current_user": current_user
        })
    else:
        # Fallback to global history if user not found
        all_datasets = dataset_history.get_history()
        # Sort by timestamp (newest first)
        all_datasets.sort(key=lambda x: x['timestamp'], reverse=True)
        return templates.TemplateResponse("history.html", {
            "request": request,
            "datasets": all_datasets,
            "current_user": current_user
        })

@app.get("/community", response_class=HTMLResponse)
async def community_page(request: Request, search: str = "", tags: str = ""):
    """Display community datasets page"""
    # Get current user
    current_user = get_current_user(request)
    
    # Parse tags if provided
    tag_list = tags.split(",") if tags else []
    tag_list = [tag.strip() for tag in tag_list if tag.strip()]
    
    # Search community datasets
    if search or tag_list:
        community_datasets_list = community_datasets.search_datasets(search, tag_list)
    else:
        community_datasets_list = community_datasets.get_community_datasets()
    
    # Sort by timestamp (newest first)
    community_datasets_list.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return templates.TemplateResponse("community.html", {
        "request": request,
        "datasets": community_datasets_list,
        "search_query": search,
        "search_tags": ", ".join(tag_list),
        "current_user": current_user
    })

@app.post("/generate")
async def generate_dataset(
    request: Request,
    text_input: str = Form(None),
    file_upload: UploadFile = File(None),
    output_format: str = Form("csv"),
    mode: str = Form("fast"),
    custom_name: str = Form(None)
):
    try:
        # Get current user
        current_user = get_current_user(request)
        
        # Lazy load the processing modules
        from preprocess import clean_text, split_sentences
        from exporter import export_to_csv, export_to_json
        
        # Handle spaCy format specially
        if output_format == "spacy":
            if mode == "smart":
                from labeling_smart import label_entities_smart, convert_to_spacy_format as convert_smart_to_spacy
                convert_function = convert_smart_to_spacy
            else:
                from labeling_fast import label_entities_fast, convert_to_spacy_format as convert_fast_to_spacy
                convert_function = convert_fast_to_spacy
            
            # Get text from input or file
            if file_upload and file_upload.filename:
                # Read file content
                content = await file_upload.read()
                if file_upload.content_type == "text/plain":
                    text = content.decode("utf-8")
                else:
                    # For other file types, we would need additional processing
                    text = content.decode("utf-8")
            else:
                text = text_input
            
            if not text:
                return templates.TemplateResponse("index.html", {
                    "request": request, 
                    "error": "Please provide text input or upload a file."
                })
            
            # Process the text
            cleaned_text = clean_text(text)
            sentences = split_sentences(cleaned_text)
            
            # Generate filename
            file_id = str(uuid.uuid4())
            custom_part = f"_{custom_name}" if custom_name else ""
            
            # Convert to spaCy format
            spacy_data = convert_function(sentences)
            
            # Save as JSON
            filename = f"dataset{custom_part}_{file_id}_spacy.json"
            filepath = f"outputs/{filename}"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(spacy_data, f, ensure_ascii=False, indent=2)
            
            # Add to user history if user is logged in
            if current_user:
                user_id = get_user_id(current_user)
                if user_id:
                    add_user_dataset(user_id, file_id, filename, mode, output_format, len(spacy_data), filepath)
            else:
                # Add to global history for anonymous users
                dataset_history.add_to_history(filename, mode, output_format, len(spacy_data))
            
            # Return file content as response with appropriate headers for download
            with open(filepath, "rb") as f:
                content = f.read()
            
            headers = {
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/json"
            }
            
            return Response(content=content, headers=headers, media_type="application/json")
        else:
            # For CSV/JSON formats
            if mode == "smart":
                from labeling_smart import label_entities_smart
                label_function = label_entities_smart
            else:
                from labeling_fast import label_entities_fast
                label_function = label_entities_fast
            
            # Get text from input or file
            if file_upload and file_upload.filename:
                # Read file content
                content = await file_upload.read()
                if file_upload.content_type == "text/plain":
                    text = content.decode("utf-8")
                else:
                    # For other file types, we would need additional processing
                    text = content.decode("utf-8")
            else:
                text = text_input
            
            if not text:
                return templates.TemplateResponse("index.html", {
                    "request": request, 
                    "error": "Please provide text input or upload a file."
                })
            
            # Process the text
            cleaned_text = clean_text(text)
            sentences = split_sentences(cleaned_text)
            
            # Generate filename
            file_id = str(uuid.uuid4())
            custom_part = f"_{custom_name}" if custom_name else ""
            
            # Apply labeling based on mode
            labeled_data = label_function(sentences)
            
            # Convert to DataFrame
            df = pd.DataFrame(labeled_data)
            
            if output_format == "json":
                filename = f"dataset{custom_part}_{file_id}.json"
                filepath = f"outputs/{filename}"
                export_to_json(df, filepath)
            else:  # Default to CSV
                filename = f"dataset{custom_part}_{file_id}.csv"
                filepath = f"outputs/{filename}"
                export_to_csv(df, filepath)
            
            # Add to user history if user is logged in
            if current_user:
                user_id = get_user_id(current_user)
                if user_id:
                    add_user_dataset(user_id, file_id, filename, mode, output_format, len(labeled_data), filepath)
            else:
                # Add to global history for anonymous users
                dataset_history.add_to_history(filename, mode, output_format, len(labeled_data))
            
            # Return file content as response with appropriate headers for download
            with open(filepath, "rb") as f:
                content = f.read()
            
            # Set appropriate content type and headers for file download
            if output_format == "json":
                media_type = "application/json"
            else:
                media_type = "text/csv"
            
            headers = {
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": media_type
            }
            
            return Response(content=content, headers=headers, media_type=media_type)
    
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": f"An error occurred: {str(e)}"
        })

@app.get("/download/{dataset_id}")
async def download_dataset(dataset_id: str, request: Request):
    """Download a previously created dataset"""
    try:
        # First, try to get dataset from global history
        dataset = dataset_history.get_dataset_by_id(dataset_id)
        if not dataset:
            # Try to get from community datasets
            dataset = community_datasets.get_dataset_by_id(dataset_id)
            if not dataset:
                # Try to get from user datasets (for logged-in users)
                current_user = get_current_user(request)
                if current_user:
                    user_id = get_user_id(current_user)
                    if user_id:
                        # Get all user datasets and search for the specific one
                        user_datasets = get_user_datasets(user_id)
                        for user_dataset in user_datasets:
                            if str(user_dataset["id"]) == str(dataset_id):
                                dataset = user_dataset
                                break
                
                # If still not found, return error
                if not dataset:
                    return Response(content="Dataset not found", status_code=404)
        
        # Get file path, with fallback to constructed path
        file_path = dataset.get("file_path")
        if not file_path:
            # Try to construct file path from filename
            filename = dataset.get("filename")
            if filename:
                file_path = os.path.join("outputs", filename)
            else:
                return Response(content="File path not available", status_code=404)
        
        # Normalize the file path
        file_path = os.path.normpath(file_path)
        
        # Check if file exists, try alternative paths if needed
        if not os.path.exists(file_path):
            # For community datasets, try to find the file in the outputs directory
            filename = dataset.get("filename", "")
            if filename:
                # Try with outputs prefix
                alt_path = os.path.join("outputs", filename)
                if os.path.exists(alt_path):
                    file_path = alt_path
                else:
                    # Try without the outputs prefix (in case it's already there)
                    if filename.startswith("outputs" + os.sep) or filename.startswith("outputs/"):
                        # Remove the outputs prefix and try the base filename
                        # Handle both \ and / separators
                        if filename.startswith("outputs" + os.sep):
                            base_filename = filename[len("outputs" + os.sep):]
                        else:
                            base_filename = filename[len("outputs/"):]
                        alt_path = os.path.join("outputs", base_filename)
                        if os.path.exists(alt_path):
                            file_path = alt_path
                        else:
                            # As a last resort, check if any file in outputs matches the filename
                            # This handles cases where the UUID part might be different
                            try:
                                import glob
                                pattern = os.path.join("outputs", f"*{filename}")
                                matches = glob.glob(pattern)
                                if matches:
                                    file_path = matches[0]
                                else:
                                    # Try pattern matching with just the base filename
                                    pattern = os.path.join("outputs", f"*{base_filename}")
                                    matches = glob.glob(pattern)
                                    if matches:
                                        file_path = matches[0]
                                    else:
                                        return Response(content="File not found", status_code=404)
                            except:
                                return Response(content="File not found", status_code=404)
                    else:
                        # As a last resort, check if any file in outputs matches the filename
                        # This handles cases where the UUID part might be different
                        try:
                            import glob
                            pattern = os.path.join("outputs", f"*{filename}")
                            matches = glob.glob(pattern)
                            if matches:
                                file_path = matches[0]
                            else:
                                return Response(content="File not found", status_code=404)
                        except:
                            return Response(content="File not found", status_code=404)
            else:
                return Response(content="File not found", status_code=404)
        
        # Increment download count (only for community datasets)
        if hasattr(community_datasets, 'increment_download_count'):
            try:
                community_datasets.increment_download_count(dataset_id)
            except:
                pass  # Ignore if increment fails
        
        # Determine media type based on file extension
        if file_path.endswith(".json"):
            media_type = "application/json"
        elif file_path.endswith(".csv"):
            media_type = "text/csv"
        else:
            media_type = "application/octet-stream"
        
        with open(file_path, "rb") as f:
            content = f.read()
        
        headers = {
            "Content-Disposition": f"attachment; filename={dataset['filename']}",
            "Content-Type": media_type
        }
        
        return Response(content=content, headers=headers, media_type=media_type)
    
    except Exception as e:
        return Response(content=f"Error downloading file: {str(e)}", status_code=500)

@app.get("/view/{dataset_id}")
async def view_dataset(dataset_id: str, request: Request):
    """View a previously created dataset"""
    try:
        # First, try to get dataset from global history
        dataset = dataset_history.get_dataset_by_id(dataset_id)
        if not dataset:
            # Try to get from community datasets
            dataset = community_datasets.get_dataset_by_id(dataset_id)
            if not dataset:
                # Try to get from user datasets (for logged-in users)
                current_user = get_current_user(request)
                if current_user:
                    user_id = get_user_id(current_user)
                    if user_id:
                        # Get all user datasets and search for the specific one
                        user_datasets = get_user_datasets(user_id)
                        for user_dataset in user_datasets:
                            if str(user_dataset["id"]) == str(dataset_id):
                                dataset = user_dataset
                                break
                
                # If still not found, return error
                if not dataset:
                    return Response(content="Dataset not found", status_code=404)
        
        # Get file path, with fallback to constructed path
        file_path = dataset.get("file_path")
        if not file_path:
            # Try to construct file path from filename
            filename = dataset.get("filename")
            if filename:
                file_path = os.path.join("outputs", filename)
            else:
                return Response(content="File path not available", status_code=404)
        
        # Normalize the file path
        file_path = os.path.normpath(file_path)
        
        # Check if file exists, try alternative paths if needed
        if not os.path.exists(file_path):
            # For community datasets, try to find the file in the outputs directory
            filename = dataset.get("filename", "")
            if filename:
                # Try with outputs prefix
                alt_path = os.path.join("outputs", filename)
                if os.path.exists(alt_path):
                    file_path = alt_path
                else:
                    # Try without the outputs prefix (in case it's already there)
                    if filename.startswith("outputs" + os.sep) or filename.startswith("outputs/"):
                        # Remove the outputs prefix and try the base filename
                        # Handle both \ and / separators
                        if filename.startswith("outputs" + os.sep):
                            base_filename = filename[len("outputs" + os.sep):]
                        else:
                            base_filename = filename[len("outputs/"):]
                        alt_path = os.path.join("outputs", base_filename)
                        if os.path.exists(alt_path):
                            file_path = alt_path
                        else:
                            # As a last resort, check if any file in outputs matches the filename
                            # This handles cases where the UUID part might be different
                            try:
                                import glob
                                pattern = os.path.join("outputs", f"*{filename}")
                                matches = glob.glob(pattern)
                                if matches:
                                    file_path = matches[0]
                                else:
                                    return Response(content="File not found", status_code=404)
                            except:
                                return Response(content="File not found", status_code=404)
                    else:
                        # As a last resort, check if any file in outputs matches the filename
                        # This handles cases where the UUID part might be different
                        try:
                            import glob
                            pattern = os.path.join("outputs", f"*{filename}")
                            matches = glob.glob(pattern)
                            if matches:
                                file_path = matches[0]
                            else:
                                return Response(content="File not found", status_code=404)
                        except:
                            return Response(content="File not found", status_code=404)
            else:
                return Response(content="File not found", status_code=404)
        
        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Determine if it's JSON or CSV
        if file_path.endswith(".json"):
            # Try to parse JSON for better formatting
            try:
                import json
                parsed_content = json.loads(content)
                formatted_content = json.dumps(parsed_content, indent=2, ensure_ascii=False)
            except:
                formatted_content = content
            content_type = "application/json"
        else:
            # For CSV and other formats, show as plain text
            formatted_content = content
            content_type = "text/plain"
        
        # Return as plain text or JSON
        return Response(content=formatted_content, media_type=content_type)
    
    except Exception as e:
        return Response(content=f"Error viewing file: {str(e)}", status_code=500)

@app.post("/share_dataset")
async def share_dataset(
    request: Request,
    dataset_id: str = Form(...),
    description: str = Form(...),
    tags: str = Form(""),
    user_name: str = Form("Anonymous")
):
    """Share a dataset with the community"""
    try:
        # Get dataset from history
        dataset = dataset_history.get_dataset_by_id(dataset_id)
        if not dataset:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Dataset not found"
            })
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Share with community
        success = community_datasets.share_dataset(
            filename=dataset["filename"],
            description=description,
            tags=tag_list,
            mode=dataset["mode"],
            format_type=dataset["format"],
            entity_count=dataset["entity_count"],
            user_name=user_name,
            file_path=dataset.get("file_path", f"outputs/{dataset['filename']}")
        )
        
        if success:
            message = "Dataset shared with community successfully!"
        else:
            message = "Error sharing dataset with community."
            
        # Get recent datasets for display
        recent_datasets = dataset_history.get_recent_datasets(5)
        # Get popular community datasets
        popular_datasets = community_datasets.get_popular_datasets(3)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "recent_datasets": recent_datasets,
            "popular_datasets": popular_datasets,
            "message": message
        })
        
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error sharing dataset: {str(e)}"
        })

@app.post("/like_dataset")
async def like_dataset(dataset_id: str = Form(...)):
    """Add a like to a community dataset"""
    try:
        success = community_datasets.add_like(dataset_id)
        if success:
            return {"success": True, "message": "Liked successfully!"}
        else:
            return {"success": False, "message": "Error liking dataset."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/chat/{dataset_id}")
async def add_chat_message(dataset_id: str, request: Request, message: str = Form(...)):
    """Add a chat message to a dataset discussion"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in to chat"}, status_code=401)
        
        # Check if user is banned
        if community_datasets.is_user_banned(current_user):
            return JSONResponse({"success": False, "message": "You are banned from chat"}, status_code=403)
        
        # Verify dataset exists
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not dataset:
            return JSONResponse({"success": False, "message": "Dataset not found"}, status_code=404)
        
        # Add chat message
        success = community_datasets.add_chat_message(dataset_id, current_user, message)
        
        if success:
            return JSONResponse({"success": True, "message": "Message posted successfully"})
        else:
            return JSONResponse({"success": False, "message": "Error posting message"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/chat/{dataset_id}")
async def get_chat_messages(dataset_id: str, request: Request):
    """Get chat messages for a dataset"""
    try:
        # Verify dataset exists
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not dataset:
            return JSONResponse({"success": False, "message": "Dataset not found"}, status_code=404)
        
        # Get chat messages
        messages = community_datasets.get_chat_messages(dataset_id)
        
        return JSONResponse({"success": True, "messages": messages})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.post("/global_chat")
async def add_global_chat_message(request: Request, message: str = Form(...)):
    """Add a message to the global chat"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in to chat"}, status_code=401)
        
        # Check if user is banned
        if community_datasets.is_user_banned(current_user):
            return JSONResponse({"success": False, "message": "You are banned from chat"}, status_code=403)
        
        # Add global chat message
        success = community_datasets.add_global_chat_message(current_user, message)
        
        if success:
            return JSONResponse({"success": True, "message": "Message posted successfully"})
        else:
            return JSONResponse({"success": False, "message": "Error posting message"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/global_chat")
async def get_global_chat_messages(request: Request, limit: int = 50):
    """Get global chat messages"""
    try:
        # Get global chat messages
        messages = community_datasets.get_global_chat_messages(limit)
        
        return JSONResponse({"success": True, "messages": messages})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/global_chat_page", response_class=HTMLResponse)
async def global_chat_page(request: Request):
    """Display global chat page"""
    # Get current user
    current_user = get_current_user(request)
    
    return templates.TemplateResponse("global_chat.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/static/{file_path:path}")
async def serve_static_files(file_path: str):
    """Serve static files to ensure they work in subpath deployments"""
    try:
        static_file_path = os.path.join("static", file_path)
        if os.path.exists(static_file_path) and not os.path.isdir(static_file_path):
            # Determine content type based on file extension
            if file_path.endswith(".css"):
                media_type = "text/css"
            elif file_path.endswith(".js"):
                media_type = "application/javascript"
            elif file_path.endswith(".png"):
                media_type = "image/png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                media_type = "image/jpeg"
            elif file_path.endswith(".gif"):
                media_type = "image/gif"
            else:
                media_type = "application/octet-stream"
            
            with open(static_file_path, "rb") as file:
                content = file.read()
            return Response(content=content, media_type=media_type)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@app.get("/static/style.css")
async def serve_css():
    """Serve the CSS file directly to ensure it's accessible"""
    try:
        with open("static/style.css", "r") as file:
            content = file.read()
        return Response(content=content, media_type="text/css")
    except Exception as e:
        raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error=None):
    """Display login page"""
    # Get current user
    current_user = get_current_user(request)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error,
        "current_user": current_user
    })

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, error=None):
    """Display signup page"""
    # Get current user
    current_user = get_current_user(request)
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "error": error,
        "current_user": current_user
    })

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login form submission"""
    # Check if user exists and password is correct
    if authenticate_user(username, password):
        # Create session
        session_id = create_session(username)
        
        # Get recent datasets for display
        recent_datasets = dataset_history.get_recent_datasets(5)
        # Get popular community datasets
        popular_datasets = community_datasets.get_popular_datasets(3)
        
        # Redirect to home page with session cookie
        response = templates.TemplateResponse("index.html", {
            "request": request,
            "message": "Login successful!",
            "recent_datasets": recent_datasets,
            "popular_datasets": popular_datasets,
            "current_user": username
        })
        # Set cookie with proper attributes for cross-site access
        response.set_cookie(
            key="session_id", 
            value=session_id, 
            httponly=True,
            samesite="lax",  # Changed from default to lax for better compatibility
            max_age=3600  # Set expiration to 1 hour
        )
        return response
    else:
        # Show login page with error
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

@app.post("/signup")
async def signup(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    """Handle signup form submission"""
    # Validate input
    if len(username) < 3:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Username must be at least 3 characters long"
        })
    
    if len(password) < 6:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Password must be at least 6 characters long"
        })
    
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords do not match"
        })
    
    # Create user
    if not create_user(username, password):
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Username already exists"
        })
    
    # Create session
    session_id = create_session(username)
    
    # Get recent datasets for display
    recent_datasets = dataset_history.get_recent_datasets(5)
    # Get popular community datasets
    popular_datasets = community_datasets.get_popular_datasets(3)
    
    # Redirect to home page with session cookie
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "message": "Account created successfully!",
        "recent_datasets": recent_datasets,
        "popular_datasets": popular_datasets,
        "current_user": username
    })
    # Set cookie with proper attributes for cross-site access
    response.set_cookie(
        key="session_id", 
        value=session_id, 
        httponly=True,
        samesite="lax",  # Changed from default to lax for better compatibility
        max_age=3600  # Set expiration to 1 hour
    )
    return response

@app.get("/logout")
async def logout(request: Request):
    """Handle logout"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in user_sessions:
        del user_sessions[session_id]
    
    # Get recent datasets for display
    recent_datasets = dataset_history.get_recent_datasets(5)
    # Get popular community datasets
    popular_datasets = community_datasets.get_popular_datasets(3)
    
    response = templates.TemplateResponse("index.html", {
        "request": request,
        "message": "You have been logged out",
        "recent_datasets": recent_datasets,
        "popular_datasets": popular_datasets,
        "current_user": None
    })
    # Delete cookie with proper attributes
    response.delete_cookie("session_id", samesite="lax")
    return response

@app.get("/api/user_datasets")
async def get_user_datasets_api(request: Request):
    """API endpoint to get current user's datasets"""
    # Check if user is logged in
    current_user = get_current_user(request)
    
    if not current_user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    
    # Get user-specific history
    user_id = get_user_id(current_user)
    
    if user_id:
        user_datasets = get_user_datasets(user_id)
        # Sort by timestamp (newest first)
        user_datasets.sort(key=lambda x: x['timestamp'], reverse=True)
        return JSONResponse(user_datasets)
    else:
        return JSONResponse([])

@app.post("/admin/delete_dataset/{dataset_id}")
async def delete_dataset(dataset_id: str, request: Request):
    """Delete a dataset from the community (admin only)"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Check if user is admin
        if current_user != "admin":
            return JSONResponse({"success": False, "message": "Only admin can delete datasets"}, status_code=403)
        
        # Delete dataset
        success = community_datasets.delete_dataset(dataset_id, current_user)
        
        if success:
            return JSONResponse({"success": True, "message": "Dataset deleted successfully"})
        else:
            return JSONResponse({"success": False, "message": "Error deleting dataset"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.post("/admin/ban_user")
async def ban_user(request: Request, target_user: str = Form(...)):
    """Ban a user from chat (admin only)"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Check if user is admin
        if current_user != "admin":
            return JSONResponse({"success": False, "message": "Only admin can ban users"}, status_code=403)
        
        # Ban user
        success = community_datasets.ban_user_from_chat(target_user, current_user)
        
        if success:
            return JSONResponse({"success": True, "message": f"User {target_user} banned successfully"})
        else:
            return JSONResponse({"success": False, "message": "Error banning user"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    import os
    # Use a different port to avoid conflicts
    port = int(os.environ.get("PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)
