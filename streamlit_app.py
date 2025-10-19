import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Produtividade - TI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .slow-activity {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #f44336;
        margin: 0.5rem 0;
    }
    .fast-activity {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin: 0.5rem 0;
    }
    .no-responsible {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff9800;
        margin: 0.5rem 0;
    }
    .on-time {
        background-color: #e8f5e8;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #4caf50;
    }
    .late {
        background-color: #ffebee;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #f44336;
    }
    .with-failure {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">📊 Dashboard de Produtividade - Time de TI</h1>', unsafe_allow_html=True)

# Prazo estabelecido pela gestão (48 horas = 2 dias)
PRAZO_GESTAO = 2

# Carregar dados do Google Sheets
@st.cache_data(ttl=300)  # Cache de 5 minutos
def load_data_from_google_sheets():
    try:
        # URL do Google Sheets
        sheet_url = "https://docs.google.com/spreadsheets/d/1jFzyNnBxjUSkIe_iL0WhK4o3G7kJU4ZjWsogWGVA1R4/edit?usp=sharing"
        
        # Converter URL para formato de exportação CSV
        csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv')
        
        # Carregar dados
        df = pd.read_csv(csv_url)
        
        # Limpeza dos dados - trata valores NaN
        df['Responsável'] = df['Responsável'].fillna('Sem Responsável')
        df['Módulo'] = df['Módulo'].fillna('Sem Módulo')
        df['Status'] = df['Status'].fillna('Sem Status')
        df['Falha/ Teste em Produção'] = df['Falha/ Teste em Produção'].fillna('Não')
        
        # Converte para string
        df['Responsável'] = df['Responsável'].astype(str)
        df['Módulo'] = df['Módulo'].astype(str)
        df['Status'] = df['Status'].astype(str)
        df['Falha/ Teste em Produção'] = df['Falha/ Teste em Produção'].astype(str)
        
        # Converter datas
        df['Data Abertura'] = pd.to_datetime(df['Data Abertura'], errors='coerce')
        df['Data Entrega'] = pd.to_datetime(df['Data Entrega'], errors='coerce')
        
        # Calcular tempo de entrega (apenas para datas válidas)
        mask = df['Data Abertura'].notna() & df['Data Entrega'].notna()
        df.loc[mask, 'Tempo Entrega (dias)'] = (df.loc[mask, 'Data Entrega'] - df.loc[mask, 'Data Abertura']).dt.days
        
        # Para datas inválidas, definir como NaN
        df.loc[~mask, 'Tempo Entrega (dias)'] = np.nan
        
        # Classificar se cumpriu o prazo (apenas atividades concluídas)
        df['Cumpriu Prazo'] = 'Não Concluída'
        mask_concluidas = (df['Status'] == 'Concluída') & df['Tempo Entrega (dias)'].notna()
        df.loc[mask_concluidas, 'Cumpriu Prazo'] = df.loc[mask_concluidas, 'Tempo Entrega (dias)'].apply(
            lambda x: 'Dentro do Prazo' if x <= PRAZO_GESTAO else 'Fora do Prazo'
        )
        
        st.success("✅ Dados carregados do Google Sheets com sucesso!")
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do Google Sheets: {e}")
        return None

# Carregar dados
df = load_data_from_google_sheets()

if df is None:
    st.stop()

# Sidebar - Filtros e informações
st.sidebar.title("🔧 Filtros")

# Função segura para obter valores únicos
def get_unique_sorted(series):
    try:
        unique_vals = series.unique()
        unique_vals = [str(x) for x in unique_vals if str(x).strip() not in ['', 'nan', 'NaN']]
        return sorted(unique_vals)
    except:
        return []

# Filtro por responsável
responsaveis_base = get_unique_sorted(df['Responsável'])
if 'Sem Responsável' not in responsaveis_base:
    responsaveis_base.append('Sem Responsável')
responsaveis = ['Todos'] + sorted(responsaveis_base)

responsavel_selecionado = st.sidebar.selectbox("Selecione o Responsável:", responsaveis)

# Filtro por módulo
modulos = ['Todos'] + get_unique_sorted(df['Módulo'])
modulo_selecionado = st.sidebar.selectbox("Selecione o Módulo:", modulos)

# Filtro por status
status_opcoes = ['Todos'] + get_unique_sorted(df['Status'])
status_selecionado = st.sidebar.selectbox("Selecione o Status:", status_opcoes)

# Botão para atualizar dados
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

# Mostrar informações sobre os dados
st.sidebar.markdown("### 📊 Estatísticas")
st.sidebar.markdown(f"**Total de Atividades:** {len(df)}")
st.sidebar.markdown(f"**Responsáveis:** {len(get_unique_sorted(df['Responsável']))}")
st.sidebar.markdown(f"**Módulos:** {len(get_unique_sorted(df['Módulo']))}")

# Contar atividades sem responsável
atividades_sem_responsavel = len(df[df['Responsável'] == 'Sem Responsável'])
st.sidebar.markdown(f"**⚠️ Sem Responsável:** {atividades_sem_responsavel}")

# Informações de atualização
ultima_atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
st.sidebar.markdown(f"**🕒 Última atualização:** {ultima_atualizacao}")

# Aplicar filtros
df_filtrado = df.copy()
if responsavel_selecionado != 'Todos':
    if responsavel_selecionado == 'Sem Responsável':
        df_filtrado = df_filtrado[df_filtrado['Responsável'] == 'Sem Responsável']
    else:
        df_filtrado = df_filtrado[df_filtrado['Responsável'] == responsavel_selecionado]

if modulo_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Módulo'] == modulo_selecionado]

if status_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Status'] == status_selecionado]

# ANÁLISE DE PRAZO - NOVAS MÉTRICAS
st.sidebar.markdown("---")
st.sidebar.markdown("### ⏰ Análise de Prazo")

# Calcular métricas de prazo para dados filtrados
df_concluidas_filtrado = df_filtrado[df_filtrado['Status'] == 'Concluída']
total_concluidas = len(df_concluidas_filtrado)

if total_concluidas > 0:
    dentro_prazo = len(df_concluidas_filtrado[df_concluidas_filtrado['Cumpriu Prazo'] == 'Dentro do Prazo'])
    fora_prazo = len(df_concluidas_filtrado[df_concluidas_filtrado['Cumpriu Prazo'] == 'Fora do Prazo'])
    
    taxa_dentro_prazo = (dentro_prazo / total_concluidas) * 100
    taxa_fora_prazo = (fora_prazo / total_concluidas) * 100
    
    st.sidebar.markdown(f"**✅ Dentro do prazo:** {dentro_prazo} ({taxa_dentro_prazo:.1f}%)")
    st.sidebar.markdown(f"**❌ Fora do prazo:** {fora_prazo} ({taxa_fora_prazo:.1f}%)")
else:
    st.sidebar.markdown("**Nenhuma atividade concluída**")

# ANÁLISE DE FALHAS - NOVAS MÉTRICAS
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔴 Análise de Falhas")

# Calcular métricas de falhas
atividades_com_falha_total = len(df_filtrado[df_filtrado['Falha/ Teste em Produção'] == 'Sim'])
taxa_falhas_total = (atividades_com_falha_total / len(df_filtrado)) * 100 if len(df_filtrado) > 0 else 0

st.sidebar.markdown(f"**🔴 Com falha:** {atividades_com_falha_total} ({taxa_falhas_total:.1f}%)")
st.sidebar.markdown(f"**🟢 Sem falha:** {len(df_filtrado) - atividades_com_falha_total} ({100 - taxa_falhas_total:.1f}%)")

# Métricas principais
st.subheader("📈 Métricas Principais")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_atividades = len(df_filtrado)
    st.metric("Total de Atividades", total_atividades)

with col2:
    taxa_conclusao = (df_filtrado['Status'] == 'Concluída').mean() * 100
    st.metric("Taxa de Conclusão", f"{taxa_conclusao:.1f}%")

with col3:
    st.metric("Taxa de Falhas", f"{taxa_falhas_total:.1f}%")

with col4:
    if not df_concluidas_filtrado.empty and 'Tempo Entrega (dias)' in df_concluidas_filtrado.columns:
        tempo_medio = df_concluidas_filtrado['Tempo Entrega (dias)'].mean()
        st.metric("Tempo Médio (dias)", f"{tempo_medio:.1f}")
    else:
        st.metric("Tempo Médio (dias)", "N/A")

with col5:
    if total_concluidas > 0:
        st.metric("Dentro do Prazo (48h)", f"{taxa_dentro_prazo:.1f}%")
    else:
        st.metric("Dentro do Prazo", "N/A")

# Banner informativo sobre o prazo
st.markdown(f"""
<div style="background-color: #e3f2fd; padding: 1rem; border-radius: 10px; border-left: 4px solid #2196f3; margin: 1rem 0;">
    <h4 style="margin: 0; color: #1976d2;">⏰ Prazo Estabelecido pela Gestão: {PRAZO_GESTAO} dias (48 horas)</h4>
    <p style="margin: 0.5rem 0 0 0; color: #1565c0;">
        Esta métrica considera apenas atividades <strong>concluídas</strong> com tempo de entrega calculado.
    </p>
</div>
""", unsafe_allow_html=True)

# Abas principais
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Visão Geral", "👥 Por Responsável", "🔧 Por Módulo", "📅 Timeline", "⏰ Análise de Prazos", "🚨 Insights"])

with tab1:
    st.subheader("Visão Geral da Produtividade")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de status
        fig_status = px.pie(df_filtrado, names='Status', title='Distribuição por Status',
                           color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig_status, use_container_width=True)
        
        # Gráfico de cumprimento de prazo (apenas concluídas)
        if total_concluidas > 0:
            prazo_counts = df_concluidas_filtrado['Cumpriu Prazo'].value_counts()
            fig_prazo = px.pie(values=prazo_counts.values, names=prazo_counts.index,
                             title=f'Cumprimento do Prazo ({PRAZO_GESTAO} dias)',
                             color=prazo_counts.index,
                             color_discrete_map={'Dentro do Prazo': '#4caf50', 'Fora do Prazo': '#f44336'})
            st.plotly_chart(fig_prazo, use_container_width=True)
    
    with col2:
        # Gráfico de módulos
        modulo_counts = df_filtrado['Módulo'].value_counts()
        fig_modulos = px.bar(x=modulo_counts.index, y=modulo_counts.values,
                           title='Atividades por Módulo',
                           labels={'x': 'Módulo', 'y': 'Quantidade'})
        fig_modulos.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_modulos, use_container_width=True)
        
        # Gráfico de responsáveis
        resp_counts = df_filtrado['Responsável'].value_counts()
        fig_resp = px.bar(x=resp_counts.index, y=resp_counts.values,
                         title='Atividades por Responsável',
                         labels={'x': 'Responsável', 'y': 'Quantidade'})
        fig_resp.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_resp, use_container_width=True)

