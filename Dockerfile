############################
# STEP 1 build & run interactively
############################
FROM python:3.11-slim-bullseye

# Set the appropriate env vars
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /usr/src/app
COPY . .

# Install the dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
