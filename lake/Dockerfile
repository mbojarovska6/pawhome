# JupyterLab for Task 2: the official scipy-notebook image from Quay.io
# plus dlt and the PostgreSQL driver (from requirements.txt).
FROM quay.io/jupyter/scipy-notebook:latest

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt