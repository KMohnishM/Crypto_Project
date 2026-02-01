FROM python:3.10-slim

WORKDIR /app

COPY model.py .
COPY requirements.txt .
COPY iforest_model.pkl .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 6000

CMD ["python", "model.py"]