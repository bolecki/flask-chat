# Flask/Redis Chat

## Info
This is a self hosted chat application utilizing the Python Flask web framework, Redis database, and server sent events.  Dockerfiles are provided for the flask application and linked redis database.  This makes it very easy to spin up new instances and give it a try!

# Setup

## Clone and Generate Key
These steps will clone the repository and generate a secret key for our app.

```bash
# Clone the repo
git clone https://github.com/bolecki/flask-chat.git

# Change directory into the repo
cd flask-chat/

# Generate a secret key
python -c 'import os; print os.urandom(24).encode("hex")'

# Use the output to create the secret key file
echo "key = '7268076c403361ebf9b835d34f0ecd72d139eeb884db2702'" > chat/secret_key.py
```

## Install Requirements
If you want to run this application in Docker, skip to the docker section below!

This app requires a **Redis** database.  Installation instructions for Redis can be found here: http://redis.io/download.  A simple configuration file for Redis is located in the database folder of this repository.  Modify the 'dbfilename' and 'dir' in redis.conf as needed in order to save the database to disk.

This command will install all of the python requirements.

```bash
pip install -r requirements
```

## Run the App
Start Redis in the background and run the app!

```bash
# Start redis with your path and config file
nohup /<path-to-redis>/src/redis-server /<path-to-config>/redis.conf &

# Start the app
cd <path-to-repo>/chat
<path-to-gunicorn>/gunicorn -b 0.0.0.0:8012 --worker-class=gevent -t 99999 chat:app
```

## Docker

```bash
# Build image for flask app
docker build -t chat/flask docker/chat/

# Build image for redis
docker build -t chat/redis docker/redis/

# Start redis db first (make sure to substitute full path below)
docker run --name chatdb -d -v <full path to repo/database>:/tmp/workdir chat/redis

# Start flask app (make sure to substitute full path below)
docker run -d --link chatdb:db -v <full path to repo>:/tmp/workdir -p 8012:8012 chat/flask
```

# TODO
1. HTTPS
2. Move more formatting to stylesheets
3. Redesign UI
