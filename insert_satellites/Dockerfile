# Base Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY insert_satellites.py .

# Copy the config file
COPY starlink_config.yaml .

# Run the script by default
CMD ["python", "insert_satellites.py","--config","starlink_config.yaml"]