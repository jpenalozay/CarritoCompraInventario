#!/usr/bin/env python3
"""
Dashboard de Inventarios para Sistema de RL
"""

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
INVENTORY_API_URL = os.getenv('INVENTORY_API_URL', 'http://localhost:5001')

# Inicializar Dash
app = dash.Dash(__name__, title="Dashboard de Inventarios RL")
app.config.suppress_callback_exceptions = True

# Layout principal
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("📦 Dashboard de Gestión Inteligente de Inventarios", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '20px'}),
        html.H3("Sistema de Reinforcement Learning para Optimización de Inventarios",
                style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'})
    ]),
    
    # Métricas principales
    html.Div([
        html.Div([
            html.Div([
                html.H4("Nivel de Servicio", id="service-level"),
                html.P("98%", style={'fontSize': '24px', 'color': '#27ae60'})
            ], className="metric-card"),
            html.Div([
                html.H4("Rotación de Inventario", id="turnover"),
                html.P("8.5x", style={'fontSize': '24px', 'color': '#3498db'})
            ], className="metric-card"),
            html.Div([
                html.H4("Productos Críticos", id="critical-products"),
                html.P("12", style={'fontSize': '24px', 'color': '#e74c3c'})
            ], className="metric-card"),
            html.Div([
                html.H4("Ahorros Estimados", id="savings"),
                html.P("$15K", style={'fontSize': '24px', 'color': '#f39c12'})
            ], className="metric-card")
        ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'})
    ]),
    
    # Controles
    html.Div([
        html.Div([
            html.Label("Productos a Analizar:"),
            dcc.Input(id="stock-codes", value="GIFT001,GIFT002,GIFT003", 
                     style={'width': '300px', 'marginRight': '10px'}),
            html.Button("Obtener Recomendaciones", id="get-recommendations", 
                       style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'padding': '10px 20px'})
        ], style={'marginBottom': '20px'}),
        
        html.Div([
            html.Label("Filtrar por:"),
            dcc.Dropdown(
                id="filter-type",
                options=[
                    {'label': 'Todos', 'value': 'all'},
                    {'label': 'Críticos', 'value': 'critical'},
                    {'label': 'Bajos', 'value': 'low'},
                    {'label': 'Altos', 'value': 'high'}
                ],
                value='all',
                style={'width': '200px', 'display': 'inline-block', 'marginRight': '10px'}
            ),
            dcc.Dropdown(
                id="abc-filter",
                options=[
                    {'label': 'Todas las Clases', 'value': 'all'},
                    {'label': 'Clase A', 'value': 'A'},
                    {'label': 'Clase B', 'value': 'B'},
                    {'label': 'Clase C', 'value': 'C'}
                ],
                value='all',
                style={'width': '200px', 'display': 'inline-block'}
            )
        ], style={'marginBottom': '20px'})
    ]),
    
    # Gráficos principales
    html.Div([
        # Gráfico de distribución de inventario
        html.Div([
            html.H3("Distribución de Inventario por Clasificación ABC"),
            dcc.Graph(id="abc-distribution")
        ], style={'width': '50%', 'display': 'inline-block'}),
        
        # Gráfico de días de suministro
        html.Div([
            html.H3("Días de Suministro por Producto"),
            dcc.Graph(id="days-supply")
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),
    
    # Tabla de recomendaciones
    html.Div([
        html.H3("Recomendaciones de RL"),
        html.Div(id="recommendations-table")
    ], style={'marginTop': '30px'}),
    
    # Métricas del modelo
    html.Div([
        html.H3("Métricas del Modelo RL"),
        html.Div(id="model-metrics")
    ], style={'marginTop': '30px'}),
    
    # Actualización automática
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30 segundos
        n_intervals=0
    )
])

# Estilos CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <title>Dashboard de Inventarios RL</title>
        <style>
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                min-width: 150px;
            }
            body {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Callbacks
@app.callback(
    Output('abc-distribution', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_abc_distribution(n):
    """Actualizar gráfico de distribución ABC"""
    try:
        # Datos simulados para demostración
        data = {
            'Clasificación': ['A', 'B', 'C'],
            'Productos': [120, 350, 800],
            'Valor': [65, 25, 10]
        }
        df = pd.DataFrame(data)
        
        fig = px.bar(df, x='Clasificación', y='Productos', 
                    color='Valor', 
                    title="Distribución de Productos por Clasificación ABC",
                    color_continuous_scale='RdYlBu')
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#2c3e50')
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error updating ABC distribution: {e}")
        return go.Figure()

@app.callback(
    Output('days-supply', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_days_supply(n):
    """Actualizar gráfico de días de suministro"""
    try:
        # Datos simulados
        products = [f"PROD{i:03d}" for i in range(1, 21)]
        days_supply = [15, 8, 25, 12, 30, 5, 18, 22, 10, 35, 
                       7, 20, 28, 3, 16, 24, 9, 32, 14, 6]
        
        fig = px.bar(x=products, y=days_supply,
                    title="Días de Suministro por Producto",
                    labels={'x': 'Producto', 'y': 'Días de Suministro'})
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#2c3e50'),
            xaxis_tickangle=-45
        )
        
        # Agregar línea de referencia para 15 días
        fig.add_hline(y=15, line_dash="dash", line_color="red", 
                     annotation_text="Límite Óptimo (15 días)")
        
        return fig
    except Exception as e:
        logger.error(f"Error updating days supply: {e}")
        return go.Figure()

@app.callback(
    Output('recommendations-table', 'children'),
    [Input('get-recommendations', 'n_clicks'),
     Input('stock-codes', 'value')]
)
def update_recommendations(n_clicks, stock_codes):
    """Actualizar tabla de recomendaciones"""
    if not n_clicks:
        return html.P("Haz clic en 'Obtener Recomendaciones' para ver las sugerencias del RL")
    
    try:
        # Obtener recomendaciones del API
        stock_list = [code.strip() for code in stock_codes.split(',')]
        
        response = requests.post(
            f"{INVENTORY_API_URL}/api/v1/inventory/recommendations",
            json={"stock_codes": stock_list},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('data', {}).get('recommendations', {})
            
            if not recommendations:
                return html.P("No se encontraron recomendaciones")
            
            # Crear tabla
            table_data = []
            for stock_code, rec in recommendations.items():
                table_data.append({
                    'Producto': stock_code,
                    'Acción': rec.get('action', 'N/A'),
                    'Stock Actual': rec.get('current_stock', 0),
                    'Cantidad a Ordenar': rec.get('order_quantity', 0),
                    'Días de Suministro': rec.get('days_of_supply', 0),
                    'Riesgo de Desabasto': f"{rec.get('stockout_risk', 0)*100:.1f}%",
                    'Confianza': f"{rec.get('confidence', 0)*100:.1f}%",
                    'Prioridad': rec.get('priority', 'N/A')
                })
            
            df = pd.DataFrame(table_data)
            
            return dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'backgroundColor': 'white'
                },
                style_header={
                    'backgroundColor': '#3498db',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Acción} = "reorder_high"'},
                        'backgroundColor': '#e74c3c',
                        'color': 'white'
                    },
                    {
                        'if': {'filter_query': '{Acción} = "reorder_medium"'},
                        'backgroundColor': '#f39c12',
                        'color': 'white'
                    },
                    {
                        'if': {'filter_query': '{Acción} = "no_reorder"'},
                        'backgroundColor': '#27ae60',
                        'color': 'white'
                    }
                ]
            )
        else:
            return html.P(f"Error al obtener recomendaciones: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return html.P(f"Error: {str(e)}")

@app.callback(
    Output('model-metrics', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_model_metrics(n):
    """Actualizar métricas del modelo"""
    try:
        response = requests.get(f"{INVENTORY_API_URL}/api/v1/inventory/metrics")
        
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('data', {})
            
            return html.Div([
                html.Div([
                    html.H4("Métricas de Negocio"),
                    html.P(f"Nivel de Servicio: {metrics.get('business_metrics', {}).get('service_level', 0)*100:.1f}%"),
                    html.P(f"Tasa de Desabasto: {metrics.get('business_metrics', {}).get('stockout_rate', 0)*100:.1f}%"),
                    html.P(f"Rotación de Inventario: {metrics.get('business_metrics', {}).get('avg_inventory_turnover', 0):.1f}x"),
                    html.P(f"Costo de Mantenimiento: {metrics.get('business_metrics', {}).get('holding_cost_ratio', 0)*100:.1f}%")
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H4("Optimización de Costos"),
                    html.P(f"Ahorros Estimados: ${metrics.get('cost_optimization', {}).get('estimated_savings', 0):,.0f}"),
                    html.P(f"Costo Total de Mantenimiento: ${metrics.get('cost_optimization', {}).get('total_holding_cost', 0):,.0f}"),
                    html.P(f"Costo Total de Desabasto: ${metrics.get('cost_optimization', {}).get('total_stockout_cost', 0):,.0f}")
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    html.H4("Parámetros del Modelo RL"),
                    html.P(f"Learning Rate: {metrics.get('model_performance', {}).get('learning_rate', 0)}"),
                    html.P(f"Epsilon: {metrics.get('model_performance', {}).get('epsilon', 0)}"),
                    html.P(f"Discount Factor: {metrics.get('model_performance', {}).get('discount_factor', 0)}"),
                    html.P(f"Tamaño Q-Table: {metrics.get('model_performance', {}).get('q_table_size', 0)}")
                ], style={'width': '100%', 'marginTop': '20px'})
            ])
        else:
            return html.P(f"Error al obtener métricas: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error getting model metrics: {e}")
        return html.P(f"Error: {str(e)}")

if __name__ == '__main__':
    logger.info("🚀 Iniciando Dashboard de Inventarios RL...")
    logger.info(f"📊 Dashboard disponible en: http://localhost:8051")
    logger.info(f"🔗 API de Inventarios: {INVENTORY_API_URL}")
    
    app.run_server(
        host='0.0.0.0',
        port=8051,
        debug=True
    )

