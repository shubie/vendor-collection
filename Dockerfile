FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/instance /app/uploads

EXPOSE 5000

CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "app:app"]
