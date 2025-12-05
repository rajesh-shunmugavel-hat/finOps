FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps for psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# copy files
COPY requirements.txt ./
COPY pyproject.toml ./
COPY main.py ./
COPY src ./src

# install python deps
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# healthcheck uses python to query the local /health endpoint
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD python -c "import sys,urllib.request as r; r.urlopen('http://localhost:5000/health'); sys.exit(0)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
