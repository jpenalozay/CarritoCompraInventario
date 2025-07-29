const cassandraConnection = require('../database/cassandra');
const redisConnection = require('../database/redis');
const moment = require('moment');

class RevenueService {
    constructor() {
        this.cachePrefix = 'revenue';
        this.defaultTTL = 300; // 5 minutos
        // Configurar el rango real de datos disponibles
        this.dataStart = moment('2010-12-01');
        this.dataEnd = moment('2011-12-31');
    }

    /**
     * Obtener revenue por país en un rango de fechas
     */
    async getRevenueByCountry(country, startDate, endDate, useCache = true) {
        const countryMapping = {
            'United Kingdom': 'UK',
            'Germany': 'Germany',
            'France': 'France'
        };
        
        const internalCountry = countryMapping[country] || country;
        const cacheKey = `${this.cachePrefix}:country:${country}:${startDate}:${endDate}`;
        
        // Intentar obtener del cache primero
        if (useCache) {
            const cached = await redisConnection.cacheGet(cacheKey);
            if (cached) {
                console.log('📦 Revenue data served from cache');
                return cached;
            }
        }

        try {
            // Ajustar fechas al rango disponible (datos reales de 2010-2012)
            const requestedStart = moment(startDate);
            const requestedEnd = moment(endDate);

            // Usar la intersección de los rangos
            const effectiveStart = moment.max(requestedStart, this.dataStart);
            const effectiveEnd = moment.min(requestedEnd, this.dataEnd);

            if (effectiveStart > effectiveEnd) {
                return {
                    country,
                    period: { start: startDate, end: endDate },
                    data: [],
                    summary: this._calculateSummary([]),
                    metadata: {
                        totalRecords: 0,
                        generatedAt: new Date().toISOString(),
                        source: 'cassandra',
                        dates: 0,
                        warning: 'No data available for the requested date range'
                    }
                };
            }

            // En lugar de consultar Cassandra, usar Redis que tiene los datos reales
            return await this._getRevenueFromRedis(country, effectiveStart, effectiveEnd, startDate, endDate);

        } catch (error) {
            console.error('❌ Error getting revenue by country:', error);
            throw new Error(`Error obteniendo revenue para ${country}: ${error.message}`);
        }
    }

    /**
     * Obtener datos desde Redis en lugar de Cassandra
     */
    async _getRevenueFromRedis(country, effectiveStart, effectiveEnd, originalStartDate, originalEndDate) {
        try {
            const client = redisConnection.getClient('apiCache'); // Cambio de 'metrics' a 'apiCache' (DB 0)
            
            // Obtener métricas por país
            const countryKey = `analytics:country:${country}`;
            const countryData = await client.HGETALL(countryKey); // Cambio de hgetall a HGETALL
            
            // Obtener métricas globales para contexto
            const globalKey = `analytics:global:revenue`;
            const globalData = await client.HGETALL(globalKey); // Cambio de hgetall a HGETALL
            
            if (!countryData || Object.keys(countryData).length === 0) {
                return {
                    country,
                    period: { start: originalStartDate, end: originalEndDate },
                    data: [],
                    summary: this._calculateSummary([]),
                    metadata: {
                        totalRecords: 0,
                        generatedAt: new Date().toISOString(),
                        source: 'redis',
                        warning: `No data found for ${country}`
                    }
                };
            }

            // Simular datos de transacciones basados en las métricas reales
            const mockData = [{
                date: effectiveStart.format('YYYY-MM-DD'),
                hour: 12,
                timestamp: effectiveStart.toISOString(),
                invoiceNo: 'AGGREGATED',
                customerId: 'MULTIPLE',
                revenueGBP: parseFloat(countryData.revenue) || 0,
                revenueUSD: (parseFloat(countryData.revenue) || 0) * 1.25,
                orderCount: parseInt(countryData.orders) || 0,
                customerCount: Math.ceil((parseInt(countryData.orders) || 0) * 0.7), // Estimación
                avgOrderValue: (parseFloat(countryData.revenue) || 0) / (parseInt(countryData.orders) || 1)
            }];

            return {
                country,
                period: { 
                    start: originalStartDate, 
                    end: originalEndDate,
                    effective: {
                        start: effectiveStart.format('YYYY-MM-DD'),
                        end: effectiveEnd.format('YYYY-MM-DD')
                    }
                },
                data: mockData,
                summary: this._calculateSummary(mockData),
                metadata: {
                    totalRecords: mockData.length,
                    generatedAt: new Date().toISOString(),
                    source: 'redis',
                    note: 'Data aggregated from Redis metrics'
                }
            };

        } catch (error) {
            console.error('❌ Error getting data from Redis:', error);
            throw error;
        }
    }

