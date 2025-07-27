FROM python:3.13-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Replace this line if you had:
# ENTRYPOINT ["./entrypoint.sh"]

# With this (forces execution via bash):
ENTRYPOINT ["bash", "entrypoint.sh"]
