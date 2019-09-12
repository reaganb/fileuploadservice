#!/bin/bash

echo $1
if [ -z $1 ]; then
	exit 1
fi 

VERSION=$1

docker build -t rgbtrend/fileuploadservice:v${VERSION} --rm .
