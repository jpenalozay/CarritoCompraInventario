FROM flink:1.17.1-scala_2.12-java11

# Instalar Python
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/* && \
    ln -s /usr/bin/python3 /usr/bin/python

# Copiar requirements.txt y instalar dependencias
COPY requirements.txt /
RUN pip3 install -r /requirements.txt

# Copiar conectores de Flink
COPY connectors/ /opt/flink/lib/

# Copiar jobs de Flink
COPY jobs/ /opt/flink/jobs/

# Copiar configuración de Flink
COPY config/flink-conf.yaml /opt/flink/conf/

# Copiar configuración de logging
COPY config/log4j2.properties /opt/flink/conf/

# Establecer el directorio de trabajo
WORKDIR /opt/flink

# Crear directorios necesarios
RUN mkdir -p /opt/flink/plugins/kafka /opt/flink/plugins/cassandra

# Descargar conectores
RUN wget -P /opt/flink/plugins/kafka https://repo.maven.apache.org/maven2/org/apache/flink/flink-connector-kafka/1.17.0/flink-connector-kafka-1.17.0.jar && \
    wget -P /opt/flink/plugins/cassandra https://repo.maven.apache.org/maven2/org/apache/flink/flink-connector-cassandra_2.12/3.1.0-1.17/flink-connector-cassandra_2.12-3.1.0-1.17.jar && \
    wget -P /opt/flink/lib https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.0.2-1.17/flink-sql-connector-kafka-3.0.2-1.17.jar

# Verificar la instalación
RUN python3 -c "from pyflink.version import __version__ as flink_version; print('Flink version:', flink_version)"

# El comando se especifica en docker-compose.yml 

# Create jobs directory and copy Python files
RUN mkdir -p /opt/flink/jobs
COPY jobs/transaction_processor.py /opt/flink/jobs/ 