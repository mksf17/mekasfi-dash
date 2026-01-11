import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Optional, Tuple, Dict

# ==============================================================================
# 1. CONFIGURAÇÃO E CONSTANTES (DESIGN SYSTEM)
# ==============================================================================

class ThemeConfig:
    """Centraliza configurações de Design e Identidade Visual"""
    APP_TITLE = "Mekasfi Asset Management"
    PAGE_ICON = "📈"
    
    # Paleta de Cores 'Fintech'
    COLOR_PRIMARY = "#0f172a"    # Slate 900 (Institucional)
    COLOR_ACCENT = "#3b82f6"     # Blue 500 (Destaque)
    COLOR_BG = "#f8fafc"         # Slate 50 (Fundo suave)
    COLOR_TEXT = "#334155"       # Slate 700
    
    # Cores Semânticas (Mercado Financeiro)
    COLOR_UP = "#16a34a"         # Green 600
    COLOR_DOWN = "#dc2626"       # Red 600
    COLOR_NEUTRAL = "#94a3b8"    # Slate 400
    
    # Configurações de Gráfico
    CHART_HEIGHT = 420
    FONT_FAMILY = "Inter, Roboto, sans-serif"

st.set_page_config(
    page_title=ThemeConfig.APP_TITLE,
    page_icon=ThemeConfig.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Injetado para Polimento Visual
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: {ThemeConfig.COLOR_TEXT};
    }}
    
    /* Header Limpo */
    header {{visibility: hidden;}}
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}
    
    /* Cards de Métricas/Gráficos */
    .stCard {{
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        margin-bottom: 1rem;
    }}
    
    /* Títulos */
    h1, h2, h3 {{
        color: {ThemeConfig.COLOR_PRIMARY};
        font-weight: 600;
        letter-spacing: -0.025em;
    }}
    
    /* Ajuste fino em tabelas */
    .stDataFrame {{ font-size: 0.9rem; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CAMADA DE DADOS (ETL & CÁLCULOS)
# ==============================================================================

class DataManager:
    """Gerencia carregamento e processamento de dados financeiros"""
    
    FILE_PATH = "PyDATA.xlsx"
    SHEET_NAME = "MKSF"

    @staticmethod
    @st.cache_data(ttl=3600)  # Cache de 1 hora
    def get_data() -> pd.DataFrame:
        """Carrega e trata os dados brutos."""
        try:
            with pd.ExcelFile(DataManager.FILE_PATH) as xls:
                df = pd.read_excel(xls, DataManager.SHEET_NAME, index_col=0)
            
            # Validação básica de schema
            required_cols = ['PL_MKSF', 'Qtd_Cotas', 'IBOV']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"Colunas faltando. Esperado: {required_cols}")
                
            return DataManager._calculate_metrics(df)
            
        except FileNotFoundError:
            st.error(f"❌ Arquivo fonte '{DataManager.FILE_PATH}' não localizado.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Erro crítico no processamento de dados: {e}")
            st.stop()

    @staticmethod
    def _calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """Aplica engenharia de features financeiras."""
        df = df.copy()
        df.sort_index(inplace=True)
        
        # Cotização
        df['CotaMKSF'] = df['PL_MKSF'] / df['Qtd_Cotas']
        
        # Retornos Diários
        df['IBOV_Ret'] = df['IBOV'].pct_change()
        df['MKSF_Ret'] = df['CotaMKSF'].pct_change()
        
        # Acumulados (Indexados em 0)
        df['IBOV_Acum'] = (1 + df['IBOV_Ret']).cumprod() - 1
        df['MKSF_Acum'] = (1 + df['MKSF_Ret']).cumprod() - 1
        
        # Alpha/Spread
        df['Spread'] = df['MKSF_Acum'] - df['IBOV_Acum']
        
        return df.dropna(how='all')

# ==============================================================================
# 3. CAMADA DE VISUALIZAÇÃO (PLOTLY)
# ==============================================================================

class ChartBuilder:
    """Fábrica de gráficos padronizados"""
    
    @staticmethod
    def plot_performance(df: pd.DataFrame) -> go.Figure:
        fig = go.Figure()
        
        # Benchmark (Cinza/Neutro)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['IBOV_Acum'],
            mode='lines', name='IBOV',
            line=dict(color=ThemeConfig.COLOR_NEUTRAL, width=1.5),
            hovertemplate='%{x|%d/%m}<br>IBOV: %{y:.2%}<extra></extra>'
        ))
        
        # Fundo (Cor Principal)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MKSF_Acum'],
            mode='lines', name='MKSF Fundo',
            line=dict(color=ThemeConfig.COLOR_ACCENT, width=2.5),
            hovertemplate='%{x|%d/%m}<br>MKSF: %{y:.2%}<extra></extra>'
        ))
        
        fig.update_layout(
            title="<b>Performance Histórica</b>",
            yaxis_tickformat='.0%',
            template="plotly_white",
            height=ThemeConfig.CHART_HEIGHT,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", y=1.02, x=0, xanchor="left", yanchor="bottom")
        )
        return fig

    @staticmethod
    def plot_spread(df: pd.DataFrame) -> go.Figure:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Spread'],
            mode='lines', name='Spread (Alpha)',
            line=dict(color=ThemeConfig.COLOR_PRIMARY, width=2),
            fill='tozeroy',
            fillcolor='rgba(15, 23, 42, 0.1)', # Slate com transparência
            hovertemplate='%{x|%d/%m}<br>Alpha: %{y:.2%}<extra></extra>'
        ))
        
        fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="<b>Alpha Gerado (Spread vs Benchmark)</b>",
            yaxis_tickformat='.1%',
            template="plotly_white",
            height=ThemeConfig.CHART_HEIGHT,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False
        )
        return fig

