# FHIR-Lite Server

A lightweight FHIR server implementation focusing on Patient and Observation resources.

## Features

- Patient resource CRUD operations
- Observation resource CRUD operations
- RESTful API following FHIR specifications
- PostgreSQL database backend
- FastAPI framework for high performance
- SQLAlchemy ORM for database operations

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the values in `.env` with your configuration

4. Initialize the database:
```bash
alembic upgrade head
```

5. Run the server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8001/docs

## Project Structure

```
fhir-lite/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models/                 # SQLAlchemy models
│   ├── routes/                 # API endpoints
│   └── db.py                   # Database configuration
├── .env                        # Environment variables
└── requirements.txt            # Project dependencies
```

## License

MIT 