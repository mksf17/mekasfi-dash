import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================

st.set_page_config(
    page_title="Mekasfi Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# ESTILIZAÇÃO (CSS MODERNIZADO)
# ==============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* Fundo geral mais suave */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Estilo para Cards (Containeres Brancos) */
    .dashboard-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
    }
    
    /* Títulos */
    h1 {
        color: #1e293b;
        font-weight: 800;
        letter-spacing: -0.025em;
    }
    
    h2, h3 {
        color: #334155;
        font-weight: 600;
    }
    
    /* Remover padding excessivo do topo */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    
    /* Botões */
    .stButton button {
        background-color: #4f46e5; /* Indigo Moderno */
        color: white;
        border-radius: 8px;
        font-weight: 500;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        background-color: #4338ca;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3);
    }

    /* Ajuste de métricas */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CONFIGURAÇÕES VISUAIS
# ==============================================================================

COLORS = {
    'primary': '#4f46e5',   # Indigo (Mekasfi)
    'secondary': '#94a3b8', # Slate (Ibov/Neutro)
    'success': '#10b981',   # Emerald
    'danger': '#ef4444',    # Rose
    'text': '#1e293b',
    'grid': '#f1f5f9'
}

CHART_THEME = {
    'plot_bgcolor': 'white',
    'paper_bgcolor': 'white',
    'font': {'family': 'Inter, sans-serif', 'color': COLORS['text']},
}

# ==============================================================================
# PROCESSAMENTO DE DADOS
# ==============================================================================

@st.cache_data
def load_data():
    try:
        with pd.ExcelFile("PyDATA.xlsx") as xls:
            df = pd.read_excel(xls, 'MKSF', index_col=0)
            return df
    except FileNotFoundError:
        st.error("⚠️ Arquivo 'PyDATA.xlsx' não encontrado.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar arquivo: {str(e)}")
        st.stop()

def process_data(df):
    df = df.copy()
    
    # Cálculos
    df['CotaMKSF'] = df['PL_MKSF'] / df['Qtd_Cotas']
    df['IBOVdaily'] = df['IBOV'].pct_change()
    df['MKSFdaily'] = df['CotaMKSF'].pct_change()
    
    df['IBOVacum'] = (1 + df['IBOVdaily']).cumprod() - 1
    df['MKSFacum'] = (1 + df['MKSFdaily']).cumprod() - 1
    df['Spread'] = df['MKSFacum'] - df['IBOVacum']
    
    return df

# Função para estilizar DataFrames (Cores Condicionais)
def color_surrenders(val):
    """Retorna cor verde ou vermelha para CSS baseado no valor numérico"""
    if pd.isna(val):
        return ''
    color = COLORS['success'] if val >= 0 else COLORS['danger']
    return f'color: {color}; font-weight: 600;'

# ==============================================================================
# GRÁFICOS
# ==============================================================================

def plot_cumulative(df):
    fig = go.Figure()
    
    # IBOV (Fundo/Referência)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['IBOVacum'],
        mode='lines', name='IBOV',
        line=dict(color=COLORS['secondary'], width=1.5),
        hovertemplate='%{x|%d/%m/%Y}<br>IBOV: %{y:.2%}<extra></extra>'
    ))
    
    # MKSF (Destaque)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MKSFacum'],
        mode='lines', name='MKSF',
        line=dict(color=COLORS['primary'], width=2.5),
        hovertemplate='%{x|%d/%m/%Y}<br>MKSF: %{y:.2%}<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Retorno Acumulado</b>',
        yaxis_tickformat='.0%',
        hovermode='x unified',
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", y=1, x=0, xanchor="left", yanchor="bottom"),
        **CHART_THEME
    )
    fig.update_xaxes(showgrid=False, linecolor='#cbd5e1')
    fig.update_yaxes(showgrid=True, gridcolor=COLORS['grid'], zeroline=True, zerolinecolor='#cbd5e1')
    
    return fig

def plot_spread(df):
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Spread'],
        mode='lines', name='Spread',
        line=dict(color=COLORS['primary'], width=2),
        fill='tozeroy',
        fillcolor='rgba(79, 70, 229, 0.1)', # Transparência do Indigo
        hovertemplate='Spread: %{y:.2%}<extra></extra>'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS['secondary'], opacity=0.5)
    
    fig.update_layout(
        title='<b>Alpha (Spread vs IBOV)</b>',
        yaxis_tickformat='.1%',
        hovermode='x unified',
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
        **CHART_THEME
    )
    fig.update_xaxes(showgrid=False, linecolor='#cbd5e1')
    fig.update_yaxes(showgrid=True, gridcolor=COLORS['grid'])
    
    return fig

# ==============================================================================
# LAYOUT PRINCIPAL
# ==============================================================================

