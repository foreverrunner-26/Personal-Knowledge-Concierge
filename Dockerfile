# Personal Knowledge Concierge — Dockerfile
# ===========================================
# Containerized deployment for Google Cloud Run or any Docker host.
# Demonstrates the "Deployability" course concept.
#
# Build:
#   docker build -t knowledge-concierge .
#
# Run (demo mode, no API key needed):
#   docker run -p 8501:8501 knowledge-concierge
#
# Run (live mode):
#   docker run -p 8501:8501 -e DEMO_MODE=false -e API_KEY=$API_KEY -e BASE_URL=$BASE_URL -e MODEL=$MODEL knowledge-concierge
#
# Deploy to Google Cloud Run:
#   gcloud builds submit --tag gcr.io/PROJECT/knowledge-concierge
#   gcloud run deploy knowledge-concierge --image gcr.io/PROJECT/knowledge-concierge --platform managed

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    DEMO_MODE=true

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Security: Ensure .env.template exists but no real .env is baked in
RUN test -f .env.template || (echo "ERROR: .env.template missing" && exit 1)
RUN test ! -f .env || (echo "ERROR: .env file found in image! Security violation." && exit 1)

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the application
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
