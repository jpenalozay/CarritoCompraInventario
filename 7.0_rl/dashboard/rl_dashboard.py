#!/usr/bin/env python3
"""
Dashboard de Dash para el componente de Reinforcement Learning
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import numpy as np

# Configuración
RL_API_URL = "http://localhost:5000/api/v1/rl"

# Inicializar app Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "RL E-commerce Dashboard"

# Layout principal
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🤖 Reinforcement Learning Dashboard", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # Métricas principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Q-Table Size", className="card-title"),
                    html.H2(id="q-table-size", children="0")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Epsilon", className="card-title"),
                    html.H2(id="epsilon-value", children="0.1")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Learning Rate", className="card-title"),
                    html.H2(id="learning-rate", children="0.01")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Current Episode", className="card-title"),
                    html.H2(id="current-episode", children="N/A")
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Gráficos principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 Recompensas por Episodio"),
                dbc.CardBody([
                    dcc.Graph(id="rewards-chart")
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎯 Distribución de Acciones"),
                dbc.CardBody([
                    dcc.Graph(id="actions-chart")
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    # Gráficos de métricas
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Métricas del Modelo"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id="metric-selector",
                        options=[
                            {"label": "Conversion Rate", "value": "conversion_rate"},
                            {"label": "Average Reward", "value": "avg_reward"},
                            {"label": "Confidence Score", "value": "confidence_score"},
                            {"label": "Revenue Generated", "value": "revenue_generated"}
                        ],
                        value="conversion_rate"
                    ),
                    dcc.Graph(id="metrics-chart")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Sección de recomendaciones
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🛍️ Generador de Recomendaciones"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(
                                id="customer-id-input",
                                placeholder="Customer ID",
                                type="text",
                                value="CUST001"
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Button("Generar Recomendaciones", id="generate-btn", color="primary")
                        ], width=6)
                    ], className="mb-3"),
                    html.Div(id="recommendations-output")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Historial de recomendaciones
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📋 Historial de Recomendaciones"),
                dbc.CardBody([
                    dcc.Graph(id="recommendations-history")
                ])
            ])
        ], width=12)
    ]),
    
    # Intervalo de actualización
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30 segundos
        n_intervals=0
    )
], fluid=True)

# Callbacks
@app.callback(
    [Output("q-table-size", "children"),
     Output("epsilon-value", "children"),
     Output("learning-rate", "children"),
     Output("current-episode", "children")],
    [Input("interval-component", "n_intervals")]
)
def update_agent_metrics(n):
    """Actualizar métricas del agente"""
    try:
        response = requests.get(f"{RL_API_URL}/agent/state")
        if response.status_code == 200:
            data = response.json()["data"]
            return (
                data["q_table_size"],
                f"{data['epsilon']:.3f}",
                f"{data['learning_rate']:.3f}",
                data["current_episode"][:8] + "..."
            )
    except:
        pass
    return "0", "0.100", "0.010", "N/A"

@app.callback(
    Output("rewards-chart", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_rewards_chart(n):
    """Actualizar gráfico de recompensas"""
    try:
        # Simular datos de recompensas (en producción vendrían de la API)
        episodes = list(range(1, 21))
        rewards = [np.random.normal(0.5, 0.2) for _ in episodes]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=episodes,
            y=rewards,
            mode='lines+markers',
            name='Recompensa',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Evolución de Recompensas por Episodio",
            xaxis_title="Episodio",
            yaxis_title="Recompensa",
            height=400
        )
        
        return fig
    except:
        return go.Figure()

@app.callback(
    Output("actions-chart", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_actions_chart(n):
    """Actualizar gráfico de distribución de acciones"""
    try:
        # Simular datos de acciones
        actions = ['low_price', 'medium_price', 'high_price', 'popular', 'personalized']
        counts = [np.random.randint(10, 50) for _ in actions]
        
        fig = go.Figure(data=[
            go.Bar(x=actions, y=counts, marker_color='lightblue')
        ])
        
        fig.update_layout(
            title="Distribución de Acciones del Agente",
            xaxis_title="Tipo de Acción",
            yaxis_title="Frecuencia",
            height=400
        )
        
        return fig
    except:
        return go.Figure()

@app.callback(
    Output("metrics-chart", "figure"),
    [Input("metric-selector", "value"),
     Input("interval-component", "n_intervals")]
)
def update_metrics_chart(metric, n):
    """Actualizar gráfico de métricas"""
    try:
        # Simular datos de métricas
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=7, freq='D')
        values = [np.random.uniform(0.3, 0.8) for _ in dates]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=metric.replace('_', ' ').title(),
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f"Evolución de {metric.replace('_', ' ').title()}",
            xaxis_title="Fecha",
            yaxis_title="Valor",
            height=400
        )
        
        return fig
    except:
        return go.Figure()

@app.callback(
    Output("recommendations-output", "children"),
    [Input("generate-btn", "n_clicks")],
    [Input("customer-id-input", "value")]
)
def generate_recommendations(n_clicks, customer_id):
    """Generar recomendaciones para un cliente"""
    if n_clicks is None:
        return ""
    
    try:
        response = requests.post(f"{RL_API_URL}/recommendations", 
                               json={"customer_id": customer_id})
        
        if response.status_code == 200:
            data = response.json()["data"]
            
            return dbc.Alert([
                html.H5("✅ Recomendaciones Generadas"),
                html.P(f"Cliente: {data['customer_id']}"),
                html.P(f"Confianza: {data['confidence_score']:.3f}"),
                html.P(f"Tipo de Acción: {data['action_type']}"),
                html.H6("Productos Recomendados:"),
                html.Ul([html.Li(product) for product in data['recommendations']])
            ], color="success")
        else:
            return dbc.Alert("❌ Error generando recomendaciones", color="danger")
            
    except Exception as e:
        return dbc.Alert(f"❌ Error: {str(e)}", color="danger")

@app.callback(
    Output("recommendations-history", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_recommendations_history(n):
    """Actualizar historial de recomendaciones"""
    try:
        # Simular datos de historial
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=7, freq='D')
        conversion_rates = [np.random.uniform(0.1, 0.4) for _ in dates]
        confidence_scores = [np.random.uniform(0.6, 0.9) for _ in dates]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=conversion_rates,
            mode='lines+markers',
            name='Tasa de Conversión',
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=confidence_scores,
            mode='lines+markers',
            name='Score de Confianza',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Historial de Rendimiento de Recomendaciones",
            xaxis_title="Fecha",
            yaxis=dict(title="Tasa de Conversión", side="left"),
            yaxis2=dict(title="Score de Confianza", side="right", overlaying="y"),
            height=400
        )
        
        return fig
    except:
        return go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050) 