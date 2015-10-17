FROM          centos:centos6
MAINTAINER    bolecki019@gmail.com

# Compilation and wget+tar utilities
RUN yum groupinstall "Development tools" -y
RUN yum install wget tar -y

# Get redis
RUN wget http://download.redis.io/releases/redis-2.8.19.tar.gz
RUN tar xzvf redis-2.8.19.tar.gz
RUN make -C redis-2.8.19

WORKDIR /tmp/workdir

EXPOSE 6379

ENTRYPOINT ["/redis-2.8.19/src/redis-server", "/tmp/workdir/redis.conf"]
