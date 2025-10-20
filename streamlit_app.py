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

# CSS personalizado - UNIFICADO
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
    background-color: #ffebee;
    border: 1px solid #f44336;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    color: #c62828;
    font-family: Arial, sans-serif;
}
.with-failure strong {
    color: inherit;
}

/* MODOS CLARO/ESCUTO PARA .with-failure */
@media (prefers-color-scheme: dark) {
    .with-failure {
        background-color: #b71c1c;
        border-color: #f44336;
        color: #ffcdd2;
    }
    
    /* Você pode adicionar outras classes para modo escuro também */
    .slow-activity {
        background-color: #b71c1c;
        border-left-color: #f44336;
        color: #ffcdd2;
    }
    .fast-activity {
        background-color: #1b5e20;
        border-left-color: #4caf50;
        color: #c8e6c9;
    }
    .on-time {
        background-color: #1b5e20;
        border-left-color: #4caf50;
        color: #c8e6c9;
    }
    .late {
        background-color: #b71c1c;
        border-left-color: #f44336;
        color: #ffcdd2;
    }
}
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">📊 Dashboard Produtividade - Produto SAI </h1>', unsafe_allow_html=True)

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
        
        # Carregar dados da ABA PRINCIPAL (gid=0)
        df_principal = pd.read_csv(csv_url + "&gid=0")
        
        # Carregar dados da ABA CONTROLADOR (gid=357919568)
        df_controlador = pd.read_csv(csv_url + "&gid=357919568")
        
        # Limpeza dos dados PRINCIPAIS - trata valores NaN
        df_principal['Responsável'] = df_principal['Responsável'].fillna('Sem Responsável')
        df_principal['Módulo'] = df_principal['Módulo'].fillna('Sem Módulo')
        df_principal['Status'] = df_principal['Status'].fillna('Sem Status')
        df_principal['Falha/ Teste em Produção'] = df_principal['Falha/ Teste em Produção'].fillna('Não')
        
        # Converte para string
        df_principal['Responsável'] = df_principal['Responsável'].astype(str)
        df_principal['Módulo'] = df_principal['Módulo'].astype(str)
        df_principal['Status'] = df_principal['Status'].astype(str)
        df_principal['Falha/ Teste em Produção'] = df_principal['Falha/ Teste em Produção'].astype(str)
        
        # Converter datas
        df_principal['Data Abertura'] = pd.to_datetime(df_principal['Data Abertura'], errors='coerce')
        df_principal['Data Entrega'] = pd.to_datetime(df_principal['Data Entrega'], errors='coerce')
        
        # Calcular tempo de entrega (apenas para datas válidas)
        mask = df_principal['Data Abertura'].notna() & df_principal['Data Entrega'].notna()
        df_principal.loc[mask, 'Tempo Entrega (dias)'] = (df_principal.loc[mask, 'Data Entrega'] - df_principal.loc[mask, 'Data Abertura']).dt.days
        
        # Para datas inválidas, definir como NaN
        df_principal.loc[~mask, 'Tempo Entrega (dias)'] = np.nan
        
        # Classificar se cumpriu o prazo (apenas atividades concluídas)
        df_principal['Cumpriu Prazo'] = 'Não Concluída'
        mask_concluidas = (df_principal['Status'] == 'Concluída') & df_principal['Tempo Entrega (dias)'].notna()
        df_principal.loc[mask_concluidas, 'Cumpriu Prazo'] = df_principal.loc[mask_concluidas, 'Tempo Entrega (dias)'].apply(
            lambda x: 'Dentro do Prazo' if x <= PRAZO_GESTAO else 'Fora do Prazo'
        )
        
        # Limpeza básica dos dados do CONTROLADOR
        df_controlador = df_controlador.fillna('')
        
        st.success("✅ Dados carregados do Google Sheets com sucesso!")
        return df_principal, df_controlador
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados do Google Sheets: {e}")
        return None, None

# Carregar dados
df, df_controlador = load_data_from_google_sheets()

if df is None:
    st.stop()

# Verificar se o Controlador foi carregado
if df_controlador is not None:
    st.sidebar.success("✅ Controlador carregado")
