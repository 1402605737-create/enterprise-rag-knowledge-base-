FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements-light.txt .
RUN pip install --no-cache-dir -r requirements-light.txt 

COPY backend/app.py .
COPY data/ ./data/

RUN mkdir -p /tmp/uploads

EXPOSE 8000

CMD ["python", "app.py"]
