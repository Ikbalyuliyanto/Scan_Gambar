FROM python:3.9-buster

WORKDIR /app

ENV FLAGS_use_mkldnn=false
ENV FLAGS_enable_mkldnn=0

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ocr_api.py .
COPY uploads ./uploads

EXPOSE 8080
CMD ["python", "ocr_api.py"]
