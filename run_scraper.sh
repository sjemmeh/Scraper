source venv/bin/activate

# Run the server. It will be accessible on all network interfaces on port 8000.
uvicorn main:app --host 0.0.0.0 --port 8000
