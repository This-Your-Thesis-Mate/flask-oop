# SplaceClassroom-RAG

A Retrieval-Augmented Generation (RAG) system for educational content management and quiz generation. This system allows users to upload PDF documents, extract text content, and generate quizzes or chat with the documents using Azure OpenAI services.

## Features

- 📄 **PDF Document Upload & Processing**: Upload and extract text from PDF files using OCR
- 🔍 **Semantic Search**: Find relevant content using vector embeddings
- 🎯 **Quiz Generation**: Automatically generate multiple choice and essay questions
- 💬 **Chat Interface**: Ask questions about uploaded documents
- 🗃️ **Vector Database**: Store and retrieve document embeddings using PostgreSQL with pgvector
- 🐳 **Dockerized**: Easy deployment with Docker and Docker Compose

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with pgvector extension
- **AI Services**: Azure OpenAI (GPT-4o, Text Embedding)
- **OCR**: Tesseract OCR, pytesseract
- **Text Processing**: Semantic Text Splitter, Hugging Face Tokenizers
- **Containerization**: Docker, Docker Compose

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL with pgvector extension
- Azure OpenAI API access
- Tesseract OCR

## Installation

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SplaceClassroom-RAG-master/SplaceClassroom-RAG-master - Azure
   ```

2. **Configure environment variables**
   
   Update the Azure OpenAI credentials in `app.py`:
   ```python
   # Update these with your Azure OpenAI credentials
   url = "https://your-resource.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15"
   headers = {
     'Content-Type': 'application/json',
     'api-key': 'your-api-key'
   }
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   The database will be automatically initialized with the pgvector extension and required tables.

### Manual Installation

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Tesseract OCR**
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`

3. **Setup PostgreSQL with pgvector**
   ```bash
   # Install PostgreSQL and pgvector extension
   # Run the init_pgvector.sql script to initialize the database
   ```

4. **Configure database connection**
   Update database credentials in `app.py`:
   ```python
   host = "localhost"
   dbname = "vectors"
   user = "postgres"
   password = "your-password"
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

## API Endpoints

### 1. Upload Document
**POST** `/uploads`

Upload a PDF file and extract text content for processing.

**Form Data:**
- `file`: PDF file
- `course_id`: Course identifier
- `module_id`: Module identifier

**Response:**
```json
{
  "course_id": "123",
  "file": "document.pdf"
}
```

### 2. Generate Quiz
**POST** `/quiz`

Generate quiz questions based on uploaded documents.

**JSON Body:**
```json
{
  "threshold": 0.7,
  "limit": 5,
  "query": "machine learning concepts",
  "course_id": "123",
  "module_id": "456",
  "question_type": "Choice, Multiple, Essay",
  "number_of_question": "3, 2, 1"
}
```

**Response:**
```json
{
  "parsed": [
    {
      "title": "What is machine learning?",
      "choices": ["a. Option A", "b. Option B", "c. Option C", "d. Option D"],
      "type": "Choice",
      "answer": ["a. Option A"]
    }
  ],
  "original": "Multiple Choice with One Answer:\n..."
}
```

### 3. Chat with Documents
**POST** `/chat`

Ask questions about uploaded documents and get AI-powered responses.

**JSON Body:**
```json
{
  "threshold": 0.4,
  "limit": 5,
  "course_id": "123",
  "prompt": "Explain the concept of neural networks",
  "messages": []
}
```

**Response:**
```json
{
  "message": "Neural networks are...",
  "module_ids": ["456", "789"]
}
```

### 4. Delete Module
**DELETE** `/delete`

Remove a module and its associated data.

**JSON Body:**
```json
{
  "module_id": "456",
  "course_id": "123"
}
```

## Database Schema

The system uses PostgreSQL with the following main tables:

- **modules**: Store module information
- **chunks**: Store text chunks from documents
- **tbl_vector**: Store vector embeddings with pgvector

## Configuration

### Azure OpenAI Setup

1. Create an Azure OpenAI resource
2. Deploy the required models:
   - `text-embedding-3-large` for embeddings
   - `gpt-4o-mini` for chat and quiz generation
3. Update the API keys and endpoints in `app.py`

### Database Configuration

The system expects a PostgreSQL database with pgvector extension. Update the connection parameters in `app.py`:

```python
host = "your-host"
dbname = "your-database"
user = "your-username"
password = "your-password"
```

## Usage Examples

### Upload a Document
```bash
curl -X POST http://localhost:5000/uploads \
  -F "file=@document.pdf" \
  -F "course_id=123" \
  -F "module_id=456"
```

### Generate Quiz Questions
```bash
curl -X POST http://localhost:5000/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 0.7,
    "limit": 5,
    "query": "machine learning",
    "course_id": "123",
    "module_id": "456",
    "question_type": "Choice, Essay",
    "number_of_question": "3, 2"
  }'
```

### Chat with Documents
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "123",
    "prompt": "What is supervised learning?",
    "threshold": 0.4,
    "limit": 5
  }'
```

## Development

### Project Structure
```
├── app.py                 # Main Flask application
├── prompt.py             # Quiz generation prompts
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yaml  # Docker Compose setup
├── init_pgvector.sql    # Database initialization
└── README.md           # This file
```

### Running in Development Mode

1. Set Flask environment variables:
   ```bash
   export FLASK_ENV=development
   export FLASK_DEBUG=1
   ```

2. Run the application:
   ```bash
   python app.py
   ```

The application will run on `http://localhost:5000` with debug mode enabled.

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract OCR is installed and in your system PATH
   - On Windows, you may need to specify the tesseract path

2. **Database connection errors**
   - Verify PostgreSQL is running and accessible
   - Check database credentials and connection string
   - Ensure pgvector extension is installed

3. **Azure OpenAI API errors**
   - Verify API keys and endpoints are correct
   - Check Azure OpenAI service quotas and limits
   - Ensure the required model deployments exist

### Logging

The application includes basic logging. Check the console output for error messages and debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team.
