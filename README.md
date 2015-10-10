# Flask/Redis Chat

## Info
This is a self hosted chat application utilizing the Python Flask web framework, Redis database, and server sent events.  Dockerfiles are provided for the flask application and linked redis database.  This makes it very easy to spin up new instances and give it a try!

## Setup
Just clone the repository, create a secret_key.py file, build docker images from the provided dockerfiles, and start em up!

```bash
# Clone the repo
git clone https://github.com/bolecki/flask-chat.git

# Change directory into the repo
cd flask-chat/

# Generate a secret key
python -c 'import os; print os.urandom(24).encode("hex")'

# Use the output to create the secret key file
echo "key = '7268076c403361ebf9b835d34f0ecd72d139eeb884db2702'" > chat/secret_key.py

# Build image for flask app
docker build -t chat/flask docker/chat/

# Build image for redis
docker build -t chat/redis docker/redis/

# Start redis db first
docker run --name chatdb -d chat/redis

# Start flask app (make sure to substitute full path below)
docker run -d --link chatdb:db -v <full path to repo>:/tmp/workdir -p 8012:8012 chat/flask
```

# TODO
1. HTTPS
2. Move more formatting to stylesheets
3. Redesign UI
