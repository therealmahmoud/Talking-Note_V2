#!/usr/bin/env bash
set -e

host="$1"
shift
cmd="$@"

until nc -z -v -w30 $host 27017
do
  echo "Waiting for mongo database connection..."
  sleep 1
done

echo "mongo is up - executing command"
exec $cmd

