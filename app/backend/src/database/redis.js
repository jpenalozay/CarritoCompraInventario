const redis = require('redis');
require('dotenv').config();

class RedisConnection {
    constructor() {
        this.clients = {};
        this.isConnected = false;
    }

    async connect() {
        try {
            const redisConfig = {
                host: process.env.REDIS_HOST || 'localhost',
                port: process.env.REDIS_PORT || 6379,
                retryDelayOnFailover: 100,
                enableOfflineQueue: false,
                maxRetriesPerRequest: 3,
                lazyConnect: true
            };

            // Solo agregar password si está configurado en Redis
            if (process.env.REDIS_PASSWORD && process.env.REDIS_PASSWORD !== '') {
                redisConfig.password = process.env.REDIS_PASSWORD;
            }

            // Crear clientes para diferentes propósitos
            this.clients.apiCache = redis.createClient({
                ...redisConfig,
                database: parseInt(process.env.REDIS_DB_API_CACHE) || 0
            });

            this.clients.sessions = redis.createClient({
                ...redisConfig,
                database: parseInt(process.env.REDIS_DB_SESSIONS) || 1
            });

            this.clients.metrics = redis.createClient({
                ...redisConfig,
                database: parseInt(process.env.REDIS_DB_METRICS) || 2
            });

            // Configurar manejo de errores
            Object.values(this.clients).forEach(client => {
                client.on('error', (err) => {
                    console.error('❌ Redis Error:', err);
                });

                client.on('connect', () => {
                    console.log('🔗 Redis conectado');
                });

                client.on('ready', () => {
                    console.log('✅ Redis listo para usar');
                });
            });

            // Conectar todos los clientes
            await Promise.all(
                Object.values(this.clients).map(client => client.connect())
            );

            this.isConnected = true;
            console.log('✅ Todos los clientes Redis conectados exitosamente');
            
            return this.clients;
        } catch (error) {
            console.error('❌ Error conectando a Redis:', error);
            throw error;
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