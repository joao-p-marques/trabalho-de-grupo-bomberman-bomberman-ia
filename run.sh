#!/bin/bash

echo "Running server..."
python3 server.py &
SERVER_PID=$!

sleep 1

echo "Running viewer..."
python3 viewer.py &
VIEWER_PID=$!

sleep 1

echo "Running client (student)..."
python3 student.py 

echo "Client killed by user"

echo "Killing viewer..."
kill $VIEWER_PID

echo "Killing Server..."
kill $SERVER_PID

