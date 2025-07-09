const cassandra = require('cassandra-driver');
require('dotenv').config();

class CassandraConnection {
    constructor() {
        this.client = null;
        this.isConnected = false;
        this.maxRetries = 30;
        this.retryInterval = 5000;
    }

    async connect() {
        let retries = 0;
        
        while (retries < this.maxRetries) {
            try {
                const host = process.env.CASSANDRA_HOSTS || 'cassandra';
                const port = parseInt(process.env.CASSANDRA_PORT || '9042', 10);
                
                console.log(`🔄 Intento de conexión a Cassandra (${retries + 1}/${this.maxRetries}):`, {
                    host,
                    port,
                    keyspace: process.env.CASSANDRA_KEYSPACE
                });

                this.client = new cassandra.Client({
                    contactPoints: [`${host}:${port}`],
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
                        },
                        heartbeatInterval: 30000
                    },
                    queryOptions: {
                        consistency: cassandra.types.consistencies.localQuorum,
                        fetchSize: 1000,
                        prepare: true,
                        retry: new cassandra.policies.retry.RetryPolicy()
                    },
                    socketOptions: {
                        connectTimeout: 10000,
                        readTimeout: 12000
                    },
                    reconnection: {
                        maxRetries: 10,
                        baseDelay: 1000,
                        maxDelay: 10000
                    }
                });

                // Verificar conexión y keyspace
                await this.client.connect();
                await this.verifyKeyspaceAndTables();
                
                this.isConnected = true;
                console.log('✅ Conectado a Cassandra exitosamente');
                console.log(`📊 Keyspace: ${process.env.CASSANDRA_KEYSPACE}`);
                console.log(`📍 Host: ${host}:${port}`);
                
                // Configurar health check periódico
                this.startHealthCheck();
                
                return this.client;

            } catch (error) {
                console.error(`❌ Error conectando a Cassandra (intento ${retries + 1}/${this.maxRetries}):`, error);
                
                if (retries === this.maxRetries - 1) {
                    throw new Error(`No se pudo conectar a Cassandra después de ${this.maxRetries} intentos: ${error.message}`);
                }

                await new Promise(resolve => setTimeout(resolve, this.retryInterval));
                retries++;
            }
        }
    }

    async verifyKeyspaceAndTables() {
        try {
            // Verificar si el keyspace existe
            const keyspaceQuery = "SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name = ?";
            const keyspaceResult = await this.client.execute(keyspaceQuery, [process.env.CASSANDRA_KEYSPACE], { prepare: true });
            
            if (keyspaceResult.rows.length === 0) {
                throw new Error(`Keyspace ${process.env.CASSANDRA_KEYSPACE} no existe`);
            }

            // Verificar tablas requeridas
            const requiredTables = [
                'revenue_by_country_time', // tabla principal de revenue
                'realtime_metrics',        // métricas en tiempo real
                'transactions'             // detalle de transacciones
            ];
            const tableQuery = "SELECT table_name FROM system_schema.tables WHERE keyspace_name = ?";
            const tableResult = await this.client.execute(tableQuery, [process.env.CASSANDRA_KEYSPACE], { prepare: true });
            
            const existingTables = tableResult.rows.map(row => row.table_name);
            const missingTables = requiredTables.filter(table => !existingTables.includes(table));
            
            if (missingTables.length > 0) {
                throw new Error(`Tablas faltantes en Cassandra: ${missingTables.join(', ')}`);
            }
        } catch (error) {
            console.error('❌ Error verificando keyspace y tablas:', error);
            throw error;
        }
    }

    startHealthCheck() {
        const HEALTH_CHECK_INTERVAL = 30000; // 30 segundos
        
        setInterval(async () => {
            try {
                if (!this.isConnected) return;
                
                const query = 'SELECT release_version FROM system.local';
                await this.client.execute(query, [], { prepare: true });
                
            } catch (error) {
                console.error('❌ Error en health check de Cassandra:', error);
                this.isConnected = false;
                
                // Intentar reconectar
                try {
                    await this.connect();
                } catch (reconnectError) {
                    console.error('❌ Error reconectando a Cassandra:', reconnectError);
                }
            }
        }, HEALTH_CHECK_INTERVAL);
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