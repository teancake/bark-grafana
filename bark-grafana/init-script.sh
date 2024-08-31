cd /app/bark-grafana || exit
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:3570 bark-grafana:app
