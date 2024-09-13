# Use the official Python image as a parent image
FROM python:3

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./requirements.txt /app/requirements.txt

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 6000 available to the world outside this container
EXPOSE 6000

# Define environment variable
ENV FLASK_APP=app.py

# This CMD instruction sets the command that will be executed when the Docker container starts.
# It runs the Gunicorn web server with the following configuration:
# -b 0.0.0.0:6000 binds the server to all network interfaces on port 6000
# app:app specifies the Flask application to run (in this case, the file app.py)
CMD ["gunicorn", "-b", "0.0.0.0:6000", "app:app"]
