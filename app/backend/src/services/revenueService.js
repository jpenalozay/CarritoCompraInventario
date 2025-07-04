const cassandraConnection = require('../database/cassandra');
const redisConnection = require('../database/redis');
const moment = require('moment');

class RevenueService {
    constructor() {
        this.cachePrefix = 'revenue';
        this.defaultTTL = 300; // 5 minutos
    }

    /**
     * Obtener revenue por país en un rango de fechas
     */
    async getRevenueByCountry(country, startDate, endDate, useCache = true) {
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
            // Obtener datos para cada fecha en el rango
            const dateRange = [];
            let currentDate = moment(startDate);
            const endMoment = moment(endDate);
            
            while (currentDate <= endMoment) {
                dateRange.push(currentDate.format('YYYY-MM-DD'));
                currentDate.add(1, 'days');
            }

            // Consultar datos para cada fecha
            const promises = dateRange.map(date => {
                const query = `
                    SELECT 
                        country, date_bucket, hour, timestamp,
                        invoice_no, customer_id, revenue_gbp, revenue_usd,
                        order_count, customer_count, avg_order_value
                    FROM revenue_by_country_time 
                    WHERE country = ? 
                    AND date_bucket = ?
                    ORDER BY hour ASC, timestamp DESC
                `;
                return cassandraConnection.executeQuery(query, [country, date]);
            });

            const results = await Promise.all(promises);
            const allRows = results.flatMap(result => result.rows);

            // Ordenar los resultados en memoria
            allRows.sort((a, b) => {
                if (a.hour !== b.hour) return b.hour - a.hour; // DESC
                return moment(b.timestamp).valueOf() - moment(a.timestamp).valueOf(); // DESC
            });

            const revenueData = {
                country,
                period: { start: startDate, end: endDate },
                data: allRows.map(row => ({
                    date: row.date_bucket,
                    hour: row.hour,
                    timestamp: row.timestamp,
                    invoiceNo: row.invoice_no,
                    customerId: row.customer_id,
                    revenueGBP: parseFloat(row.revenue_gbp) || 0,
                    revenueUSD: parseFloat(row.revenue_usd) || 0,
                    orderCount: row.order_count || 0,
                    customerCount: row.customer_count || 0,
                    avgOrderValue: parseFloat(row.avg_order_value) || 0
                })),
                summary: this._calculateSummary(allRows),
                metadata: {
                    totalRecords: allRows.length,
                    generatedAt: new Date().toISOString(),
                    source: 'cassandra'
                }
            };

            // Guardar en cache
            if (useCache) {
                await redisConnection.cacheSet(cacheKey, revenueData, this.defaultTTL);
            }

            console.log(`📊 Revenue data for ${country}: ${allRows.length} records`);
            return revenueData;

        } catch (error) {
            console.error('❌ Error getting revenue by country:', error);
            throw new Error(`Error obteniendo revenue para ${country}: ${error.message}`);
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
            // Obtener lista de países y fechas disponibles
            const query = `
                SELECT DISTINCT country, date_bucket
                FROM revenue_by_country_time
                WHERE date_bucket = ?
                ALLOW FILTERING
            `;

            const today = moment().format('YYYY-MM-DD');
            const result = await cassandraConnection.executeQuery(query, [today]);
            
            // Extraer países únicos
            const countries = [...new Set(result.rows.map(row => row.country))];

            // Obtener datos para cada país
            const promises = countries.map(async (country) => {
                const query = `
                    SELECT 
                        country, date_bucket, hour, timestamp,
                        revenue_gbp, revenue_usd, order_count, 
                        customer_count, avg_order_value
                    FROM revenue_by_country_time 
                    WHERE country = ? 
                    AND date_bucket = ?
                    ORDER BY hour ASC, timestamp DESC
                `;
                const result = await cassandraConnection.executeQuery(query, [country, today]);
                return {
                    country,
                    records: result.rows || []
                };
            });

            const countryResults = await Promise.all(promises);
            
            // Calcular resumen por país
            const summaryByCountry = {};
            countryResults.forEach(({ country, records }) => {
                summaryByCountry[country] = this._calculateSummary(records);
            });

            // Calcular resumen global
            const allRecords = countryResults.flatMap(({ records }) => records);
            const globalSummary = this._calculateSummary(allRecords);

            const responseData = {
                byCountry: summaryByCountry,
                global: globalSummary,
                metadata: {
                    totalCountries: countries.length,
                    totalRecords: allRecords.length,
                    generatedAt: new Date().toISOString(),
                    source: 'cassandra'
                }
            };

            if (useCache) {
                await redisConnection.cacheSet(cacheKey, responseData, this.defaultTTL);
            }

            return responseData;

        } catch (error) {
            console.error('❌ Error getting revenue summary:', error);
            throw new Error(`Error obteniendo resumen de revenue: ${error.message}`);
        }
    }

    /**
     * Obtener revenue en tiempo real (últimas 24 horas)
     */
    async getRealtimeRevenue() {
        try {
            // Obtener lista de países para la fecha actual
            const query = `
                SELECT DISTINCT country, date_bucket
                FROM revenue_by_country_time
                WHERE date_bucket = ?
                ALLOW FILTERING
            `;

            const today = moment().format('YYYY-MM-DD');
            const result = await cassandraConnection.executeQuery(query, [today]);
            
            // Extraer países únicos
            const countries = [...new Set(result.rows.map(row => row.country))];

            // Obtener datos en tiempo real para cada país
            const promises = countries.map(async (country) => {
                const query = `
                    SELECT 
                        country, date_bucket, hour, timestamp,
                        revenue_gbp, revenue_usd, order_count,
                        customer_count, avg_order_value
                    FROM revenue_by_country_time 
                    WHERE country = ? 
                    AND date_bucket = ?
                    ORDER BY hour ASC, timestamp DESC
                    LIMIT 1
                `;
                const result = await cassandraConnection.executeQuery(query, [country, today]);
                return result.rows[0] || null;
            });

            const results = await Promise.all(promises);
            const realtimeData = results.filter(Boolean).reduce((acc, row) => {
                acc[row.country] = {
                    revenue: {
                        gbp: parseFloat(row.revenue_gbp) || 0,
                        usd: parseFloat(row.revenue_usd) || 0
                    },
                    orders: row.order_count || 0,
                    customers: row.customer_count || 0,
                    avgOrderValue: {
                        gbp: parseFloat(row.avg_order_value) || 0,
                        usd: (parseFloat(row.avg_order_value) || 0) * 1.25
                    },
                    lastUpdate: row.timestamp
                };
                return acc;
            }, {});

            return {
                data: realtimeData,
                metadata: {
                    totalCountries: Object.keys(realtimeData).length,
                    generatedAt: new Date().toISOString(),
                    source: 'cassandra'
                }
            };
        } catch (error) {
            console.error('❌ Error getting realtime revenue:', error);
            throw new Error(`Error obteniendo revenue en tiempo real: ${error.message}`);
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