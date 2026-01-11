import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================

st.set_page_config(
    page_title="Mekasfi Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para design profissional
st.markdown("""
<style>
    /* Importa fonte Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Aplica fonte em todo o app */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Remove padding superior */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Estilo do header */
    h1 {
        color: #0066cc;
        font-weight: 700;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        color: #212529;
        font-weight: 600;
        font-size: 1.5rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        color: #495057;
        font-weight: 600;
        font-size: 1.1rem !important;
    }
    
    /* Estilo das métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Tabelas */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Botão sidebar */
    .stButton button {
        background-color: #0066cc;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        border: none;
    }
    
    .stButton button:hover {
        background-color: #0052a3;
    }
    
    /* Divisor */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CONSTANTES E CONFIGURAÇÕES
# ==============================================================================

# Cores padronizadas (baseadas no PDF original)
COLORS = {
    'mksf': '#0066cc',      # Azul Mekasfi
    'ibov': '#dc3545',      # Vermelho para Ibovespa
    'positive': '#28a745',  # Verde para valores positivos
    'negative': '#dc3545',  # Vermelho para valores negativos
    'grid': '#e9ecef',      # Cinza claro para grid
    'background': '#ffffff' # Fundo branco
}

# Configuração base dos gráficos
CHART_CONFIG = {
    'font_family': 'Inter, sans-serif',
    'font_size': 12,
    'title_size': 16,
    'height': 400,
    'margin': dict(l=60, r=40, t=60, b=60),
    'plot_bgcolor': COLORS['background'],
    'paper_bgcolor': COLORS['background'],
}

# ==============================================================================
# FUNÇÕES DE CARREGAMENTO E PROCESSAMENTO
# ==============================================================================

@st.cache_data
def load_data():
    """Carrega dados do Excel com cache"""
    try:
        with pd.ExcelFile("PyDATA.xlsx") as xls:
            df = pd.read_excel(xls, 'MKSF', index_col=0)
            return df
    except FileNotFoundError:
        st.error("⚠️ Arquivo 'PyDATA.xlsx' não encontrado. Certifique-se de que está no mesmo diretório.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar arquivo: {str(e)}")
        st.stop()

def process_data(df):
    """Processa e calcula todas as métricas necessárias"""
    df = df.copy()
    
    # Cálculos básicos
    df['CotaMKSF'] = df['PL_MKSF'] / df['Qtd_Cotas']
    df['IBOVdaily'] = df['IBOV'].pct_change()
    df['MKSFdaily'] = df['CotaMKSF'].pct_change()
    
    # Retornos acumulados
    df['IBOVacum'] = (1 + df['IBOVdaily']).cumprod() - 1
    df['MKSFacum'] = (1 + df['MKSFdaily']).cumprod() - 1
    df['Spread'] = df['MKSFacum'] - df['IBOVacum']
    
    return df

# ==============================================================================
# FUNÇÕES DE VISUALIZAÇÃO
# ==============================================================================

def create_cumulative_return_chart(df):
    """Cria gráfico de retorno acumulado"""
    fig = go.Figure()
    
    # Linha IBOV
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['IBOVacum'] * 100,
        mode='lines',
        name='IBOV',
        line=dict(color=COLORS['ibov'], width=2),
        hovertemplate='%{x|%d/%m/%Y}<br>IBOV: %{y:.2f}%<extra></extra>'
    ))
    
    # Linha MKSF
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['MKSFacum'] * 100,
        mode='lines',
        name='MKSF',
        line=dict(color=COLORS['mksf'], width=2),
        hovertemplate='%{x|%d/%m/%Y}<br>MKSF: %{y:.2f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': 'Retorno Acumulado',
            'font': {'size': CHART_CONFIG['title_size'], 'family': CHART_CONFIG['font_family']},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title='',
        yaxis_title='Retorno (%)',
        hovermode='x unified',
        height=CHART_CONFIG['height'],
        margin=CHART_CONFIG['margin'],
        plot_bgcolor=CHART_CONFIG['plot_bgcolor'],
        paper_bgcolor=CHART_CONFIG['paper_bgcolor'],
        font=dict(family=CHART_CONFIG['font_family'], size=CHART_CONFIG['font_size']),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLORS['grid'],
            showline=True,
            linecolor='#dee2e6',
            linewidth=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS['grid'],
            showline=True,
            linecolor='#dee2e6',
            linewidth=1,
            ticksuffix='%'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_spread_chart(df):
    """Cria gráfico de spread"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Spread'] * 100,
        mode='lines',
        name='Spread',
        line=dict(color=COLORS['mksf'], width=2),
        fill='tozeroy',
        fillcolor=f'rgba(0, 102, 204, 0.1)',
        hovertemplate='%{x|%d/%m/%Y}<br>Spread: %{y:.2f}%<extra></extra>'
    ))
    
    # Linha zero
    fig.add_hline(y=0, line_dash="dash", line_color="#6c757d", line_width=1)
    
    fig.update_layout(
        title={
            'text': 'Spread (MKSF vs IBOV)',
            'font': {'size': CHART_CONFIG['title_size'], 'family': CHART_CONFIG['font_family']},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title='',
        yaxis_title='Spread (%)',
        hovermode='x unified',
        height=CHART_CONFIG['height'],
        margin=CHART_CONFIG['margin'],
        plot_bgcolor=CHART_CONFIG['plot_bgcolor'],
        paper_bgcolor=CHART_CONFIG['paper_bgcolor'],
        font=dict(family=CHART_CONFIG['font_family'], size=CHART_CONFIG['font_size']),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLORS['grid'],
            showline=True,
            linecolor='#dee2e6',
            linewidth=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS['grid'],
            showline=True,
            linecolor='#dee2e6',
            linewidth=1,
            ticksuffix='%'
        ),
        showlegend=False
    )
    
    return fig

