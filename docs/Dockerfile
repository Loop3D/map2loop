FROM continuumio/miniconda3
LABEL maintainer="lachlan.grose@monash.edu"
#This docker image has been adapted from the lavavu dockerfile
# install things

RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    gcc \
    g++ \
    libc-dev \
    make\
    libgl1\
    libtinfo5\
    libtiff6\
    libgl1-mesa-glx


COPY . /map2loop 

WORKDIR /map2loop

COPY dependencies.txt dependencies.txt
RUN conda install  -c conda-forge -c loop3d --file dependencies.txt -y
RUN conda install  --solver=classic -c conda-forge -c loop3d --file ./docs/requirements.txt -y

RUN pip install .

WORKDIR /