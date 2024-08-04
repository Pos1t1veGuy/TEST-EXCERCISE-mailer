FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/
COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x /app/entrypoint.sh

CMD python manage.py migrate && python manage.py runserver 0.0.0.0:8000