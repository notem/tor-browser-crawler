# This dockerfile allows to run an crawl inside a docker container

# Pull base image.
#FROM debian:stable-slim
FROM python:2.7

# Install required packages.
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get --assume-yes --yes install sudo build-essential autoconf git zip unzip xz-utils
RUN DEBIAN_FRONTEND=noninteractive apt-get --assume-yes --yes install libtool libevent-dev libssl-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get --assume-yes --yes install python python-dev python-setuptools python-pip
RUN DEBIAN_FRONTEND=noninteractive apt-get --assume-yes --yes install net-tools ethtool tshark libpcap-dev iw tcpdump
RUN DEBIAN_FRONTEND=noninteractive apt-get --assume-yes --yes install xvfb firefox-esr
RUN apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

# Install python requirements.
RUN pip install --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# add host user to container
RUN adduser --system --group --disabled-password --gecos '' --shell /bin/bash docker

# download geckodriver
ADD https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz /bin/
RUN tar -zxvf /bin/geckodriver* -C /bin/
ENV PATH /bin/geckodriver:$PATH

# add setup.py
RUN git clone https://gist.github.com/notem/4242fe5c7f8dd6c443cab3d4ca38b85b.git /home/docker/tbb_setup
RUN python /home/docker/tbb_setup/setup.py 8.0.2

# Set the display
ENV DISPLAY $DISPLAY
