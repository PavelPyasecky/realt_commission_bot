FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
