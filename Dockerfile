FROM ubuntu:14.04

# Install Forseti dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libmysqlclient-dev \
    python-pip \
    python-dev \
    unzip \
    wget \
  && rm -rf /var/lib/apt/lists/*

# Install gcloud
RUN curl https://sdk.cloud.google.com | bash

# Install cloud_sql_proxy
RUN wget -qO- -O cloud_sql_proxy \
    https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 && \
    chmod +x cloud_sql_proxy && \
    mv cloud_sql_proxy /usr/local/bin/cloud_sql_proxy

# Get Forseti source code
RUN git clone https://github.com/GoogleCloudPlatform/forseti-security

# Install protoc
RUN wget -qO- -O protoc.zip \
    $(cat /forseti-security/data/protoc_url.txt) && \
    unzip protoc.zip && \
    cp bin/protoc /usr/local/bin

WORKDIR /forseti-security

CMD ["python", "setup.py", "install"]
