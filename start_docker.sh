set -e
IMAGE=$(docker ps -aq --filter ancestor="constellation" )
if [ "$IMAGE" ]
then
	echo "FOUND"
	docker stop $IMAGE
	docker rm $IMAGE
fi

docker build -t constellation .
# docker run  -d --restart unless-stopped -p 5000:5000 constellation
docker run -p 5000:5000 constellation