    /**
     * Obtener resumen de revenue por todos los países
     */
    async getRevenueSummaryByCountries(startDate, endDate, useCache = true) {
        const cacheKey = `${this.cachePrefix}:summary:${startDate}:${endDate}`;
        
        if (useCache) {
            const cached = await redisConnection.cacheGet(cacheKey);
            if (cached) return cached;
        }

        try {
            // Ajustar fechas al rango disponible
            const requestedStart = moment(startDate);
            const requestedEnd = moment(endDate);

            // Usar la intersección de los rangos
            const effectiveStart = moment.max(requestedStart, this.dataStart);
            const effectiveEnd = moment.min(requestedEnd, this.dataEnd);

            if (effectiveStart > effectiveEnd) {
                return {
                    byCountry: {},
                    global: this._calculateSummary([]),
                    metadata: {
                        totalCountries: 0,
                        totalRecords: 0,
                        generatedAt: new Date().toISOString(),
                        source: 'redis',
                        warning: 'No data available for the requested date range'
                    }
                };
            }

            // Obtener datos de Redis
            const client = redisConnection.getClient('metrics');
            
            // Buscar todas las claves de países
            const countryKeys = await client.KEYS('analytics:country:*'); // Cambio de keys a KEYS
            const countries = countryKeys.map(key => key.replace('analytics:country:', ''));
            
            const summaryByCountry = {};
            let allRecords = [];
            
            for (const country of countries) {
                try {
                    const countryData = await this._getRevenueFromRedis(country, effectiveStart, effectiveEnd, startDate, endDate);
                    if (countryData && countryData.data.length > 0) {
                        summaryByCountry[country] = countryData.summary;
                        allRecords = allRecords.concat(countryData.data);
                    }
                } catch (error) {
                    console.error(`Error getting data for ${country}:`, error);
                }
            }

            const globalSummary = this._calculateSummary(allRecords);

            const responseData = {
                byCountry: summaryByCountry,
                global: globalSummary,
                metadata: {
                    totalCountries: Object.keys(summaryByCountry).length,
                    totalRecords: allRecords.length,
                    generatedAt: new Date().toISOString(),
                    source: 'redis',
                    period: {
                        requested: { start: startDate, end: endDate },
                        effective: {
                            start: effectiveStart.format('YYYY-MM-DD'),
                            end: effectiveEnd.format('YYYY-MM-DD')
                        }
                    },
                    availableCountries: countries
                }
            };

            if (useCache) {
                await redisConnection.cacheSet(cacheKey, responseData, this.defaultTTL);
            }

            console.log(`📊 Revenue summary: ${Object.keys(summaryByCountry).length} countries, ${allRecords.length} records`);
            return responseData;

        } catch (error) {
            console.error('❌ Error getting revenue summary:', error);
            throw new Error(`Error obteniendo resumen de revenue: ${error.message}`);
        }
    }

