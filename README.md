# Volt

A smart finance and expense tracker that helps you manage your finances with intelligent insights and comprehensive tracking capabilities.

## Features

- **Expense Tracking**: Track your daily expenses with ease and categorize them for better organization
- **Intelligent Insights**: Get AI-powered insights into your spending patterns and financial habits
- **Smart Analytics**: Visualize your financial data with charts and reports
- **Budget Management**: Set and monitor budgets across different categories
- **Multi-platform Support**: Available on mobile and web platforms

## Tech Stack

### Mobile
- **Flutter**: Cross-platform mobile framework for iOS and Android

### Backend
- **FastAPI**: Modern, high-performance Python web framework
- **Pydantic AI**: AI-powered data validation and intelligent analysis
- **PostgreSQL**: Robust relational database for data persistence
- **Supabase**: Backend-as-a-Service for authentication and real-time features
- **SQLAlchemy**: SQL toolkit and ORM

### Additional Tools
- **Uvicorn**: ASGI server for running FastAPI
- **JWT**: Secure token-based authentication
- **Docker**: Containerization for consistent development and deployment environments

## Project Structure

```
volt/
├── mobile/                 # Flutter mobile application
│   ├── lib/               # Dart source code
│   ├── android/           # Android-specific files
│   ├── ios/               # iOS-specific files
│   └── pubspec.yaml       # Flutter dependencies
│
├── server/                # FastAPI backend server
│   ├── app/
│   │   ├── main.py       # Application entry point
│   │   ├── config.py     # Configuration management
│   │   ├── database.py   # Database setup and connection
│   │   ├── oauth2.py     # Authentication logic
│   │   ├── models/       # SQLAlchemy database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── routers/      # API route handlers
│   ├── run.py            # Server startup script
│   └── requirements.txt  # Python dependencies
│
└── README.md             # This file
```

## Getting Started

### Prerequisites

- Flutter SDK (latest stable version)
- Python 3.8 or higher
- PostgreSQL
- Git

### Backend Setup

1. Navigate to the server directory:
   ```bash
   cd server
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

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the database URL and secret key

5. Run the server:
   ```bash
   python run.py
   ```

   The API will be available at `http://localhost:8000`

### Docker Setup

You can run the application using Docker for a consistent environment:

1. Ensure Docker and Docker Compose are installed on your system

2. From the server directory, build and run the containers:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Start the FastAPI backend server
   - Start the PostgreSQL database
   - Run database migrations
   - Expose the API at `http://localhost:8000`

3. To stop the containers:
   ```bash
   docker-compose down
   ```

### Mobile Setup

1. Navigate to the mobile directory:
   ```bash
   cd mobile
   ```

2. Install dependencies:
   ```bash
   flutter pub get
   ```

3. Run the application:
   ```bash
   flutter run
   ```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Backend Development

The backend follows a modular structure:
- **Models**: Define database schema using SQLAlchemy
- **Schemas**: Define request/response models using Pydantic
- **Routers**: Handle API endpoints and business logic
- **Authentication**: JWT-based authentication system

### Mobile Development

The mobile app is built with Flutter and follows clean architecture principles.

## Documentation

### Mobile UI/UX
- **UI/UX Planning**: `mobile/docs/UI_UX_PLAN.md`
