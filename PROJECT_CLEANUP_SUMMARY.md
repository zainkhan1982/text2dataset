# Project Cleanup Summary

## Overview

This document summarizes the cleanup performed on the text2dataset project and identifies important variables and keys needed for operation.

## Files Removed

The following unnecessary/test files have been removed:

- All test files (`test_*.py`, `*_test.py`)
- Debug files (`debug_*.py`)
- Example usage files
- Cache directories (`__pycache__`)
- Generated output files in `outputs/` directory
- History and community JSON files

## Current Directory Structure

```
text2dataset/
├── app.py                 # Main application file
├── community_datasets.py   # Community datasets management
├── dataset_history.py      # Dataset history management
├── exporter.py            # Data export functionality
├── labeling_fast.py       # Fast mode entity labeling
├── labeling_smart.py      # Smart mode entity labeling
├── preprocess.py          # Text preprocessing
├── requirements.txt       # Python dependencies
├── start.bat             # Windows startup script
├── README.md             # Project documentation
├── USAGE.md              # Usage instructions
├── PROJECT_SUMMARY.md    # Project overview
├── MONGODB_INTEGRATION.md # MongoDB integration details
├── community/            # Community datasets directory (empty)
├── history/              # History datasets directory (empty)
├── outputs/              # Generated datasets directory (empty)
├── static/               # CSS files
│   └── style.css
└── templates/            # HTML templates
    ├── index.html
    ├── history.html
    └── community.html
```

## Important Variables and Keys

### MongoDB Connection

- **URI**: `mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/`
- **Database Name**: `text2dataset`
- **Collections**:
  - `dataset_history` - Stores generation history
  - `community_datasets` - Stores shared community datasets

### API Endpoints

- [/](file://c:\Users\Admin\OneDrive\Desktop\text\best_text_classifier.pkl) - Main page
- `/generate` - Generate dataset (POST)
- `/download/{dataset_id}` - Download dataset
- `/share_dataset` - Share dataset with community (POST)
- `/like_dataset` - Like a community dataset (POST)
- `/history` - View dataset history
- `/community` - View community datasets
- `/health` - Health check

### Form Parameters

- `text_input` - Text content for processing
- `file_upload` - File upload
- `output_format` - Output format (csv/json/spacy)
- `mode` - Processing mode (fast/smart)
- `custom_name` - Custom name for files (newly added)
- `dataset_id` - Dataset ID for sharing/downloading
- `description` - Dataset description for sharing
- `tags` - Comma-separated tags for sharing
- `user_name` - User name for sharing

### Custom Filename Feature

The application now supports custom filenames. When generating a dataset, you can provide a `custom_name` parameter to include your name in the filename:

- Format: `dataset_{custom_name}_{uuid}.{extension}`
- Example: `dataset_myname_123e4567-e89b-12d3-a456-426614174000.csv`

## Running the Application

1. Install dependencies: `pip install -r requirements.txt`
2. Start the application: `python app.py` or `start.bat`
3. Access the application at `http://localhost:8003`

## MongoDB Integration

The application uses MongoDB for persistent storage of:

1. Dataset generation history
2. Community-shared datasets

Both collections are automatically created when the application starts and data is added.