def main():
    # --- Sidebar ---
    with st.sidebar:
        st.header("Mekasfi Asset")
        st.caption("Controles do Dashboard")
        
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        st.divider()
        st.info("Dados extraídos de PyDATA.xlsx (Aba MKSF)")

    # --- Header ---
    df_mksf = load_data()
    df_mksf = process_data(df_mksf)
    ultima_data = df_mksf.index.max()
    
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title("Dashboard de Performance")
        st.markdown(f"Data base: **{ultima_data.strftime('%d/%m/%Y')}**")
    
    st.markdown("---")

    # --- Container Gráficos (Estilo Card) ---
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    col_chart1, col_chart2 = st.columns([1.5, 1])
    
    with col_chart1:
        st.plotly_chart(plot_cumulative(df_mksf), use_container_width=True)
    
    with col_chart2:
        st.plotly_chart(plot_spread(df_mksf), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Cálculos para Tabelas ---
    
    # 1. Tabela Semanal
    numero_semana = ultima_data.isocalendar()[1]
    
    # Lógica de datas da semana
    start_of_week = ultima_data - timedelta(days=ultima_data.weekday())
    data_semana = [start_of_week + timedelta(days=i) for i in range(5)]
    
    # Preparar DataFrame Semanal (Valores Numéricos)
    dados_semana_list = []
    
    for data in data_semana:
        row = {'Dia': data.strftime('%d.%m - %A')}
        if data in df_mksf.index:
            row['Mekasfi'] = df_mksf.loc[data, 'MKSFdaily']
            row['Ibovespa'] = df_mksf.loc[data, 'IBOVdaily']
        else:
            row['Mekasfi'] = None
            row['Ibovespa'] = None
        dados_semana_list.append(row)
        
    df_semana = pd.DataFrame(dados_semana_list)
    
    # Adicionar linha de total semanal
    dia_semana_anterior = ultima_data - timedelta(weeks=1)
    # Tenta achar a última data disponível da semana anterior
    mask_semana_anterior = df_mksf.index.isocalendar().week == dia_semana_anterior.isocalendar()[1]
    if any(mask_semana_anterior):
        dt_base_semana = df_mksf.index[mask_semana_anterior].max()
        
        var_mksf_sem = (df_mksf.loc[ultima_data, 'CotaMKSF'] / df_mksf.loc[dt_base_semana, 'CotaMKSF']) - 1
        var_ibov_sem = (df_mksf.loc[ultima_data, 'IBOV'] / df_mksf.loc[dt_base_semana, 'IBOV']) - 1
        
        # Adiciona como uma nova linha
        nova_linha = pd.DataFrame([{
            'Dia': f'Total Semana {numero_semana}',
            'Mekasfi': var_mksf_sem,
            'Ibovespa': var_ibov_sem
        }])
        df_semana = pd.concat([df_semana, nova_linha], ignore_index=True)

    df_semana = df_semana.set_index('Dia')

    # 2. Tabela Resumo (Variações Acumuladas)
    def calc_return(dt_start, dt_end, col):
        try:
            return (df_mksf.loc[dt_end, col] / df_mksf.loc[dt_start, col]) - 1
        except:
            return None

    # Datas de referência
    dt_inicio_mes = df_mksf.index[(df_mksf.index.year == ultima_data.year) & (df_mksf.index.month == ultima_data.month)].min()
    dt_inicio_ano = df_mksf.index[df_mksf.index.year == ultima_data.year].min()
    dt_12m = df_mksf.loc[:ultima_data - timedelta(days=365)].index.max() # Aproximação segura
    dt_inicio = df_mksf.index.min()

    # Montagem dos dados
    resumo_data = {
        'Período': ['Mês Atual', 'Ano (YTD)', '12 Meses', 'Início'],
        'Mekasfi': [
            calc_return(dt_inicio_mes, ultima_data, 'CotaMKSF'),
            calc_return(dt_inicio_ano, ultima_data, 'CotaMKSF'),
            calc_return(dt_12m, ultima_data, 'CotaMKSF') if pd.notna(dt_12m) else None,
            calc_return(dt_inicio, ultima_data, 'CotaMKSF')
        ],
        'Ibovespa': [
            calc_return(dt_inicio_mes, ultima_data, 'IBOV'),
            calc_return(dt_inicio_ano, ultima_data, 'IBOV'),
            calc_return(dt_12m, ultima_data, 'IBOV') if pd.notna(dt_12m) else None,
            calc_return(dt_inicio, ultima_data, 'IBOV')
        ]
    }
    df_resumo = pd.DataFrame(resumo_data).set_index('Período')

    # --- Renderização das Tabelas ---
    
    col_tab1, col_tab2 = st.columns([1, 1])
    
    with col_tab1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("📅 Performance Semanal")
        
        # Estilização com Pandas Styler (O jeito moderno de colorir tabelas)
        st.dataframe(
            df_semana.style
            .format("{:.2%}", subset=['Mekasfi', 'Ibovespa'])
            .applymap(color_surrenders, subset=['Mekasfi', 'Ibovespa']),
            use_container_width=True,
            height=250
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_tab2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.subheader("📈 Variações Acumuladas")
        
        st.dataframe(
            df_resumo.style
            .format("{:.2%}", subset=['Mekasfi', 'Ibovespa'])
            .applymap(color_surrenders, subset=['Mekasfi', 'Ibovespa']),
            use_container_width=True,
            height=250
        )
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()