else:
    st.sidebar.warning("⚠️ Controlador não carregado")

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

# Filtro por DATA - VERSÃO CORRIGIDA
st.sidebar.markdown("---")
st.sidebar.subheader("📅 Filtro por Período")

# Verifica quais colunas de data existem no DataFrame
colunas_data_disponiveis = []
nomes_possiveis = ['data abertura', 'data entrega', 'data_abertura', 'data_entrega', 
                   'Data Abertura', 'Data Entrega', 'data', 'Data', 'Data de Abertura', 'Data de Entrega']

for nome in nomes_possiveis:
    if nome in df.columns:
        colunas_data_disponiveis.append(nome)

if colunas_data_disponiveis:
    # Se encontrou colunas de data, permite escolher
    if len(colunas_data_disponiveis) > 1:
        coluna_data = st.sidebar.selectbox(
            "Selecionar coluna para filtro:",
            colunas_data_disponiveis,
            help="Escolha qual coluna de data usar como referência"
        )
    else:
        coluna_data = colunas_data_disponiveis[0]
        st.sidebar.write(f"**Usando coluna:** {coluna_data}")
    
    # Agora processa a coluna selecionada
    try:
        df[coluna_data] = pd.to_datetime(df[coluna_data], errors='coerce')
        datas_validas = df[coluna_data].dropna()
        
        if not datas_validas.empty:
            data_min = datas_validas.min().date()
            data_max = datas_validas.max().date()
            
            st.sidebar.write(f"Período disponível: {data_min} a {data_max}")
            
            # Seleção de período
            data_inicio = st.sidebar.date_input(
                "Data de início:",
                value=data_min,
                min_value=data_min,
                max_value=data_max
            )
            
            data_fim = st.sidebar.date_input(
                "Data de fim:",
                value=data_max,
                min_value=data_min,
                max_value=data_max
            )
            
            # Garante que a data início seja menor que data fim
            if data_inicio > data_fim:
                st.sidebar.error("❌ Data de início não pode ser maior que data de fim")
                data_inicio, data_fim = data_min, data_max
                
            periodo_selecionado = True
            
        else:
            st.sidebar.warning("⚠️ Não há datas válidas para filtrar")
            periodo_selecionado = False
            data_inicio, data_fim = None, None
            
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao processar datas: {e}")
        periodo_selecionado = False
        data_inicio, data_fim = None, None
        
else:
    # Se não encontrou nenhuma coluna de data conhecida
    st.sidebar.warning("""
    ⚠️ Nenhuma coluna de data encontrada. 
    Colunas disponíveis serão mostradas abaixo.
    """)
    periodo_selecionado = False
    data_inicio, data_fim = None, None

st.sidebar.markdown("---")
    
# Filtro por SPRINT (NOVO)
sprints = ['Todos'] + get_unique_sorted(df['Sprint'])
sprint_selecionada = st.sidebar.selectbox("Selecione a Sprint:", sprints)

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

# Filtro por PERÍODO (USANDO A COLUNA SELECIONADA)
if periodo_selecionado and data_inicio and data_fim:
    try:
        mask_periodo = (df_filtrado[coluna_data].dt.date >= data_inicio) & (df_filtrado[coluna_data].dt.date <= data_fim)
        df_filtrado = df_filtrado[mask_periodo]
        
        # Verifica se há dados após o filtro de período
        if df_filtrado.empty:
            st.warning("📭 Não há dados registrados no período selecionado. Atualize o filtro.")
    except Exception as e:
        st.error(f"Erro ao filtrar por período: {e}")

# Filtro por sprint (NOVO)
if sprint_selecionada != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Sprint'] == sprint_selecionada]

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
    
    taxa_dentro_prazo = (dentro_prazo / total_concluidas) * 100 if total_concluidas > 0 else 0
    taxa_fora_prazo = (fora_prazo / total_concluidas) * 100 if total_concluidas > 0 else 0
    
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
    <h4 style="margin: 0; color: #1976d2;">⏰ Prazo Médio Estabelecido pela Gestão: {PRAZO_GESTAO} dias (48 horas)</h4>
    <p style="margin: 0.5rem 0 0 0; color: #1565c0;">
        Esta métrica considera apenas atividades <strong>concluídas</strong> com tempo de entrega calculado.
    </p>