# ==============================================================================
# 4. UTILITÁRIOS DE RELATÓRIO
# ==============================================================================

def style_financial_df(df: pd.DataFrame, subset_cols: list) -> pd.io.formats.style.Styler:
    """
    Aplica formatação condicional profissional (Verde/Vermelho) 
    usando Pandas Styler nativo.
    """
    def color_negative_red(val):
        if pd.isna(val): return ''
        color = ThemeConfig.COLOR_UP if val >= 0 else ThemeConfig.COLOR_DOWN
        return f'color: {color}; font-weight: 600;'

    return (df.style
            .format("{:.2%}", subset=subset_cols)
            .map(color_negative_red, subset=subset_cols)
            .set_properties(**{'text-align': 'center', 'background-color': 'white'})
            .set_table_styles([{
                'selector': 'th',
                'props': [('background-color', '#f1f5f9'), 
                          ('color', '#475569'),
                          ('font-weight', '600')]
            }]))

def get_period_return(df: pd.DataFrame, start_date: date, end_date: date, col: str) -> Optional[float]:
    """Calcula retorno entre dois períodos com segurança."""
    try:
        if start_date not in df.index or end_date not in df.index:
            # Tenta buscar a data válida mais próxima se exata não existir (fallback simples)
            return None 
        return (df.loc[end_date, col] / df.loc[start_date, col]) - 1
    except Exception:
        return None

# ==============================================================================
# 5. APLICAÇÃO PRINCIPAL
# ==============================================================================

