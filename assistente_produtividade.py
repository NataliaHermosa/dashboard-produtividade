import pandas as pd
import google.generativeai as genai
import os
from datetime import datetime
import numpy as np

def consultar_assistente_produtividade(pergunta, df_manutencao, df_controlador, tipo_modelo, gemini_key):
    """
    Consulta o assistente de IA para análise de dados de produtividade - VERSÃO CORRIGIDA
    """
    try:
        # Configurar a API do Gemini
        genai.configure(api_key=gemini_key)
        
        # ✅ USANDO OS MODELOS QUE JÁ FUNCIONAM NA SUA OUTRA APLICAÇÃO
        if "Flash" in tipo_modelo:
            model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Preparar contexto detalhado com análise avançada
        contexto = preparar_contexto_detalhado(df_manutencao, df_controlador)
        
        # Prompt especializado e contextualizado
        prompt = f"""
        # CONTEXTO DO SISTEMA DE PRODUTIVIDADE - TIME SAI

        Você é um analista sênior de produtividade especializado em equipes de TI. 
        Analise os dados fornecidos e forneça insights acionáveis baseados em métricas reais.

        ## DADOS E ANÁLISES DISPONÍVEIS:
        {contexto}

        ## PERGUNTA DO USUÁRIO: 
        {pergunta}

        ## DIRETRIZES PARA RESPOSTA:
        1. **Seja específico** - Use números, porcentagens e exemplos concretos dos dados
        2. **Contextualize** - Relacione com o contexto do time SAI e módulos específicos
        3. **Aponte causas** - Identifique padrões e causas raiz dos problemas
        4. **Sugira soluções** - Recomendações práticas e acionáveis
        5. **Destaque oportunidades** - Pontos fortes a manter e fraquezas a corrigir
        6. **Use linguagem técnica** adequada ao contexto de desenvolvimento

        Formate a resposta de forma clara e estruturada, usando markdown quando apropriado.
        """
        
        # Gerar resposta
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ Erro ao consultar o assistente: {str(e)}\n\n📊 **Análise Local:**\n- Manutenção: {len(df_manutencao)} registros\n- Controlador: {len(df_controlador)} registros"
    
