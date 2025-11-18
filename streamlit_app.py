import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
import os

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

# Função para criar campo com dropdown SIMPLIFICADA (sem "Outro")
def criar_campo_dropdown(label, obrigatorio=False, key_suffix=""):
    """
    Cria um campo com dropdown baseado nas opções reais da planilha
    """
    # OPÇÕES REAIS DA SUA PLANILHA
    if "Módulo" in label:
        opcoes_reais = ["Controlador", "Home Page", "Portal da Transparência", "Sai Conecta", 
                       "Ouvidoria/Esic", "Diário Oficial/SEJ", "E-mail", "PNCP", 
                       "Publicação Tutorial", "Fora do ar"]
    elif "Responsável" in label:
        opcoes_reais = ["Georgeton", "Felipe A.", "Vanessa", "Jonas", "Danilo", 
                       "Rebeca", "Filipe", "Elton", "Cristiano (estagiário)", "Fredson"]
    elif "Sprint" in label:
        opcoes_reais = ["Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4"]
    else:
        opcoes_reais = []
    
    # Criar opções completas (sem "Outro")
    opcoes_completas = ["Selecione..."] + opcoes_reais
    
    # Dropdown simples
    selecionado = st.selectbox(
        f"{label}{'*' if obrigatorio else ''}", 
        opcoes_completas, 
        key=f"{label}_{key_suffix}"
    )
    
    return selecionado

# Função para inserir dados na planilha com seleção de aba
def inserir_dados_planilha():
    st.header("📝 Inserir Nova Atividade")
    
    # Seleção da aba
    st.subheader("1. Selecionar Planilha")
    aba_selecionada = st.radio(
        "Em qual planilha deseja inserir os dados?",
        ["Manutenção", "Controlador"],
        horizontal=True,
        key="aba_selecao"
    )
    
    st.markdown("---")
    
    # Formulário específico para cada aba
    if aba_selecionada == "Manutenção":
        inserir_dados_manutencao()
    else:
        inserir_dados_controlador()

# Função para inserir dados na aba MANUTENÇÃO (SIMPLIFICADA)
def inserir_dados_manutencao():
    st.subheader("📋 Formulário - Aba Manutenção")
    
    with st.form("form_manutencao"):
        col1, col2 = st.columns(2)
        
        with col1:
            atividade = st.text_input("Atividade*", placeholder="Descreva a atividade", key="atividade_manutencao")
            
            # Campo Módulo com dropdown SIMPLES
            modulo = criar_campo_dropdown("Módulo", obrigatorio=True, key_suffix="manutencao")
            
            data_abertura = st.date_input("Data de Abertura*", datetime.now(), key="data_abertura_manutencao")
            
            # Campo Responsável com dropdown SIMPLES
            responsavel = criar_campo_dropdown("Responsável", obrigatorio=True, key_suffix="manutencao")
            
        with col2:
            status = st.selectbox("Status*", ["Pendente", "Em Andamento", "Concluída", "Cancelada"], key="status_manutencao")
            falha_teste = st.selectbox("Falha/Teste em Produção*", ["Sim", "Não"], key="falha_teste_manutencao")
            
            # Campo Sprint com dropdown SIMPLES
            sprint = criar_campo_dropdown("Sprint", key_suffix="manutencao")
            
            data_entrega = st.date_input("Data de Entrega", datetime.now(), key="data_entrega_manutencao")
        
        observacoes = st.text_area("Observações", placeholder="Observações adicionais...", key="obs_manutencao")
        
        submitted = st.form_submit_button("💾 Salvar na Aba Manutenção", key="submit_manutencao")
        
        if submitted:
            # Validações
            campos_obrigatorios = [
                (atividade, "Atividade"),
                (modulo, "Módulo"),
                (responsavel, "Responsável")
            ]
            
            campos_faltantes = [nome for campo, nome in campos_obrigatorios if not campo or campo == "Selecione..."]
            
            if campos_faltantes:
                st.error(f"❌ Preencha todos os campos obrigatórios: {', '.join(campos_faltantes)}")
            else:
                try:
                    # Conectar com a planilha
                    aba_manutencao, _ = setup_gsheets()
                    
                    # Preparar os dados para inserção (na ordem das colunas)
                    novo_registro = [
                        len(aba_manutencao.get_all_records()) + 1,  # ID automático
                        atividade,
                        modulo,
                        data_abertura.strftime("%Y-%m-%d"),
                        data_entrega.strftime("%Y-%m-%d") if data_entrega else "",
                        responsavel,
                        falha_teste,
                        status,
                        sprint if sprint != "Selecione..." else ""
                    ]
                    
                    # Inserir na planilha
                    aba_manutencao.append_row(novo_registro)
                    
                    st.success("✅ Atividade salva na aba Manutenção com sucesso!")
                    st.balloons()
                    
                    # Limpar cache para atualizar os dados
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar atividade: {e}")

