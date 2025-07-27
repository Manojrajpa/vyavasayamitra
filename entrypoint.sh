#!/bin/bash
set -e
exec gunicorn --bind 0.0.0.0:$PORT app:app
