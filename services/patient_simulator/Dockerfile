FROM python:3.10-slim

WORKDIR /app

COPY generate_excel.py .
COPY send_data.py .
COPY requirements.txt .

RUN pip install requests pandas openpyxl 

CMD ["python", "send_data.py"]