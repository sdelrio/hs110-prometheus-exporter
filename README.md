![https://travis-ci.org/sdelrio/hs110-prometheus-exporter](https://travis-ci.org/sdelrio/hs110-prometheus-exporter.svg?branch=master)

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

Sample:

```
./hs110-exporter.py -t 192.168.1.53 -f 2 -p 8110
```