# Função para inserir dados na aba CONTROLADOR (SIMPLIFICADA)
def inserir_dados_controlador():
    st.subheader("🎯 Formulário - Aba Controlador")
    
    with st.form("form_controlador"):
        col1, col2 = st.columns(2)
        
        with col1:
            atividade = st.text_input("Atividade*", placeholder="Descreva a atividade", key="atividade_controlador")
            
            # Campo Módulo com dropdown SIMPLES
            modulo = criar_campo_dropdown("Módulo", obrigatorio=True, key_suffix="controlador")
            
            data_abertura = st.date_input("Data de Abertura*", datetime.now(), key="data_abertura_controlador")
            
        with col2:
            # Campo Responsável com dropdown SIMPLES
            responsavel = criar_campo_dropdown("Responsável", obrigatorio=True, key_suffix="controlador")
            
            data_entrega = st.date_input("Data de Entrega", datetime.now(), key="data_entrega_controlador")
            pontos = st.number_input("Pontos*", min_value=0, max_value=100, value=1, step=1, key="pontos_controlador")
        
        observacoes = st.text_area("Observações", placeholder="Observações adicionais...", key="obs_controlador")
        
        submitted = st.form_submit_button("💾 Salvar na Aba Controlador", key="submit_controlador")
        
        if submitted:
            # Validações
            campos_obrigatorios = [
                (atividade, "Atividade"),
                (modulo, "Módulo"),
                (responsavel, "Responsável")
            ]
            
            campos_faltantes = [nome for campo, nome in campos_obrigatorios if not campo or campo == "Selecione..."]
            
            if campos_faltantes:
                st.error(f"❌ Preencha todos os campos obrigatórios: {', '.join(campos_faltantes)}")
            else:
                try:
                    # Conectar com a planilha
                    _, aba_controlador = setup_gsheets()
                    
                    # Preparar os dados para inserção (na ordem das colunas do Controlador)
                    novo_registro = [
                        len(aba_controlador.get_all_records()) + 1,  # ID automático
                        atividade,
                        modulo,
                        data_abertura.strftime("%Y-%m-%d"),
                        data_entrega.strftime("%Y-%m-%d") if data_entrega else "",
                        responsavel,
                        pontos
                    ]
                    
                    # Inserir na planilha
                    aba_controlador.append_row(novo_registro)
                    
                    st.success("✅ Atividade salva na aba Controlador com sucesso!")
                    st.balloons()
                    
                    # Limpar cache para atualizar os dados
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar atividade: {e}")

def calcular_dias_em_aberto(df):
    """
    Calcula dias em aberto para demandas não finalizadas
    """
    if df.empty:
        return pd.DataFrame()
    
    df_alerta = df.copy()
    
    # Status que indicam "não finalizado"
    status_nao_finalizados = ['Pendente', 'Em Andamento', 'Aberta', 'Aberto', 'Open', 'To Do', 'In Progress', 'Em Desenvolvimento']
    
    # Filtrar por status não finalizados
    status_existentes = [s for s in status_nao_finalizados if s in df_alerta['Status'].values]
    
    if status_existentes:
        df_alerta = df_alerta[df_alerta['Status'].isin(status_existentes)]
    else:
        # Fallback: usar data entrega vazia
        if 'Data Entrega' in df_alerta.columns:
            df_alerta = df_alerta[
                df_alerta['Data Entrega'].isna() | 
                (df_alerta['Data Entrega'] == '') |
                (df_alerta['Data Entrega'].astype(str).str.strip() == '') |
                (df_alerta['Data Entrega'].astype(str).str.strip() == 'NaT')
            ]
    
    if df_alerta.empty or 'Data Abertura' not in df_alerta.columns:
        return pd.DataFrame()
    
    # Garantir que as datas estão em formato correto
    df_alerta['Data Abertura'] = pd.to_datetime(df_alerta['Data Abertura'], errors='coerce')
    df_alerta = df_alerta.dropna(subset=['Data Abertura'])
    
    if df_alerta.empty:
        return pd.DataFrame()
    
    # Calcular dias em aberto
    hoje = pd.Timestamp.now().normalize()
    df_alerta['Dias em Aberto'] = (hoje - df_alerta['Data Abertura']).dt.days
    
    # Classificar alertas
    def classificar_alerta(dias):
        if dias >= 7:
            return '🔴 Crítico'
        elif dias >= 5:
            return '🟡 Alerta'
        else:
            return '✅ Normal'
    
    df_alerta['Nível Alerta'] = df_alerta['Dias em Aberto'].apply(classificar_alerta)
    
    # Filtrar apenas alertas (5+ dias)
    df_alerta = df_alerta[df_alerta['Dias em Aberto'] >= 5]
    
    return df_alerta.sort_values('Dias em Aberto', ascending=False)

# Sistema de navegação
st.sidebar.title("🧭 Navegação")
pagina = st.sidebar.radio(
    "Selecione a página:", 
    ["📊 Dashboard", "📝 Inserir Dados"],
    key="navegacao_principal"
)

# =============================================================================
# SISTEMA DO ASSISTENTE IA PARA PRODUTIVIDADE - VERSÃO MELHORADA
# =============================================================================

