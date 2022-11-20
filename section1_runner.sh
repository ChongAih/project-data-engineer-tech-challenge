#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Read Docker config and export for docker-compose usage
. "$SCRIPT_DIR"/section1/conf/section1_python.ini

command="$1"

if [ "$command" = "start" ]; then

  echo && echo "==================================== BUILDING DOCKER IMAGE ====================================" && echo

  # Remove the old image
  docker image ls | grep -q "$PIPELINE_IMAGE_NAME" && docker image rm -f "$PIPELINE_IMAGE_NAME":"$PIPELINE_TAG_NAME"

  # Build a new image based on the Dockerfile
  docker build \
    --build-arg DEPLOYMENT_ENV="docker" \
    -t "$PIPELINE_IMAGE_NAME":"$PIPELINE_TAG_NAME" -f "$SCRIPT_DIR"/docker/section1_dockerfile .

  echo && echo "==================================== RUNNING DOCKER CONTAINER ====================================" && echo

  docker container run \
    -v "${PWD}"/section1:/data_pipeline/section1 \
    --rm --name "$PIPELINE_CONTAINER_NAME" -p 80:4040 -d "$PIPELINE_IMAGE_NAME":"$PIPELINE_TAG_NAME"

  # docker container exec section1_python bash -c 'python3 section1_manage.py --task-config section1_process.yaml'

elif [ "$command" = "stop" ]; then

  echo && echo "==================================== STOPPING DOCKER CONTAINER ====================================" && echo

  # docker stop and remove existing instance if any
  docker container ls -a -q --filter "name=$PIPELINE_CONTAINER_NAME" | grep -q . && docker container stop $PIPELINE_CONTAINER_NAME

else

  echo "sh section1_runner.sh <start | stop> "
  echo "<start | stop> start or stop all docker container"
  exit 1

fi