def main():
    # --- Sidebar ---
    with st.sidebar:
        st.caption("INVESTMENT MANAGER SYSTEM")
        st.title("Mekasfi Asset")
        st.markdown("---")
        if st.button("Recalcular Posições", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("---")
        st.caption("v2.0.1 | Prod Environment")

    # --- Load Data ---
    df = DataManager.get_data()
    last_date = df.index.max()
    
    # --- Header ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("Performance Attribution")
        st.markdown(f"**Data Base:** {last_date.strftime('%d de %B, %Y')} | **Status:** Auditado")
    with c2:
        # Mini KPI Header
        last_ret = df.loc[last_date, 'MKSF_Ret']
        st.metric("Retorno Diário", f"{last_ret:.2%}", delta_color="normal")

    st.markdown("---")

    # --- Charts Section ---
    # Usando container para efeito de card (CSS)
    with st.container():
        c_chart1, c_chart2 = st.columns([1.6, 1])
        with c_chart1:
            st.plotly_chart(ChartBuilder.plot_performance(df), use_container_width=True)
        with c_chart2:
            st.plotly_chart(ChartBuilder.plot_spread(df), use_container_width=True)

    st.markdown("---")

    # --- Tables Section ---
    c_tbl1, c_tbl2 = st.columns([1, 1])

    # 1. Tabela Semanal (Lógica Robusta)
    with c_tbl1:
        st.subheader("📅 Atribuição Semanal")
        
        # Gera datas da semana atual
        start_of_week = last_date - timedelta(days=last_date.weekday())
        week_dates = [start_of_week + timedelta(days=i) for i in range(5)]
        
        weekly_data = []
        for d in week_dates:
            row = {'Data': d.strftime('%d/%m - %A')}
            if d in df.index:
                row['Mekasfi'] = df.loc[d, 'MKSF_Ret']
                row['Ibovespa'] = df.loc[d, 'IBOV_Ret']
            else:
                row['Mekasfi'] = None
                row['Ibovespa'] = None
            weekly_data.append(row)
        
        df_week = pd.DataFrame(weekly_data).set_index('Data')
        
        # Cálculo do acumulado da semana
        try:
            prev_week_date = last_date - timedelta(weeks=1)
            # Busca data disponível mais próxima na semana anterior
            mask_prev = df.index.isocalendar().week == prev_week_date.isocalendar()[1]
            if mask_prev.any():
                ref_date = df.index[mask_prev].max()
                week_acc_mksf = (df.loc[last_date, 'CotaMKSF'] / df.loc[ref_date, 'CotaMKSF']) - 1
                week_acc_ibov = (df.loc[last_date, 'IBOV'] / df.loc[ref_date, 'IBOV']) - 1
                
                df_week.loc['<b>TOTAL SEMANA</b>'] = [week_acc_mksf, week_acc_ibov]
        except Exception as e:
            pass # Falha silenciosa em caso de dados insuficientes na semana anterior

        # Renderiza com Styler
        st.dataframe(style_financial_df(df_week, ['Mekasfi', 'Ibovespa']), use_container_width=True)

    # 2. Tabela de Períodos (Window Analysis)
    with c_tbl2:
        st.subheader("📈 Janelas de Retorno")
        
        # Definição de datas de referência
        try:
            dt_start_month = df.index[(df.index.year == last_date.year) & (df.index.month == last_date.month)].min()
            dt_start_year = df.index[df.index.year == last_date.year].min()
            dt_12m = df.loc[:last_date - timedelta(days=365)].index.max() if (last_date - df.index.min()).days > 365 else None
            dt_start = df.index.min()
            
            # Helper para extrair retornos baseados em cota
            def calc_window(start_dt, col):
                if pd.isna(start_dt): return None
                return (df.loc[last_date, col] / df.loc[start_dt, col]) - 1

            windows_data = {
                'Janela': ['Mês Atual (MTD)', 'Ano Atual (YTD)', '12 Meses (LTM)', 'Desde Início (ITD)'],
                'Mekasfi': [
                    calc_window(dt_start_month, 'CotaMKSF'),
                    calc_window(dt_start_year, 'CotaMKSF'),
                    calc_window(dt_12m, 'CotaMKSF'),
                    calc_window(dt_start, 'CotaMKSF')
                ],
                'Ibovespa': [
                    calc_window(dt_start_month, 'IBOV'),
                    calc_window(dt_start_year, 'IBOV'),
                    calc_window(dt_12m, 'IBOV'),
                    calc_window(dt_start, 'IBOV')
                ]
            }
            
            df_windows = pd.DataFrame(windows_data).set_index('Janela')
            
            # Renderiza com Styler
            st.dataframe(style_financial_df(df_windows, ['Mekasfi', 'Ibovespa']), use_container_width=True)
            
        except Exception as e:
            st.warning("Dados insuficientes para cálculo de todas as janelas.")

if __name__ == "__main__":
    main()