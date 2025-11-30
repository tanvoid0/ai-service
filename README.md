# AI Service

Flask-based microservice for AI operations with support for multiple providers (Ollama, Gemini).

## Features

- Multi-provider support (Ollama, Gemini)
- Streaming and non-streaming chat
- API key authentication
- Standalone mode (no external dependencies)

## Quick Start

```bash
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:8081 app.main:app
```

## Environment Variables

**Required for standalone mode:**
- `ENABLE_SECURITY_SERVICE=false`
- `HARDCODED_API_KEY` - Your API key (generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `GEMINI_API_KEY` - Google Gemini API key (if using Gemini)

**Optional:**
- `DEFAULT_PROVIDER` - `ollama` or `gemini` (default: `ollama`)
- `OLLAMA_BASE_URL` - Ollama server URL (default: `http://localhost:11434`)
- `FLASK_PORT` - Port number (default: `8081`, Render.com uses `PORT`)
- `ENABLE_ANONYMOUS_ACCESS` - Enable anonymous endpoints (default: `false`)

## API Endpoints

- `POST /api/v1/chat` - Non-streaming chat
- `POST /api/v1/chat/stream` - Streaming chat (SSE)
- `GET /api/v1/models` - List available models
- `GET /health` - Health check

**Authentication:** Send API key in `X-API-Key` header or `Authorization: Bearer <key>`

## Deployment

### Google Cloud Platform (Free Tier)

**Prerequisites:**
- GCP account with billing enabled (free tier credits)
- `gcloud` CLI installed: https://cloud.google.com/sdk/docs/install

**Quick Deploy:**

```bash
# 1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
# 2. Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. Deploy (uses deploy-gcp.sh script)
chmod +x deploy-gcp.sh
./deploy-gcp.sh

# 4. Set environment variables
gcloud run services update ai-service \
  --update-env-vars "HARDCODED_API_KEY=your-key,GEMINI_API_KEY=your-gemini-key"
```

**Manual Deploy:**
```bash
gcloud run deploy ai-service \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "HARDCODED_API_KEY=your-key,GEMINI_API_KEY=your-key,ENABLE_SECURITY_SERVICE=false,DEFAULT_PROVIDER=gemini"
```

**Free Tier Limits:**
- 2 million requests/month
- 360,000 GB-seconds memory
- 180,000 vCPU-seconds
- 1 GB egress/day

### Docker

```bash
docker build -t ai-service .
docker run -p 8081:8081 --env-file .env ai-service
```

## Security

- ✅ No hardcoded secrets (all use environment variables)
- ✅ API key authentication required
- ✅ Anonymous access disabled by default
- ✅ HTTPS supported (Render.com provides automatically)

**Never commit `.env` files or API keys to Git.**
