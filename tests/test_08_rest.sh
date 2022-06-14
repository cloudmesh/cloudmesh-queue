#!/bin/bash
echo "run from ~/cm/cloudmesh-queue"
echo "removes existing experiment directories and then creates a test host and queue to test various functions and the fifo_multi scheduler"

echo "remove local and remote experiment dirs"
rm -rf ./experiment
cms host ssh red,red0[1-3] "'rm -rf ./experiment'"
echo

echo
echo "create a queue a"
echo

curl -X 'POST' \
  'http://127.0.0.1:8000/queue/?name=a' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA==' \
  -d ''

echo
echo
echo "get the list of queues"
echo

curl -X 'GET' \
  'http://127.0.0.1:8000/queue/' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "add jobs to queue"
echo

curl -X 'POST' \
  'http://127.0.0.1:8000/queue/a?name=job0%5B1-5%5D&command=hostname' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA==' \
  -d ''

echo
echo
echo "list json of queue a"
echo

curl -X 'GET' \
  'http://127.0.0.1:8000/queue/a' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "get queue info"
echo

curl -X 'GET' \
  'http://127.0.0.1:8000/queue/a/info' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "get job01 json"
echo

curl -X 'GET' \
  'http://127.0.0.1:8000/queue/a/job/job01' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "delete job01"
echo

curl -X 'DELETE' \
  'http://127.0.0.1:8000/queue/a/job/{job}?name=job01' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "create a cluster a"
echo

curl -X 'POST' \
  'http://127.0.0.1:8000/cluster/?name=a' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA==' \
  -d ''

echo
echo
echo "list clusters"
echo

curl -X 'GET' \
  'http://127.0.0.1:8000/cluster/' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "add hosts to cluster"
echo

curl -X 'POST' \
  'http://127.0.0.1:8000/cluster/a?id=host0%5B1-4%5D&name=red&user=pi' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA==' \
  -d ''

echo
echo
echo "get json of cluster a"
echo

curl -X 'GET' \
  'http://127.0.0.1:8000/cluster/a' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "get cluster a info"
echo

curl -X 'GET' \
  'http://127.0.0.1:8000/cluster/a/info' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "delete host 01"
echo

curl -X 'DELETE' \
  'http://127.0.0.1:8000/cluster/a/id/host01' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "get json of host02"
echo

curl -X 'GET' \
  'http://127.0.0.1:8000/cluster/a/id/host02' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "deactivate host02"
echo

curl -X 'PUT' \
  'http://127.0.0.1:8000/cluster/a/id/host02/deactivate' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "activate host02"
echo

curl -X 'PUT' \
  'http://127.0.0.1:8000/cluster/a/id/host02/activate' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "set host02 name to red01"
echo

curl -X 'PUT' \
  'http://127.0.0.1:8000/cluster/a/id/host02/set?key=name&value=red01' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "run queue a on cluster a"
echo

curl -X 'PUT' \
  'http://127.0.0.1:8000/queue/a/run_fifo_multi?cluster=a&timeout=10' \
  -H 'accept: application/json' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "refresh and list ran queues"
echo

curl -X 'PUT' \
  'http://127.0.0.1:8000/queue/ran' \
  -H 'accept: text/plain' \
  -H 'Authorization: Basic dXNlcjpwYXNzd29yZA=='

echo
echo
echo "wait for queue to stop running before running test_09_rest to test the simple fifo scheduler"
echo
