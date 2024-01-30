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
    libtiff5\
    libgl1-mesa-glx
COPY . /map2loop
WORKDIR /map2loop
COPY dependencies.txt dependencies.txt
RUN conda install -c conda-forge -c loop3d --file dependencies.txt
RUN conda install -c conda-forge -c loop3d LoopStructural
RUN pip install -r docs/requirements.txt
RUN pip install .

RUN pip install lavavu-osmesa==1.8.45 
ENV LD_LIBRARY_PATH=/opt/conda/lib/python3.10/site-packages/lavavu_osmesa.libs
RUN conda install -c conda-forge pydata-sphinx-theme 
RUN pip install sphinxcontrib-bibtex
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
# ENTRYPOINT ["/tini", "--"]

WORKDIR /