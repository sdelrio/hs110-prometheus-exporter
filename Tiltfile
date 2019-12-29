# point Tilt at the existing docker-compose configuration.
docker_compose('./docker-compose.yml')

docker_build('tilt.dev/hs110-exporter', '.',
  live_update=[
    sync('./hs110exporter.py', '/usr/local/bin/hs110exporter.py'),
    restart_container(),
  ],
  only=['./hs110exporter.py', './entrypoint.sh', './requirements.txt']
)
# https://docs.tilt.dev/file_changes.html

docker_build('tilt.dev/prometheus', './prometheus',
  live_update=[
    sync('./prometheus/prometheus.yml', '/etc/prometheus/prometheus.yml'),
    restart_container(),
  ],
  only=['./prometheus.yml']
)

docker_build('tilt.dev/grafana', './grafana',
  live_update=[
    sync('./grafana/provisioning/', '/etc/grafana/provisioning/'),
    restart_container(),
  ],
  only=['./provisioning/']
)

