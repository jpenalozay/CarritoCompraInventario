#!/bin/bash

# Start Cassandra in the background
/docker-entrypoint.sh cassandra -f &

# Wait for Cassandra to be ready and run the initialization script
/docker-entrypoint-initdb.d/init-schema.sh

# Keep the container running
wait 