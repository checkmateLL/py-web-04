# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# If you have any dependencies, uncomment the next two lines
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt

# Make port 3000 and 5000 available to the world outside this container
EXPOSE 3000
EXPOSE 5000

# Define environment variable
ENV NAME World
ENV SOCKET_HOST 0.0.0.0

# Run main.py when the container launches
CMD ["python", "main.py"]