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
import io

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

# Import enhanced NLP module
from enhanced_nlp import process_text_enhanced, process_multilanguage_text

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

# User management functions using MongoDB
def get_user_id(username: str) -> Optional[str]:
    """Get user ID from username using MongoDB."""
    if hasattr(dataset_history, 'db') and dataset_history.db is not None:
        try:
            users_collection = dataset_history.db["users"]
            user = users_collection.find_one({"username": username})
            return str(user["_id"]) if user else None
        except Exception:
            return None
    return None

# Global user plans dictionary to store user plan information
user_plans = {}


def add_user_dataset(user_id: str, filename: str, mode: str, format_type: str, entity_count: int, file_content: Optional[bytes] = None):
    """Add a dataset to a user's history using MongoDB."""
    if hasattr(dataset_history, 'db') and dataset_history.db is not None:
        try:
            user_datasets_collection = dataset_history.db["user_datasets"]
            
            # Generate a unique ID for this user dataset
            import uuid
            user_dataset_id = str(uuid.uuid4())
            
            # Store file content in GridFS if provided
            file_id = None
            if file_content and dataset_history.gridfs is not None:
                file_id = str(dataset_history.gridfs.put(file_content, filename=filename))
            
            user_dataset_entry = {
                "user_dataset_id": user_dataset_id,  # Unique ID for this user dataset
                "user_id": user_id,
                "filename": filename,
                "mode": mode,
                "format_type": format_type,
                "entity_count": entity_count,
                "timestamp": datetime.now().isoformat(),
                "file_id": file_id
            }
            result = user_datasets_collection.insert_one(user_dataset_entry)
            print(f"Added user dataset: {user_dataset_entry}")  # Debug line
            return user_dataset_id
        except Exception as e:
            print(f"Error adding user dataset: {e}")
            return None
    return None

def get_user_datasets(user_id: str):
    """Get all datasets for a user using MongoDB."""
    if hasattr(dataset_history, 'db') and dataset_history.db is not None:
        try:
            user_datasets_collection = dataset_history.db["user_datasets"]
            datasets = list(user_datasets_collection.find({"user_id": user_id}))
            print(f"Retrieved {len(datasets)} user datasets for user {user_id}")  # Debug line
            
            # Process datasets to ensure they have proper structure for the template
            processed_datasets = []
            for dataset in datasets:
                # Convert ObjectId to string for the id field
                if '_id' in dataset:
                    dataset['_id'] = str(dataset['_id'])
                
                # Create a dataset entry that matches the template expectations
                # The template expects: id, filename, mode, format, entity_count, timestamp
                processed_dataset = {
                    "id": dataset.get("user_dataset_id", ""),  # Use user_dataset_id as the id for download/view links
                    "filename": dataset.get("filename", ""),
                    "mode": dataset.get("mode", ""),
                    "format": dataset.get("format_type", ""),
                    "entity_count": dataset.get("entity_count", 0),
                    "timestamp": dataset.get("timestamp", "")
                }
                processed_datasets.append(processed_dataset)
            
            # Sort by timestamp (newest first)
            processed_datasets.sort(key=lambda x: x['timestamp'], reverse=True)
            print(f"Processed user datasets: {processed_datasets}")  # Debug line
            return processed_datasets
        except Exception as e:
            print(f"Error retrieving user datasets: {e}")
            return []
    return []

def get_user_dataset_by_id(user_id: str, user_dataset_id: str):
    """Get a specific user dataset by its user_dataset_id"""
    if hasattr(dataset_history, 'db') and dataset_history.db is not None:
        try:
            user_datasets_collection = dataset_history.db["user_datasets"]
            dataset = user_datasets_collection.find_one({
                "user_id": user_id, 
                "user_dataset_id": user_dataset_id
            })
            if dataset:
                # Convert ObjectId to string
                if '_id' in dataset:
                    dataset['_id'] = str(dataset['_id'])
                return dataset
        except Exception as e:
            print(f"Error retrieving user dataset: {e}")
    return None

