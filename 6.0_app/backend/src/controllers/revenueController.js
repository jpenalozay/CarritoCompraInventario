const revenueService = require('../services/revenueService');
const moment = require('moment');
const Joi = require('joi');

class RevenueController {
    
    /**
     * GET /api/v1/revenue/country/:country
     * Obtener revenue por país
     */
    async getRevenueByCountry(req, res) {
        try {
            // Validación de parámetros
            const schema = Joi.object({
                country: Joi.string().required().min(2).max(50),
                startDate: Joi.date().iso().default('2010-12-01'),
                endDate: Joi.date().iso().default('2011-12-31'),
                useCache: Joi.boolean().default(true)
            });

            const { error, value } = schema.validate({
                country: req.params.country,
                startDate: req.query.startDate,
                endDate: req.query.endDate,
                useCache: req.query.useCache
            });

            if (error) {
                return res.status(400).json({
                    success: false,
                    error: 'Parámetros inválidos',
                    details: error.details[0].message
                });
            }

            const { country, startDate, endDate, useCache } = value;

            // Validar que startDate sea anterior a endDate
            if (moment(startDate).isAfter(moment(endDate))) {
                return res.status(400).json({
                    success: false,
                    error: 'La fecha de inicio debe ser anterior a la fecha final'
                });
            }

            // Validar que el rango no exceda 2 años (para datos históricos)
            const daysDiff = moment(endDate).diff(moment(startDate), 'days');
            if (daysDiff > 730) {
                return res.status(400).json({
                    success: false,
                    error: 'El rango de fechas no puede exceder 2 años'
                });
            }

            // Validar que las fechas no sean futuras
            if (moment(endDate).isAfter(moment())) {
                return res.status(400).json({
                    success: false,
                    error: 'La fecha final no puede ser futura'
                });
            }

            const data = await revenueService.getRevenueByCountry(
                country, 
                startDate, 
                endDate, 
                useCache
            );

            res.json({
                success: true,
                data,
                requestInfo: {
                    country,
                    period: { start: startDate, end: endDate },
                    cached: useCache,
                    timestamp: new Date().toISOString()
                }
            });

        } catch (error) {
            console.error('❌ Error in getRevenueByCountry:', error);
            res.status(500).json({
                success: false,
                error: 'Error interno del servidor',
                message: error.message
            });
        }
    }

    /**
     * GET /api/v1/revenue/summary
     * Obtener resumen de revenue de todos los países
     */
    async getRevenueSummary(req, res) {
        try {
            const schema = Joi.object({
                startDate: Joi.date().iso().default('2010-12-01'),
                endDate: Joi.date().iso().default('2011-12-31'),
                useCache: Joi.boolean().default(true)
            });

            const { error, value } = schema.validate(req.query);

            if (error) {
                return res.status(400).json({
                    success: false,
                    error: 'Parámetros inválidos',
                    details: error.details[0].message
                });
            }

            const { startDate, endDate, useCache } = value;

            const data = await revenueService.getRevenueSummaryByCountries(
                startDate, 
                endDate, 
                useCache
            );

            res.json({
                success: true,
                data,
                requestInfo: {
                    period: { start: startDate, end: endDate },
                    cached: useCache,
                    timestamp: new Date().toISOString()
                }
            });

        } catch (error) {
            console.error('❌ Error in getRevenueSummary:', error);
            res.status(500).json({
                success: false,
                error: 'Error interno del servidor',
                message: error.message
            });
        }
    }

    /**
     * GET /api/v1/revenue/realtime
     * Obtener revenue en tiempo real (últimas 24 horas)
     */
    async getRealtimeRevenue(req, res) {
        try {
            const schema = Joi.object({
                country: Joi.string().optional().min(2).max(50)
            });

            const { error, value } = schema.validate(req.query);

            if (error) {
                return res.status(400).json({
                    success: false,
                    error: 'Parámetros inválidos',
                    details: error.details[0].message
                });
            }

            const { country } = value;

            const data = await revenueService.getRealtimeRevenue(country);

            res.json({
                success: true,
                data,
                requestInfo: {
                    country: country || 'all',
                    period: 'last_24_hours',
                    timestamp: new Date().toISOString()
                }
            });

        } catch (error) {
            console.error('❌ Error in getRealtimeRevenue:', error);
            res.status(500).json({
                success: false,
                error: 'Error interno del servidor',
                message: error.message
            });
        }
    }

    /**
     * GET /api/v1/revenue/countries
     * Obtener lista de países disponibles
     */
    async getAvailableCountries(req, res) {
        try {
            // Esta consulta es ligera y puede cacharse por más tiempo
            const cacheKey = 'revenue:countries:list';
            const cached = await require('../database/redis').cacheGet(cacheKey);
            
            if (cached) {
                return res.json({
                    success: true,
                    data: cached,
                    cached: true
                });
            }

            const countries = await revenueService.getAvailableCountries();
            
            // Cache por 1 hora ya que la lista de países cambia poco
            await require('../database/redis').cacheSet(cacheKey, countries, 3600);

            res.json({
                success: true,
                data: countries,
                cached: false,
                metadata: {
                    count: countries.length,
                    timestamp: new Date().toISOString()
                }
            });

        } catch (error) {
            console.error('❌ Error in getAvailableCountries:', error);
            res.status(500).json({
                success: false,
                error: 'Error interno del servidor',
                message: error.message
            });
        }
    }

    /**
     * GET /api/v1/revenue/stats
     * Obtener estadísticas generales de revenue
     */
    async getRevenueStats(req, res) {
        try {
            const cacheKey = 'revenue:stats:general';
            const cached = await require('../database/redis').cacheGet(cacheKey);
            
            if (cached) {
                return res.json({
                    success: true,
                    data: cached,
                    cached: true
                });
            }

            // Obtener estadísticas básicas
            const queries = [
                'SELECT COUNT(*) as total_records FROM revenue_by_country_time',
                'SELECT MIN(date_bucket) as earliest_date, MAX(date_bucket) as latest_date FROM revenue_by_country_time',
                'SELECT COUNT(DISTINCT country) as total_countries FROM revenue_by_country_time'
            ];

            const results = await Promise.all(
                queries.map(query => require('../database/cassandra').executeQuery(query))
            );

            const stats = {
                totalRecords: results[0].rows[0]?.total_records || 0,
                dateRange: {
                    earliest: results[1].rows[0]?.earliest_date,
                    latest: results[1].rows[0]?.latest_date
                },
                totalCountries: results[2].rows[0]?.total_countries || 0,
                generatedAt: new Date().toISOString()
            };

            // Cache por 30 minutos
            await require('../database/redis').cacheSet(cacheKey, stats, 1800);

            res.json({
                success: true,
                data: stats,
                cached: false
            });

        } catch (error) {
            console.error('❌ Error in getRevenueStats:', error);
            res.status(500).json({
                success: false,
                error: 'Error interno del servidor',
                message: error.message
            });
        }
    }
}

module.exports = new RevenueController(); 