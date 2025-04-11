FROM python:3.9-slim

WORKDIR /app

# ✅ Tambahkan libgomp1 agar PaddleOCR tidak error
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ocr_api.py .

EXPOSE 5001

CMD ["python", "ocr_api.py"]