def get_user_dataset_file_content(dataset: dict) -> Optional[bytes]:
    """Get the file content for a user dataset from GridFS"""
    if dataset.get("file_id") and dataset_history.gridfs is not None:
        try:
            from bson import ObjectId
            return dataset_history.gridfs.get(ObjectId(dataset["file_id"])).read()
        except Exception as e:
            print(f"Error retrieving file from GridFS: {e}")
    return None

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user against MongoDB."""
    if hasattr(dataset_history, 'db') and dataset_history.db is not None:
        try:
            users_collection = dataset_history.db["users"]
            user = users_collection.find_one({"username": username})
            if user and verify_password(password, user["password_hash"]):
                return True
        except Exception as e:
            print(f"Error authenticating user: {e}")
    return False

def create_user(username: str, password: str) -> bool:
    """Create a new user in MongoDB."""
    if hasattr(dataset_history, 'db') and dataset_history.db is not None:
        try:
            users_collection = dataset_history.db["users"]
            # Check if user already exists
            if users_collection.find_one({"username": username}):
                return False
            password_hash = hash_password(password)
            user_entry = {
                "username": username,
                "password_hash": password_hash,
                "created_at": datetime.now().isoformat()
            }
            users_collection.insert_one(user_entry)
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    return False

# Create a default admin user if it doesn't exist
def create_default_admin():
    """Create a default admin user if it doesn't exist."""
    if hasattr(dataset_history, 'db') and dataset_history.db is not None:
        try:
            users_collection = dataset_history.db["users"]
            # Check if admin user already exists
            if not users_collection.find_one({"username": "admin"}):
                password_hash = hash_password("password")
                user_entry = {
                    "username": "admin",
                    "password_hash": password_hash,
                    "created_at": datetime.now().isoformat()
                }
                users_collection.insert_one(user_entry)
                print("Default admin user created")
        except Exception as e:
            print(f"Error creating default admin user: {e}")

# Initialize database
create_default_admin()

app = FastAPI()

@app.get("/plans", response_class=HTMLResponse)
async def plans_page(request: Request):
    """Display plans page"""
    # Get current user
    current_user = get_current_user(request)
    
    # Default to basic plan
    user_plan = "basic"
    
    # Check if user has premium plan
    if current_user and current_user in user_plans and user_plans[current_user] == "premium":
        user_plan = "premium"
    
    return templates.TemplateResponse("plans.html", {
        "request": request,
        "current_user": current_user,
        "user_plan": user_plan
    })

@app.get("/api/user_plan")
async def get_user_plan(request: Request):
    """API endpoint to get current user's plan"""
    # Get current user
    current_user = get_current_user(request)
    
    # Default to basic plan
    user_plan = "basic"
    
    # Check if user has premium plan
    if current_user and current_user in user_plans and user_plans[current_user] == "premium":
        user_plan = "premium"
    
    return JSONResponse({"plan": user_plan})


# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

templates = Jinja2Templates(directory="templates")

# Create outputs directory if it doesn't exist (for fallback)
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
    print(f"History page requested by user: {current_user}")  # Debug line
    
    if not current_user:
        # Redirect to login page
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view history"
        })
    
    # Get user-specific history
    user_id = get_user_id(current_user)
    print(f"User ID for {current_user}: {user_id}")  # Debug line
    
    if user_id:
        user_datasets = get_user_datasets(user_id)
        print(f"Rendering history page with {len(user_datasets)} user datasets")  # Debug line
        return templates.TemplateResponse("history.html", {
            "request": request,
            "datasets": user_datasets,
            "current_user": current_user
        })
    else:
        # Only show empty history for users not found in database
        print(f"User {current_user} not found in database, showing empty history")  # Debug line
        return templates.TemplateResponse("history.html", {
            "request": request,
            "datasets": [],
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
                # For API requests, return JSON error
                if request.headers.get("accept") == "application/json":
                    return JSONResponse({"error": "Please provide text input or upload a file."}, status_code=400)
                # For browser requests, return HTML template
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
            
            # Convert to JSON bytes for storage
            json_content = json.dumps(spacy_data, ensure_ascii=False, indent=2)
            file_content = json_content.encode('utf-8')
            
            # Save file content
            filename = f"dataset{custom_part}_{file_id}_spacy.json"
            
            # Add to user history if user is logged in
            if current_user:
                user_id = get_user_id(current_user)
                if user_id:
                    # Add to user-specific history directly
                    user_dataset_id = add_user_dataset(user_id, filename, mode, output_format, len(spacy_data), file_content)
                    print(f"Added spaCy to user history. User Dataset ID: {user_dataset_id}")  # Debug line
            # For anonymous users, we don't store in global history anymore
            # else:
            #     # Add to global history for anonymous users
            #     dataset_history.add_to_history(filename, mode, output_format, len(spacy_data), file_content)
            #     print(f"Added spaCy to global history for anonymous user. Filename: {filename}")  # Debug line
            
            # Return file content as response with appropriate headers for download
            headers = {
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/json"
            }
            
            return Response(content=file_content, headers=headers, media_type="application/json")
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
                # For API requests, return JSON error
                if request.headers.get("accept") == "application/json":
                    return JSONResponse({"error": "Please provide text input or upload a file."}, status_code=400)
                # For browser requests, return HTML template
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
            
            # Convert to bytes for storage
            if output_format == "json":
                filename = f"dataset{custom_part}_{file_id}.json"
                # Use temporary file approach for exporter functions
                temp_file_path = f"temp_{file_id}.json"
                export_to_json(df, temp_file_path)
                with open(temp_file_path, "rb") as f:
                    file_content = f.read()
                os.remove(temp_file_path)  # Clean up temp file
            else:  # Default to CSV
                filename = f"dataset{custom_part}_{file_id}.csv"
                # Use temporary file approach for exporter functions
                temp_file_path = f"temp_{file_id}.csv"
                export_to_csv(df, temp_file_path)
                with open(temp_file_path, "rb") as f:
                    file_content = f.read()
                os.remove(temp_file_path)  # Clean up temp file
            
            # Add to user history if user is logged in
            if current_user:
                user_id = get_user_id(current_user)
                if user_id:
                    # Add to user-specific history directly
                    user_dataset_id = add_user_dataset(user_id, filename, mode, output_format, len(labeled_data), file_content)
                    print(f"Added to user history. User Dataset ID: {user_dataset_id}")  # Debug line
            # For anonymous users, we don't store in global history anymore
            # else:
            #     # Add to global history for anonymous users
            #     dataset_history.add_to_history(filename, mode, output_format, len(labeled_data), file_content)
            #     print(f"Added to global history for anonymous user. Filename: {filename}")  # Debug line
            
            # Return file content as response with appropriate headers for download
            # Set appropriate content type and headers for file download
            if output_format == "json":
                media_type = "application/json"
            else:
                media_type = "text/csv"
            
            headers = {
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": media_type
            }
            
            return Response(content=file_content, headers=headers, media_type=media_type)
    
    except Exception as e:
        # For API requests, return JSON error
        if request.headers.get("accept") == "application/json":
            return JSONResponse({"error": f"An error occurred: {str(e)}"}, status_code=500)
        # For browser requests, return HTML template
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": f"An error occurred: {str(e)}"
        })

