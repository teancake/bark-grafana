FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH /app
CMD [ "gunicorn --daemon --bind 0.0.0.0:3570 bark-grafana:app" ]
