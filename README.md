# bark-grafana
Translate grafana webhook alert to bark messages. 

Grafana webhook alert posts JSON to the specified webhook url, yet bark only accepts a formatted url containing the title and body. For example
* Grafana webhook JSON data 
```json
{
    "receiver": "test",
    "status": "firing",
    "alerts": [
        {
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "instance": "Grafana"
            },
            "annotations": {
                "summary": "Notification test"
            },
            "startsAt": "2024-08-30T00:57:24.903808729Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "",
            "fingerprint": "57c6d9296de2ad39",
            "silenceURL": "http://localhost:3000/alerting/silence/new?alertmanager=grafana\\u0026matcher=alertname%3DTestAlert\\u0026matcher=instance%3DGrafana",
            "dashboardURL": "",
            "panelURL": "",
            "values": null
        }
    ],
    "groupLabels": {
        "alertname": "TestAlert",
        "instance": "Grafana"
    },
    "commonLabels": {
        "alertname": "TestAlert",
        "instance": "Grafana"
    },
    "commonAnnotations": {
        "summary": "Notification test"
    },
    "externalURL": "http://localhost:3000/",
    "version": "1",
    "groupKey": "test-57c6d9296de2ad39-1724979444",
    "truncatedAlerts": 0,
    "orgId": 1,
    "title": "[FIRING:1] TestAlert Grafana ",
    "state": "alerting",
    "message": "**Firing**\\n\\nValue: [no value]\\nLabels:\\n - alertname = TestAlert\\n - instance = Grafana\\nAnnotations:\\n - summary = Notification test\\nSilence: http://localhost:3000/alerting/silence/new?alertmanager=grafana\\u0026matcher=alertname%3DTestAlert\\u0026matcher=instance%3DGrafana\\n"
}
```

* Bark message 
```
http(s)://address:port/token/title/body
```

bark-grafana starts a flask service, which accepts the JSON from grafana and translates it into the url that bark requires. 

`bark-grafana.py` is the main file, it can either run in an existing environment, for example, on the machine that hosts bark. It is also possible to deploy it in docker or a k8s cluster.

When using bark-grafana, the webhook of grafana should be `http(s)://bark_grafana_address:port1/forward/bark_address:port2/bark_token`


## Run in an existing environment
```bash
gunicorn --daemon --bind 0.0.0.0:3570 webhook:app
```
Remove `--daemon` if you want gunicorn to run in foreground.

## Deploy in docker
```bash
docker build -t bark-grafana:tag .
```

## Deploy in kubernetes
`bark-grafana.yaml` specifies a start-up command for the container, waiting for the program to be copied into the pvc.
`kubectl cp` does the copying.
Then `init-script.sh` is executed in the container, which prepares the environment and starts flask service.
Note that there is no `--daemon` in the gunicorn command, because when gunicorn is put into background, the init-script finishes, and the pod enters completed state.

```bash
kubectl create namespace myspace
kubectl apply -f kubernetes/bark-grafana.yaml
pods=$(kubectl get pods -n myspace -l app=bark-grafana -o jsonpath='{.items[*].metadata.name}')
for pod in $pods; do echo $pod; kubectl cp bark-grafana $pod:/app -n myspace; done
```
If `bark-grafana.py` is updated, simply do the copy again, delete the pod. New pod will be started using the updated code. 