@app.get("/download/{dataset_id}")
async def download_dataset(dataset_id: str, request: Request):
    """Download a previously created dataset"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return Response(content="Please log in to download datasets", status_code=401)
        
        # Get user ID
        user_id = get_user_id(current_user)
        if not user_id:
            return Response(content="User not found", status_code=404)
        
        # Try to get dataset from user history
        dataset = get_user_dataset_by_id(user_id, dataset_id)
        if not dataset:
            return Response(content="Dataset not found", status_code=404)
        
        # Get file content from GridFS
        file_content = None
        if dataset.get("file_id") and dataset_history.gridfs is not None:
            try:
                from bson import ObjectId
                file_content = dataset_history.gridfs.get(ObjectId(dataset["file_id"])).read()
            except Exception as e:
                print(f"Error retrieving file from GridFS: {e}")
        
        if not file_content:
            return Response(content="File content not available", status_code=404)
        
        # Determine media type based on file extension
        filename = dataset.get("filename", "")
        if filename.endswith(".json"):
            media_type = "application/json"
        elif filename.endswith(".csv"):
            media_type = "text/csv"
        else:
            media_type = "application/octet-stream"
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": media_type
        }
        
        return Response(content=file_content, headers=headers, media_type=media_type)
    
    except Exception as e:
        return Response(content=f"Error downloading file: {str(e)}", status_code=500)

@app.get("/view/{dataset_id}")
async def view_dataset(dataset_id: str, request: Request):
    """View a previously created dataset"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return Response(content="Please log in to view datasets", status_code=401)
        
        # Get user ID
        user_id = get_user_id(current_user)
        if not user_id:
            return Response(content="User not found", status_code=404)
        
        # Try to get dataset from user history
        dataset = get_user_dataset_by_id(user_id, dataset_id)
        if not dataset:
            return Response(content="Dataset not found", status_code=404)
        
        # Get file content from GridFS
        file_content = None
        if dataset.get("file_id") and dataset_history.gridfs is not None:
            try:
                from bson import ObjectId
                file_content = dataset_history.gridfs.get(ObjectId(dataset["file_id"])).read()
            except Exception as e:
                print(f"Error retrieving file from GridFS: {e}")
        
        if not file_content:
            return Response(content="File content not available", status_code=404)
        
        # Determine if it's JSON or CSV
        filename = dataset.get("filename", "")
        if filename.endswith(".json"):
            # Try to parse JSON for better formatting
            try:
                import json
                parsed_content = json.loads(file_content.decode('utf-8'))
                formatted_content = json.dumps(parsed_content, indent=2, ensure_ascii=False)
            except:
                formatted_content = file_content.decode('utf-8')
            content_type = "application/json"
        else:
            # For CSV and other formats, show as plain text
            formatted_content = file_content.decode('utf-8')
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
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Please log in to share datasets"
            })
        
        # Get user ID
        user_id = get_user_id(current_user)
        if not user_id:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "User not found"
            })
        
        # Try to get dataset from user history first
        dataset = get_user_dataset_by_id(user_id, dataset_id)
        if not dataset:
            # If not found in user history, try global history (for backward compatibility)
            dataset = dataset_history.get_dataset_by_id(dataset_id)
        
        if not dataset:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Dataset not found"
            })
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Get file content
        file_content = None
        if dataset.get("file_id"):
            # Try to get from user dataset GridFS first
            file_content = get_user_dataset_file_content(dataset)
        
        if not file_content:
            # Try to get from dataset_history GridFS (for backward compatibility)
            file_content = dataset_history.get_file_content(dataset)
        
        # If still not found, try file-based approach
        if not file_content:
            # Get file path, with fallback to constructed path
            file_path = dataset.get("file_path")
            if not file_path:
                # Try to construct file path from filename
                filename = dataset.get("filename")
                if filename:
                    file_path = os.path.join("outputs", filename)
            
            # Check if file exists
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_content = f.read()
        
        # Share with community
        success = community_datasets.share_dataset(
            filename=dataset["filename"],
            description=description,
            tags=tag_list,
            mode=dataset.get("mode", dataset.get("format_type", "csv")),
            format_type=dataset.get("format_type", dataset.get("format", "csv")),
            entity_count=dataset.get("entity_count", 0),
            user_name=current_user,  # Use current user name instead of form input
            file_content=file_content
        )
        
        # Get recent datasets for display
        recent_datasets = dataset_history.get_recent_datasets(5)
        # Get popular community datasets
        popular_datasets = community_datasets.get_popular_datasets(3)
        
        if success:
            # Add notification for the user
            try:
                community_datasets.add_notification(
                    current_user, 
                    f"Your dataset '{dataset['filename']}' has been shared with the community!",
                    "new-dataset"
                )
            except:
                pass  # Ignore notification errors
            
            return templates.TemplateResponse("index.html", {
                "request": request,
                "recent_datasets": recent_datasets,
                "popular_datasets": popular_datasets,
                "message": "Dataset shared with community successfully!",
                "current_user": current_user
            })
        else:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "recent_datasets": recent_datasets,
                "popular_datasets": popular_datasets,
                "error": "Error sharing dataset with community.",
                "current_user": current_user
            })
        
    except Exception as e:
        # Get recent datasets for display
        recent_datasets = dataset_history.get_recent_datasets(5)
        # Get popular community datasets
        popular_datasets = community_datasets.get_popular_datasets(3)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "recent_datasets": recent_datasets,
            "popular_datasets": popular_datasets,
            "error": f"Error sharing dataset: {str(e)}",
            "current_user": get_current_user(request) if hasattr(request, 'cookies') else None
        })

