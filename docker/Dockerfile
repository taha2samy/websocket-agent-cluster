FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app

# Expose the port
EXPOSE 8000  
# Run the WebSocket handler
CMD ["/bin/sh", "-c", "tail -f /dev/null"]