    /**
     * Obtener revenue en tiempo real usando Redis
     */
    async getRealtimeRevenue() {
        try {
            const client = redisConnection.getClient('apiCache'); // Cambio de 'metrics' a 'apiCache' (DB 0)
            
            console.log('🔍 DEBUG Realtime: Buscando keys de países...');
            
            // Buscar todas las claves de países
            const countryKeys = await client.KEYS('analytics:country:*'); // Cambio de keys a KEYS
            console.log('🔍 DEBUG Realtime: Keys encontradas:', countryKeys);
            
            const countries = countryKeys.map(key => key.replace('analytics:country:', ''));
            console.log('🔍 DEBUG Realtime: Países extraídos:', countries);

            const realtimeData = {};
            
            for (const country of countries) {
                try {
                    const countryData = await client.HGETALL(`analytics:country:${country}`); // Cambio de hgetall a HGETALL
                    if (countryData && Object.keys(countryData).length > 0) {
                        realtimeData[country] = {
                            revenue: {
                                gbp: parseFloat(countryData.revenue) || 0,
                                usd: (parseFloat(countryData.revenue) || 0) * 1.25
                            },
                            orders: parseInt(countryData.orders) || 0,
                            customers: Math.ceil((parseInt(countryData.orders) || 0) * 0.7),
                            avgOrderValue: {
                                gbp: (parseFloat(countryData.revenue) || 0) / (parseInt(countryData.orders) || 1),
                                usd: ((parseFloat(countryData.revenue) || 0) / (parseInt(countryData.orders) || 1)) * 1.25
                            },
                            lastUpdate: new Date().toISOString()
                        };
                    }
                } catch (error) {
                    console.error(`Error getting realtime data for ${country}:`, error);
                }
            }

            return {
                data: realtimeData,
                metadata: {
                    totalCountries: Object.keys(realtimeData).length,
                    generatedAt: new Date().toISOString(),
                    source: 'redis'
                }
            };
        } catch (error) {
            console.error('❌ Error getting realtime revenue:', error);
            throw new Error(`Error obteniendo revenue en tiempo real: ${error.message}`);
        }
    }

    /**
     * Obtener lista de países disponibles
     */
    async getAvailableCountries() {
        try {
            const client = redisConnection.getClient('metrics');
            const countryKeys = await client.KEYS('analytics:country:*'); // Cambio de keys a KEYS
            const countries = countryKeys.map(key => key.replace('analytics:country:', ''));
            
            return countries.sort();
        } catch (error) {
            console.error('❌ Error getting available countries:', error);
            return ['United Kingdom', 'Germany', 'France']; // fallback
        }
    }

    // Métodos helper privados
    _calculateSummary(rows) {
        if (!rows || rows.length === 0) {
            return { totalRevenue: 0, totalOrders: 0, avgOrderValue: 0 };
        }

        const totalRevenueGBP = rows.reduce((sum, row) => sum + (parseFloat(row.revenue_gbp) || 0), 0);
        const totalRevenueUSD = rows.reduce((sum, row) => sum + (parseFloat(row.revenue_usd) || 0), 0);
        const totalOrders = rows.reduce((sum, row) => sum + (row.order_count || 0), 0);
        const uniqueCustomers = new Set(rows.map(row => row.customer_id)).size;

        return {
            totalRevenueGBP: Math.round(totalRevenueGBP * 100) / 100,
            totalRevenueUSD: Math.round(totalRevenueUSD * 100) / 100,
            totalOrders,
            uniqueCustomers,
            avgOrderValue: totalOrders > 0 ? Math.round((totalRevenueGBP / totalOrders) * 100) / 100 : 0
        };
    }

    _groupByCountry(rows) {
        const grouped = {};
        
        rows.forEach(row => {
            const country = row.country;
            if (!grouped[country]) {
                grouped[country] = [];
            }
            grouped[country].push({
                date: row.date_bucket,
                revenueGBP: parseFloat(row.total_revenue_gbp) || 0,
                revenueUSD: parseFloat(row.total_revenue_usd) || 0,
                orders: row.total_orders || 0,
                customers: row.total_customers || 0,
                avgOrderValue: parseFloat(row.avg_order_value) || 0
            });
        });

        return grouped;
    }

    _calculateGlobalSummary(countryData) {
        let totalRevenue = 0;
        let totalOrders = 0;
        let totalCustomers = 0;

        Object.values(countryData).forEach(countryRecords => {
            countryRecords.forEach(record => {
                totalRevenue += record.revenueGBP;
                totalOrders += record.orders;
                totalCustomers += record.customers;
            });
        });

        return {
            totalRevenueGBP: Math.round(totalRevenue * 100) / 100,
            totalOrders,
            totalCustomers,
            avgOrderValue: totalOrders > 0 ? Math.round((totalRevenue / totalOrders) * 100) / 100 : 0
        };
    }

    _calculateRealtimeSummary(rows) {
        const summary = this._calculateSummary(rows);
        const countries = new Set(rows.map(row => row.country));
        
        return {
            ...summary,
            countriesActive: countries.size,
            lastUpdate: rows.length > 0 ? rows[0].timestamp : null
        };
    }
}

module.exports = new RevenueService(); 