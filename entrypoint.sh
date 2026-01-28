#!/usr/bin/env bash


uv run manage.py migrate
uv run -m gunicorn project.wsgi --bind 0.0.0.0:8000 --workers 3 --log-level info
