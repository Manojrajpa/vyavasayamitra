
# Use official Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Add execute permission to entrypoint
RUN chmod +x /app/entrypoint.sh

# Run the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