@app.post("/like_dataset")
async def like_dataset(request: Request, dataset_id: str = Form(...)):
    """Add a like to a community dataset"""
    try:
        # Get current user
        current_user = get_current_user(request)
        
        # Call add_like with user name to prevent multiple likes
        success = community_datasets.add_like(dataset_id, current_user)
        
        if success:
            return {"success": True, "message": "Liked successfully!"}
        else:
            if current_user:
                return {"success": False, "message": "You have already liked this dataset."}
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
        # Add debug information
        print(f"API: Found {len(user_datasets)} datasets for user {current_user} (ID: {user_id})")
        return JSONResponse(user_datasets)
    else:
        print(f"API: No user ID found for user {current_user}")
        return JSONResponse([])

# Global user plans dictionary to store user plan information
user_plans = {}

@app.get("/health")
async def health_check_endpoint():
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

@app.get("/api/current_user_plan")
async def api_get_current_user_plan(request: Request):
    """API endpoint to get current user's plan"""
    # Get current user
    current_user = get_current_user(request)
    
    # Default to basic plan
    user_plan = "basic"
    
    # Check if user has premium plan
    if current_user and current_user in user_plans and user_plans[current_user] == "premium":
        user_plan = "premium"
    
    return JSONResponse({"plan": user_plan})

@app.post("/upgrade_plan")
async def upgrade_user_plan_endpoint(request: Request):
    """Upgrade user's plan to premium"""
    # Get current user
    current_user = get_current_user(request)
    
    if not current_user:
        return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
    
    # In a real application, this would involve payment processing
    # For now, we'll just upgrade the user's plan
    user_plans[current_user] = "premium"
    
    return JSONResponse({"success": True, "message": "Plan upgraded successfully"})

@app.post("/downgrade_plan")
async def downgrade_user_plan_endpoint(request: Request):
    """Downgrade user's plan to basic"""
    # Get current user
    current_user = get_current_user(request)
    
    if not current_user:
        return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
    
    # Downgrade the user's plan
    user_plans[current_user] = "basic"
    
    return JSONResponse({"success": True, "message": "Plan downgraded successfully"})

