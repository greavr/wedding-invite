# Use an official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=True
ENV APP_HOME=/app

# Create and set the working directory
WORKDIR $APP_HOME

# Copy the requirements file and install dependencies
COPY code/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY code/ .

# Expose the port Gunicorn will run on
EXPOSE 8080

CMD ["python3", "main.py"]