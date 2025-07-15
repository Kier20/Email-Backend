#!/bin/bash

# Ensure dependencies are installed
pip install -r requirements.txt

# Run FastAPI app using uvicorn
uvicorn api.send_email:app --host 0.0.0.0 --port 10000
