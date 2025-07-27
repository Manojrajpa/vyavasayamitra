FROM python:3.9

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# If using entrypoint.sh, do:
# ENTRYPOINT ["bash", "entrypoint.sh"]

# Otherwise, if running directly with gunicorn:
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
