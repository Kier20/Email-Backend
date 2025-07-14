#!/bin/bash
uvicorn api.send_email:app --host 0.0.0.0 --port 10000
