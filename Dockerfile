
# UBUNTU 20.04
#
FROM ubuntu:20.04
MAINTAINER Gregor von Laszewski <laszewski@gmail.com>


ENV DEBIAN_FRONTEND noninteractive

#
# UPDATE THE SYSTEM
#
RUN apt-get -y update
RUN apt-get -y dist-upgrade
RUN apt-get install -y --no-install-recommends apt-utils

#
# SYSTEM TOOLS
#
RUN apt-get install -y \
    git \
    git-core \
    wget \
    curl \
    rsync \
    emacs-nox

#
# DEVELOPMENT TOOLS
#
RUN apt-get install -y build-essential checkinstall --fix-missing
RUN apt-get install -y \
    lsb-core \
    dnsutils \
    libssl-dev \
    libffi-dev \
    libreadline-gplv2-dev \
    libncursesw5-dev \
    libsqlite3-dev \
    libgdbm-dev \
    libc6-dev \
    libbz2-dev \
    libffi-dev \
    zlib1g-dev

#
# INSTALL PYTHON 3.10 FROM SOURCE
#
WORKDIR /usr/src
ENV PYTHON_VERSION=3.10.5

RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz
RUN tar xzf Python-${PYTHON_VERSION}.tgz
WORKDIR /usr/src/Python-${PYTHON_VERSION}
RUN ./configure --enable-optimizations
RUN make -j8 build_all
RUN make -j8 altinstall
RUN update-alternatives --install /usr/bin/python python /usr/local/bin/python3.10 20
RUN update-alternatives --config python
RUN update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3.10 20
RUN update-alternatives --config pip
RUN yes '' | update-alternatives --force --all
ENV PATH="/usr/bin:/usr/local/bin:${PATH}"

WORKDIR /usr/local/code

#
# CHECK
#
RUN python --version
RUN pip install -U pip
RUN pip --version
RUN pandoc --version

WORKDIR ~

# TODO add publich private key .ssh dir to image not COPY! with -v
pip install cloudmesh-installer -U
cloudmesh-installer -ssh get cmd5


ENTRYPOINT ["cms"]

WORKDIR /data