def preparar_contexto_detalhado(df_manutencao, df_controlador):
    """
    Prepara um contexto rico e detalhado com análises avançadas dos dados
    """
    contexto = "## 📊 ANÁLISE DETALHADA DOS DADOS\n\n"
    
    # ANÁLISE DA ABA MANUTENÇÃO
    contexto += "### 🔧 ABA MANUTENÇÃO - ANÁLISE DETALHADA\n"
    
    if not df_manutencao.empty:
        # Limpeza e preparação dos dados
        df = df_manutencao.copy()
        df['Data Abertura'] = pd.to_datetime(df['Data Abertura'], errors='coerce')
        df['Data Entrega'] = pd.to_datetime(df['Data Entrega'], errors='coerce')
        
        # ESTATÍSTICAS GERAIS
        total_atividades = len(df)
        atividades_concluidas = len(df[df['Status'] == 'Concluída'])
        taxa_conclusao = (atividades_concluidas / total_atividades) * 100 if total_atividades > 0 else 0
        
        contexto += f"#### 📈 Estatísticas Gerais\n"
        contexto += f"- **Total de atividades:** {total_atividades}\n"
        contexto += f"- **Atividades concluídas:** {atividades_concluidas}\n"
        contexto += f"- **Taxa de conclusão:** {taxa_conclusao:.1f}%\n"
        contexto += f"- **Atividades pendentes/andamento:** {total_atividades - atividades_concluidas}\n"
        
        # ANÁLISE DE STATUS DETALHADA
        contexto += f"\n#### 📋 Distribuição por Status\n"
        status_counts = df['Status'].value_counts()
        for status, count in status_counts.items():
            percentual = (count / total_atividades) * 100
            contexto += f"- **{status}:** {count} atividades ({percentual:.1f}%)\n"
        
        # ANÁLISE AVANÇADA POR RESPONSÁVEL
        contexto += f"\n#### 👥 Análise por Responsável\n"
        if 'Responsável' in df.columns:
            responsaveis_analysis = df.groupby('Responsável').agg({
                'ID': 'count',
                'Status': lambda x: (x == 'Concluída').sum(),
                'Falha/ Teste em Produção': lambda x: (x == 'Sim').sum()
            }).round(2)
            
            responsaveis_analysis.columns = ['Total', 'Concluídas', 'Falhas']
            responsaveis_analysis['Taxa Conclusão'] = (responsaveis_analysis['Concluídas'] / responsaveis_analysis['Total']) * 100
            responsaveis_analysis['Taxa Falhas'] = (responsaveis_analysis['Falhas'] / responsaveis_analysis['Total']) * 100
            
            for resp, dados in responsaveis_analysis.sort_values('Total', ascending=False).iterrows():
                contexto += f"- **{resp}:** {int(dados['Total'])} atividades, {dados['Taxa Conclusão']:.1f}% concluídas, {dados['Taxa Falhas']:.1f}% com falha\n"
        
        # ANÁLISE DETALHADA POR MÓDULO
        contexto += f"\n#### 🔧 Análise por Módulo\n"
        if 'Módulo' in df.columns:
            modulos_analysis = df.groupby('Módulo').agg({
                'ID': 'count',
                'Status': lambda x: (x == 'Concluída').sum(),
                'Falha/ Teste em Produção': lambda x: (x == 'Sim').sum()
            }).round(2)
            
            modulos_analysis.columns = ['Total', 'Concluídas', 'Falhas']
            modulos_analysis['Taxa Conclusão'] = (modulos_analysis['Concluídas'] / modulos_analysis['Total']) * 100
            modulos_analysis['Taxa Falhas'] = (modulos_analysis['Falhas'] / modulos_analysis['Total']) * 100
            
            for modulo, dados in modulos_analysis.sort_values('Total', ascending=False).iterrows():
                contexto += f"- **{modulo}:** {int(dados['Total'])} atividades, {dados['Taxa Conclusão']:.1f}% concluídas, {dados['Taxa Falhas']:.1f}% com falha\n"
        
        # ANÁLISE DE PRAZOS AVANÇADA
        contexto += f"\n#### ⏰ Análise de Prazos e Tempos\n"
        if all(col in df.columns for col in ['Data Abertura', 'Data Entrega']):
            # Calcular tempo de entrega apenas para atividades concluídas
            df_concluidas = df[df['Status'] == 'Concluída']
            mask_tempo = df_concluidas['Data Abertura'].notna() & df_concluidas['Data Entrega'].notna()
            
            if mask_tempo.any():
                df_concluidas_validas = df_concluidas[mask_tempo]
                df_concluidas_validas['Tempo Entrega (dias)'] = (df_concluidas_validas['Data Entrega'] - df_concluidas_validas['Data Abertura']).dt.days
                
                tempo_medio = df_concluidas_validas['Tempo Entrega (dias)'].mean()
                tempo_mediano = df_concluidas_validas['Tempo Entrega (dias)'].median()
                tempo_min = df_concluidas_validas['Tempo Entrega (dias)'].min()
                tempo_max = df_concluidas_validas['Tempo Entrega (dias)'].max()
                
                # Análise de cumprimento de prazo (48h = 2 dias)
                PRAZO_GESTAO = 2
                dentro_prazo = len(df_concluidas_validas[df_concluidas_validas['Tempo Entrega (dias)'] <= PRAZO_GESTAO])
                taxa_dentro_prazo = (dentro_prazo / len(df_concluidas_validas)) * 100 if len(df_concluidas_validas) > 0 else 0
                
                contexto += f"- **Tempo médio de entrega:** {tempo_medio:.1f} dias\n"
                contexto += f"- **Tempo mediano:** {tempo_mediano:.1f} dias\n"
                contexto += f"- **Variação:** {tempo_min} a {tempo_max} dias\n"
                contexto += f"- **Dentro do prazo (48h):** {taxa_dentro_prazo:.1f}% ({dentro_prazo}/{len(df_concluidas_validas)})\n"
                
                # Top atividades mais rápidas e mais lentas
                mais_rapidas = df_concluidas_validas.nsmallest(3, 'Tempo Entrega (dias)')
                mais_lentas = df_concluidas_validas.nlargest(3, 'Tempo Entrega (dias)')
                
                contexto += f"- **Atividades mais rápidas:** "
                for idx, atividade in mais_rapidas.iterrows():
                    contexto += f"{atividade['Módulo']} ({atividade['Tempo Entrega (dias)']}d), "
                contexto += "\n"
                
                contexto += f"- **Atividades mais lentas:** "
                for idx, atividade in mais_lentas.iterrows():
                    contexto += f"{atividade['Módulo']} ({atividade['Tempo Entrega (dias)']}d), "
                contexto += "\n"
        
        # ANÁLISE DE FALHAS DETALHADA
        contexto += f"\n#### 🔴 Análise de Qualidade (Falhas/Testes)\n"
        if 'Falha/ Teste em Produção' in df.columns:
            total_falhas = len(df[df['Falha/ Teste em Produção'] == 'Sim'])
            taxa_falhas_geral = (total_falhas / total_atividades) * 100
            
            contexto += f"- **Total de atividades com falha:** {total_falhas}\n"
            contexto += f"- **Taxa geral de falhas:** {taxa_falhas_geral:.1f}%\n"
            
            # Falhas por módulo
            falhas_por_modulo = df[df['Falha/ Teste em Produção'] == 'Sim'].groupby('Módulo').size()
            if not falhas_por_modulo.empty:
                contexto += f"- **Falhas por módulo:** "
                for modulo, count in falhas_por_modulo.items():
                    contexto += f"{modulo} ({count}), "
                contexto += "\n"
            
            # Falhas por responsável
            falhas_por_responsavel = df[df['Falha/ Teste em Produção'] == 'Sim'].groupby('Responsável').size()
            if not falhas_por_responsavel.empty:
                contexto += f"- **Falhas por responsável:** "
                for resp, count in falhas_por_responsavel.items():
                    contexto += f"{resp} ({count}), "
                contexto += "\n"
        
        # ANÁLISE TEMPORAL AVANÇADA
        contexto += f"\n#### 📅 Análise Temporal e Tendências\n"
        if 'Data Abertura' in df.columns:
            df['Mês'] = df['Data Abertura'].dt.to_period('M')
            evolucao_mensal = df.groupby('Mês').size()
            
            if len(evolucao_mensal) > 1:
                ultimo_mes = evolucao_mensal.iloc[-1]
                penultimo_mes = evolucao_mensal.iloc[-2]
                variacao = ((ultimo_mes - penultimo_mes) / penultimo_mes) * 100
                
                contexto += f"- **Atividades no último mês:** {ultimo_mes}\n"
                contexto += f"- **Variação vs mês anterior:** {variacao:+.1f}%\n"
                contexto += f"- **Tendência:** {'📈 Crescendo' if variacao > 0 else '📉 Diminuindo' if variacao < 0 else '➡️ Estável'}\n"
        
        # ANÁLISE POR SPRINT
        contexto += f"\n#### 🚀 Análise por Sprint\n"
        if 'Sprint' in df.columns:
            sprint_analysis = df.groupby('Sprint').agg({
                'ID': 'count',
                'Status': lambda x: (x == 'Concluída').sum(),
                'Falha/ Teste em Produção': lambda x: (x == 'Sim').sum()
            }).round(2)
            
            sprint_analysis.columns = ['Total', 'Concluídas', 'Falhas']
            sprint_analysis['Taxa Conclusão'] = (sprint_analysis['Concluídas'] / sprint_analysis['Total']) * 100
            sprint_analysis['Taxa Falhas'] = (sprint_analysis['Falhas'] / sprint_analysis['Total']) * 100
            
            for sprint, dados in sprint_analysis.sort_index().iterrows():
                contexto += f"- **{sprint}:** {int(dados['Total'])} atividades, {dados['Taxa Conclusão']:.1f}% concluídas, {dados['Taxa Falhas']:.1f}% com falha\n"
    
    # ANÁLISE DA ABA CONTROLADOR
    contexto += "\n### 🎯 ABA CONTROLADOR - ANÁLISE DE COMPLEXIDADE\n"
    
    if not df_controlador.empty:
        df_controlador_clean = df_controlador.copy()
        df_controlador_clean['Pontos'] = pd.to_numeric(df_controlador_clean['Pontos'], errors='coerce').fillna(0)
        
        total_demandas = len(df_controlador_clean)
        total_pontos = df_controlador_clean['Pontos'].sum()
        media_pontos = df_controlador_clean['Pontos'].mean()
        
        contexto += f"- **Total de demandas:** {total_demandas}\n"
        contexto += f"- **Total de pontos:** {total_pontos:.0f}\n"
        contexto += f"- **Média de pontos/demanda:** {media_pontos:.1f}\n"
        
        # Análise por responsável no controlador
        if 'Responsável' in df_controlador_clean.columns:
            controlador_por_resp = df_controlador_clean.groupby('Responsável').agg({
                'ID': 'count',
                'Pontos': 'sum'
            })
            controlador_por_resp.columns = ['Demandas', 'Pontos Totais']
            controlador_por_resp['Média Pontos'] = controlador_por_resp['Pontos Totais'] / controlador_por_resp['Demandas']
            
            contexto += f"- **Distribuição por responsável:**\n"
            for resp, dados in controlador_por_resp.sort_values('Pontos Totais', ascending=False).iterrows():
                contexto += f"  - {resp}: {int(dados['Demandas'])} demandas, {dados['Pontos Totais']:.0f} pontos, {dados['Média Pontos']:.1f} pts/demanda\n"
    
    # RESUMO EXECUTIVO
    contexto += "\n### 🎖️ RESUMO EXECUTIVO\n"
    
    if not df_manutencao.empty:
        # Principais métricas
        contexto += f"- **Performance Geral:** {taxa_conclusao:.1f}% das atividades concluídas\n"
        
        if 'Tempo Entrega (dias)' in locals():
            contexto += f"- **Velocidade:** {tempo_medio:.1f} dias em média para conclusão\n"
            contexto += f"- **Cumprimento de Prazo:** {taxa_dentro_prazo:.1f}% dentro de 48h\n"
        
        if 'taxa_falhas_geral' in locals():
            contexto += f"- **Qualidade:** {taxa_falhas_geral:.1f}% de atividades com falha\n"
        
        # Identificar pontos fortes e fracos
        if 'modulos_analysis' in locals():
            modulo_mais_atividades = modulos_analysis.nlargest(1, 'Total')
            if not modulo_mais_atividades.empty:
                mod, dados = list(modulo_mais_atividades.iterrows())[0]
                contexto += f"- **Módulo mais ativo:** {mod} ({int(dados['Total'])} atividades)\n"
        
        if 'responsaveis_analysis' in locals():
            resp_mais_produtivo = responsaveis_analysis.nlargest(1, 'Total')
            if not resp_mais_produtivo.empty:
                resp, dados = list(resp_mais_produtivo.iterrows())[0]
                contexto += f"- **Colaborador mais produtivo:** {resp} ({int(dados['Total'])} atividades)\n"
    
    contexto += f"\n📅 **Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    contexto += f"\n📊 **Base de dados:** {len(df_manutencao)} atividades Manutenção + {len(df_controlador)} demandas Controlador"
    
    return contexto

