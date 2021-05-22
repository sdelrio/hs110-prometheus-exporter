![Docker CI and image publish](https://github.com/sdelrio/hs110-prometheus-exporter/workflows/Docker%20CI%20and%20image%20publish/badge.svg)

# TP-Link HS110 prometheus exporter

The script will get values from the IP where HS110 is configured and export on port default 8110 for prometheus metrics.

# Usage

```
 hs110-exporter.py [-h] -t <ip> [-f <seconds>] [-p <port>]
```

- `-h` Help
- `-t` The IP address where the device HS110 is running
- `-f` Seconds to wait on each measure. Default 1 second
- `-p` port to listen (where prometheus will connect). Default port 8110
- `-l` extra label to add to prometheus exporter. Defaults to `location=home`

# Samples

## Execute with python
```
./hs110-exporter.py -t 192.168.1.53 -f 2 -p 8110
```


## Execute with docker

```
docker run -d  --restart=always -p 8110:8110 -e HS110IP=192.168.1.111 -e FREQUENCY=15 sdelrio/hs110-exporter
```

## Execute with docker-compose

```
docker-compose up -d
```

## Execute with k8s

```
apiVersion: v1
items:
- apiVersion: extensions/v1beta1
  kind: Deployment
  metadata:
    labels:
      app: hs110
    name: hs110
    namespace: monitoring
  spec:
    replicas: 1
    selector:
      matchLabels:
        app: hs110
    template:
      metadata:
        labels:
          app: hs110
      spec:
        containers:
        - env:
          - name: HS110IP
            value: 192.168.1.111
          - name: FREQUENCY
            value: "15"
          - name: LISTENPORT
            value: "8110"
          image: sdelrio/hs110-exporter
          imagePullPolicy: Always
          name: hs110
          ports:
          - containerPort: 8110
            name: web
            protocol: TCP
        restartPolicy: Always
```

## Sample screenshot on grafana

You can get the data exported to prometheus to use into grafana like this:

![](img/hs110-grafana.png?raw=true "Grafana Screenshot")

# Development environment

* Tilt
  * Autoreload and autoupdate container when hs110-exporter.py is updated
  * [tilt.dev](https://docs.tilt.dev/install.html) to be installed
* docker-compose (can also do docker-compose up without tilt.dev)
  * Grafana: <http://localhost:300> (admin/developer)
  * Prometheus: Time Database for the metrics
  * hs110sim: HS110 simulator
  * hs110-exporter: container version from your source code
)

To startup with Tilt.dev

```
tilt up
```

To startup withh docker-compose (but you will have to do the docker-compose build manually each change)

```
docker-compose up
```
