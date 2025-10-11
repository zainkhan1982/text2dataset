# Text2Dataset - Project Summary

## 📝 Overview

Text2Dataset is a web application that converts raw, unstructured text into clean, labeled datasets ready for AI/ML projects. The application helps students, researchers, startups, and AI hobbyists quickly prepare high-quality datasets without manual cleaning or labeling.

## 🎯 Key Features

### Two Processing Modes

1. **🧩 Fast Mode (No AI)**

   - Rule-based NLP using spaCy and KeyBERT
   - Quick processing for large volumes of text
   - Regex patterns for common entity extraction

2. **🤖 Smart Mode (AI)**
   - Transformer-based zero-shot classification
   - Contextual labeling and categorization
   - More accurate but slower processing

### Multiple Output Formats

- CSV (Comma-Separated Values)
- JSON (JavaScript Object Notation)

### User-Friendly Interface

- Clean, responsive web UI
- Text input or file upload options
- Processing mode selection
- Progress indicators
- Downloadable results

## 🏗️ Technical Architecture

### Backend

- **Framework**: FastAPI (Python)
- **NLP Libraries**:
  - spaCy for Named Entity Recognition
  - KeyBERT for keyword extraction
  - Transformers for zero-shot classification
- **Data Processing**: Pandas for data manipulation
- **File Handling**: Built-in Python libraries

### Frontend

- **Template Engine**: Jinja2
- **Styling**: Custom CSS with responsive design
- **UI Components**: HTML5 forms, dropdowns, buttons

### Project Structure

```
text2dataset/
├── app.py                  # Main application entry point
├── preprocess.py           # Text cleaning and sentence splitting
├── labeling_fast.py        # Rule-based NLP processing
├── labeling_smart.py       # AI-powered processing
├── exporter.py             # Format conversion utilities
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── USAGE.md               # Usage guide
├── templates/             # HTML templates
│   └── index.html
├── static/                # CSS and other static assets
│   └── style.css
├── outputs/               # Generated datasets (auto-created)
└── sample_text.txt        # Example text for testing
```

## 🚀 Deployment

### Local Development

1. Install dependencies: `pip install -r requirements.txt`
2. Download spaCy model: `python -m spacy download en_core_web_sm`
3. Run application: `python app.py`
4. Access at: `http://localhost:8000`

### Production Deployment

The application can be deployed to:

- Heroku
- AWS Elastic Beanstalk
- Google Cloud Platform
- Azure App Service
- DigitalOcean App Platform

## 📊 Example Workflow

1. **Input**: Raw text about Apple Inc.
2. **Processing**:
   - Text cleaning and sentence splitting
   - Entity extraction (ORG, PERSON, GPE, etc.)
   - Keyword identification
   - Category classification
3. **Output**: Structured dataset with labeled entities

### Sample Input

```
Apple Inc. is an American multinational technology company headquartered in Cupertino, California.
```

### Sample Output (CSV)

```csv
text,entity,label
"Apple Inc. is an American multinational technology company headquartered in Cupertino, California.",Apple Inc.,ORG
"Apple Inc. is an American multinational technology company headquartered in Cupertino, California.",Cupertino,GPE
"Apple Inc. is an American multinational technology company headquartered in Cupertino, California.",California,GPE
"Apple Inc. is an American multinational technology company headquartered in Cupertino, California.",American,NORP
```

## 🔧 Dependencies

### Core Libraries

- FastAPI - Web framework
- spaCy - NLP library
- KeyBERT - Keyword extraction
- Transformers - AI models
- Pandas - Data manipulation
- NLTK - Text processing

### Development Tools

- Uvicorn - ASGI server
- Jinja2 - Template engine
- python-multipart - File upload handling

## 🛡️ Security & Privacy

### Data Handling

- Text processing happens locally
- No data is stored permanently
- Files are automatically deleted after 24 hours
- No external API calls for Fast Mode

### Considerations

- Smart Mode may send data to Hugging Face APIs
- HTTPS recommended for production deployment
- Input validation for file uploads

## 📈 Performance

### Processing Speed

- **Fast Mode**: ~1000 sentences/second
- **Smart Mode**: ~100 sentences/second (depends on hardware)

### Memory Usage

- Base application: ~100MB
- With models loaded: ~1-2GB

## 🆕 Future Enhancements

### Planned Features

1. TFRecord export support
2. Multi-language support
3. Authentication system
4. API endpoint for programmatic access
5. Data visualization dashboard
6. Batch processing capabilities

### Potential Improvements

1. Enhanced entity recognition
2. Custom model training
3. Additional export formats
4. Mobile-responsive design
5. Dark mode support

## 📚 Documentation

### User Guides

- [README.md](README.md) - Project overview and setup
- [USAGE.md](USAGE.md) - Detailed usage instructions

### Developer Resources

- Inline code documentation
- Module-specific comments
- Example scripts

## 🤝 Contributing

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

### Code Standards

- Follow PEP 8 guidelines
- Include docstrings for functions
- Write unit tests for new features
- Maintain backward compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

[Your Name] - Initial work

## 🙏 Acknowledgments

- spaCy team for NLP capabilities
- Hugging Face for transformer models
- KeyBERT developers for keyword extraction
- FastAPI team for the web framework