</div>
""", unsafe_allow_html=True)

# Abas principais
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
     "📈 Visão Geral", 
    "👥 Por Responsável", 
    "🔧 Por Módulo", 
    "📅 Timeline", 
    "⏰ Análise de Prazos",
    "🎛️ Controlador",  
    "🚨 Insights"      
])

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
    resp_analysis.columns = ['Total Atividades', 'Tempo Médio (dias)', 'Taxa Falhas (%)', 'Dentro Prazo (%)']
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
            prazo_resp = resp_analysis[resp_analysis['Total Atividades'] > 0][['Dentro Prazo (%)']]
            prazo_resp = prazo_resp.sort_values('Dentro Prazo (%)', ascending=True)  # Do menor para o maior

            if not prazo_resp.empty:

                fig_prazo_resp = px.bar(prazo_resp, 
                                x=prazo_resp.index,
                                y='Dentro Prazo (%)',
                                title=f'% Dentro do Prazo por Responsável ({PRAZO_GESTAO} dias)',
                                color='Dentro Prazo (%)',
                                color_continuous_scale='RdYlGn')
                        
                fig_prazo_resp.update_layout(xaxis_tickangle=-45,
                                         yaxis_range=[0, 100])  # Forçar escala de 0-100%
                fig_prazo_resp.update_traces(texttemplate='%{y:.1f}%', textposition='outside')

                st.plotly_chart(fig_prazo_resp, use_container_width=True)
            else:
                st.info("📊 Não há dados de prazo para exibir")
        else:
            st.info("📊 Nenhuma atividade concluída para análise de prazos")

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
            prazo_mod = modulo_analysis[modulo_analysis['Total'] > 0][['Dentro Prazo (%)']]
            prazo_mod = prazo_mod.sort_values('Dentro Prazo (%)', ascending=True)  # Do menor para o maior

            if not prazo_mod.empty:
                fig_prazo_mod = px.bar(prazo_mod,
                                       x=prazo_mod.index,
                                       y='Dentro Prazo (%)',
                                       title=f'% Dentro do Prazo por Módulo ({PRAZO_GESTAO} dias)',
                                       color='Dentro Prazo (%)',
                                       color_continuous_scale='RdYlGn')
                
                fig_prazo_mod.update_layout(xaxis_tickangle=-45,
                                            yaxis_range=[0, 100])
                fig_prazo_mod.update_traces(texttemplate='%{y:.1f}%', textposition='outside')

                st.plotly_chart(fig_prazo_mod, use_container_width=True)
            else:
                st.info("📊 Não há dados de prazo por módulo para exibir")
        else:
            st.info("📊 Nenhuma atividade concluída para análise de prazos por módulo")                            

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
    
    # Adiciona CSS para cores consistentes
    st.markdown("""
    <style>
    .on-time-card {
        background-color: #f0f9f0;
        border: 1px solid #4CAF50;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #2e7d32;
    }
    .late-card {
        background-color: #fff3e0;
        border: 1px solid #FF9800;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        color: #e65100;
    }
    .slow-activity {
        background-color: #ffebee;
        border: 1px solid #f44336;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        color: #c62828;
    }
    .fast-activity {
        background-color: #e8f5e8;
        border: 1px solid #66bb6a;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        color: #2e7d32;
    }
    @media (prefers-color-scheme: dark) {
        .on-time-card {
            background-color: #1b5e20;
            border-color: #4CAF50;
            color: #a5d6a7;
        }
        .late-card {
            background-color: #e65100;
            border-color: #FF9800;
            color: #ffe0b2;
        }
        .slow-activity {
            background-color: #b71c1c;
            border-color: #f44336;
            color: #ffcdd2;
        }
        .fast-activity {
            background-color: #1b5e20;
            border-color: #66bb6a;
            color: #c8e6c9;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # CARDS NO TOPO - SEM DIVIDIR ESPAÇO
    st.markdown("### 📊 Estatísticas de Prazo")
    
    if total_concluidas > 0:
        # Cálculo dinâmico
        dentro_prazo_correto = len(df_concluidas_filtrado[df_concluidas_filtrado['Cumpriu Prazo'] == 'Dentro do Prazo'])
        fora_prazo_correto = len(df_concluidas_filtrado[df_concluidas_filtrado['Cumpriu Prazo'] == 'Fora do Prazo'])
        taxa_dentro_correta = (dentro_prazo_correto / total_concluidas) * 100
        taxa_fora_correta = (fora_prazo_correto / total_concluidas) * 100
        
        # Cards lado a lado no topo
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="on-time-card">
                <h4 style="margin:0; color: inherit;">✅ Dentro do Prazo ({PRAZO_GESTAO} dias)</h4>
                <p style="margin:5px 0; font-size: 1.2em;"><strong>{dentro_prazo_correto} atividades</strong> ({taxa_dentro_correta:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="late-card">
                <h4 style="margin:0; color: inherit;">❌ Fora do Prazo ({PRAZO_GESTAO} dias)</h4>
                <p style="margin:5px 0; font-size: 1.2em;"><strong>{fora_prazo_correto} atividades</strong> ({taxa_fora_correta:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
    
    # CONTEÚDO ABAIXO DOS CARDS (agora em colunas separadas)
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Distribuição de tempos
        st.markdown("### 📈 Distribuição dos Tempos de Entrega")
        if total_concluidas > 0:
            fig_dist_tempo = px.histogram(df_concluidas_filtrado, x='Tempo Entrega (dias)',
                                        title='Distribuição dos Tempos de Entrega',
                                        nbins=20,
                                        color_discrete_sequence=['#4285f4'])
            fig_dist_tempo.add_vline(x=PRAZO_GESTAO, line_dash="dash", line_color="#FF6B6B",
                                   annotation_text=f"Prazo: {PRAZO_GESTAO}d")
            fig_dist_tempo.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_dist_tempo, use_container_width=True)
    
    with col4:
        st.markdown("### 🐌 Top 5 Atividades Mais Atrasadas")
        
        if total_concluidas > 0:
            atividades_atrasadas = df_concluidas_filtrado[df_concluidas_filtrado['Cumpriu Prazo'] == 'Fora do Prazo']
            if not atividades_atrasadas.empty:
                top5_atrasadas = atividades_atrasadas.nlargest(5, 'Tempo Entrega (dias)')
                for idx, atividade in top5_atrasadas.iterrows():
                    dias_atraso = atividade['Tempo Entrega (dias)'] - PRAZO_GESTAO
                    st.markdown(f"""
                    <div class="slow-activity">
                        <strong style="color: inherit;">+{dias_atraso:.0f} dias de atraso</strong><br>
                        <strong>ID:</strong> {atividade['ID']} | <strong>Responsável:</strong> {atividade['Responsável']}<br>
                        <strong>Módulo:</strong> {atividade['Módulo']}<br>
                        <strong>Tempo total:</strong> {atividade['Tempo Entrega (dias)']:.1f} dias<br>
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
                    <strong style="color: inherit;">{atividade['Tempo Entrega (dias)']:.1f} dias</strong><br>
                    <strong>ID:</strong> {atividade['ID']} | <strong>Responsável:</strong> {atividade['Responsável']}<br>
                    {atividade['Atividade'][:60]}...
                </div>
                """, unsafe_allow_html=True)


with tab6:
    st.subheader("🎛️ Análise da Aba Controlador")
    
    if df_controlador is not None:
        # Limpeza e preparação dos dados do Controlador
        df_controlador_clean = df_controlador.copy()
        
        # Preencher valores vazios
        df_controlador_clean['Responsável'] = df_controlador_clean['Responsável'].fillna('Sem Responsável')
        df_controlador_clean['Módulo'] = df_controlador_clean['Módulo'].fillna('Sem Módulo')
        df_controlador_clean['Pontos'] = pd.to_numeric(df_controlador_clean['Pontos'], errors='coerce').fillna(0)
        
        # Converter datas
        df_controlador_clean['Data Abertura'] = pd.to_datetime(df_controlador_clean['Data Abertura'], errors='coerce')
        df_controlador_clean['Data Entrega'] = pd.to_datetime(df_controlador_clean['Data Entrega'], errors='coerce')
        
        # Calcular tempo de entrega
        mask = df_controlador_clean['Data Abertura'].notna() & df_controlador_clean['Data Entrega'].notna()
        df_controlador_clean.loc[mask, 'Tempo Entrega (dias)'] = (df_controlador_clean.loc[mask, 'Data Entrega'] - df_controlador_clean.loc[mask, 'Data Abertura']).dt.days
        
        # VISUALIZAÇÃO DOS DADOS COM LUPA EXPANSÍVEL
        st.markdown("### 📋 Visualização dos Dados")
        
        # Criar colunas para o cabeçalho com lupa
        col_header1, col_header2 = st.columns([3, 1])
        
        with col_header1:
            st.write(f"**Total de demandas:** {len(df_controlador_clean)}")
        
        with col_header2:
            # Botão de lupa para expandir/recolher
            expandir_tabela = st.button("🔍 Expandir Tabela", key="expandir_controlador")
        
        # Mostrar tabela compacta ou expandida
        if expandir_tabela:
            st.dataframe(df_controlador_clean, use_container_width=True, height=400)
            st.button("↸ Recolher Tabela", key="recolher_controlador")
        else:
            # Mostrar apenas as primeiras linhas
            st.dataframe(df_controlador_clean.head(8), use_container_width=True)
            if len(df_controlador_clean) > 8:
                st.caption(f"Mostrando 8 de {len(df_controlador_clean)} registros. Use o botão 🔍 para ver todos.")
        
        # ESTATÍSTICAS PRINCIPAIS
        st.markdown("### 📊 Estatísticas do Controlador")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_demandas = len(df_controlador_clean)
            st.metric("Total de Demandas", total_demandas)
        
        with col2:
            total_pontos = df_controlador_clean['Pontos'].sum()
            st.metric("Total de Pontos", f"{total_pontos:.0f}")
        
        with col3:
            demanda_media_pontos = df_controlador_clean['Pontos'].mean()
            st.metric("Média de Pontos/Demanda", f"{demanda_media_pontos:.1f}")
        
        with col4:
            responsaveis_ativos = df_controlador_clean['Responsável'].nunique()
            st.metric("Responsáveis Ativos", responsaveis_ativos)
        
        # ANÁLISE DE PONTOS (DIFICULDADE)
        st.markdown("### 🎯 Análise de Dificuldade (Pontos)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição de pontos
            st.markdown("#### 📈 Distribuição de Pontos por Demanda")
            fig_pontos = px.histogram(df_controlador_clean, x='Pontos', 
                                    title='Distribuição de Pontos (Dificuldade)',
                                    nbins=10,
                                    color_discrete_sequence=['#FF6B6B'])
            st.plotly_chart(fig_pontos, use_container_width=True)
        
        with col2:
            # Top demandas mais difíceis
            st.markdown("#### 🏆 Top 5 Demandas Mais Complexas")
            top_dificil = df_controlador_clean.nlargest(5, 'Pontos')[['ID', 'Atividade', 'Pontos', 'Responsável']]
            for idx, demanda in top_dificil.iterrows():
                st.markdown(f"""
                <div class="slow-activity">
                    <strong>{demanda['Pontos']} pontos</strong><br>
                    <strong>ID:</strong> {demanda['ID']} | <strong>Responsável:</strong> {demanda['Responsável']}<br>
                    {demanda['Atividade'][:60]}...
                </div>
                """, unsafe_allow_html=True)
        
        # ANÁLISE POR RESPONSÁVEL
        st.markdown("### 👤 Análise por Responsável")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pontos por responsável
            pontos_por_resp = df_controlador_clean.groupby('Responsável').agg({
                'ID': 'count',
                'Pontos': 'sum',
                'Tempo Entrega (dias)': 'mean'
            }).round(1)
            pontos_por_resp.columns = ['Total Demandas', 'Pontos Totais', 'Tempo Médio (dias)']
            pontos_por_resp = pontos_por_resp.sort_values('Pontos Totais', ascending=False)
            
            st.markdown("#### 📊 Pontos por Responsável")
            st.dataframe(pontos_por_resp, use_container_width=True)
        
        with col2:
            # Gráfico de pontos por responsável
            if not pontos_por_resp.empty:
                fig_pontos_resp = px.bar(pontos_por_resp.head(10), 
                                       x=pontos_por_resp.head(10).index,
                                       y='Pontos Totais',
                                       title='Top 10 - Pontos por Responsável',
                                       color='Pontos Totais',
                                       color_continuous_scale='Viridis')
                fig_pontos_resp.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_pontos_resp, use_container_width=True)
        
        # ANÁLISE POR MÓDULO
        st.markdown("### 🔧 Análise por Módulo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pontos por módulo
            pontos_por_modulo = df_controlador_clean.groupby('Módulo').agg({
                'ID': 'count',
                'Pontos': 'sum'
            }).round(1)
            pontos_por_modulo.columns = ['Total Demandas', 'Pontos Totais']
            pontos_por_modulo = pontos_por_modulo.sort_values('Pontos Totais', ascending=False)
            
            st.markdown("#### 📊 Módulos por Complexidade")
            st.dataframe(pontos_por_modulo, use_container_width=True)
        
        with col2:
            # Gráfico de pontos por módulo
            if not pontos_por_modulo.empty:
                fig_pontos_mod = px.pie(pontos_por_modulo, 
                                      values='Pontos Totais', 
                                      names=pontos_por_modulo.index,
                                      title='Distribuição de Pontos por Módulo')
                st.plotly_chart(fig_pontos_mod, use_container_width=True)
        
                
        # INSIGHTS ESPECÍFICOS DO CONTROLADOR
        st.markdown("### 💡 Insights do Controlador")
        
        # Responsável com mais pontos (mais complexidade)
        resp_mais_pontos = pontos_por_resp.nlargest(1, 'Pontos Totais')
        if not resp_mais_pontos.empty:
            resp, dados = list(resp_mais_pontos.iterrows())[0]
            st.info(f"**🏆 Maior complexidade:** {resp} - {dados['Pontos Totais']} pontos totais")
        
        # Módulo mais complexo
        modulo_mais_pontos = pontos_por_modulo.nlargest(1, 'Pontos Totais')
        if not modulo_mais_pontos.empty:
            mod, dados = list(modulo_mais_pontos.iterrows())[0]
            st.info(f"**🔧 Módulo mais complexo:** {mod} - {dados['Pontos Totais']} pontos totais")
        
        # Demanda mais difícil
        if not df_controlador_clean.empty:
            demanda_mais_dificil = df_controlador_clean.nlargest(1, 'Pontos')
            if not demanda_mais_dificil.empty:
                demanda = demanda_mais_dificil.iloc[0]
                st.warning(f"**🚨 Demanda mais complexa:** ID {demanda['ID']} - {demanda['Pontos']} pontos - {demanda['Responsável']}")
    
    else:
        st.error("❌ Não foi possível carregar os dados do Controlador")             
      

with tab7:
    st.subheader("🚨 Insights e Recomendações")
    
    # Insights baseados nos dados
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Insights de Performance")
          
    if total_concluidas > 0:
        # EXCLUIR "Sem Responsável" da análise - FILTRO ADICIONADO
        resp_analysis_filtrado = resp_analysis[
            (resp_analysis['Total Atividades'] > 0) & 
            (resp_analysis.index != 'Sem Responsável')  # ✅ EXCLUI SEM RESPONSÁVEL
        ]
        
        # Três responsáveis com performance mais baixa (mais lentos)
        piores_prazo_resp = resp_analysis_filtrado.nsmallest(3, 'Dentro Prazo (%)') 

        if not piores_prazo_resp.empty:
            st.warning("**🐌 Maiores dificuldades com prazos:**")

            for idx, (resp, dados) in enumerate(piores_prazo_resp.iterrows(), 1):
                emoji = "🥉" if idx == 3 else "🥈" if idx == 2 else "🥇"
                st.write(f"{emoji} **{idx}º {resp}** - {dados['Dentro Prazo (%)']:.1f}% dentro do prazo")

                # Mostra estatísticas detalhadas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", int(dados['Total Atividades']))
                with col2:
                    dentro_prazo_qtd = int(dados['Total Atividades'] * (dados['Dentro Prazo (%)'] / 100))
                    st.metric("Dentro Prazo", dentro_prazo_qtd)
                with col3:
                    fora_prazo_qtd = int(dados['Total Atividades'] - dentro_prazo_qtd)
                    st.metric("Fora Prazo", fora_prazo_qtd)

                st.markdown("---")
        else:
            st.info("📊 Não há responsáveis com dados suficientes para análise")

    else:
        st.info("📊 Dados insuficientes para análise de performance")

    # Módulo com melhor performance no prazo (mantido igual)
    melhor_prazo_mod = modulo_analysis[modulo_analysis['Total'] > 0].nlargest(1, 'Dentro Prazo (%)')
    if not melhor_prazo_mod.empty:
        mod, dados = list(melhor_prazo_mod.iterrows())[0]
        st.info(f"**🔧 Módulo mais eficiente:** {mod} - {dados['Dentro Prazo (%)']:.1f}% dentro do prazo")
    
    # Identificar problemas (mantido igual)
    if taxa_fora_prazo > 50:
        st.error(f"**⚠️ Atenção:** Mais de 50% das atividades estão fora do prazo!")
    elif taxa_fora_prazo > 30:
        st.warning(f"**📊 Observação:** {taxa_fora_prazo:.1f}% das atividades estão fora do prazo")
    else:
        st.success(f"**✅ Excelente:** Apenas {taxa_fora_prazo:.1f}% das atividades estão fora do prazo")

with col2:
    st.markdown("<h3 style='text-align: left;'>💡 Recomendações</h3>", unsafe_allow_html=True)

recomendacoes = []

if total_concluidas > 0:
    if taxa_fora_prazo > 40:
        recomendacoes.append("**🔴 Prioridade:** Revisar processos que estão causando atrasos frequentes")
    
    if atividades_sem_responsavel > 0:
        recomendacoes.append(f"**👥 Atribuição:** {atividades_sem_responsavel} atividades sem responsável precisam ser atribuídas")
    
    # Verificar responsáveis com baixa performance no prazo - EXCLUIR SEM RESPONSÁVEL
    resp_baixa_performance = resp_analysis[
        (resp_analysis['Total Atividades'] >= 3) & 
        (resp_analysis['Dentro Prazo (%)'] < 50) &
        (resp_analysis.index != 'Sem Responsável')  # ✅ EXCLUI SEM RESPONSÁVEL
    ]
    if not resp_baixa_performance.empty:
        for resp, dados in resp_baixa_performance.iterrows():
            recomendacoes.append(f"**🎯 Treinamento:** {resp} tem apenas {dados['Dentro Prazo (%)']:.1f}% dentro do prazo")
    
    # Verificar módulos problemáticos (mantido igual)
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
    
    # Responsáveis com alta taxa de falhas - EXCLUIR SEM RESPONSÁVEL
    resp_alta_falhas = resp_analysis[
        (resp_analysis['Total Atividades'] >= 3) & 
        (resp_analysis['Taxa Falhas (%)'] > 20) &
        (resp_analysis.index != 'Sem Responsável')  # ✅ EXCLUI SEM RESPONSÁVEL
    ]
    if not resp_alta_falhas.empty:
        for resp, dados in resp_alta_falhas.iterrows():
            recomendacoes.append(f"**🧪 Testes:** {resp} tem {dados['Taxa Falhas (%)']:.1f}% de falhas - fortalecer testes")

if not recomendacoes:
    recomendacoes.append("**✅ Manutenção:** Continue com os processos atuais - performance dentro do esperado")

# Exibir recomendações
for rec in recomendacoes:
    st.markdown(rec)

# Rodapé
st.markdown("---")
st.markdown("**Dashboard de Produtividade** - Desenvolvido para análise do Time SAI")
st.markdown(f"📊 **Fonte de dados:** Google Sheets | ⏰ **Prazo estabelecido:** {PRAZO_GESTAO} dias (48h)")