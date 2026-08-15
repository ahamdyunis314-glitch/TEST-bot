FROM python:3.10-slim

# دابەزاندنی Poppler کە بۆ pdf2image پێویستە
RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# بەگەڕخستنی bot.py
CMD ["python", "bot.py"]
