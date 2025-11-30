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

### Render.com

1. Connect your Git repository
2. Set environment variables in Render dashboard:
   - `HARDCODED_API_KEY` (required)
   - `GEMINI_API_KEY` (required for Gemini)
   - `ENABLE_SECURITY_SERVICE=false`
   - `DEFAULT_PROVIDER=gemini`
3. Deploy (uses `render.yaml`)

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