with tab2:
    st.subheader("Análise por Responsável")
    
    # Métricas por responsável incluindo análise de prazo E FALHAS
    resp_analysis = df_filtrado.groupby('Responsável').agg({
        'ID': 'count',
        'Tempo Entrega (dias)': 'mean',
        'Falha/ Teste em Produção': lambda x: (x == 'Sim').mean() * 100
    }).round(2)
    
    # Adicionar análise de prazo por responsável
    prazo_por_responsavel = []
    falhas_por_responsavel = []
    atividades_com_falha_detalhes = []
    
    for responsavel in resp_analysis.index:
        df_resp = df_filtrado[df_filtrado['Responsável'] == responsavel]
        df_resp_concluidas = df_resp[df_resp['Status'] == 'Concluída']
        
        # Análise de prazo
        if len(df_resp_concluidas) > 0:
            dentro_prazo = len(df_resp_concluidas[df_resp_concluidas['Cumpriu Prazo'] == 'Dentro do Prazo'])
            taxa_dentro_prazo = (dentro_prazo / len(df_resp_concluidas)) * 100
        else:
            taxa_dentro_prazo = 0
            
        prazo_por_responsavel.append(taxa_dentro_prazo)
        
        # Análise de falhas
        atividades_com_falha = df_resp[df_resp['Falha/ Teste em Produção'] == 'Sim']
        if len(df_resp) > 0:
            taxa_falhas = (len(atividades_com_falha) / len(df_resp)) * 100
        else:
            taxa_falhas = 0
            
        falhas_por_responsavel.append(taxa_falhas)
        
        # Detalhes das atividades com falha
        for idx, atividade in atividades_com_falha.iterrows():
            atividades_com_falha_detalhes.append({
                'Responsável': responsavel,
                'ID': atividade['ID'],
                'Atividade': atividade['Atividade'],
                'Módulo': atividade['Módulo'],
                'Tempo Entrega (dias)': atividade.get('Tempo Entrega (dias)', 'N/A'),
                'Status': atividade['Status']
            })
    
    resp_analysis['Dentro Prazo (%)'] = prazo_por_responsavel
    resp_analysis['Taxa Falhas (%)'] = falhas_por_responsavel
    resp_analysis.columns = ['Total Atividades', 'Tempo Médio (dias)', 'Taxa Falhas Base (%)', 'Dentro Prazo (%)', 'Taxa Falhas (%)']
    resp_analysis = resp_analysis.sort_values('Total Atividades', ascending=False)
    
    st.dataframe(resp_analysis, use_container_width=True)
    
    # NOVA SEÇÃO: Atividades com Falha por Responsável
    st.markdown("### 🔴 Atividades com Falha/Teste em Produção por Responsável")
    
    if atividades_com_falha_detalhes:
        df_falhas_detalhes = pd.DataFrame(atividades_com_falha_detalhes)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de taxa de falhas por responsável
            fig_falhas_resp = px.bar(resp_analysis, x=resp_analysis.index, y='Taxa Falhas (%)',
                                   title='Taxa de Falhas por Responsável',
                                   color='Taxa Falhas (%)',
                                   color_continuous_scale='Reds')
            fig_falhas_resp.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_falhas_resp, use_container_width=True)
        
        with col2:
            # Lista detalhada de atividades com falha
            st.markdown("#### 📋 Detalhes das Atividades com Falha")
            for falha in atividades_com_falha_detalhes:
                st.markdown(f"""
                <div class="with-failure">
                    <strong>Responsável:</strong> {falha['Responsável']}<br>
                    <strong>ID:</strong> {falha['ID']} | <strong>Módulo:</strong> {falha['Módulo']}<br>
                    <strong>Tempo:</strong> {falha['Tempo Entrega (dias)']} dias<br>
                    <strong>Atividade:</strong> {falha['Atividade'][:70]}...
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("✅ Nenhuma atividade com falha encontrada para os filtros selecionados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tempo médio por responsável (apenas concluídas)
        df_concluidas = df_filtrado[df_filtrado['Status'] == 'Concluída']
        if not df_concluidas.empty and 'Tempo Entrega (dias)' in df_concluidas.columns:
            tempo_resp = df_concluidas.groupby('Responsável')['Tempo Entrega (dias)'].mean().sort_values()
            fig_tempo_resp = px.bar(tempo_resp, orientation='h',
                                  title='Tempo Médio por Responsável (dias)',
                                  color=tempo_resp.values,
                                  color_continuous_scale='Viridis')
            
            # Adicionar linha do prazo estabelecido
            fig_tempo_resp.add_vline(x=PRAZO_GESTAO, line_dash="dash", line_color="red", 
                                   annotation_text=f"Prazo: {PRAZO_GESTAO}d", 
                                   annotation_position="top right")
            
            st.plotly_chart(fig_tempo_resp, use_container_width=True)
    
    with col2:
        # Cumprimento de prazo por responsável
        if total_concluidas > 0:
            prazo_resp = resp_analysis[['Dentro Prazo (%)']].sort_values('Dentro Prazo (%)')
            fig_prazo_resp = px.bar(prazo_resp, orientation='h',
                                  title=f'% Dentro do Prazo por Responsável ({PRAZO_GESTAO} dias)',
                                  color=prazo_resp['Dentro Prazo (%)'],
                                  color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_prazo_resp, use_container_width=True)

with tab3:
    st.subheader("Análise por Módulo")
    
    # Métricas por módulo incluindo análise de prazo
    modulo_analysis = df_filtrado.groupby('Módulo').agg({
        'ID': 'count',
        'Tempo Entrega (dias)': 'mean',
        'Falha/ Teste em Produção': lambda x: (x == 'Sim').mean() * 100,
        'Status': lambda x: (x == 'Concluída').mean() * 100
    }).round(2)
    
    # Adicionar análise de prazo por módulo
    prazo_por_modulo = []
    for modulo in modulo_analysis.index:
        df_mod = df_filtrado[df_filtrado['Módulo'] == modulo]
        df_mod_concluidas = df_mod[df_mod['Status'] == 'Concluída']
        
        if len(df_mod_concluidas) > 0:
            dentro_prazo = len(df_mod_concluidas[df_mod_concluidas['Cumpriu Prazo'] == 'Dentro do Prazo'])
            taxa_dentro_prazo = (dentro_prazo / len(df_mod_concluidas)) * 100
        else:
            taxa_dentro_prazo = 0
            
        prazo_por_modulo.append(taxa_dentro_prazo)
    
    modulo_analysis['Dentro Prazo (%)'] = prazo_por_modulo
    modulo_analysis.columns = ['Total', 'Tempo Médio', 'Taxa Falhas (%)', 'Taxa Conclusão (%)', 'Dentro Prazo (%)']
    modulo_analysis = modulo_analysis.sort_values('Total', ascending=False)
    
    st.dataframe(modulo_analysis, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tempo por módulo (apenas concluídas)
        df_concluidas = df_filtrado[df_filtrado['Status'] == 'Concluída']
        if not df_concluidas.empty and 'Tempo Entrega (dias)' in df_concluidas.columns:
            tempo_modulo = df_concluidas.groupby('Módulo')['Tempo Entrega (dias)'].mean().sort_values()
            fig_tempo_modulo = px.bar(tempo_modulo, orientation='h',
                                    title='Tempo Médio por Módulo (dias)',
                                    color=tempo_modulo.values,
                                    color_continuous_scale='Plasma')
            
            # Adicionar linha do prazo estabelecido
            fig_tempo_modulo.add_vline(x=PRAZO_GESTAO, line_dash="dash", line_color="red", 
                                     annotation_text=f"Prazo: {PRAZO_GESTAO}d", 
                                     annotation_position="top right")
            
            st.plotly_chart(fig_tempo_modulo, use_container_width=True)
    
    with col2:
        # Cumprimento de prazo por módulo
        if total_concluidas > 0:
            prazo_modulo = modulo_analysis[['Dentro Prazo (%)']].sort_values('Dentro Prazo (%)')
            fig_prazo_modulo = px.bar(prazo_modulo, orientation='h',
                                    title=f'% Dentro do Prazo por Módulo ({PRAZO_GESTAO} dias)',
                                    color=prazo_modulo['Dentro Prazo (%)'],
                                    color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_prazo_modulo, use_container_width=True)

with tab4:
    st.subheader("Timeline e Evolução")
    
    # Evolução mensal
    if 'Data Abertura' in df_filtrado.columns:
        df_filtrado['Mês'] = df_filtrado['Data Abertura'].dt.to_period('M').astype(str)
        evolucao_mensal = df_filtrado.groupby('Mês').size()
        
        fig_timeline = px.line(x=evolucao_mensal.index, y=evolucao_mensal.values,
                              title='Evolução de Atividades ao Longo do Tempo',
                              markers=True)
        fig_timeline.update_layout(xaxis_title='Mês', yaxis_title='Quantidade de Atividades')
        st.plotly_chart(fig_timeline, use_container_width=True)

with tab5:
    st.subheader("⏰ Análise Detalhada de Prazos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Estatísticas de Prazo")
        
        if total_concluidas > 0:
            # Métricas detalhadas
            st.markdown(f"""
            <div class="on-time">
                <h4>✅ Dentro do Prazo ({PRAZO_GESTAO} dias)</h4>
                <p><strong>{dentro_prazo} atividades</strong> ({taxa_dentro_prazo:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="late">
                <h4>❌ Fora do Prazo ({PRAZO_GESTAO} dias)</h4>
                <p><strong>{fora_prazo} atividades</strong> ({taxa_fora_prazo:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Distribuição de tempos
            st.markdown("### 📈 Distribuição dos Tempos de Entrega")
            fig_dist_tempo = px.histogram(df_concluidas_filtrado, x='Tempo Entrega (dias)',
                                        title='Distribuição dos Tempos de Entrega',
                                        nbins=20)
            fig_dist_tempo.add_vline(x=PRAZO_GESTAO, line_dash="dash", line_color="red",
                                   annotation_text=f"Prazo: {PRAZO_GESTAO}d")
            st.plotly_chart(fig_dist_tempo, use_container_width=True)
        
    with col2:
        st.markdown("### 🐌 Top 5 Atividades Mais Atrasadas")
        
        if total_concluidas > 0:
            atividades_atrasadas = df_concluidas_filtrado[df_concluidas_filtrado['Cumpriu Prazo'] == 'Fora do Prazo']
            if not atividades_atrasadas.empty:
                top5_atrasadas = atividades_atrasadas.nlargest(5, 'Tempo Entrega (dias)')
                for idx, atividade in top5_atrasadas.iterrows():
                    dias_atraso = atividade['Tempo Entrega (dias)'] - PRAZO_GESTAO
                    st.markdown(f"""
                    <div class="slow-activity">
                        <strong>+{dias_atraso:.0f} dias de atraso</strong><br>
                        <strong>ID:</strong> {atividade['ID']} | <strong>Responsável:</strong> {atividade['Responsável']}<br>
                        <strong>Módulo:</strong> {atividade['Módulo']}<br>
                        <strong>Tempo total:</strong> {atividade['Tempo Entrega (dias)']} dias<br>
                        {atividade['Atividade'][:80]}...
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("🎉 Nenhuma atividade fora do prazo!")
        
        st.markdown("### ⚡ Atividades Mais Rápidas")
        if total_concluidas > 0:
            atividades_rapidas = df_concluidas_filtrado.nsmallest(5, 'Tempo Entrega (dias)')
            for idx, atividade in atividades_rapidas.iterrows():
                st.markdown(f"""
                <div class="fast-activity">
                    <strong>{atividade['Tempo Entrega (dias)']} dias</strong><br>
                    <strong>ID:</strong> {atividade['ID']} | <strong>Responsável:</strong> {atividade['Responsável']}<br>
                    {atividade['Atividade'][:60]}...
                </div>
                """, unsafe_allow_html=True)

with tab6:
    st.subheader("🚨 Insights e Recomendações")
    
    # Insights baseados nos dados
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Insights de Performance")
        
        if total_concluidas > 0:
            # Responsável com melhor performance no prazo
            melhor_prazo_resp = resp_analysis[resp_analysis['Total Atividades'] > 0].nlargest(1, 'Dentro Prazo (%)')
            if not melhor_prazo_resp.empty:
                resp, dados = list(melhor_prazo_resp.iterrows())[0]
                st.success(f"**🏆 Melhor no prazo:** {resp} - {dados['Dentro Prazo (%)']:.1f}% dentro do prazo")
            
            # Módulo com melhor performance no prazo
            melhor_prazo_mod = modulo_analysis[modulo_analysis['Total'] > 0].nlargest(1, 'Dentro Prazo (%)')
            if not melhor_prazo_mod.empty:
                mod, dados = list(melhor_prazo_mod.iterrows())[0]
                st.info(f"**🔧 Módulo mais eficiente:** {mod} - {dados['Dentro Prazo (%)']:.1f}% dentro do prazo")
            
            # Identificar problemas
            if taxa_fora_prazo > 50:
                st.error(f"**⚠️ Atenção:** Mais de 50% das atividades estão fora do prazo!")
            elif taxa_fora_prazo > 30:
                st.warning(f"**📊 Observação:** {taxa_fora_prazo:.1f}% das atividades estão fora do prazo")
            else:
                st.success(f"**✅ Excelente:** Apenas {taxa_fora_prazo:.1f}% das atividades estão fora do prazo")
    
    with col2:
        st.markdown("### 💡 Recomendações")
        
        recomendacoes = []
        
        if total_concluidas > 0:
            if taxa_fora_prazo > 40:
                recomendacoes.append("**🔴 Prioridade:** Revisar processos que estão causando atrasos frequentes")
            
            if atividades_sem_responsavel > 0:
                recomendacoes.append(f"**👥 Atribuição:** {atividades_sem_responsavel} atividades sem responsável precisam ser atribuídas")
            
            # Verificar responsáveis com baixa performance no prazo
            resp_baixa_performance = resp_analysis[
                (resp_analysis['Total Atividades'] >= 3) & 
                (resp_analysis['Dentro Prazo (%)'] < 50)
            ]
            if not resp_baixa_performance.empty:
                for resp, dados in resp_baixa_performance.iterrows():
                    recomendacoes.append(f"**🎯 Treinamento:** {resp} tem apenas {dados['Dentro Prazo (%)']:.1f}% dentro do prazo")
            
            # Verificar módulos problemáticos
            mod_problematicos = modulo_analysis[
                (modulo_analysis['Total'] >= 5) & 
                (modulo_analysis['Dentro Prazo (%)'] < 40)
            ]
            if not mod_problematicos.empty:
                for mod, dados in mod_problematicos.iterrows():
                    recomendacoes.append(f"**🔧 Otimização:** Módulo {mod} tem apenas {dados['Dentro Prazo (%)']:.1f}% dentro do prazo")
            
            # NOVAS RECOMENDAÇÕES BASEADAS EM FALHAS
            if atividades_com_falha_total > 0:
                recomendacoes.append(f"**🔴 Qualidade:** {atividades_com_falha_total} atividades tiveram falha - revisar processos de teste")
            
            # Responsáveis com alta taxa de falhas
            resp_alta_falhas = resp_analysis[
                (resp_analysis['Total Atividades'] >= 3) & 
                (resp_analysis['Taxa Falhas (%)'] > 20)
            ]
            if not resp_alta_falhas.empty:
                for resp, dados in resp_alta_falhas.iterrows():
                    recomendacoes.append(f"**🧪 Testes:** {resp} tem {dados['Taxa Falhas (%)']:.1f}% de falhas - fortalecer testes")
        
        if not recomendacoes:
            recomendacoes.append("**✅ Manutenção:** Continue com os processos atuais - performance dentro do esperado")
        
        for rec in recomendacoes:
            st.markdown(f"- {rec}")

# Rodapé
st.markdown("---")
st.markdown("**Dashboard de Produtividade** - Desenvolvido para análise do Time de TI")
st.markdown(f"📊 **Fonte de dados:** Google Sheets | ⏰ **Prazo estabelecido:** {PRAZO_GESTAO} dias (48h)")