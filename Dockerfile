# Dockerfile for manual GDAL installation

# Use the official Ubuntu base image
FROM ubuntu:20.04

# Set non-interactive frontend for installing packages
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages and dependencies for GDAL
RUN apt-get update && \
    apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:ubuntugis/ubuntugis-unstable && \
    apt-get update && \
    apt-get install -y \
    gdal-bin \
    libgdal-dev \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    && apt-get clean

# Set GDAL version environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Upgrade pip and install GDAL Python bindings
RUN pip3 install --upgrade pip && \
    pip3 install GDAL==$(gdal-config --version) && \
    pip3 install pytest

# Set the working directory
WORKDIR /app

# Copy the repository code into the container
COPY . .

# Default command to run Python inside the container
CMD ["python3"]