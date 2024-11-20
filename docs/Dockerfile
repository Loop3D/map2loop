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
    python3-sphinx\
    libtinfo5\
    libtiff6\
    libgl1-mesa-glx\
    libarchive13

COPY . /map2loop 

WORKDIR /map2loop

COPY dependencies.txt dependencies.txt
COPY dependencies.txt dependenciesdocs.txt

RUN cat ./docs/requirements.txt >> dependenciesdocs.txt
RUN conda install -c conda-forge -c loop3d --file dependenciesdocs.txt -y

#temporary code  to align with fix_thicknesses branch
RUN pip uninstall loopprojectfile -y
RUN pip install git+https://github.com/loop3d/loopprojectfile.git@fix_thicknesses
####

RUN pip install .

WORKDIR /
