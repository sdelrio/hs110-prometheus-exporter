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

# Samples

## Execute with python
```
./hs110-exporter.py -t 192.168.1.53 -f 2 -p 8110
```


## Execute with docker

```
docker run -d  --restart=always -p 8110:8110 -e HS110IP 192.168.1.111 -e FREQUENCY 15 sdelrio/hs110-exporter
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

* Requires [tilt.dev](https://docs.tilt.dev/install.html) to be installed
* Autoreload and autoupdate container when hs110-exporter.py is updated

```
tilt up
```
