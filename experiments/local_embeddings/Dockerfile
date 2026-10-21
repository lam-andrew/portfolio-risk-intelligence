FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./
RUN useradd --uid 10001 --create-home orbit && mkdir /models && chown orbit /models
USER orbit
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/health', timeout=2)"
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1", "--limit-concurrency", "8", "--no-access-log"]

FROM runtime AS test
COPY requirements-dev.txt .
RUN pip install --no-cache-dir --user -r requirements-dev.txt
ENV PATH="/home/orbit/.local/bin:$PATH"
COPY tests ./tests
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]
