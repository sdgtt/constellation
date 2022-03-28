set -e
CONTAINER=$(docker ps -a --filter ancestor="constellation" --format "{{.ID}}")
IMAGE=$(docker ps -a --filter ancestor="constellation" --format "{{.Image}}")
if [ "$CONTAINER" ]
then
	echo "FOUND"
	docker stop $CONTAINER
	docker rm $CONTAINER
	docker image rm $IMAGE
fi

docker build -t constellation .
# docker run  -d --restart unless-stopped -p 5000:5000 constellation
docker run -d --restart unless-stopped -p 5000:5000 constellation --env GH_TOKEN=$GH_TOKEN
