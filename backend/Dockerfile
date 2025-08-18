# Use an official lightweight Python image as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables for Python and the application port
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Copy the requirements file into the container
COPY code/requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY code/ .

# Expose the port the app runs on
EXPOSE 8080

# Define the command to run the application using Gunicorn
# This command starts a Gunicorn server with 4 worker processes,
# binding it to all network interfaces on the specified port.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]