FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
RUN apt-get update && apt-get install -y curl iputils-ping
# Запускаем FastAPI на 8000 порту
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
