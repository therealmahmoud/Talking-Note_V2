# Use the official Python image as a parent image
FROM python:3

# Install necessary dependencies
RUN apt-get update && apt-get install -y netcat-openbsd

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy wait script
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Make port 5000 available to the world outside this container
EXPOSE 6000

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches # this is the command you use to run your projectt
CMD ["/wait-for-it.sh", "mysql", "--", "gunicorn", "-b", "0.0.0.0:6000", "app:app"]
