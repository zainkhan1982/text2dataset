# Text2Dataset - From Raw Text to Premium Dataset

Text2Dataset is a web application that converts raw text into clean, labeled datasets for AI/ML projects. It features both Fast Mode (rule-based) and Smart Mode (AI-powered) processing with support for multiple output formats.

## Features

- **Fast Mode**: Rule-based NLP using spaCy for quick processing
- **Smart Mode**: AI-powered processing with lightweight classification
- **Multiple Formats**: Export to CSV, JSON, or spaCy format
- **Community Sharing**: Share and discover datasets with other researchers
- **Dataset History**: Keep track of previously created datasets
- **MongoDB Integration**: Online community dataset storage

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Download the spaCy language model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Usage

### Local Development

1. Run the application:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:8002`

### Deployment Options

#### Railway (Recommended for Free Deployment)

1. Go to [Railway.app](https://railway.app/)
2. Create an account
3. Create a new project
4. Connect your GitHub repository or upload your code
5. Set environment variables:
   - `MONGODB_URI`: `mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/`
6. Add a requirements.txt file with all dependencies
7. Set the start command to: `python app.py`

#### Heroku

1. Install Heroku CLI
2. Create a new Heroku app
3. Set environment variables:
   - `MONGODB_URI`: `mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/`
4. Deploy using `git push heroku main`

#### Render

1. Go to [render.com](https://render.com/)
2. Create a new Web Service
3. Connect your GitHub repository
4. Set environment variables:
   - `MONGODB_URI`: `mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/`
5. Set the build command: `pip install -r requirements.txt`
6. Set the start command: `python app.py`

## Environment Variables

- `MONGODB_URI`: Your MongoDB Atlas connection string (required for community features)

## Project Structure

- `app.py`: Main FastAPI application
- `preprocess.py`: Text preprocessing functions
- `labeling_fast.py`: Fast mode entity labeling
- `labeling_smart.py`: Smart mode entity labeling
- `exporter.py`: Export functions for different formats
- `dataset_history.py`: Dataset history tracking
- `community_datasets.py`: Community dataset sharing with MongoDB integration
- `templates/`: HTML templates
- `static/`: CSS and other static files
- `outputs/`: Generated dataset files

## API Endpoints

- `GET /`: Main page
- `GET /history`: Dataset history page
- `GET /community`: Community datasets page
- `POST /generate`: Generate dataset from text
- `GET /download/{dataset_id}`: Download a previously created dataset
- `POST /share_dataset`: Share a dataset with the community
- `POST /like_dataset`: Like a community dataset

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
