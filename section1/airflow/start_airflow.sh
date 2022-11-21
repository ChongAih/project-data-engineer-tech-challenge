#!/bin/bash

command="$1"

if [ "$command" = "start" ]; then

  docker pull puckel/docker-airflow
  docker container run -d -p 8080:8080 --rm -v "${PWD}"/dags/:/usr/local/airflow/dags --name airflow_webserver puckel/docker-airflow webserver

else

  docker container ls -a -q --filter "name=airflow_webserver" | grep -q . && docker container stop airflow_webserver

fi