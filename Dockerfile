FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/ data/
COPY config.yaml .

RUN mkdir -p logs

CMD ["python", "src/pipeline.py", "--config", "config.yaml"]
