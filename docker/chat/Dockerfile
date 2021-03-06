FROM          centos:centos6
MAINTAINER    bolecki019@gmail.com

# Python dependencies and wget+tar utilities
RUN yum groupinstall "Development tools" -y && \
    yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel wget tar -y && \

    # Python and virtualenv source
    wget https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz && \
    wget https://pypi.python.org/packages/source/v/virtualenv/virtualenv-13.0.3.tar.gz#md5=cd2043ea72448d65dcc54d33744c2214 && \

    # Extract source
    tar -xzvf Python-2.7.10.tgz && \
    tar -xzvf virtualenv-13.0.3.tar.gz && \

    # Cleanup some
    rm Python-2.7.10.tgz virtualenv-13.0.3.tar.gz && \

    # Compile python
    mkdir /tmp/.localpython && \
    Python-2.7.10/configure --prefix=/tmp/.localpython && \
    make && make altinstall && \

    # Setup virtualenv (mainly for pip)
    cd virtualenv-13.0.3/ && \
    /tmp/.localpython/bin/python2.7 setup.py install && \
    mkdir /tmp/virtualenvs && \
    cd /tmp/virtualenvs && /tmp/.localpython/bin/virtualenv py2.7 --python=/tmp/.localpython/bin/python2.7 && \

    # Flask
    . /tmp/virtualenvs/py2.7/bin/activate && pip install flask gunicorn gevent redis passlib

WORKDIR /tmp/workdir/chat

EXPOSE 8012

CMD /tmp/virtualenvs/py2.7/bin/gunicorn -b 0.0.0.0:8012 --worker-class=gevent -t 99999 chat:app
