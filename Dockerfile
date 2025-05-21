FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

EXPOSE 8000

CMD python Melkradar/detector_scrapper/new_scrapper.py && python sql_script.py && uvicorn Server-side.main:app --host 0.0.0.0 --port 8000
