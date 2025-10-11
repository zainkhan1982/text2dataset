from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
import tempfile
import uuid
import json
from preprocess import clean_text, split_sentences
from labeling_fast import label_entities_fast, convert_to_spacy_format as convert_fast_to_spacy
from labeling_smart import label_entities_smart, convert_to_spacy_format as convert_smart_to_spacy
from exporter import export_to_csv, export_to_json
from dataset_history import dataset_history

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create outputs directory if it doesn't exist
os.makedirs("outputs", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Get recent datasets for display
    recent_datasets = dataset_history.get_recent_datasets(5)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_datasets": recent_datasets
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

@app.post("/generate")
async def generate_dataset(
    request: Request,
    text_input: str = Form(None),
    file_upload: UploadFile = File(None),
    output_format: str = Form("csv"),
    mode: str = Form("fast")
):
    try:
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
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        
        # Handle spaCy format specially
        if output_format == "spacy":
            # Convert to spaCy format
            if mode == "smart":
                spacy_data = convert_smart_to_spacy(sentences)
            else:
                spacy_data = convert_fast_to_spacy(sentences)
            
            # Save as JSON
            filename = f"dataset_{file_id}_spacy.json"
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
        
        # Apply labeling based on mode
        if mode == "smart":
            labeled_data = label_entities_smart(sentences)
        else:
            labeled_data = label_entities_fast(sentences)
        
        # Convert to DataFrame
        df = pd.DataFrame(labeled_data)
        
        if output_format == "json":
            filename = f"dataset_{file_id}.json"
            filepath = f"outputs/{filename}"
            export_to_json(df, filepath)
        else:  # Default to CSV
            filename = f"dataset_{file_id}.csv"
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
async def download_dataset(dataset_id: int):
    """Download a previously created dataset"""
    try:
        dataset = dataset_history.get_dataset_by_id(dataset_id)
        if not dataset:
            return Response(content="Dataset not found", status_code=404)
        
        file_path = dataset["file_path"]
        if not os.path.exists(file_path):
            return Response(content="File not found", status_code=404)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)