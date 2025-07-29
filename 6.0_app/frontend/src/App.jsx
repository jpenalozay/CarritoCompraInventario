import React, { useState, useEffect } from 'react';
import { Layout, Menu, Card, Row, Col, Statistic, Table, Select, DatePicker, Spin, Alert, Button } from 'antd';
import { 
  DollarCircleOutlined, 
  ShoppingCartOutlined, 
  UserOutlined, 
  GlobalOutlined,
  LineChartOutlined,
  DatabaseOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import moment from 'moment';
import axios from 'axios';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Option } = Select;
const { RangePicker } = DatePicker;

// Configuración de la API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const App = () => {
  // Estados principales
  const [loading, setLoading] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState('United Kingdom');
  const [dateRange, setDateRange] = useState([
    moment('2011-07-15'),
    moment('2011-07-22')
  ]);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Estados de datos
  const [dashboardData, setDashboardData] = useState({
    summary: null,
    realtime: null,
    revenue: [],
    countries: []
  });
  const [error, setError] = useState(null);

  // Cargar datos iniciales
  useEffect(() => {
    loadDashboardData();
    loadCountries();
  }, []);

  // Recargar datos cuando cambian los filtros
  useEffect(() => {
    if (selectedCountry && dateRange) {
      loadRevenueData();
      loadDashboardData(); // También recargar el dashboard cuando cambie el rango de fechas
    }
  }, [selectedCountry, dateRange]);

  // Función para cargar países disponibles
  const loadCountries = async () => {
    // Los países se cargan automáticamente con loadDashboardData()
    // desde el endpoint realtime que sí funciona
  };

  // Función para cargar datos del dashboard
  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // TEMPORAL: Solo usar realtime que sí funciona
      const realtimeRes = await axios.get(`${API_BASE_URL}/revenue/realtime`);
      
      // Extraer datos del realtime para calcular totales
      const realtimeData = realtimeRes.data.data;
      
      // Calcular totales desde realtime
      let totalRevenueGBP = 0;
      let totalOrders = 0;
      let totalCustomers = 0;
      const countries = Object.keys(realtimeData.data || {});
      
      countries.forEach(country => {
        const countryData = realtimeData.data[country];
        totalRevenueGBP += countryData.revenue?.gbp || 0;
        totalOrders += countryData.orders || 0;
        totalCustomers += countryData.customers || 0;
      });

      // Estructura compatible con el dashboard
      const summary = {
        globalSummary: {
          totalRevenueGBP: totalRevenueGBP,
          totalOrders: totalOrders,
          totalCustomers: totalCustomers
        },
        metadata: {
          totalCountries: countries.length
        }
      };

      setDashboardData(prev => ({
        ...prev,
        summary: summary,
        realtime: {
          data: realtimeData.data,
          summary: {
            totalRevenueGBP: totalRevenueGBP,
            totalOrders: totalOrders,
            countriesActive: countries.length
          }
        },
        countries: countries,  // Mantener como array de strings, no objetos
      }));
      setError(null);
    } catch (error) {
      setError('Error cargando datos del dashboard');
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Función para cargar datos de revenue específicos
  const loadRevenueData = async () => {
    if (!selectedCountry || !dateRange) return;
    
    setLoading(true);
    try {
      const startDate = dateRange[0].format('YYYY-MM-DD');
      const endDate = dateRange[1].format('YYYY-MM-DD');
      
      const response = await axios.get(
        `${API_BASE_URL}/revenue/country/${encodeURIComponent(selectedCountry)}`,
        {
          params: { startDate, endDate }
        }
      );

      setDashboardData(prev => ({
        ...prev,
        revenue: response.data.data.data
      }));
      setError(null);
    } catch (error) {
      setError('Error cargando datos de revenue');
      console.error('Error loading revenue data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Preparar datos para gráficos
  const chartData = (dashboardData.revenue || []).map(item => ({
    date: moment(item.date).format('MM/DD'),
    revenue: item.revenueGBP,
    orders: item.orderCount
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
            >
              {(dashboardData.countries || []).map(country => (
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

            <Table
              dataSource={dashboardData.revenue || []}
              columns={columns}
              rowKey={(record) => `${record.date}-${record.invoiceNo}`}
              style={{ marginTop: 24 }}
            />
          </>
        )}
      </Card>
    </div>
  );

  const renderRLDashboard = () => (
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
              <p><strong>Q-Table Size:</strong> <span id="rl-q-table-size">Cargando...</span></p>
              <p><strong>Epsilon:</strong> <span id="rl-epsilon">Cargando...</span></p>
              <p><strong>Learning Rate:</strong> <span id="rl-learning-rate">Cargando...</span></p>
              <p><strong>Current Episode:</strong> <span id="rl-episode">Cargando...</span></p>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="🛍️ Generar Recomendaciones">
              <p>Prueba el sistema de recomendaciones inteligente:</p>
              <Button 
                type="primary" 
                onClick={() => window.open('http://localhost:8050', '_blank')}
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