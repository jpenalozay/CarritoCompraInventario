import React, { useState, useEffect } from 'react';
import { Layout, Menu, Card, Row, Col, Statistic, Table, DatePicker, Select, Button, Alert, Spin } from 'antd';
import { LineChartOutlined, DollarCircleOutlined, DatabaseOutlined, RobotOutlined, ShoppingCartOutlined, UserOutlined, GlobalOutlined, InboxOutlined } from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';

const { Header, Sider, Content } = Layout;
const { RangePicker } = DatePicker;
const { Option } = Select;

// Configuración de URLs
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3003/api/v1';
const RL_API_URL = import.meta.env.VITE_RL_API_URL || 'http://localhost:5000/api/v1';
const RL_DASHBOARD_URL = import.meta.env.VITE_RL_DASHBOARD_URL || 'http://localhost:8050';
const INVENTORY_DASHBOARD_URL = import.meta.env.VITE_INVENTORY_DASHBOARD_URL || 'http://localhost:8051';

const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState({
    summary: {},
    revenue: [],
    realtime: {}
  });
  const [selectedCountry, setSelectedCountry] = useState('United Kingdom');
  const [dateRange, setDateRange] = useState([moment('2011-07-15'), moment('2011-07-22')]);
  const [availableCountries, setAvailableCountries] = useState([]);
  const [rlData, setRlData] = useState({
    q_table_size: 'Cargando...',
    epsilon: 'Cargando...',
    learning_rate: 'Cargando...',
    current_episode: 'Cargando...'
  });
  const [inventoryData, setInventoryData] = useState({
    service_level: 'Cargando...',
    turnover: 'Cargando...',
    critical_products: 'Cargando...',
    estimated_savings: 'Cargando...'
  });

  // Cargar datos del RL cuando el componente se monte
  useEffect(() => {
    if (activeTab === 'rl') {
      loadRLData();
    }
  }, [activeTab]);

  // Cargar datos de inventario cuando se seleccione la pestaña
  useEffect(() => {
    if (activeTab === 'inventory') {
      loadInventoryData();
    }
  }, [activeTab]);

  // Cargar datos específicos de país cuando cambie la selección
  useEffect(() => {
    if (selectedCountry && selectedCountry !== 'United Kingdom') {
      loadCountrySpecificData();
    }
  }, [selectedCountry]);

  // Cargar datos cuando cambien las fechas
  useEffect(() => {
    if (dateRange && dateRange.length === 2) {
      loadRevenueDataWithDateRange();
    }
  }, [dateRange]);

  // Cargar datos iniciales del dashboard
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadCountries = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/revenue/countries`);      
      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      return [];
    } catch (error) {
      console.error('Error cargando países:', error);
      return [];
    }
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Cargar datos de revenue realtime (que tiene los datos correctos)
      const realtimeResponse = await axios.get(`${API_BASE_URL}/revenue/realtime`);      
      const realtimeData = realtimeResponse.data.success ? realtimeResponse.data.data : {};
      
      // Cargar países disponibles
      const countriesResponse = await axios.get(`${API_BASE_URL}/revenue/countries`);
      const countries = countriesResponse.data.success ? countriesResponse.data.data : [];
      setAvailableCountries(countries);
      
      // Calcular summary global desde los datos realtime
      const realtimeCountries = Object.keys(realtimeData.data || {});
      let totalRevenueGBP = 0;
      let totalOrders = 0;
      let totalCustomers = 0;
      
      realtimeCountries.forEach(country => {
        const countryData = realtimeData.data[country];
        totalRevenueGBP += countryData.revenue.gbp || 0;
        totalOrders += countryData.orders || 0;
        totalCustomers += countryData.customers || 0;
      });
      
      const summary = {
        globalSummary: {
          totalRevenueGBP: Math.round(totalRevenueGBP * 100) / 100,
          totalOrders,
          totalCustomers
        },
        metadata: {
          totalCountries: realtimeCountries.length
        }
      };
      
      // Calcular datos de actividad en tiempo real (últimas 24h)
      const realtimeSummary = {
        totalRevenueGBP: Math.round(totalRevenueGBP * 100) / 100,
        totalOrders,
        totalCustomers,
        countriesActive: realtimeCountries.length
      };

      setDashboardData({
        summary,
        revenue: realtimeData.data || {},
        realtime: {
          summary: realtimeSummary,
          data: realtimeData.data || {}
        }
      });
      
    } catch (error) {
      console.error('Error cargando datos del dashboard:', error);      
      setError(`Error cargando datos del dashboard: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadRevenueData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/revenue/summary`);      
      if (response.data.success) {
        return response.data.data.byCountry || {};
      }
      return {};
    } catch (error) {
      console.error('Error cargando datos de revenue:', error);
      return [];
    }
  };

  const loadRevenueDataWithDateRange = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!dateRange || dateRange.length !== 2) {
        return;
      }

      const startDate = dateRange[0].format('YYYY-MM-DD');
      const endDate = dateRange[1].format('YYYY-MM-DD');
      
      // Cargar datos con filtro de fechas
      const response = await axios.get(`${API_BASE_URL}/revenue/summary`, {
        params: {
          startDate,
          endDate
        }
      });
      
      if (response.data.success) {
        const revenueData = response.data.data.byCountry || {};
        
        // Calcular summary global desde los datos filtrados
        const countries = Object.keys(revenueData);
        let totalRevenueGBP = 0;
        let totalOrders = 0;
        let totalCustomers = 0;
        
        countries.forEach(country => {
          const countryData = revenueData[country];
          totalRevenueGBP += countryData.totalRevenueGBP || 0;
          totalOrders += countryData.totalOrders || 0;
          totalCustomers += countryData.uniqueCustomers || 0;
        });
        
        const summary = {
          globalSummary: {
            totalRevenueGBP: Math.round(totalRevenueGBP * 100) / 100,
            totalOrders,
            totalCustomers
          },
          metadata: {
            totalCountries: countries.length
          }
        };
        
        // Actualizar los datos del dashboard con los nuevos datos filtrados
        setDashboardData(prev => ({
          ...prev,
          summary,
          revenue: revenueData
        }));
      }
    } catch (error) {
      console.error('Error cargando datos con filtro de fechas:', error);
      setError(`Error cargando datos: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadCountrySpecificData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/revenue/country/${encodeURIComponent(selectedCountry)}`);
      if (response.data.success) {
        // Actualizar los datos del dashboard con los datos específicos del país
        const countryData = response.data.data;
        setDashboardData(prev => ({
          ...prev,
          selectedCountryData: countryData
        }));
      }
    } catch (error) {
      console.error('Error cargando datos específicos del país:', error);
    }
  };

  const loadRLData = async () => {
    try {
      const response = await axios.get(`${RL_API_URL}/rl/agent/state`);      
      if (response.data.success) {
        const data = response.data.data;
        setRlData({
          q_table_size: data.q_table_size,
          epsilon: data.epsilon,
          learning_rate: data.learning_rate,
          current_episode: data.current_episode
        });
      }
    } catch (error) {
      console.error('Error cargando datos del RL:', error);
      setRlData({
        q_table_size: 'Error',
        epsilon: 'Error',
        learning_rate: 'Error',
        current_episode: 'Error'
      });
    }
  };

  const loadInventoryData = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/v1/inventory/metrics');
      if (response.data.success) {
        const data = response.data.data;
        setInventoryData({
          service_level: `${(data.business_metrics?.service_level || 0) * 100}%`,
          turnover: `${data.business_metrics?.avg_inventory_turnover || 0}x`,
          critical_products: '12', // Simulado por ahora
          estimated_savings: `$${(data.cost_optimization?.estimated_savings || 0).toLocaleString()}`
        });
      }
    } catch (error) {
      console.error('Error cargando datos de inventario:', error);
      setInventoryData({
        service_level: 'Error',
        turnover: 'Error',
        critical_products: 'Error',
        estimated_savings: 'Error'
      });
    }
  };

  // Preparar datos para gráficos - filtrar por país seleccionado
  const chartData = Object.entries(dashboardData.revenue || {})
    .filter(([country, data]) => {
      // Si no hay país seleccionado o es "United Kingdom" (default), mostrar todos
      if (!selectedCountry || selectedCountry === 'United Kingdom') {
        return true;
      }
      // Si hay país seleccionado, filtrar solo ese país
      return country === selectedCountry;
    })
    .map(([country, data]) => ({
      country: country,
      revenue: data.totalRevenueGBP || 0,
      orders: data.totalOrders || 0,
      customers: data.uniqueCustomers || 0
    }));

  // Columnas para la tabla de datos detallados
  const columns = [
    {
      title: 'Fecha',
      dataIndex: 'date',
      key: 'date',
      render: (date) => moment(date).format('YYYY-MM-DD HH:mm')
    },
    {
      title: 'Invoice',
      dataIndex: 'invoiceNo',
      key: 'invoiceNo'
    },
    {
      title: 'Cliente',
      dataIndex: 'customerId',
      key: 'customerId'
    },
    {
      title: 'Revenue (GBP)',
      dataIndex: 'revenueGBP',
      key: 'revenueGBP',
      render: (value) => `£${value.toFixed(2)}`
    },
    {
      title: 'Revenue (USD)',
      dataIndex: 'revenueUSD',
      key: 'revenueUSD',
      render: (value) => `$${value.toFixed(2)}`
    },
    {
      title: 'Órdenes',
      dataIndex: 'orderCount',
      key: 'orderCount'
    }
  ];

  // Items del menú
  const menuItems = [
    {
      key: 'dashboard',
      icon: <LineChartOutlined />,
      label: 'Dashboard'
    },
    {
      key: 'revenue',
      icon: <DollarCircleOutlined />,
      label: 'Revenue Analysis'
    },
    {
      key: 'realtime',
      icon: <DatabaseOutlined />,
      label: 'Real-time Metrics'
    },
    {
      key: 'rl',
      icon: <RobotOutlined />,
      label: 'AI Recommendations'
    },
    {
      key: 'inventory',
      icon: <InboxOutlined />,
      label: 'Inventarios'
    }
  ];

  const renderDashboard = () => (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Revenue Total (GBP)"
              value={dashboardData.summary?.globalSummary?.totalRevenueGBP || 0}
              precision={2}
              valueStyle={{ color: '#3f8600' }}
              prefix={<DollarCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Órdenes"
              value={dashboardData.summary?.globalSummary?.totalOrders || 0}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Clientes"
              value={dashboardData.summary?.globalSummary?.totalCustomers || 0}
              valueStyle={{ color: '#722ed1' }}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Países Activos"
              value={dashboardData.summary?.metadata?.totalCountries || 0}
              valueStyle={{ color: '#f5222d' }}
              prefix={<GlobalOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {dashboardData.realtime && (
        <Card title="Actividad en Tiempo Real (Últimas 24h)" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic
                title="Revenue Activo"
                value={dashboardData.realtime.summary?.totalRevenueGBP || 0}
                precision={2}
                prefix="£"
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Órdenes Activas"
                value={dashboardData.realtime.summary?.totalOrders || 0}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Países Activos"
                value={dashboardData.realtime.summary?.countriesActive || 0}
              />
            </Col>
          </Row>
        </Card>
      )}
    </div>
  );

  const renderRevenueAnalysis = () => (
    <div>
      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Card title="Revenue Analysis" style={{ marginBottom: 24 }}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}>
            <Select
              style={{ width: '100%' }}
              value={selectedCountry}
              onChange={setSelectedCountry}
              loading={loading}
              placeholder="Seleccionar país"
            >
              {availableCountries.map(country => (
                <Option key={country} value={country}>{country}</Option>
              ))}
            </Select>
          </Col>
          <Col span={12}>
            <RangePicker
              style={{ width: '100%' }}
              value={dateRange}
              onChange={setDateRange}
              disabled={loading}
            />
          </Col>
        </Row>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
          </div>
        ) : (
          <>
            {/* The chart component was removed from imports, so this section is commented out */}
            {/*
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="revenue" stroke="#8884d8" name="Revenue (GBP)" />
                <Line type="monotone" dataKey="orders" stroke="#82ca9d" name="Orders" />
              </LineChart>
            </ResponsiveContainer>
            */}

            <Table
              dataSource={chartData}
              columns={[
                {
                  title: 'País',
                  dataIndex: 'country',
                  key: 'country'
                },
                {
                  title: 'Revenue (GBP)',
                  dataIndex: 'revenue',
                  key: 'revenue',
                  render: (value) => `£${value.toLocaleString()}`
                },
                {
                  title: 'Órdenes',
                  dataIndex: 'orders',
                  key: 'orders'
                },
                {
                  title: 'Clientes',
                  dataIndex: 'customers',
                  key: 'customers'
                }
              ]}
              rowKey={(record) => record.country}
              style={{ marginTop: 24 }}
            />
          </>
        )}
      </Card>
    </div>
  );

  const renderRLDashboard = () => {
    return (
      <div>
        <Card title="🤖 AI Recommendations - Reinforcement Learning" style={{ marginBottom: 24 }}>
          <Alert
            message="Dashboard de RL"
            description="El dashboard completo de Reinforcement Learning está disponible en una ventana separada. Haz clic en el botón para abrirlo."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Row gutter={16}>
            <Col span={12}>
              <Card title="📊 Estado del Agente RL">
                <p><strong>Q-Table Size:</strong> <span id="rl-q-table-size">{rlData.q_table_size}</span></p>
                <p><strong>Epsilon:</strong> <span id="rl-epsilon">{rlData.epsilon}</span></p>
                <p><strong>Learning Rate:</strong> <span id="rl-learning-rate">{rlData.learning_rate}</span></p>
                <p><strong>Current Episode:</strong> <span id="rl-episode">{rlData.current_episode}</span></p>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="🛍️ Generar Recomendaciones">
                <p>Prueba el sistema de recomendaciones inteligente:</p>
                <Button 
                  type="primary" 
                  onClick={() => window.open(RL_DASHBOARD_URL, '_blank')}                  
                  icon={<RobotOutlined />}
                >
                  Abrir Dashboard RL Completo
                </Button>
              </Card>
            </Col>
          </Row>
        </Card>
      </div>
    );
  };

  const renderInventoryDashboard = () => {
    return (
      <div>
        <Card title="📦 Gestión Inteligente de Inventarios" style={{ marginBottom: 24 }}>
          <Alert
            message="Dashboard de Inventarios"
            description="El sistema de RL para gestión de inventarios está disponible en una ventana separada. Haz clic en el botón para abrirlo."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Row gutter={16}>
            <Col span={12}>
              <Card title="📊 Métricas de Inventario">
                <p><strong>Nivel de Servicio:</strong> <span id="inventory-service-level">{inventoryData.service_level}</span></p>
                <p><strong>Rotación de Inventario:</strong> <span id="inventory-turnover">{inventoryData.turnover}</span></p>
                <p><strong>Productos Críticos:</strong> <span id="inventory-critical">{inventoryData.critical_products}</span></p>
                <p><strong>Ahorros Estimados:</strong> <span id="inventory-savings">{inventoryData.estimated_savings}</span></p>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="🛍️ Gestión de Inventarios">
                <p>Prueba el sistema de gestión inteligente de inventarios:</p>
                <Button 
                  type="primary" 
                  onClick={() => window.open(INVENTORY_DASHBOARD_URL, '_blank')}                  
                  icon={<InboxOutlined />}
                >
                  Abrir Dashboard de Inventarios
                </Button>
              </Card>
            </Col>
          </Row>
        </Card>
      </div>
    );
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16 }}>Cargando datos...</p>
        </div>
      );
    }

    if (error) {
      return (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          style={{ margin: 24 }}
        />
      );
    }

    switch (activeTab) {
      case 'dashboard':
        return renderDashboard();
      case 'revenue':
        return renderRevenueAnalysis();
      case 'realtime':
        return renderDashboard(); // Por ahora usa el mismo componente
      case 'rl':
        return renderRLDashboard();
      case 'inventory':
        return renderInventoryDashboard();
      default:
        return renderDashboard();
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" width={200}>
        <div style={{ color: 'white', padding: '16px', textAlign: 'center', fontSize: '18px', fontWeight: 'bold' }}>
          E-commerce Analytics
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[activeTab]}
          items={menuItems}
          onClick={(e) => setActiveTab(e.key)}
        />
      </Sider>
      
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px' }}>
          <h1 style={{ margin: 0, fontSize: '24px' }}>
            Dashboard de Analytics - {selectedCountry}
          </h1>
        </Header>
        
        <Content style={{ margin: '24px' }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App; 