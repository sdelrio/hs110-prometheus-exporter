#!/usr/bin/env bash

echo Checking env DOCKER_USERNAME defined
[ -z $DOCKER_USERNAME ] && exit 1
echo Checking env DOCKER_PASSWORD defined
[ -z $DOCKER_PASSWORD ] && exit 2

ORGANIZATION="sdelrio"
IMAGE="hs110-exporter"
KEEP=4
login_data() {
cat <<EOF
{
  "username": "$DOCKER_USERNAME",
  "password": "$DOCKER_PASSWORD"
}
EOF
}

# Get Dockertoken for API usage

DOCKER_TOKEN=`curl -s -H "Content-Type: application/json" -X POST -d "$(login_data)" "https://hub.docker.com/v2/users/login/" | jq -r .token`

# List last 100 images, get tags with 40 hex values and keep the 4 most recent

curl -s "https://hub.docker.com/v2/repositories/${ORGANIZATION}/${IMAGE}/tags/?page_size=100" \
-X GET \
-H "Authorization: JWT ${DOCKER_TOKEN}" \
    | jq -r '.results|.[]|.name' | egrep "[0-f]{7}" \
    | tail -n +${KEEP} \
    | xargs -L1 -I {} \
    | curl "https://hub.docker.com/v2/repositories/${ORGANIZATION}/${IMAGE}/tags/{}/" \
        -X DELETE \
        -H "Authorization: JWT ${DOCKER_TOKEN}"

