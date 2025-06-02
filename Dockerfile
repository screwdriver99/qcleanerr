FROM python:3.9-slim-buster

ENV RADARR_URL='http://127.0.0.1:7878'
ENV RADARR_API_KEY=

ENV SONARR_URL='http://127.0.0.1:8989'
ENV SONARR_API_KEY=

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
