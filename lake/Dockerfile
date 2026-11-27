# JupyterLab for Tasks 2-4: the official scipy-notebook image from Quay.io
# + Java (Spark runs on the Java virtual machine)            -> Task 4
# + dlt, PyIceberg, PySpark ... (from requirements.txt)
FROM quay.io/jupyter/scipy-notebook:latest

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
USER ${NB_UID}

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
