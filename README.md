# Text2Dataset

Convert raw text into clean, labeled datasets for AI/ML projects.

## 📝 Project Overview

Text2Dataset is a web application that transforms unstructured text into structured, labeled datasets ready for machine learning training. It helps students, researchers, startups, and AI hobbyists quickly prepare high-quality datasets without manual cleaning or labeling.

## 🎯 Features

- **Two Processing Modes**:
  - 🧩 Fast Mode: Rule-based NLP using spaCy and KeyBERT
  - 🤖 Smart Mode: AI-powered processing with transformers
- **Multiple Output Formats**: CSV, JSON
- **Simple UI**: Clean, responsive interface with progress indicators
- **File Support**: Upload TXT files or paste text directly

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip package manager

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd text2dataset
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Download spaCy language model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

### Running the Application

1. Start the server:

   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:8000`

## 🛠️ Usage

1. Paste text or upload a TXT file
2. Select output format (CSV/JSON)
3. Choose processing mode (Fast/Smart)
4. Click "Generate Dataset"
5. Download the processed dataset

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

## 🔧 Technical Details

### Fast Mode (Rule-based)

- Uses spaCy for Named Entity Recognition (NER)
- Employs KeyBERT for keyword extraction
- Regex patterns for common entities (dates, emails, etc.)

### Smart Mode (AI-powered)

- Uses Hugging Face transformers (`facebook/bart-large-mnli`) for zero-shot classification
- Combines with spaCy NER for comprehensive labeling
- Categorizes text into domains like technology, health, sports, etc.

## 📊 Example Output

**Input:**

```
India won the Cricket World Cup in 2011 under the captaincy of MS Dhoni.
```

**Output (CSV):**

```csv
text,entity,label
"India won the Cricket World Cup in 2011 under the captaincy of MS Dhoni.",India,GPE
"India won the Cricket World Cup in 2011 under the captaincy of MS Dhoni.",Cricket World Cup,EVENT
"India won the Cricket World Cup in 2011 under the captaincy of MS Dhoni.",MS Dhoni,PERSON
```

## 📦 Dependencies

- FastAPI - Web framework
- spaCy - NLP library
- KeyBERT - Keyword extraction
- transformers - AI models
- pandas - Data manipulation
- NLTK - Text processing

## 🌐 API Endpoints

- `GET /` - Serve frontend
- `POST /generate` - Process text and return dataset

## 📝 License

This project is licensed under the MIT License.

## 👥 Authors

[Your Name]

## 🙏 Acknowledgments

- spaCy for NLP capabilities
- Hugging Face for transformer models
- KeyBERT for keyword extraction
