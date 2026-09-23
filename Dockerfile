FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    sqlmap \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/outputs

EXPOSE 8080

CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8080"]