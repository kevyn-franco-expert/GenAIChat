# Virtual HR Assistant - ACME

This project implements a virtual assistant API for the human resources team, designed to facilitate personnel selection through CV analysis.

## Architecture

This project follows Clean Architecture principles, separating concerns into distinct layers:

- **API Layer**: Handles HTTP requests and responses
- **Service Layer**: Contains business logic
- **Infrastructure Layer**: Manages external services (S3, Bedrock, OpenAI, ChromaDB)

The application integrates with:

- **AWS Services**:
  - S3 for CV storage
  - Amazon Bedrock for generative AI
- **Local Services**:
  - ChromaDB for vector storage and retrieval

## Prerequisites

- Docker and Docker Compose
- AWS account with Amazon Bedrock access
- Configured AWS access keys

## Setup

1. Clone the repository:

   ```
   git clone
   cd cv-assistant
   ```

2. Create a `.env` file from the example:

   ```
   cp .env.example .env
   ```

3. Edit the `.env` file with your AWS credentials and desired configuration.

## Execution

Start the application with Docker Compose:

```bash
docker-compose up -d
```

The application will be available at:

- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Usage

### Upload CV

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/your/cv.pdf"
```

### Query Information

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who lives in Lima?"}'
```

### Check Available CVs

```bash
curl -X GET http://localhost:8000/cv
```

### Example Questions:

- Which candidate would you recommend for a DevOps profile?
- Who lives in Lima?
- Who knows English?
- Who has the most experience?

## Project Structure

```
cv_assistant/
│
├── app/                        # Application core
│   ├── main.py                 # Entry point
│   ├── api/                    # API layer
│   │   ├── routes/             # Route definitions
│   │   └── models/             # Pydantic models for API
│   ├── core/                   # Application core
│   │   ├── config.py           # Configuration settings
│   │   └── exceptions.py       # Custom exceptions
│   ├── services/               # Business logic
│   └── infrastructure/         # External services integration
│
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Dockerfile for the API
├── requirements.txt            # Python dependencies
```

## AWS Configuration

1. **S3 Bucket**: Create a bucket for storing CVs
2. **IAM Permissions**: Ensure your AWS credentials have access to S3 and Bedrock
3. **Bedrock Models**: Enable access to Claude and embedding models in your AWS account

## Challenges and Learnings

- Implementing proper separation of concerns in a complex application
- Integrating multiple AI services with fallback options
- Optimizing vector search for relevant results
- Building a scalable and maintainable architecture

## Scalability

- The Clean Architecture allows for easy replacement of components
- ChromaDB can scale to handle thousands of CVs
- API can be deployed behind a load balancer for higher throughput
- Service components can be extracted to microservices if needed
