# Environment Variables

This document describes the environment variables used in the Text2Dataset application.

## Required Environment Variables

### MongoDB Configuration

- `MONGODB_URI` - MongoDB connection string with credentials

  - Default: `mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/`
  - Format: `mongodb+srv://username:password@host/database`

- `MONGODB_DATABASE` - MongoDB database name
  - Default: `text2dataset`

### Server Configuration

- `HOST` - Host address for the server

  - Default: `0.0.0.0`

- `PORT` - Port number for the server
  - Default: `8003`

### Application Configuration

- `SECRET_KEY` - Secret key for the application

  - Default: `your-secret-key-here-change-in-production`
  - Note: Change this in production environments

- `DEBUG` - Debug mode flag

  - Default: `True`
  - Set to `False` in production

- `APP_NAME` - Application name
  - Default: `Text2Dataset`

## Setting Environment Variables

### Using the .env file

The application will automatically load environment variables from the `.env` file in the project root directory.

### Manual setting

You can also set environment variables manually:

#### On Windows (Command Prompt):

```cmd
set MONGODB_URI=mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/
set PORT=8003
python app.py
```

#### On Windows (PowerShell):

```powershell
$env:MONGODB_URI="mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/"
$env:PORT=8003
python app.py
```

#### On Linux/macOS:

```bash
export MONGODB_URI="mongodb+srv://Zain_admin:2ea898dxeI%40@cluster0.flv8jkk.mongodb.net/"
export PORT=8003
python app.py
```

## Security Recommendations

1. **Change the SECRET_KEY** in production environments
2. **Use different MongoDB credentials** for production
3. **Don't commit the .env file** to version control (it's already in .gitignore)
4. **Use environment-specific .env files** for different environments:
   - `.env.development`
   - `.env.production`
   - `.env.testing`

## Installation

To use environment variables, install the required package:

```bash
pip install python-dotenv
```

The application will automatically load the `.env` file when started.
