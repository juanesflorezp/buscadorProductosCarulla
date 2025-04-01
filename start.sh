#!/bin/bash
gunicorn --bind 0.0.0.0:$PORT --timeout 120 api:app
