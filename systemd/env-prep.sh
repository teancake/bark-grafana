apt install python3 python3-flask python3-gunicorn python3-requests gunicorn python3-loguru python3-cachetools

# create file /etc/systemd/system/bark-server.service, note the path /root need to be changed.

systemctl enable bark-server.service
systemctl start bark-server.service
