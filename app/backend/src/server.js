const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
require('dotenv').config();

// Importar conexiones de base de datos
const cassandraConnection = require('./database/cassandra');
const redisConnection = require('./database/redis');

// Importar controladores
const revenueController = require('./controllers/revenueController');

const app = express();
const PORT = process.env.PORT || 3001;
const API_VERSION = process.env.API_VERSION || 'v1';

// ========================================
// MIDDLEWARE DE SEGURIDAD Y PERFORMANCE
// ========================================

// Helmet para seguridad
app.use(helmet({
    crossOriginEmbedderPolicy: false,
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", "data:", "https:"],
        },
    },
}));

// CORS
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:5173'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
}));

// Compression
app.use(compression());

// Rate limiting
const limiter = rateLimit({
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutos
    max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
    message: {
        error: 'Demasiadas solicitudes desde esta IP, intenta de nuevo más tarde.',
        retryAfter: '15 minutes'
    },
    standardHeaders: true,
    legacyHeaders: false,
});

app.use(limiter);

// Logging
app.use(morgan('combined'));

// Parse JSON
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// ========================================
// MIDDLEWARE PERSONALIZADO
// ========================================

// Middleware de validación de conexión a bases de datos
app.use(async (req, res, next) => {
    try {
        // Verificar conexiones están activas
        if (!cassandraConnection.isConnected) {
            return res.status(503).json({
                success: false,
                error: 'Servicio no disponible - Cassandra desconectado'
            });
        }

        if (!redisConnection.isConnected) {
            return res.status(503).json({
                success: false,
                error: 'Servicio no disponible - Redis desconectado'
            });
        }

        next();
    } catch (error) {
        res.status(503).json({
            success: false,
            error: 'Error verificando conexiones de base de datos'
        });
    }
});

// Middleware de logging de requests
app.use((req, res, next) => {
    console.log(`📊 ${req.method} ${req.path} - ${new Date().toISOString()}`);
    next();
});

// ========================================
// RUTAS
// ========================================

// Health Check
app.get('/health', async (req, res) => {
    try {
        const cassandraMetrics = cassandraConnection.getConnectionMetrics();
        const redisInfo = redisConnection.getConnectionInfo();

        res.json({
            success: true,
            status: 'healthy',
            timestamp: new Date().toISOString(),
            services: {
                cassandra: {
                    connected: cassandraMetrics?.isConnected || false,
                    hosts: cassandraMetrics?.hosts || 0,
                    keyspace: cassandraMetrics?.keyspace
                },
                redis: {
                    connected: redisInfo.isConnected,
                    clients: redisInfo.clients,
                    activeConnections: redisInfo.activeConnections
                }
            },
            environment: process.env.NODE_ENV || 'development',
            version: API_VERSION
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            status: 'unhealthy',
            error: error.message
        });
    }
});

// API Info
app.get(`/api/${API_VERSION}`, (req, res) => {
    res.json({
        success: true,
        message: 'E-commerce Analytics API',
        version: API_VERSION,
        timestamp: new Date().toISOString(),
        endpoints: {
            revenue: {
                byCountry: `GET /api/${API_VERSION}/revenue/country/:country`,
                summary: `GET /api/${API_VERSION}/revenue/summary`,
                realtime: `GET /api/${API_VERSION}/revenue/realtime`,
                countries: `GET /api/${API_VERSION}/revenue/countries`,
                stats: `GET /api/${API_VERSION}/revenue/stats`
            },
            health: 'GET /health'
        }
    });
});

// ========================================
// RUTAS DE REVENUE
// ========================================
app.get(`/api/${API_VERSION}/revenue/country/:country`, revenueController.getRevenueByCountry);
app.get(`/api/${API_VERSION}/revenue/summary`, revenueController.getRevenueSummary);
app.get(`/api/${API_VERSION}/revenue/realtime`, revenueController.getRealtimeRevenue);
app.get(`/api/${API_VERSION}/revenue/countries`, revenueController.getAvailableCountries);
app.get(`/api/${API_VERSION}/revenue/stats`, revenueController.getRevenueStats);

// ========================================
// MANEJO DE ERRORES
// ========================================

// Ruta no encontrada
app.use('*', (req, res) => {
    res.status(404).json({
        success: false,
        error: 'Endpoint no encontrado',
        path: req.originalUrl,
        availableEndpoints: {
            health: 'GET /health',
            api: `GET /api/${API_VERSION}`,
            revenue: `GET /api/${API_VERSION}/revenue/*`
        }
    });
});

// Middleware de manejo global de errores
app.use((error, req, res, next) => {
    console.error('❌ Error global:', error);
    
    res.status(error.status || 500).json({
        success: false,
        error: 'Error interno del servidor',
        message: process.env.NODE_ENV === 'development' ? error.message : 'Ha ocurrido un error',
        timestamp: new Date().toISOString()
    });
});

// ========================================
// INICIALIZACIÓN DEL SERVIDOR
// ========================================

async function startServer() {
    try {
        console.log('🚀 Iniciando E-commerce Analytics API...');
        
        // Conectar a Cassandra
        console.log('📊 Conectando a Cassandra...');
        await cassandraConnection.connect();
        
        // Conectar a Redis
        console.log('🔄 Conectando a Redis...');
        await redisConnection.connect();
        
        // Iniciar servidor
        app.listen(PORT, () => {
            console.log('');
            console.log('✅ ===================================');
            console.log('🎉 SERVIDOR INICIADO EXITOSAMENTE');
            console.log('✅ ===================================');
            console.log(`🌐 API URL: http://localhost:${PORT}`);
            console.log(`📚 API Docs: http://localhost:${PORT}/api/${API_VERSION}`);
            console.log(`💚 Health Check: http://localhost:${PORT}/health`);
            console.log('');
            console.log('📊 Endpoints disponibles:');
            console.log(`   Revenue por país: GET /api/${API_VERSION}/revenue/country/:country`);
            console.log(`   Resumen revenue: GET /api/${API_VERSION}/revenue/summary`);
            console.log(`   Revenue tiempo real: GET /api/${API_VERSION}/revenue/realtime`);
            console.log(`   Lista países: GET /api/${API_VERSION}/revenue/countries`);
            console.log(`   Estadísticas: GET /api/${API_VERSION}/revenue/stats`);
            console.log('');
            console.log('🔗 Servicios externos:');
            console.log('   📊 Cassandra Web UI: http://localhost:3000');
            console.log('   🔄 Redis Commander: http://localhost:8081 (admin/admin123)');
            console.log('');
        });
        
    } catch (error) {
        console.error('❌ Error iniciando servidor:', error);
        process.exit(1);
    }
}

// Manejo de señales de cierre
process.on('SIGINT', async () => {
    console.log('\n🔄 Cerrando servidor...');
    
    try {
        await cassandraConnection.disconnect();
        await redisConnection.disconnect();
        console.log('✅ Conexiones cerradas correctamente');
        process.exit(0);
    } catch (error) {
        console.error('❌ Error cerrando conexiones:', error);
        process.exit(1);
    }
});

process.on('SIGTERM', async () => {
    console.log('\n🔄 Señal SIGTERM recibida, cerrando servidor...');
    await cassandraConnection.disconnect();
    await redisConnection.disconnect();
    process.exit(0);
});

// Iniciar el servidor
startServer(); 