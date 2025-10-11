# Text2Dataset Usage Guide

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip package manager

### Installation

1. Clone or download the Text2Dataset repository
2. Navigate to the project directory:
   ```bash
   cd text2dataset
   ```
3. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Download the spaCy language model:
   ```bash
   pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
   ```

### Running the Application

1. Start the server:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:8000`

## 🖥️ Using the Web Interface

### 1. Text Input

- **Paste Text**: Directly paste your text content into the text area
- **Upload File**: Upload a TXT file containing your text data

### 2. Configuration Options

- **Output Format**: Choose between CSV or JSON format for your dataset
- **Processing Mode**:
  - **Fast Mode**: Rule-based NLP using spaCy and KeyBERT (faster)
  - **Smart Mode**: AI-powered processing with transformers (more accurate)

### 3. Generate Dataset

Click the "Generate Dataset" button to process your text and create the labeled dataset.

### 4. Download

Once processing is complete, you can download your dataset in the selected format.

## 🧪 Example Usage

The application includes a sample text file (`sample_text.txt`) for testing purposes. This file contains information about Apple Inc. that demonstrates how the application extracts entities and labels them.

## 🛠️ API Endpoints

- `GET /` - Serve the main web interface
- `POST /generate` - Process text and return dataset file

### POST /generate Parameters

- `text_input` (form) - Text content to process
- `file_upload` (form) - Uploaded file (TXT format)
- `output_format` (form) - Output format: "csv" or "json"
- `mode` (form) - Processing mode: "fast" or "smart"

## 📊 Output Format

The generated dataset contains the following columns:

- `text`: The original sentence
- `entity`: The extracted entity
- `label`: The entity type or category

### Example Output (CSV)

```csv
text,entity,label
"Apple Inc. is an American multinational technology company headquartered in Cupertino, California.",Apple Inc.,ORG
"Apple Inc. is an American multinational technology company headquartered in Cupertino, California.",Cupertino,GPE
"Apple Inc. is an American multinational technology company headquartered in Cupertino, California.",California,GPE
"Apple Inc. is an American multinational technology company headquartered in Cupertino, California.",American,NORP
```

## 🔧 Processing Modes

### Fast Mode

- Uses spaCy for Named Entity Recognition (NER)
- Employs KeyBERT for keyword extraction
- Regex patterns for common entities (dates, emails, etc.)
- Faster processing time

### Smart Mode

- Uses Hugging Face transformers (`facebook/bart-large-mnli`) for zero-shot classification
- Combines with spaCy NER for comprehensive labeling
- Categorizes text into domains like technology, health, sports, etc.
- More accurate but slower processing

## 📁 Project Structure

```
text2dataset/
├── app.py                  # FastAPI backend
├── preprocess.py           # Text cleaning and sentence splitting
├── labeling_fast.py        # spaCy + KeyBERT processing
├── labeling_smart.py       # Transformers processing
├── exporter.py             # Format conversion
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Frontend template
├── static/
│   └── style.css           # Styling
└── outputs/                # Generated datasets (auto-created)
```

## 🐛 Troubleshooting

### Common Issues

1. **spaCy model not found**

   - Solution: Install the model using the pip command in the installation section

2. **Transformers library not installed**

   - Solution: Run `pip install transformers`

3. **Port already in use**
   - Solution: Change the port in `app.py` or stop the process using the port

### Error Handling

The application includes error handling for:

- Invalid file formats
- Empty text input
- Processing errors
- File I/O issues

## 📝 License

This project is licensed under the MIT License.

## 👥 Authors

[Your Name]
