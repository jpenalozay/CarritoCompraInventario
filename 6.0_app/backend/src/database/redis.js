const redis = require('redis');
require('dotenv').config();

class RedisConnection {
    constructor() {
        this.clients = {};
        this.isConnected = false;
        this.maxRetries = 30;
        this.retryInterval = 2000;
    }

    async connect() {
        let retries = 0;
        
        while (retries < this.maxRetries) {
            try {
                const redisHost = process.env.REDIS_HOST || 'redis';
                const redisPort = parseInt(process.env.REDIS_PORT || '6379', 10);
                
                console.log(`🔄 Intento de conexión a Redis (${retries + 1}/${this.maxRetries}):`, {
                    host: redisHost,
                    port: redisPort,
                    hasPassword: !!(process.env.REDIS_PASSWORD && process.env.REDIS_PASSWORD !== '')
                });

                const redisUrl = `redis://${redisHost}:${redisPort}`;
                
                // Crear clientes para diferentes propósitos con configuración de reconexión
                const createClientWithRetry = (db) => {
                    const client = redis.createClient({
                        url: redisUrl,
                        database: db,
                        socket: {
                            reconnectStrategy: (retries) => {
                                if (retries > 10) {
                                    console.error('❌ Redis - Máximo de reintentos de reconexión alcanzado');
                                    return new Error('Máximo de reintentos de reconexión alcanzado');
                                }
                                return Math.min(retries * 100, 3000);
                            },
                            connectTimeout: 10000,
                            keepAlive: 5000
                        }
                    });

                    client.on('error', (err) => {
                        console.error('❌ Redis Error:', err);
                        if (!this.isConnected) {
                            client.quit().catch(console.error);
                        }
                    });

                    client.on('connect', () => {
                        console.log(`🔗 Redis DB${db} conectado`);
                    });

                    client.on('ready', () => {
                        console.log(`✅ Redis DB${db} listo para usar`);
                    });

                    client.on('reconnecting', () => {
                        console.log(`🔄 Redis DB${db} intentando reconectar...`);
                    });

                    return client;
                };

                this.clients.apiCache = createClientWithRetry(parseInt(process.env.REDIS_DB_API_CACHE) || 0);
                this.clients.sessions = createClientWithRetry(parseInt(process.env.REDIS_DB_SESSIONS) || 1);
                this.clients.metrics = createClientWithRetry(parseInt(process.env.REDIS_DB_METRICS) || 2);

                // Conectar todos los clientes
                await Promise.all(
                    Object.values(this.clients).map(client => client.connect())
                );

                this.isConnected = true;
                console.log('✅ Todos los clientes Redis conectados exitosamente');
                return this.clients;

            } catch (error) {
                console.error(`❌ Error conectando a Redis (intento ${retries + 1}/${this.maxRetries}):`, error);
                
                if (retries === this.maxRetries - 1) {
                    throw new Error(`No se pudo conectar a Redis después de ${this.maxRetries} intentos: ${error.message}`);
                }

                await new Promise(resolve => setTimeout(resolve, this.retryInterval));
                retries++;
            }
        }
    }

    async disconnect() {
        if (this.isConnected) {
            await Promise.all(
                Object.values(this.clients).map(async (client) => {
                    try {
                        await client.quit();
                    } catch (error) {
                        console.error('Error desconectando cliente Redis:', error);
                    }
                })
            );
            this.isConnected = false;
            console.log('🔌 Desconectado de Redis');
        }
    }

    getClient(type = 'apiCache') {
        if (!this.isConnected || !this.clients[type]) {
            throw new Error(`Redis ${type} no está conectado. Llama connect() primero.`);
        }
        return this.clients[type];
    }

    // Métodos helper para cache de API
    async cacheSet(key, value, ttl = 300) {
        try {
            const client = this.getClient('apiCache');
            await client.setEx(key, ttl, JSON.stringify(value));
        } catch (error) {
            console.error('❌ Error cacheando en Redis:', error);
            throw error;
        }
    }

    async cacheGet(key) {
        try {
            const client = this.getClient('apiCache');
            const cached = await client.get(key);
            return cached ? JSON.parse(cached) : null;
        } catch (error) {
            console.error('❌ Error obteniendo cache de Redis:', error);
            return null;
        }
    }

    async cacheDelete(key) {
        try {
            const client = this.getClient('apiCache');
            await client.del(key);
        } catch (error) {
            console.error('❌ Error eliminando cache de Redis:', error);
            throw error;
        }
    }

    // Métodos helper para métricas en tiempo real
    async setMetric(key, value, ttl = 300) {
        try {
            const client = this.getClient('metrics');
            await client.setEx(`metrics:${key}`, ttl, value.toString());
        } catch (error) {
            console.error('❌ Error guardando métrica en Redis:', error);
            throw error;
        }
    }

    async getMetric(key) {
        try {
            const client = this.getClient('metrics');
            const value = await client.get(`metrics:${key}`);
            return value ? parseFloat(value) : null;
        } catch (error) {
            console.error('❌ Error obteniendo métrica de Redis:', error);
            return null;
        }
    }

    // Obtener información de estado
    getConnectionInfo() {
        return {
            isConnected: this.isConnected,
            clients: Object.keys(this.clients),
            activeConnections: Object.keys(this.clients).length
        };
    }
}

// Singleton para la conexión
const redisConnection = new RedisConnection();

module.exports = redisConnection; 