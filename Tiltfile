# point Tilt at the existing docker-compose configuration.
docker_compose('./docker-compose.yml')
docker_build('tilt.dev/hs110-exporter', '.',
  live_update=[
    sync('./hs110exporter.py', '/usr/local/bin/hs110exporter.py'),
    restart_container(),
  ]
)

