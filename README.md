# Text2Dataset - From Raw Text to Premium Dataset

Text2Dataset is a web application that converts raw text into clean, labeled datasets for AI/ML projects. It features both Fast Mode (rule-based) and Smart Mode (AI-powered) processing with support for multiple output formats.

## Features

- **Fast Mode**: Rule-based NLP using spaCy for quick processing
- **Smart Mode**: AI-powered processing with lightweight classification
- **Multiple Formats**: Export to CSV, JSON, or spaCy format
- **Community Sharing**: Share and discover datasets with other researchers
- **Dataset History**: Keep track of previously created datasets
- **MongoDB Integration**: Online community dataset storage
- **User Authentication**: Secure login and signup system
- **Global Chat**: Community-wide discussion forum
- **Admin Features**: Admin can delete datasets and ban users from chat

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
2. Open your browser and navigate to `http://localhost:8006`

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

### Main Pages

- `GET /`: Main page
- `GET /history`: Dataset history page
- `GET /community`: Community datasets page
- `GET /global_chat_page`: Global chat page

### Authentication

- `GET /login`: Login page
- `GET /signup`: Signup page
- `POST /login`: Handle login
- `POST /signup`: Handle signup
- `GET /logout`: Logout

### Dataset Operations

- `POST /generate`: Generate dataset from text
- `GET /download/{dataset_id}`: Download a previously created dataset
- `GET /view/{dataset_id}`: View a previously created dataset
- `POST /share_dataset`: Share a dataset with the community

### Community Features

- `POST /like_dataset`: Like a community dataset
- `POST /chat/{dataset_id}`: Add chat message to dataset discussion
- `GET /chat/{dataset_id}`: Get chat messages for a dataset
- `POST /global_chat`: Add message to global chat
- `GET /global_chat`: Get global chat messages

### Admin Features

- `POST /admin/delete_dataset/{dataset_id}`: Delete a dataset (admin only)
- `POST /admin/ban_user`: Ban a user from chat (admin only)

### API Endpoints

- `GET /api/user_datasets`: Get current user's datasets
- `GET /health`: Health check endpoint

## Admin Features

The application includes special admin features that are only accessible to the user with username "admin":

1. **Delete Datasets**: Admin can delete any dataset from the community
2. **Ban Users**: Admin can ban users from both global and dataset-specific chat

To use admin features:

1. Login with username "admin" and password "password"
2. Navigate to the community page to delete datasets
3. Use the global chat to ban users

## Community Features

### Dataset Sharing

Users can share their generated datasets with the community for others to discover and download.

### Chat System

The application includes two types of chat:

1. **Dataset-specific chat**: Discussion threads attached to individual datasets
2. **Global chat**: Community-wide discussion forum

### Search and Discovery

Users can search for community datasets by:

- Keywords in dataset names or descriptions
- Tags associated with datasets

## Data Storage

The application supports two storage mechanisms:

1. **MongoDB** (Primary): For production deployments with community features
2. **File-based storage** (Fallback): For local development and testing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
