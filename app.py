from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
import tempfile
import uuid
import json

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

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
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
    # Get recent datasets for display
    recent_datasets = dataset_history.get_recent_datasets(5)
    # Get popular community datasets
    popular_datasets = community_datasets.get_popular_datasets(3)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_datasets": recent_datasets,
        "popular_datasets": popular_datasets
    })

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Display dataset history page"""
    all_datasets = dataset_history.get_history()
    # Sort by timestamp (newest first)
    all_datasets.sort(key=lambda x: x['timestamp'], reverse=True)
    return templates.TemplateResponse("history.html", {
        "request": request,
        "datasets": all_datasets
    })

@app.get("/community", response_class=HTMLResponse)
async def community_page(request: Request, search: str = "", tags: str = ""):
    """Display community datasets page"""
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
        "search_tags": ", ".join(tag_list)
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
            
            # Add to history
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
            
            # Add to history
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
async def download_dataset(dataset_id: str):
    """Download a previously created dataset"""
    try:
        dataset = dataset_history.get_dataset_by_id(dataset_id)
        if not dataset:
            # Try to get from community datasets
            dataset = community_datasets.get_dataset_by_id(dataset_id)
            if not dataset:
                return Response(content="Dataset not found", status_code=404)
        
        file_path = dataset["file_path"]
        if not os.path.exists(file_path):
            return Response(content="File not found", status_code=404)
        
        # Increment download count
        community_datasets.increment_download_count(dataset_id)
        
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

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