def format_percent_color(value):
    """Formata percentual com cor"""
    if pd.isna(value):
        return ""
    color = COLORS['positive'] if value >= 0 else COLORS['negative']
    return f'<span style="color: {color}; font-weight: 500;">{value:.2f}%</span>'

# ==============================================================================
# APLICAÇÃO PRINCIPAL
# ==============================================================================

def main():
    # Header
    st.title("📊 Dashboard Mekasfi")
    st.markdown("**Análise de Retorno Acumulado e Spread**")
    
    # Sidebar com botão de refresh
    with st.sidebar:
        st.markdown("### ⚙️ Controles")
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ Informações")
        st.markdown("""
        **Última atualização:**  
        Confira a data no dashboard
        
        **Fonte de dados:**  
        PyDATA.xlsx (Aba MKSF)
        """)
    
    # Carrega e processa dados
    df_mksf = load_data()
    df_mksf = process_data(df_mksf)
    
    # Data da última atualização
    ultima_data = df_mksf.index.max()
    st.markdown(f"*Última atualização: {ultima_data.strftime('%d/%m/%Y')}*")
    
    st.markdown("---")
    
    # ==============================================================================
    # GRÁFICOS PRINCIPAIS
    # ==============================================================================
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        fig_retorno = create_cumulative_return_chart(df_mksf)
        st.plotly_chart(fig_retorno, use_container_width=True)
    
    with col2:
        fig_spread = create_spread_chart(df_mksf)
        st.plotly_chart(fig_spread, use_container_width=True)
    
    st.markdown("---")
    
    # ==============================================================================
    # SEÇÃO SEMANAL
    # ==============================================================================
    
    numero_semana = ultima_data.isocalendar()[1]
    st.markdown(f"## Semana {numero_semana}")
    
    # Pega última data da semana anterior
    dia_semana_anterior = ultima_data - timedelta(weeks=1)
    ultima_data_semana_anterior = df_mksf.index[
        df_mksf.index.isocalendar().week == dia_semana_anterior.isocalendar()[1]
    ].max()
    
    # Cria lista dos dias da semana (segunda a sexta)
    data_semana = []
    start_of_week = ultima_data - timedelta(days=ultima_data.weekday())
    for i in range(5):
        data_semana.append(start_of_week + timedelta(days=i))
    
    # Prepara dados da tabela semanal
    dados_semana = {
        'Dia': [d.strftime('%d.%m - %A') for d in data_semana],
        'Mekasfi': [''] * 5,
        'Ibovespa': [''] * 5
    }
    
    for i, data in enumerate(data_semana):
        if data in df_mksf.index:
            dados_semana['Mekasfi'][i] = f"{df_mksf.loc[data, 'MKSFdaily']:.2%}"
            dados_semana['Ibovespa'][i] = f"{df_mksf.loc[data, 'IBOVdaily']:.2%}"
    
    df_tabela_semanal = pd.DataFrame(dados_semana)
    
    # Calcula variação semanal
    if ultima_data_semana_anterior and ultima_data:
        var_mksf_semanal = (df_mksf.loc[ultima_data, 'CotaMKSF'] / 
                           df_mksf.loc[ultima_data_semana_anterior, 'CotaMKSF']) - 1
        var_ibov_semanal = (df_mksf.loc[ultima_data, 'IBOV'] / 
                           df_mksf.loc[ultima_data_semana_anterior, 'IBOV']) - 1
        
        df_tabela_semanal.loc[len(df_tabela_semanal)] = [
            f"**Semana {numero_semana}**",
            f"{var_mksf_semanal:.2%}",
            f"{var_ibov_semanal:.2%}"
        ]
    
    df_tabela_semanal = df_tabela_semanal.set_index('Dia')
    
    # ==============================================================================
    # TABELAS LADO A LADO
    # ==============================================================================
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown("### 📅 Performance Semanal")
        st.dataframe(df_tabela_semanal, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Variações Acumuladas")
        
        # Calcula variações
        ano_atual = ultima_data.year
        
        # Mês
        primeira_data_mes = df_mksf.index[
            (df_mksf.index.year == ultima_data.year) &
            (df_mksf.index.month == ultima_data.month)
        ].min()
        var_mksf_mes = (df_mksf.loc[ultima_data, 'CotaMKSF'] / 
                       df_mksf.loc[primeira_data_mes, 'CotaMKSF']) - 1
        var_ibov_mes = (df_mksf.loc[ultima_data, 'IBOV'] / 
                       df_mksf.loc[primeira_data_mes, 'IBOV']) - 1
        
        # Ano
        primeira_data_ano = df_mksf.index[df_mksf.index.year == ano_atual].min()
        var_mksf_ano = (df_mksf.loc[ultima_data, 'CotaMKSF'] / 
                       df_mksf.loc[primeira_data_ano, 'CotaMKSF']) - 1
        var_ibov_ano = (df_mksf.loc[ultima_data, 'IBOV'] / 
                       df_mksf.loc[primeira_data_ano, 'IBOV']) - 1
        
        # 12 meses
        data_12meses_atras = ultima_data - timedelta(days=365)
        primeira_data_12m = df_mksf.loc[data_12meses_atras:].index.min()
        var_mksf_12m = (df_mksf.loc[ultima_data, 'CotaMKSF'] / 
                       df_mksf.loc[primeira_data_12m, 'CotaMKSF']) - 1
        var_ibov_12m = (df_mksf.loc[ultima_data, 'IBOV'] / 
                       df_mksf.loc[primeira_data_12m, 'IBOV']) - 1
        
        # Desde o início
        inicio_df = df_mksf.index.min()
        var_mksf_inicio = (df_mksf.loc[ultima_data, 'CotaMKSF'] / 
                          df_mksf.loc[inicio_df, 'CotaMKSF']) - 1
        var_ibov_inicio = (df_mksf.loc[ultima_data, 'IBOV'] / 
                          df_mksf.loc[inicio_df, 'IBOV']) - 1
        
        # Cria DataFrame resumo
        dados_resumo = {
            'Período': ['Mekasfi', 'Ibovespa'],
            'Mês': [f"{var_mksf_mes:.2%}", f"{var_ibov_mes:.2%}"],
            'Ano': [f"{var_mksf_ano:.2%}", f"{var_ibov_ano:.2%}"],
            '12 meses': [f"{var_mksf_12m:.2%}", f"{var_ibov_12m:.2%}"],
            'Desde o início': [f"{var_mksf_inicio:.2%}", f"{var_ibov_inicio:.2%}"]
        }
        df_resumo = pd.DataFrame(dados_resumo).set_index('Período')
        
        st.dataframe(df_resumo, use_container_width=True)

# ==============================================================================
# EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":
    main()
