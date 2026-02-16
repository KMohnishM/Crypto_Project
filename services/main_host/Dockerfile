FROM python:3.10-slim

WORKDIR /app

COPY app.py .
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --default-timeout=100 --retries 5 -r requirements.txt

EXPOSE 8000

CMD ["python", "app.py"]