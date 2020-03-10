FROM resin/raspberry-pi-python:3
LABEL maintainer "Philipp Schmitt <philipp@schmitt.co>"
RUN READTHEDOCS=True pip install picamera


RUN [ "cross-build-start" ]
# to stop complaints about picam
ENV READTHEDOCS True
ENV INITSYSTEM off
RUN apt-get update && apt-get install -y \
        python-pip \
	&& rm -rf /var/lib/apt/lists/*
RUN apt-get install python3-pip
COPY requirements.txt requirements.txt
COPY src src
COPY setup.py setup.py
COPY model.model model.model
COPY README.md README.md
RUN pip3 install -r requirements.txt.
RUN pip3 install .
ENTRYPOINT ["cameraai","to_http"]

