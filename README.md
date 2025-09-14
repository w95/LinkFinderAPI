# LinkFinderAPI

## About LinkFinderAPI

LinkFinderAPI is a FastAPI-based web service that discovers endpoints and their parameters in JavaScript files. This tool helps penetration testers and bug hunters gather new, hidden endpoints on the websites they are testing, resulting in new testing ground that may contain vulnerabilities. 

The service uses [jsbeautifier](https://github.com/beautify-web/js-beautify) for Python in combination with a comprehensive regular expression. The regex consists of four patterns responsible for finding:

- Full URLs (`https://example.com/*`)
- Absolute URLs or dotted URLs (`/\*` or `../*`)
- Relative URLs with at least one slash (`text/test.php`)
- Relative URLs without a slash (`test.php`)

**Key Features:**
- 🚀 **REST API**: Web service interface for easy integration
- 📝 **Text Input**: Accepts JavaScript content directly as text
- 🔍 **Flexible Filtering**: Regex-based endpoint filtering
- 📊 **JSON Output**: Structured response with endpoints and context
- 🐳 **Docker Ready**: Containerized deployment with Docker Compose
- 📚 **Auto Documentation**: Interactive API docs at `/docs`

## Installation

LinkFinderAPI requires **Python 3.10+**.

### Option 1: Local Installation
```bash
git clone https://github.com/w05/LinkFinderAPI.git
cd LinkFinderAPI
pip3.10 install -r requirements.txt
```

### Option 2: Docker (Recommended)
```bash
git clone https://github.com/w05/LinkFinderAPI.git
cd LinkFinderAPI
docker-compose up --build
```

## Dependencies

The FastAPI version depends on:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `jsbeautifier` - JavaScript beautification
- `pydantic` - Data validation (included with FastAPI)

Install dependencies:
```bash
pip3.10 install -r requirements.txt
```

## Usage

### Starting the API

**Local Development:**
```bash
python3.10 api.py
# or
uvicorn api:app --reload --host 0.0.0.0 --port 9402
```

**Docker:**
```bash
docker-compose up
```

The API will be available at: `http://localhost:9402`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and available endpoints |
| `/analyze` | POST | Analyze JavaScript content for endpoints |
| `/health` | GET | Health check endpoint |
| `/docs` | GET | Interactive API documentation |
| `/redoc` | GET | ReDoc API documentation |

### API Usage Examples

**Basic Analysis:**
```bash
curl -X POST "http://localhost:9402/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "content": "var api = \"/api/users\"; fetch(\"https://example.com/data.json\");",
       "include_context": true,
       "remove_duplicates": true
     }'
```

**With Regex Filter:**
```bash
curl -X POST "http://localhost:9402/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "content": "var endpoint = \"/api/users\"; var file = \"config.php\";",
       "filter_regex": "^/api/",
       "include_context": false
     }'
```

**Python Example:**
```python
import requests
import json

response = requests.post(
    "http://localhost:9402/analyze",
    headers={"Content-Type": "application/json"},
    data=json.dumps({
        "content": "var apiUrl = '/api/v1/users'; fetch('data.json');",
        "include_context": True,
        "filter_regex": "^/api/",
        "remove_duplicates": True
    })
)

result = response.json()
print(f"Found {result['total_count']} endpoints:")
for endpoint in result['endpoints']:
    print(f"- {endpoint['link']}")
```

## Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start the service
docker-compose up --build

# Run in background
docker-compose up -d

# Stop the service
docker-compose down
```

### Manual Docker Build
```bash
# Build the image
docker build -t linkfinder-api .

# Run the container
docker run -p 9402:9402 linkfinder-api
```

The API will be available at `http://localhost:9402`

## Request/Response Format

### Request Body
```json
{
  "content": "JavaScript content as string",
  "include_context": true,
  "filter_regex": "^/api/",
  "remove_duplicates": true
}
```

### Response Format
```json
{
  "endpoints": [
    {
      "link": "/api/users",
      "context": "var api = '/api/users';"
    }
  ],
  "total_count": 1
}
```

## Features

- **Text Input**: No file uploads needed - send JavaScript content directly
- **Context Extraction**: Optional surrounding code context for each endpoint
- **Regex Filtering**: Filter results with custom regex patterns
- **Duplicate Removal**: Automatically remove duplicate endpoints
- **Health Checks**: Built-in health monitoring for production deployments
- **Auto Documentation**: Interactive API docs at `/docs`
- **Docker Ready**: Production-ready containerization

## Migration from CLI Version

This FastAPI version replaces the original CLI tool with a web service. Key differences:

| Feature | CLI Version | FastAPI Version |
|---------|-------------|-----------------|
| Input | Files, URLs, Burp exports | Text content via API |
| Output | HTML files, CLI | JSON response |
| Usage | Command line | REST API |
| Integration | Standalone | Web service |
| Deployment | Local execution | Containerized service |