@app.post("/delete_user_dataset/{dataset_id}")
async def delete_user_dataset(dataset_id: str, request: Request):
    """Delete a user's own dataset from history"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Get user ID
        user_id = get_user_id(current_user)
        if not user_id:
            return JSONResponse({"success": False, "message": "User not found"}, status_code=404)
        
        # Delete dataset from user history
        success = dataset_history.delete_user_dataset(user_id, dataset_id)
        
        if success:
            return JSONResponse({"success": True, "message": "Dataset deleted successfully from history"})
        else:
            return JSONResponse({"success": False, "message": "Dataset not found in history or already deleted"}, status_code=404)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.post("/delete_community_dataset/{dataset_id}")
async def delete_community_dataset(dataset_id: str, request: Request):
    """Delete a user's own dataset from community"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Delete dataset from community (owners and admin only)
        success = community_datasets.delete_dataset(dataset_id, current_user)
        
        if success:
            return JSONResponse({"success": True, "message": "Dataset deleted successfully from community"})
        else:
            return JSONResponse({"success": False, "message": "Dataset not found, not owned by you, or already deleted"}, status_code=404)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

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

@app.post("/dataset/{dataset_id}/version")
async def create_dataset_version(dataset_id: str, request: Request, version_notes: str = Form(...)):
    """Create a new version of a dataset"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Verify dataset exists
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not dataset:
            return JSONResponse({"success": False, "message": "Dataset not found"}, status_code=404)
        
        # Create dataset version
        success = community_datasets.create_dataset_version(dataset_id, version_notes, current_user)
        
        if success:
            return JSONResponse({"success": True, "message": "Dataset version created successfully"})
        else:
            return JSONResponse({"success": False, "message": "Error creating dataset version"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/dataset/{dataset_id}/versions", response_class=HTMLResponse)
async def dataset_versions_page(dataset_id: str, request: Request):
    """Display dataset versions page"""
    # Get current user
    current_user = get_current_user(request)
    
    # Get dataset
    dataset = community_datasets.get_dataset_by_id(dataset_id)
    if not dataset:
        return templates.TemplateResponse("community.html", {
            "request": request,
            "datasets": [],
            "current_user": current_user,
            "error": "Dataset not found"
        })
    
    # Get dataset versions
    versions = community_datasets.get_dataset_versions(dataset_id)
    
    return templates.TemplateResponse("dataset_versions.html", {
        "request": request,
        "dataset": dataset,
        "versions": versions,
        "current_user": current_user
    })

@app.get("/collections", response_class=HTMLResponse)
async def collections_page(request: Request):
    """Display collections page"""
    # Get current user
    current_user = get_current_user(request)
    
    # Get collections based on user status
    if current_user:
        # Get user's collections and public collections
        user_collections = community_datasets.get_user_collections(current_user)
        public_collections = community_datasets.get_public_collections()
        # Filter out user's collections from public collections to avoid duplicates
        other_public_collections = [c for c in public_collections if c["created_by"] != current_user]
        collections = user_collections + other_public_collections
    else:
        # Get only public collections for anonymous users
        collections = community_datasets.get_public_collections()
    
    return templates.TemplateResponse("collections.html", {
        "request": request,
        "collections": collections,
        "current_user": current_user
    })

@app.post("/collections")
async def create_dataset_collection(request: Request, name: str = Form(...), 
                                  description: str = Form(""), is_public: bool = Form(False),
                                  dataset_ids: str = Form("[]")):
    """Create a collection of datasets"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Parse dataset IDs
        try:
            dataset_ids_list = json.loads(dataset_ids) if dataset_ids else []
        except json.JSONDecodeError:
            dataset_ids_list = []
        
        # Create dataset collection
        success = community_datasets.create_dataset_collection(
            name, description, is_public, dataset_ids_list, current_user
        )
        
        if success:
            return JSONResponse({"success": True, "message": "Dataset collection created successfully"})
        else:
            return JSONResponse({"success": False, "message": "Error creating dataset collection"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/collections/user")
async def get_user_collections(request: Request):
    """Get all collections created by the current user"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Get user collections
        collections = community_datasets.get_user_collections(current_user)
        
        return JSONResponse({"success": True, "collections": collections})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/collections/public")
async def get_public_collections(request: Request):
    """Get all public collections"""
    try:
        # Get public collections
        collections = community_datasets.get_public_collections()
        
        return JSONResponse({"success": True, "collections": collections})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.post("/notifications")
async def add_notification(request: Request, user_name: str = Form(...), message: str = Form(...), 
                          notification_type: str = Form(...)):
    """Add a notification for a user (internal use)"""
    try:
        # In a real implementation, this would be called internally
        # For now, we'll allow it for testing
        success = community_datasets.add_notification(user_name, message, notification_type)
        
        if success:
            return JSONResponse({"success": True, "message": "Notification added successfully"})
        else:
            return JSONResponse({"success": False, "message": "Error adding notification"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request):
    """Display notifications page"""
    # Check if user is logged in
    current_user = get_current_user(request)
    
    if not current_user:
        # Redirect to login page
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Please log in to view notifications"
        })
    
    # Get user notifications
    notifications = community_datasets.get_user_notifications(current_user)
    
    return templates.TemplateResponse("notifications.html", {
        "request": request,
        "notifications": notifications,
        "current_user": current_user
    })

@app.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(notification_id: str, request: Request):
    """Mark a notification as read"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Mark notification as read
        success = community_datasets.mark_notification_as_read(current_user, notification_id)
        
        if success:
            return JSONResponse({"success": True, "message": "Notification marked as read"})
        else:
            return JSONResponse({"success": False, "message": "Error marking notification as read"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.post("/api_keys")
async def create_api_key(request: Request, key_name: str = Form(...)):
    """Create an API key for the current user"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Create API key
        api_key = community_datasets.create_api_key(current_user, key_name)
        
        if api_key:
            return JSONResponse({"success": True, "api_key": api_key, "message": "API key created successfully"})
        else:
            return JSONResponse({"success": False, "message": "Error creating API key"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/dataset/{dataset_id}/quality")
async def get_dataset_quality(dataset_id: str, request: Request):
    """Get quality metrics for a dataset"""
    try:
        # Verify dataset exists
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not dataset:
            return JSONResponse({"success": False, "message": "Dataset not found"}, status_code=404)
        
        # Get dataset quality metrics
        quality_metrics = community_datasets.calculate_dataset_quality_score(dataset_id)
        
        return JSONResponse({"success": True, "quality": quality_metrics})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)


@app.get("/dataset/{dataset_id}/edit")
async def edit_dataset_page(dataset_id: str, request: Request):
    """Display dataset editing page"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Please log in to edit datasets"
            })
        
        # Get dataset
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not dataset:
            return templates.TemplateResponse("community.html", {
                "request": request,
                "datasets": [],
                "current_user": current_user,
                "error": "Dataset not found"
            })
        
        # Check if user is owner or admin
        is_owner = dataset.get("user_name") == current_user
        is_admin = current_user == "admin"
        
        if not is_owner and not is_admin:
            return templates.TemplateResponse("community.html", {
                "request": request,
                "datasets": [],
                "current_user": current_user,
                "error": "You don't have permission to edit this dataset"
            })
        
        # Get file content
        file_content = None
        if dataset.get("file_id") and community_datasets.gridfs is not None:
            try:
                from bson import ObjectId
                file_content = community_datasets.gridfs.get(ObjectId(dataset["file_id"])).read()
                # Decode content for display
                if dataset.get("filename", "").endswith(".json"):
                    file_content = file_content.decode('utf-8')
                else:
                    file_content = file_content.decode('utf-8')
            except Exception as e:
                print(f"Error retrieving file content: {e}")
        
        return templates.TemplateResponse("edit_dataset.html", {
            "request": request,
            "dataset": dataset,
            "file_content": file_content,
            "current_user": current_user
        })
        
    except Exception as e:
        return templates.TemplateResponse("community.html", {
            "request": request,
            "datasets": [],
            "current_user": get_current_user(request) if hasattr(request, 'cookies') else None,
            "error": f"Error loading edit page: {str(e)}"
        })


@app.post("/dataset/{dataset_id}/edit")
async def edit_dataset(dataset_id: str, request: Request, 
                      description: str = Form(...), 
                      tags: str = Form(""), 
                      file_content: str = Form(None)):
    """Edit a dataset and create a new version"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"success": False, "message": "You must be logged in"}, status_code=401)
        
        # Get original dataset
        original_dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not original_dataset:
            return JSONResponse({"success": False, "message": "Dataset not found"}, status_code=404)
        
        # Check if user is owner or admin
        is_owner = original_dataset.get("user_name") == current_user
        is_admin = current_user == "admin"
        
        if not is_owner and not is_admin:
            return JSONResponse({"success": False, "message": "You don't have permission to edit this dataset"}, status_code=403)
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Update dataset
        updated_dataset = {
            "filename": original_dataset["filename"],
            "description": description,
            "tags": tag_list,
            "mode": original_dataset["mode"],
            "format": original_dataset["format"],
            "entity_count": original_dataset["entity_count"],
            "user_name": original_dataset["user_name"],
            "timestamp": datetime.now().isoformat(),
            "download_count": original_dataset.get("download_count", 0),
            "likes": original_dataset.get("likes", 0)
        }
        
        # If file content was modified, update it
        file_bytes = None
        if file_content:
            file_bytes = file_content.encode('utf-8')
            # Update entity count based on file content
            try:
                if original_dataset["filename"].endswith(".json"):
                    import json
                    data = json.loads(file_content)
                    if isinstance(data, list):
                        updated_dataset["entity_count"] = len(data)
                    elif isinstance(data, dict) and "entities" in data:
                        updated_dataset["entity_count"] = len(data["entities"])
                # For CSV, count lines
                elif original_dataset["filename"].endswith(".csv"):
                    lines = file_content.strip().split('\n')
                    # Subtract 1 for header row
                    updated_dataset["entity_count"] = max(0, len(lines) - 1)
            except Exception as e:
                print(f"Error updating entity count: {e}")
        
        # Update in MongoDB or file storage
        if community_datasets.use_mongodb and community_datasets.collection is not None:
            try:
                from bson import ObjectId
                # Update the dataset
                result = community_datasets.collection.update_one(
                    {"_id": ObjectId(dataset_id)},
                    {"$set": updated_dataset}
                )
                
                # If file content was updated, store in GridFS
                if file_bytes and community_datasets.gridfs is not None:
                    # Delete old file
                    if "file_id" in original_dataset:
                        try:
                            community_datasets.gridfs.delete(ObjectId(original_dataset["file_id"]))
                        except Exception as e:
                            print(f"Error deleting old file: {e}")
                    
                    # Store new file
                    new_file_id = community_datasets.gridfs.put(file_bytes, filename=original_dataset["filename"])
                    # Update file_id in dataset
                    community_datasets.collection.update_one(
                        {"_id": ObjectId(dataset_id)},
                        {"$set": {"file_id": str(new_file_id)}}
                    )
            except Exception as e:
                return JSONResponse({"success": False, "message": f"Error updating dataset: {str(e)}"}, status_code=500)
        else:
            # File-based storage - this is more complex, so we'll just create a new version
            return JSONResponse({"success": False, "message": "Editing only supported with MongoDB"}, status_code=500)
        
        return JSONResponse({"success": True, "message": "Dataset updated successfully"})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

# Add API endpoints for programmatic access
@app.get("/api/datasets")
async def api_get_datasets(api_key: str):
    """Get all community datasets (API endpoint)"""
    try:
        # Validate API key
        user_name = community_datasets.validate_api_key(api_key)
        if not user_name:
            return JSONResponse({"success": False, "message": "Invalid API key"}, status_code=401)
        
        # Get community datasets
        datasets = community_datasets.get_community_datasets()
        
        return JSONResponse({"success": True, "datasets": datasets})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/api/dataset/{dataset_id}")
async def api_get_dataset(dataset_id: str, api_key: str):
    """Get a specific dataset (API endpoint)"""
    try:
        # Validate API key
        user_name = community_datasets.validate_api_key(api_key)
        if not user_name:
            return JSONResponse({"success": False, "message": "Invalid API key"}, status_code=401)
        
        # Get dataset
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not dataset:
            return JSONResponse({"success": False, "message": "Dataset not found"}, status_code=404)
        
        return JSONResponse({"success": True, "dataset": dataset})
        
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

@app.get("/api/download/{dataset_id}")
async def api_download_dataset(dataset_id: str, api_key: str):
    """Download a dataset (API endpoint)"""
    try:
        # Validate API key
        user_name = community_datasets.validate_api_key(api_key)
        if not user_name:
            return JSONResponse({"success": False, "message": "Invalid API key"}, status_code=401)
        
        # First, try to get dataset from global history
        dataset = dataset_history.get_dataset_by_id(dataset_id)
        if not dataset:
            # Try to get from community datasets
            dataset = community_datasets.get_dataset_by_id(dataset_id)
            if not dataset:
                return JSONResponse({"success": False, "message": "Dataset not found"}, status_code=404)
        
        # Get file content
        file_content = None
        
        # Try to get from dataset_history first
        if not file_content:
            file_content = dataset_history.get_file_content(dataset)
        
        # Try to get from community_datasets if not found
        if not file_content:
            file_content = community_datasets.get_file_content(dataset)
        
        # If still not found, try file-based approach
        if not file_content:
            # Get file path, with fallback to constructed path
            file_path = dataset.get("file_path")
            if not file_path:
                # Try to construct file path from filename
                filename = dataset.get("filename")
                if filename:
                    file_path = os.path.join("outputs", filename)
                else:
                    return JSONResponse({"success": False, "message": "File path not available"}, status_code=404)
            
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
                                            return JSONResponse({"success": False, "message": "File not found"}, status_code=404)
                                except:
                                    return JSONResponse({"success": False, "message": "File not found"}, status_code=404)
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
                                    return JSONResponse({"success": False, "message": "File not found"}, status_code=404)
                            except:
                                return JSONResponse({"success": False, "message": "File not found"}, status_code=404)
                else:
                    return JSONResponse({"success": False, "message": "File not found"}, status_code=404)
            
            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()
        
        if not file_content:
            return JSONResponse({"success": False, "message": "File content not available"}, status_code=404)
        
        # Increment download count (only for community datasets)
        if hasattr(community_datasets, 'increment_download_count'):
            try:
                community_datasets.increment_download_count(dataset_id)
            except:
                pass  # Ignore if increment fails
        
        # Determine media type based on file extension
        filename = dataset.get("filename", "")
        if filename.endswith(".json"):
            media_type = "application/json"
        elif filename.endswith(".csv"):
            media_type = "text/csv"
        else:
            media_type = "application/octet-stream"
        
        return Response(content=file_content, media_type=media_type)
    
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error downloading file: {str(e)}"}, status_code=500)

@app.get("/api_docs", response_class=HTMLResponse)
async def api_docs_page(request: Request):
    """Display API documentation page"""
    # Get current user
    current_user = get_current_user(request)
    
    return templates.TemplateResponse("api_docs.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/view_community/{dataset_id}")
async def view_community_dataset(dataset_id: str, request: Request):
    """View a community dataset"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return Response(content="Please log in to view datasets", status_code=401)
        
        # Try to get dataset from community datasets
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not dataset:
            return Response(content="Dataset not found", status_code=404)
        
        # Get file content from GridFS
        file_content = None
        if dataset.get("file_id") and community_datasets.gridfs is not None:
            try:
                from bson import ObjectId
                file_content = community_datasets.gridfs.get(ObjectId(dataset["file_id"])).read()
            except Exception as e:
                print(f"Error retrieving file from GridFS: {e}")
        
        # If not found in GridFS, try file-based approach
        if not file_content:
            # Get file path, with fallback to constructed path
            file_path = dataset.get("file_path")
            if not file_path:
                # Try to construct file path from filename
                filename = dataset.get("filename")
                if filename:
                    file_path = os.path.join("outputs", filename)
            
            # Check if file exists
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_content = f.read()
        
        if not file_content:
            return Response(content="File content not available", status_code=404)
        
        # Determine if it's JSON or CSV
        filename = dataset.get("filename", "")
        if filename.endswith(".json"):
            # Try to parse JSON for better formatting
            try:
                import json
                parsed_content = json.loads(file_content.decode('utf-8'))
                formatted_content = json.dumps(parsed_content, indent=2, ensure_ascii=False)
            except:
                formatted_content = file_content.decode('utf-8')
            content_type = "application/json"
        else:
            # For CSV and other formats, show as plain text
            formatted_content = file_content.decode('utf-8')
            content_type = "text/plain"
        
        # Return as plain text or JSON
        return Response(content=formatted_content, media_type=content_type)
    
    except Exception as e:
        return Response(content=f"Error viewing file: {str(e)}", status_code=500)

@app.get("/download_community/{dataset_id}")
async def download_community_dataset(dataset_id: str, request: Request):
    """Download a community dataset"""
    try:
        # Get current user
        current_user = get_current_user(request)
        if not current_user:
            return Response(content="Please log in to download datasets", status_code=401)
        
        # Try to get dataset from community datasets
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if not dataset:
            return Response(content="Dataset not found", status_code=404)
        
        # Get file content from GridFS
        file_content = None
        if dataset.get("file_id") and community_datasets.gridfs is not None:
            try:
                from bson import ObjectId
                file_content = community_datasets.gridfs.get(ObjectId(dataset["file_id"])).read()
            except Exception as e:
                print(f"Error retrieving file from GridFS: {e}")
        
        # If not found in GridFS, try file-based approach
        if not file_content:
            # Get file path, with fallback to constructed path
            file_path = dataset.get("file_path")
            if not file_path:
                # Try to construct file path from filename
                filename = dataset.get("filename")
                if filename:
                    file_path = os.path.join("outputs", filename)
            
            # Check if file exists
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_content = f.read()
        
        if not file_content:
            return Response(content="File content not available", status_code=404)
        
        # Increment download count
        try:
            community_datasets.increment_download_count(dataset_id)
        except:
            pass  # Ignore if increment fails
        
        # Determine media type based on file extension
        filename = dataset.get("filename", "")
        if filename.endswith(".json"):
            media_type = "application/json"
        elif filename.endswith(".csv"):
            media_type = "text/csv"
        else:
            media_type = "application/octet-stream"
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": media_type
        }
        
        return Response(content=file_content, headers=headers, media_type=media_type)
    
    except Exception as e:
        return Response(content=f"Error downloading file: {str(e)}", status_code=500)

# Add a helper function to get dataset by ID for templates
def get_dataset_by_id(dataset_id):
    """Helper function to get dataset by ID for templates"""
    return community_datasets.get_dataset_by_id(dataset_id)

# Register the helper function with Jinja2
templates.env.globals["get_dataset_by_id"] = get_dataset_by_id

@app.get("/dataset/{dataset_id}")
async def get_dataset(dataset_id: str, request: Request):
    """Get a specific dataset by ID"""
    try:
        dataset = community_datasets.get_dataset_by_id(dataset_id)
        if dataset:
            return JSONResponse({"success": True, "dataset": dataset})
        else:
            return JSONResponse({"success": False, "message": "Dataset not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"Error: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    import os
    # Use a different port to avoid conflicts
    port = int(os.environ.get("PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)