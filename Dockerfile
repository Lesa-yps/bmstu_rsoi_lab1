FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY person-service/ ./person-service/

WORKDIR /app/person-service

EXPOSE 8080

CMD ["uvicorn", "apiServer:app", "--host", "0.0.0.0", "--port", "8080"]