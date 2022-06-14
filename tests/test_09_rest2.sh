#!/bin/bash

echo "resests the queue from test_08 and tests the simple fifo scheduler"
echo
echo "reset queue a with status=end"
echo

curl -X 'PUT' \
  'http://127.0.0.1:8000/queue/a/reset?status=end' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo "run fifo scheduler"
echo

curl -X 'PUT' \
  'http://127.0.0.1:8000/queue/a/run_fifo?max_parallel=2&timeout=10' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo "refresh and list ran queues"
echo

curl -X 'PUT' \
  'http://127.0.0.1:8000/queue/ran' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo "manually test for queue run completion"