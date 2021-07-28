#!/bin/bash

#test.sh -o=~/ENV4/output -i=~/ENV4 -g=4

while getopts ":o:i:g:" opt; do
  case $opt in
    o) output="$OPTARG"
    ;;
    i) input="$OPTARG"
    ;;
    g) gpu="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

dt=`date +%m%d%Y_%H%M%S`
output_file="$output"_"$dt".txt
echo ' ' > "$output_file"

{
echo "$(date) Started the script."
echo "output will be at: " $output_file
echo "input is taken from: " $input
echo "gpu to use is: " $gpu

echo "sleep for 2 sec"
sleep 2

echo "$(date)"

echo "sleep for 2 sec"
sleep 2

echo "$(date)"

echo "END"
} | tee -a $output_file

