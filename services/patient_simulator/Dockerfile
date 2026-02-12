FROM python:3.10-slim

WORKDIR /app

COPY generate_excel.py .
COPY send_data.py .
COPY send_data_encrypted.py .
COPY send_data_legacy.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "send_data_encrypted.py"]