def gerar_insights_automaticos(df_manutencao, df_controlador):
    """
    Gera insights automáticos baseados nos dados
    """
    insights = "## 🎯 INSIGHTS AUTOMÁTICOS\n\n"
    
    if not df_manutencao.empty:
        df = df_manutencao.copy()
        
        # Insight 1: Módulo com mais atividades
        if 'Módulo' in df.columns:
            modulo_mais_atividades = df['Módulo'].value_counts().index[0]
            total_modulo = df['Módulo'].value_counts().iloc[0]
            insights += f"🔧 **Módulo mais demandado:** {modulo_mais_atividades} ({total_modulo} atividades)\n\n"
        
        # Insight 2: Responsável mais produtivo
        if 'Responsável' in df.columns:
            resp_mais_atividades = df['Responsável'].value_counts().index[0]
            total_resp = df['Responsável'].value_counts().iloc[0]
            insights += f"👥 **Colaborador mais ativo:** {resp_mais_atividades} ({total_resp} atividades)\n\n"
        
        # Insight 3: Taxa de falhas
        if 'Falha/ Teste em Produção' in df.columns:
            total_falhas = len(df[df['Falha/ Teste em Produção'] == 'Sim'])
            taxa_falhas = (total_falhas / len(df)) * 100
            insights += f"🔴 **Qualidade do trabalho:** {taxa_falhas:.1f}% de atividades com falha\n\n"
        
        # Insight 4: Status da sprint atual
        if 'Sprint' in df.columns and 'Status' in df.columns:
            sprint_atual = df['Sprint'].value_counts().index[0] if not df['Sprint'].empty else 'N/A'
            concluidas_sprint = len(df[(df['Sprint'] == sprint_atual) & (df['Status'] == 'Concluída')])
            total_sprint = len(df[df['Sprint'] == sprint_atual])
            taxa_sprint = (concluidas_sprint / total_sprint) * 100 if total_sprint > 0 else 0
            
            insights += f"🚀 **Progresso da {sprint_atual}:** {taxa_sprint:.1f}% concluída ({concluidas_sprint}/{total_sprint})\n\n"
    
    return insights