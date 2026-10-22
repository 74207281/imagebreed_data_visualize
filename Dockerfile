# syntax=docker/dockerfile:1

# 1. Base Python image (slim for reduced image size)
FROM python:3.12-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# 3. Set working directory
WORKDIR /app

# 4. Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Create a non-privileged user for security
RUN useradd -m -u 1000 appuser

# 6. Install Python dependencies (leverage Docker build cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copy project files
COPY . .

# 8. Ensure non-root user has write permissions (needed for CSV file uploads)
RUN chown -R appuser:appuser /app

# 9. Switch to non-root user
USER appuser

# 10. Expose application port
EXPOSE 8000

# 11. Health check to monitor server responsiveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/plot/info || exit 1

# 12. Run the FastAPI application using uvicorn binding to 0.0.0.0
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
