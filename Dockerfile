FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp/ ./mcp/
COPY db/ ./db/

ENV MAX_TIER=3
EXPOSE 8000

CMD ["python", "mcp/server_postgres.py"]
