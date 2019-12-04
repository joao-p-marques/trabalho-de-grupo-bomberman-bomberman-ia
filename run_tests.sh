#!/bin/bash

python3 server.py --grading-server "http://localhost:8080/game" &
SERVER_PID=$!

sleep 1

for n in {1..$1}
do

  for i in {1..10}
  do
    
    echo Running $i...

    python3 student.py

    echo Done
    
  done

  echo 'Run (10) done'
  echo 'Average: '
  curl http://localhost:8080/avg

done

kill $SERVER_PID
