#!/bin/bash
set -e
 
echo $1
if [ -z $1 ]; then
	exit 1
fi 


docker volume inspect server-log-volume &> /dev/null
if [ "$?" != "0" ]; then
	docker volume create server-log-volume
fi

docker volume inspect server-data-volume  &> /dev/null
if [ "$?" != "0" ]; then
	docker volume create server-data-volume
fi

VERSION=$1

docker run -d -p 80:8000 \
--name fileupload_service_v${VERSION} \
--env DB_PORT=5432 \
--env DB_TYPE="postgresql" \
--env DB_USER="postgres" \
--env DB_HOST="10.0.2.2" \
--env DB_PASSWORD="nopassword" \
--env DB_NAME="fileservice_db" \
-v server-log-volume:/server/logs \
-v server-data-volume:/server/data \
rgbtrend/fileuploadservice:v${VERSION} 