def show_assistente_produtividade_ia(df_manutencao_filtrado, df_controlador_filtrado, gemini_key=None):
    """Exibe a interface do assistente de IA para análise de produtividade - VERSÃO MELHORADA"""
    
    st.header("🤖 Assistente de IA - Análise de Produtividade")
    st.write("Faça perguntas em português sobre os dados de produtividade e receba insights automatizados.")
    
    # Inicializar estado da sessão
    if 'produtividade_assistant_responses' not in st.session_state:
        st.session_state.produtividade_assistant_responses = []
    if 'produtividade_current_question' not in st.session_state:
        st.session_state.produtividade_current_question = ""
    if 'produtividade_last_response' not in st.session_state:
        st.session_state.produtividade_last_response = ""
    if 'produtividade_processing_question' not in st.session_state:
        st.session_state.produtividade_processing_question = False
    
    # Configuração do modelo
    model_options = [
        '🚀 Gemini Pro - Análise Avançada',
        '⚡ Gemini Flash - Resposta Rápida' 
    ]

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_model = st.selectbox(
            label='**Nível de análise:**',
            options=model_options,
            index=0,
            key='produtividade_assistant_model'
        )
    
        if selected_model == '🚀 Gemini Pro - Análise Avançada':
            st.caption("💡 Análises profundas e insights detalhados")
        elif selected_model == '⚡ Gemini Flash - Resposta Rápida':
            st.caption("💡 Respostas rápidas para perguntas simples")
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 Limpar Histórico", key='reset_produtividade_assistant'):
            st.session_state.produtividade_assistant_responses = []
            st.session_state.produtividade_last_response = ""
            st.session_state.produtividade_current_question = ""
            st.session_state.produtividade_processing_question = False
            st.success("✅ Histórico limpo!")
            st.rerun()
    
    st.markdown("---")
    
    # SUGESTÕES DE PERGUNTAS CONTEXTUAIS MELHORADAS
    st.markdown("### 💡 Sugestões de Perguntas Contextuais")
    
    # Primeira linha de sugestões
    col_sug1, col_sug2, col_sug3, col_sug4 = st.columns(4)

    with col_sug1:
        if st.button("📊 Análise Geral", use_container_width=True):
            st.session_state.produtividade_current_question = "Faça uma análise geral completa da produtividade do time, incluindo métricas de conclusão, prazos, qualidade e distribuição por módulos."
            st.rerun()

    with col_sug2:
        if st.button("⏰ Desempenho", use_container_width=True):
            st.session_state.produtividade_current_question = "Como está o desempenho da equipe em relação aos prazos de 48 horas? Quem são os colaboradores com melhor e pior performance em termos de tempo de entrega?"
            st.rerun()

    with col_sug3:
        if st.button("🔧 Módulos", use_container_width=True):
            st.session_state.produtividade_current_question = "Quais módulos têm mais atividades, falhas e atrasos? Há algum padrão específico no Portal da Transparência ou outros módulos que precise de atenção?"
            st.rerun()

    with col_sug4:
        if st.button("👥 Equipe", use_container_width=True):
            st.session_state.produtividade_current_question = "Analise o desempenho individual de cada colaborador. Quem tem a melhor taxa de conclusão? Há alguém com muitos problemas de qualidade ou atrasos?"
            st.rerun()

    # Segunda linha de sugestões
    col_sug5, col_sug6, col_sug7, col_sug8 = st.columns(4)

    with col_sug5:
        if st.button("🚀 Sprint", use_container_width=True):
            st.session_state.produtividade_current_question = "Como está o andamento da sprint atual? Qual é o progresso e há riscos de não cumprimento dos objetivos?"
            st.rerun()

    with col_sug6:
        if st.button("🔴 Qualidade", use_container_width=True):
            st.session_state.produtividade_current_question = "Qual é a taxa de falhas geral da equipe? Quais módulos e colaboradores têm mais problemas de qualidade? O que pode ser feito para melhorar?"
            st.rerun()

    with col_sug7:
        if st.button("📈 Tendências", use_container_width=True):
            st.session_state.produtividade_current_question = "Quais são as tendências de produtividade ao longo do tempo? Estamos melhorando ou piorando em termos de velocidade e qualidade?"
            st.rerun()

    with col_sug8:
        if st.button("🎯 Recomendações", use_container_width=True):
            st.session_state.produtividade_current_question = "Baseado nos dados, quais são as 3 principais recomendações para melhorar a produtividade e qualidade do time SAI?"
            st.rerun()
    
    # INSIGHTS AUTOMÁTICOS (NOVO)
    st.markdown("---")
    st.markdown("### 🎯 Insights Automáticos")
    
    # Botão para gerar insights automáticos
    if st.button("✨ Gerar Insights Automáticos", use_container_width=True):
        try:
            from assistente_produtividade import gerar_insights_automaticos
            insights = gerar_insights_automaticos(df_manutencao_filtrado, df_controlador_filtrado)
            st.session_state.produtividade_current_question = "Com base nos insights automáticos gerados, forneça uma análise detalhada e recomendações específicas."
            # Armazenar insights para uso na consulta
            st.session_state.insights_automaticos = insights
            st.rerun()
        except ImportError:
            st.error("❌ Módulo de insights não disponível")
    
    # Mostrar insights se disponíveis
    if 'insights_automaticos' in st.session_state:
        with st.expander("📊 Insights Gerados Automaticamente"):
            st.markdown(st.session_state.insights_automaticos)
    
    st.markdown("---")
    
    # Área de pergunta
    user_question = st.text_area(
        '**Digite sua pergunta:**',
        placeholder='Ex: Quem são os colaboradores com melhor desempenho? Quais módulos demandam mais atenção? Como melhorar nossa taxa de entrega dentro do prazo? Analise o desempenho do Portal da Transparência...',
        height=100,
        key='produtividade_assistant_question',
        value=st.session_state.produtividade_current_question
    )
    
    # Atualizar a pergunta atual no session_state
    st.session_state.produtividade_current_question = user_question
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        consultar_button = st.button('🔍 Consultar Assistente', type='primary', key='produtividade_assistant_btn', use_container_width=True)
    
    with col2:
        if st.session_state.produtividade_last_response and not st.session_state.produtividade_processing_question:
            if st.button('📋 Copiar Resposta', key='produtividade_copy_response', use_container_width=True):
                st.code(st.session_state.produtividade_last_response, language='markdown')
                st.success("✅ Resposta copiada para a área de transferência!")
    
    # VERIFICAR SE HÁ UMA CONSULTA PENDENTE PARA PROCESSAR
    if consultar_button and user_question and not st.session_state.produtividade_processing_question:
        # Marcar que estamos processando
        st.session_state.produtividade_processing_question = True
        st.session_state.produtividade_current_question = user_question
        
        # Armazenar a pergunta para processamento
        st.session_state.produtividade_pending_question = user_question
        st.session_state.produtividade_pending_model = selected_model
        
        # Incluir insights automáticos se disponíveis
        if 'insights_automaticos' in st.session_state:
            st.session_state.produtividade_pending_insights = st.session_state.insights_automaticos
        else:
            st.session_state.produtividade_pending_insights = None
        
        # Forçar rerun imediatamente para mostrar o spinner
        st.rerun()
    
    # PROCESSAR A CONSULTA APÓS O RERUN
    if st.session_state.get('produtividade_processing_question', False) and st.session_state.get('produtividade_pending_question'):
        # Container para o spinner
        processing_placeholder = st.empty()
        
        with processing_placeholder.container():
            with st.spinner('🤔 Analisando dados de produtividade... Isso pode levar alguns segundos'):
                try:
                    # Importar módulo do assistente
                    try:
                        from assistente_produtividade import consultar_assistente_produtividade
                    except ImportError as e:
                        # Fallback local
                        def consultar_assistente_produtividade_fallback(pergunta, df_manutencao, df_controlador, tipo_modelo, gemini_key):
                            return f"❌ Módulo do assistente não disponível. Erro: {e}\n\n📊 **Análise Local:**\n- Manutenção: {len(df_manutencao)} registros\n- Controlador: {len(df_controlador)} registros"
                        consultar_assistente_produtividade = consultar_assistente_produtividade_fallback
                    
                    # Executar consulta
                    resposta = consultar_assistente_produtividade(
                        pergunta=st.session_state.produtividade_pending_question,
                        df_manutencao=df_manutencao_filtrado,
                        df_controlador=df_controlador_filtrado,
                        tipo_modelo=st.session_state.produtividade_pending_model,
                        gemini_key=gemini_key
                    )
                    
                    # Salvar no histórico
                    nova_resposta = {
                        'pergunta': st.session_state.produtividade_pending_question,
                        'resposta': resposta,
                        'modelo': st.session_state.produtividade_pending_model,
                        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'registros_manutencao': len(df_manutencao_filtrado),
                        'registros_controlador': len(df_controlador_filtrado)
                    }
                    
                    st.session_state.produtividade_assistant_responses.append(nova_resposta)
                    st.session_state.produtividade_last_response = resposta
                    
                except Exception as e:
                    error_msg = f"❌ Erro ao consultar assistente: {str(e)}"
                    st.error(error_msg)
                    st.session_state.produtividade_last_response = error_msg
        
        # Limpar estados de processamento
        st.session_state.produtividade_processing_question = False
        st.session_state.produtividade_pending_question = None
        st.session_state.produtividade_pending_model = None
        st.session_state.produtividade_pending_insights = None
        
        # Limpar o placeholder do spinner
        processing_placeholder.empty()
        
        # Rerun final para mostrar a resposta
        st.rerun()
    
    # MOSTRAR RESPOSTAS
    if not st.session_state.produtividade_processing_question:
        # Mostrar última resposta
        if st.session_state.produtividade_last_response:
            st.markdown("---")
            st.subheader("📋 Resposta:")
            st.markdown(st.session_state.produtividade_last_response)
            
            # Informações do contexto
            with st.expander("ℹ️ Informações do contexto"):
                st.write(f"**Modelo usado:** {selected_model}")
                st.write(f"**Registros Manutenção analisados:** {len(df_manutencao_filtrado)}")
                st.write(f"**Registros Controlador analisados:** {len(df_controlador_filtrado)}")
                
                # Estatísticas rápidas
                if not df_manutencao_filtrado.empty:
                    concluidas = len(df_manutencao_filtrado[df_manutencao_filtrado['Status'] == 'Concluída'])
                    taxa_conclusao = (concluidas / len(df_manutencao_filtrado)) * 100
                    st.write(f"**Taxa de conclusão:** {taxa_conclusao:.1f}%")
                    
                    if 'Falha/ Teste em Produção' in df_manutencao_filtrado.columns:
                        falhas = len(df_manutencao_filtrado[df_manutencao_filtrado['Falha/ Teste em Produção'] == 'Sim'])
                        taxa_falhas = (falhas / len(df_manutencao_filtrado)) * 100
                        st.write(f"**Taxa de falhas:** {taxa_falhas:.1f}%")
                
                st.write(f"**Data/hora:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Mostrar histórico de conversas
        if len(st.session_state.produtividade_assistant_responses) > 1:
            st.markdown("---")
            st.subheader("📚 Histórico de Consultas")
            
            # Mostrar do mais recente para o mais antigo (exceto o último que já está mostrado)
            for i, resp in enumerate(reversed(st.session_state.produtividade_assistant_responses[:-1])):
                with st.expander(f"🗨️ {resp['pergunta'][:50]}... - {resp['timestamp']}"):
                    st.write(f"**Pergunta:** {resp['pergunta']}")
                    st.markdown("**Resposta:**")
                    st.markdown(resp['resposta'])
                    st.caption(f"Modelo: {resp['modelo']} | Manutenção: {resp['registros_manutencao']} | Controlador: {resp['registros_controlador']} | {resp['timestamp']}")


# =============================================================================
# BUSCA E VERIFICAÇÃO DA CHAVE GEMINI
# =============================================================================

def get_gemini_key():
    """Busca a chave Gemini - VERSÃO SIMPLIFICADA SEM TESTE"""
    try:
        # Acesso direto à chave
        chave = st.secrets["gemini"]["api_key"]
        st.sidebar.success(f"✅ Chave Gemini carregada: {chave[:7]}...")
        return chave
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao carregar chave Gemini: {e}")
        return None

if pagina == "📊 Dashboard":
    st.markdown('<h1 class="main-header">📊 Dashboard Produtividade - Produto SAI </h1>', unsafe_allow_html=True)

    # Prazo estabelecido pela gestão (48 horas = 2 dias)
    PRAZO_GESTAO = 2

    # Configurar conexão com Google Sheets
    def setup_gsheets():
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        client = gspread.authorize(creds)
        
        # Conecta com a planilha "Produtividade"
        planilha = client.open("Produtividade")
        
        # Acessa as abas específicas
        aba_manutencao = planilha.worksheet("Manutenção")  # Sua aba principal
        aba_controlador = planilha.worksheet("Controlador")  # Sua aba controlador
        
        return aba_manutencao, aba_controlador

    # Carregar dados do Google Sheets 
    @st.cache_data(ttl=300)  # Cache de 5 minutos
    def load_data_from_google_sheets():
        try:
            # Conectar com as abas
            aba_manutencao, aba_controlador = setup_gsheets()
            
            # Carregar dados da ABA MANUTENÇÃO (sua aba principal)
            dados_manutencao = aba_manutencao.get_all_records()
            df_principal = pd.DataFrame(dados_manutencao)
            
            # Carregar dados da ABA CONTROLADOR
            dados_controlador = aba_controlador.get_all_records()
            df_controlador = pd.DataFrame(dados_controlador)
            
            # Limpeza dos dados PRINCIPAIS - trata valores NaN
            # USANDO OS NOMES CORRETOS DA SUA PLANILHA
            if 'Responsável' in df_principal.columns:
                df_principal['Responsável'] = df_principal['Responsável'].fillna('Sem Responsável')
            if 'Módulo' in df_principal.columns:
                df_principal['Módulo'] = df_principal['Módulo'].fillna('Sem Módulo')
            if 'Status' in df_principal.columns:
                df_principal['Status'] = df_principal['Status'].fillna('Sem Status')
            if 'Falha / Teste em Produção' in df_principal.columns:  # NOME CORRETO!
                df_principal['Falha / Teste em Produção'] = df_principal['Falha / Teste em Produção'].fillna('Não')

            # Converte para string (se as colunas existirem)
            colunas_string = ['Responsável', 'Módulo', 'Status', 'Falha / Teste em Produção']  # NOME CORRETO!
            for coluna in colunas_string:
                if coluna in df_principal.columns:
                    df_principal[coluna] = df_principal[coluna].astype(str)

            # Converter datas (se as colunas existirem)
            if 'Data Abertura' in df_principal.columns:
                df_principal['Data Abertura'] = pd.to_datetime(df_principal['Data Abertura'], errors='coerce')
            if 'Data Entrega' in df_principal.columns:
                df_principal['Data Entrega'] = pd.to_datetime(df_principal['Data Entrega'], errors='coerce')

            # Calcular tempo de entrega (apenas para datas válidas)
            if all(col in df_principal.columns for col in ['Data Abertura', 'Data Entrega']):
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

    # Filtro por DATA 
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
    st.sidebar.markdown("### 📊 Estatísticas Gerais - Manutenção")
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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
         "📈 Visão Geral", 
        "👥 Por Responsável", 
        "🔧 Por Módulo", 
        "📅 Timeline", 
        "⏰ Análise de Prazos",
        "🎛️ Controlador",  
        "💡 Insights",
        "🚨 Alertas",
        "🤖 Assistente IA"      
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
        st.subheader("💡 Análise de Rendimento")
    
        col1, col2 = st.columns(2)
    
        with col1:
            # 🆕 ALTERNATIVA 1 - VISÃO COMPLETA DO TOP 5
            st.markdown("#### 🐌 Top 5 - Mais Entregas Fora do Prazo")
        
            if total_concluidas > 0:
                df_concluidas_validas = df_filtrado[
                    (df_filtrado['Status'] == 'Concluída') & 
                    (df_filtrado['Responsável'] != 'Sem Responsável') &
                    (df_filtrado['Responsável'].notna()) &
                    (df_filtrado['Cumpriu Prazo'].isin(['Dentro do Prazo', 'Fora do Prazo']))
                ]
            
                if not df_concluidas_validas.empty:
                    entregas_fora_prazo = df_concluidas_validas[
                        df_concluidas_validas['Cumpriu Prazo'] == 'Fora do Prazo'
                    ].groupby('Responsável').agg({
                        'ID': 'count',
                        'Tempo Entrega (dias)': 'mean'
                    }).round(1)
                
                    if not entregas_fora_prazo.empty:
                        entregas_fora_prazo.columns = ['Qtd Fora Prazo', 'Tempo Médio Atraso (dias)']
                        entregas_fora_prazo = entregas_fora_prazo.sort_values('Qtd Fora Prazo', ascending=False)
                        top5_fora_prazo = entregas_fora_prazo.head(5)
                    
                        # ALTERNATIVA 1 - TABELA ESTILIZADA
                        st.markdown("##### 📋 Visão em Tabela")
                        df_display = top5_fora_prazo.reset_index()
                        df_display.columns = ['Responsável', 'Qtd Atrasos', 'Dias Médio Atraso']
                        df_display['Posição'] = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
                        df_display = df_display[['Posição', 'Responsável', 'Qtd Atrasos', 'Dias Médio Atraso']]
                    
                    # Estilizar a tabela
                        st.dataframe(
                            df_display,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                        st.markdown("---")
                    
                        # ALTERNATIVA 1 - BARRAS HORIZONTAIS
                        st.markdown("##### 📊 Visão em Gráfico")
                    
                        import matplotlib.pyplot as plt
                    
                        fig, ax = plt.subplots(figsize=(10, 4))
                        colors = ['#ff6b6b', '#ff8e8e', '#ffaaaa', '#ffc4c4', '#ffd8d8']
                    
                        bars = ax.barh(
                            top5_fora_prazo.index[::-1],  # Inverter para ranking correto
                            top5_fora_prazo['Qtd Fora Prazo'][::-1],
                            color=colors,
                            height=0.6
                        )
                    
                        # Adicionar valores nas barras
                        for i, bar in enumerate(bars):
                            width = bar.get_width()
                            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                                f'{int(width)} atrasos', 
                                ha='left', va='center', fontweight='bold')
                    
                        ax.set_xlabel('Quantidade de Entregas Fora do Prazo')
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        ax.grid(axis='x', alpha=0.3, linestyle='--')
                    
                        st.pyplot(fig, use_container_width=True)
                    
                        st.markdown("---")
                    
                        # ALTERNATIVA 1 - CARDS COMPACTOS EM COLUNAS
                        st.markdown("##### 👥 Visão em Cards")
                    
                        cols_cards = st.columns(2)
                        for idx, (resp, dados) in enumerate(top5_fora_prazo.iterrows()):
                            with cols_cards[idx % 2]:  # Alterna entre as colunas
                                emoji = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "4️⃣" if idx == 3 else "5️⃣"
                            
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #ffebee, #ffcdd2); 
                                            padding: 0.8rem; 
                                            border-radius: 10px; 
                                            border-left: 5px solid #f44336;
                                            margin: 0.3rem 0;
                                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong style="font-size: 0.9em;">{emoji} {resp}</strong>
                                        <span style="background: #f44336; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.8em;">
                                            {idx + 1}º
                                    </span>
                                </div>
                                <div style="margin-top: 0.5rem;">
                                    <div style="font-size: 0.8em;">🚫 <strong>{int(dados['Qtd Fora Prazo'])}</strong> atrasos</div>
                                    <div style="font-size: 0.8em;">⏱️ <strong>{dados['Tempo Médio Atraso (dias)']}d</strong> médio</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                else:
                    st.success("🎉 Nenhum colaborador com entregas fora do prazo!")
            else:
                st.info("📊 Nenhuma atividade concluída válida para análise")
        
        st.markdown("---")
        
        # 🆕 SEÇÃO DE CASOS ESPECIAIS - JONAS E CRISTIANO
        st.markdown("#### ⚠️ Casos que Precisam de Atenção Imediata")
        
        if total_concluidas > 0:
            # Calcular performance para identificar casos especiais
            performance_responsaveis = []
            
            for responsavel in df_filtrado['Responsável'].unique():
                if responsavel != 'Sem Responsável' and pd.notna(responsavel):
                    df_resp = df_filtrado[
                        (df_filtrado['Responsável'] == responsavel) & 
                        (df_filtrado['Status'] == 'Concluída') &
                        (df_filtrado['Cumpriu Prazo'].isin(['Dentro do Prazo', 'Fora do Prazo']))
                    ]
                    
                    total_resp = len(df_resp)
                    if total_resp > 0:
                        dentro_prazo = len(df_resp[df_resp['Cumpriu Prazo'] == 'Dentro do Prazo'])
                        percentual_dentro = (dentro_prazo / total_resp) * 100
                        
                        performance_responsaveis.append({
                            'Responsável': responsavel,
                            'Total': total_resp,
                            'Dentro Prazo': dentro_prazo,
                            'Fora Prazo': total_resp - dentro_prazo,
                            'Dentro Prazo (%)': percentual_dentro
                        })
            
            if performance_responsaveis:
                df_performance = pd.DataFrame(performance_responsaveis)
                
                # Identificar casos especiais: 100% fora do prazo com pelo menos 2 atividades
                casos_especiais = df_performance[
                    (df_performance['Total'] >= 2) &  # Pelo menos 2 atividades
                    (df_performance['Dentro Prazo (%)'] == 0)  # 100% fora do prazo
                ]
                
                if not casos_especiais.empty:
                    for idx, row in casos_especiais.iterrows():
                        st.markdown(f"""
                        <div style="background-color: #ffcdd2; padding: 1rem; border-radius: 8px; border-left: 6px solid #d32f2f; margin: 0.5rem 0;">
                            <strong style="font-size: 1.1em;">🚨 {row['Responsável']} - ATENÇÃO IMEDIATA</strong><br>
                            <strong>📊 Total de atividades:</strong> {int(row['Total'])}<br>
                            <strong>❌ Situação crítica:</strong> 100% das entregas fora do prazo<br>
                            <strong>🚫 Entregas fora do prazo:</strong> {int(row['Fora Prazo'])}<br>
                            <em>💡 Necessita de mentoria urgente e revisão de processos</em>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ Nenhum colaborador com 100% de entregas fora do prazo")
        
        st.markdown("---")
        
        # 🎯 PERFORMANCE GERAL (APENAS OS PIORES)
        st.markdown("#### 📊 Dificuldades com Prazos")
        
        if total_concluidas > 0:
            if performance_responsaveis:
                df_performance = pd.DataFrame(performance_responsaveis)
                df_performance = df_performance.sort_values('Dentro Prazo (%)')
                
                # Filtrar apenas os que têm performance baixa (< 60%)
                baixa_performance = df_performance[df_performance['Dentro Prazo (%)'] < 60]
                
                if not baixa_performance.empty:
                    for idx, row in baixa_performance.iterrows():
                        # Pular os casos especiais que já foram mostrados acima
                        if row['Dentro Prazo (%)'] == 0:
                            continue
                            
                        st.markdown(f"""
                        <div style="background-color: #fff3e0; padding: 0.8rem; border-radius: 8px; border-left: 4px solid #ff9800; margin: 0.5rem 0;">
                            <strong>📉 {row['Responsável']}</strong><br>
                            <strong>Performance:</strong> {row['Dentro Prazo (%)']:.1f}% dentro do prazo<br>
                            <strong>📊 Estatísticas:</strong> {int(row['Dentro Prazo'])} dentro | {int(row['Fora Prazo'])} fora
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ Todos os colaboradores têm boa performance com prazos")
            else:
                st.info("📊 Não há dados de performance para exibir")
        else:
            st.info("📊 Dados insuficientes para análise de performance")

    with col2:
        st.markdown("<h3 style='text-align: left;'>💡 Recomendações Ações</h3>", unsafe_allow_html=True)

        recomendacoes = []

        if total_concluidas > 0:
            # 🆕 RECOMENDAÇÕES ESPECÍFICAS PARA CASOS CRÍTICOS
            if 'casos_especiais' in locals() and not casos_especiais.empty:
                for _, caso in casos_especiais.iterrows():
                    recomendacoes.append(f"**🚨 Ação Imediata:** {caso['Responsável']} precisa de mentoria urgente - 100% fora do prazo em {int(caso['Total'])} atividades")
            
            # Recomendações baseadas no ranking
            if 'top5_fora_prazo' in locals() and not top5_fora_prazo.empty:
                top1_fora_prazo = top5_fora_prazo.iloc[0]
                recomendacoes.append(f"**🎯 Foco Prioritário:** {top5_fora_prazo.index[0]} lidera com {int(top1_fora_prazo['Qtd Fora Prazo'])} entregas fora do prazo")
            
            if taxa_fora_prazo > 40:
                recomendacoes.append("**🔴 Revisão de Processos:** Analisar causas dos atrasos frequentes na equipe")
            
            if atividades_sem_responsavel > 0:
                recomendacoes.append(f"**👥 Atribuição Pendente:** {atividades_sem_responsavel} atividades sem responsável definido")
            
            # Verificar responsáveis com baixa performance no prazo
            if 'df_performance' in locals():
                resp_baixa_performance = df_performance[
                    (df_performance['Total'] >= 3) & 
                    (df_performance['Dentro Prazo (%)'] < 50) &
                    (df_performance['Dentro Prazo (%)'] > 0)  # Exclui os 0% já tratados
                ]
                if not resp_baixa_performance.empty:
                    for _, row in resp_baixa_performance.iterrows():
                        recomendacoes.append(f"**📚 Capacitação:** {row['Responsável']} tem apenas {row['Dentro Prazo (%)']:.1f}% dentro do prazo")
            
            # Verificar módulos problemáticos
            mod_problematicos = modulo_analysis[
                (modulo_analysis['Total'] >= 5) & 
                (modulo_analysis['Dentro Prazo (%)'] < 40)
            ]
            if not mod_problematicos.empty:
                for mod, dados in mod_problematicos.iterrows():
                    recomendacoes.append(f"**🔧 Otimização de Processo:** Módulo {mod} tem apenas {dados['Dentro Prazo (%)']:.1f}% dentro do prazo")
            
            # Análise de falhas
            if atividades_com_falha_total > 0:
                recomendacoes.append(f"**🧪 Melhoria de Qualidade:** {atividades_com_falha_total} atividades tiveram falha - fortalecer testes")

        if not recomendacoes:
            recomendacoes.append("**✅ Manutenção:** Continue com os processos atuais - performance dentro do esperado")

        # Exibir recomendações
        for rec in recomendacoes:
            st.markdown(f"• {rec}")

        st.markdown("---")
        st.markdown("#### 📈 Métricas Gerais")
        
        col_met1, col_met2, col_met3 = st.columns(3)
        with col_met1:
            st.metric("Taxa Fora do Prazo", f"{taxa_fora_prazo:.1f}%")
        with col_met2:
            st.metric("Atividades Concluídas", total_concluidas)
        with col_met3:
            st.metric("Sem Responsável", atividades_sem_responsavel)

    # Rodapé
    st.markdown("---")
    st.markdown("**Dashboard de Produtividade** - Desenvolvido para análise do Time SAI")
    st.markdown(f"📊 **Fonte de dados:** Google Sheets | ⏰ **Prazo estabelecido pela Gestão para entrega:** {PRAZO_GESTAO} dias (48h)")


    with tab8:
        st.subheader("🚨 Alertas - Demandas em Aberto")
    
        st.markdown("""
        <div style="background-color: #fff3e0; padding: 1rem; border-radius: 10px; border-left: 4px solid #ff9800; margin: 1rem 0;">
            <h4 style="margin: 0; color: #e65100;">📋 Sistema de Classificação de Alertas</h4>
            <p style="margin: 0.5rem 0 0 0; color: #e65100;">
                <strong>🟡 Alerta:</strong> 5-6 dias em aberto | <strong>🔴 Crítico:</strong> 7+ dias em aberto
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Calcular demandas em alerta
        df_alertas = calcular_dias_em_aberto(df_filtrado)
    
        if not df_alertas.empty:
            # Estatísticas rápidas
            total_alertas = len(df_alertas)
            criticos = len(df_alertas[df_alertas['Nível Alerta'] == '🔴 Crítico'])
            alertas = len(df_alertas[df_alertas['Nível Alerta'] == '🟡 Alerta'])
        
            col1, col2, col3 = st.columns(3)
        
            with col1:
                st.metric("🚨 Total em Alerta", total_alertas)
            with col2:
                st.metric("🔴 Críticos", criticos)
            with col3:
                st.metric("🟡 Alertas", alertas)
        
            # Filtro por nível de alerta
            st.markdown("---")
            st.subheader("🔍 Filtrar Alertas")
        
            nivel_alerta = st.selectbox(
                "Selecione o nível de alerta:",
                ["Todos", "🔴 Crítico", "🟡 Alerta"],
                key="filtro_alerta"
            )
        
            # Aplicar filtro
            if nivel_alerta != "Todos":
                df_alertas_filtrado = df_alertas[df_alertas['Nível Alerta'] == nivel_alerta]
            else:
                df_alertas_filtrado = df_alertas
        
            if not df_alertas_filtrado.empty:
                # Mostrar detalhes das demandas
                st.markdown(f"### 📋 Detalhes das Demandas em Alerta ({len(df_alertas_filtrado)})")
            
                for idx, demanda in df_alertas_filtrado.iterrows():
                    # Definir cor baseada no nível
                    if demanda['Nível Alerta'] == '🔴 Crítico':
                        cor_borda = "#f44336"
                        cor_fundo = "#ffebee"
                        emoji = "🔴"
                    else:
                        cor_borda = "#ff9800"
                        cor_fundo = "#fff3e0"
                        emoji = "🟡"
                
                    # Determinar a classe CSS baseada no nível
                    classe_css = "card-critico" if demanda['Nível Alerta'] == '🔴 Crítico' else "card-alerta"

                    st.markdown(f"""
                    <div class="{classe_css}">
                        <div style="display: flex; justify-content: between; align-items: center;">
                            <h4 style="margin: 0;">{demanda['Nível Alerta']} - {demanda['Dias em Aberto']} dias em aberto</h4>
                        </div>
                        <div style="margin-top: 0.5rem;">
                            <strong>📝 Atividade:</strong> {demanda['Atividade']}<br>
                            <strong>👤 Responsável:</strong> {demanda['Responsável']}<br>
                            <strong>🔧 Módulo:</strong> {demanda['Módulo']}<br>
                            <strong>📅 Data Abertura:</strong> {demanda['Data Abertura']}<br>
                            <strong>📊 Status:</strong> {demanda['Status']}<br>
                            <strong>🚀 Sprint:</strong> {demanda.get('Sprint', 'N/A')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Gráfico de distribuição
                st.markdown("---")
                st.subheader("📊 Análise dos Alertas")
            
                col1, col2 = st.columns(2)
            
                with col1:
                    # Gráfico por nível de alerta
                    contagem_alertas = df_alertas_filtrado['Nível Alerta'].value_counts()
                    fig_alertas = px.pie(
                        values=contagem_alertas.values,
                        names=contagem_alertas.index,
                        title='Distribuição por Nível de Alerta',
                        color=contagem_alertas.index,
                        color_discrete_map={'🔴 Crítico': '#f44336', '🟡 Alerta': '#ff9800'}
                    )
                    st.plotly_chart(fig_alertas, use_container_width=True)
            
                with col2:
                    # Gráfico por responsável
                    if len(df_alertas_filtrado) > 0:
                        alertas_por_resp = df_alertas_filtrado.groupby('Responsável').size().sort_values(ascending=False)
                        fig_resp_alertas = px.bar(
                            x=alertas_por_resp.index,
                            y=alertas_por_resp.values,
                            title='Alertas por Responsável',
                            labels={'x': 'Responsável', 'y': 'Quantidade de Alertas'},
                            color=alertas_por_resp.values,
                            color_continuous_scale='Reds'
                        )
                        fig_resp_alertas.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_resp_alertas, use_container_width=True)
        
            else:
                st.success(f"✅ Nenhuma demanda encontrada para o filtro '{nivel_alerta}'!")
    
        else:
            st.success("""
        🎉 **Excelente! Não há demandas em situação de alerta.**
        
        Todas as demandas em aberto estão com menos de 5 dias de pendência.
        """)
        
        # Mostrar algumas estatísticas positivas
            st.markdown("""
            <div style="background-color: #e8f5e8; padding: 1rem; border-radius: 10px; border-left: 4px solid #4caf50;">
                <h4 style="margin: 0; color: #2e7d32;">📈 Status Positivo</h4>
                <p style="margin: 0.5rem 0 0 0; color: #2e7d32;">
                Todas as demandas estão sendo tratadas dentro dos prazos estabelecidos!
                </p>
            </div>
            """, unsafe_allow_html=True)

    # Adicionar CSS ESPECÍFICO para os cards de alerta
    st.markdown("""
    <style>
    /* Aplicar apenas aos cards de demanda - MODO CLARO (padrão) */
    .card-alerta {
        background-color: #fff3e0;
        border: 2px solid #ff9800;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    
    .card-critico {
        background-color: #ffebee;
        border: 2px solid #f44336;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    
    /* MODO ESCURO */
    @media (prefers-color-scheme: dark) {
        .card-alerta {
            background-color: #5d4037 !important;
            border-color: #ff9800 !important;
            color: #ffcc80 !important;
        }
        
        .card-critico {
            background-color: #4a148c !important;
            border-color: #f44336 !important;
            color: #e1bee7 !important;
        }
        
        .card-alerta strong,
        .card-critico strong {
            color: inherit !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    with tab9:  # NOVA ABA DO ASSISTENTE IA
        show_assistente_produtividade_ia(df_filtrado, df_controlador, gemini_key=get_gemini_key())


else:  # Página "📝 Inserir Dados"
    st.markdown('<h1 class="main-header">📝 Inserir Dados - Produto SAI </h1>', unsafe_allow_html=True)
    inserir_dados_planilha()