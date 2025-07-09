FROM cassandra:latest

# Install cqlsh
RUN apt-get update && apt-get install -y python3-pip && \
    pip3 install cqlsh

# Copy schema files
COPY schemas/ /docker-entrypoint-initdb.d/

# Copy initialization script
COPY init-schema.sh /docker-entrypoint-initdb.d/

# Make the script executable
RUN chmod +x /docker-entrypoint-initdb.d/init-schema.sh

# Set the entrypoint to run both Cassandra and our init script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command
CMD ["cassandra", "-f"] 