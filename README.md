# Flask/Redis Chat

## Info
This is a self hosted chat application utilizing the Python Flask web framework, Redis database, and server sent events.  Dockerfiles are provided for the flask application and linked redis database.  This makes it very easy to spin up new instances and give it a try!

## Setup
Just clone the repository, build docker images from the provided dockerfiles, and start em up!

```bash
# Build image for flask app
cd docker/chat
docker build -t chat/flask .

# Build image for redis
cd ../redis
docker build -t chat/redis .

# Start redis db first
docker run --name chatdb -d chat/redis

# Start flask app (make sure to substitute full path below)
docker run -d --link chatdb:db -v <full path to chat folder>:/tmp/workdir -p 8012:8012 chat/flask
```
