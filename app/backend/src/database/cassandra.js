const cassandra = require('cassandra-driver');
require('dotenv').config();

class CassandraConnection {
    constructor() {
        this.client = null;
        this.isConnected = false;
    }

    async connect() {
        try {
            this.client = new cassandra.Client({
                contactPoints: [process.env.CASSANDRA_HOSTS || 'localhost'],
                localDataCenter: process.env.CASSANDRA_DATACENTER || 'datacenter1',
                keyspace: process.env.CASSANDRA_KEYSPACE || 'ecommerce_analytics',
                credentials: {
                    username: process.env.CASSANDRA_USERNAME || 'cassandra',
                    password: process.env.CASSANDRA_PASSWORD || 'cassandra'
                },
                pooling: {
                    coreConnectionsPerHost: {
                        [cassandra.types.distance.local]: 2,
                        [cassandra.types.distance.remote]: 1
                    }
                },
                queryOptions: {
                    consistency: cassandra.types.consistencies.localQuorum,
                    fetchSize: 1000
                },
                requestTimeout: 12000,
                connectTimeout: 5000
            });

            await this.client.connect();
            this.isConnected = true;
            
            console.log('✅ Conectado a Cassandra exitosamente');
            console.log(`📊 Keyspace: ${process.env.CASSANDRA_KEYSPACE}`);
            
            return this.client;
        } catch (error) {
            console.error('❌ Error conectando a Cassandra:', error);
            throw error;
        }
    }

    async disconnect() {
        if (this.client && this.isConnected) {
            await this.client.shutdown();
            this.isConnected = false;
            console.log('🔌 Desconectado de Cassandra');
        }
    }

    getClient() {
        if (!this.isConnected || !this.client) {
            throw new Error('Cassandra no está conectado. Llama connect() primero.');
        }
        return this.client;
    }

    // Método helper para queries preparadas
    async executeQuery(query, params = []) {
        try {
            const client = this.getClient();
            const result = await client.execute(query, params, { prepare: true });
            return result;
        } catch (error) {
            console.error('❌ Error ejecutando query Cassandra:', error);
            throw error;
        }
    }

    // Método helper para obtener métricas de conexión
    getConnectionMetrics() {
        if (!this.client) return null;
        
        return {
            hosts: this.client.getState().getConnectedHosts().length,
            keyspace: this.client.keyspace,
            isConnected: this.isConnected
        };
    }
}

// Singleton para la conexión
const cassandraConnection = new CassandraConnection();

module.exports = cassandraConnection; 