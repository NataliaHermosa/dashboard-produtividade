import pandas as pd
import google.generativeai as genai
import os
from datetime import datetime
import numpy as np

def consultar_assistente_produtividade(pergunta, df_manutencao, tipo_modelo, gemini_key):
    """
    Consulta o assistente de IA para análise de dados de produtividade - VERSÃO MELHORADA
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
        contexto = preparar_contexto_detalhado(df_manutencao)
        
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
        7. **Priorize insights** que possam levar a ações imediatas
        8. **Considere o prazo** de 48 horas estabelecido pela gestão

        Formate a resposta de forma clara e estruturada, usando markdown quando apropriado.
        Inclua métricas específicas, comparações e recomendações práticas.
        """
        
        # Gerar resposta
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ Erro ao consultar o assistente: {str(e)}\n\n📊 **Análise Local:**\n- Manutenção: {len(df_manutencao)} registros"
    
def preparar_contexto_detalhado(df_manutencao):
    """
    Prepara um contexto rico e detalhado com análises avançadas dos dados - VERSÃO MELHORADA
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
        
        # 🆕 ANÁLISE AVANÇADA DE PERFORMANCE POR RESPONSÁVEL
        contexto += f"\n#### 🏆 Ranking de Performance por Responsável\n"
        if 'Responsável' in df.columns:
            performance_data = []
            
            for responsavel in df['Responsável'].unique():
                df_resp = df[df['Responsável'] == responsavel]
                total = len(df_resp)
                concluidas = len(df_resp[df_resp['Status'] == 'Concluída'])
                falhas = len(df_resp[df_resp['Falha/ Teste em Produção'] == 'Sim'])
                
                # Score composto
                taxa_conclusao_resp = (concluidas / total) * 100 if total > 0 else 0
                taxa_qualidade = 100 - ((falhas / total) * 100) if total > 0 else 100
                
                # Score final (50% conclusão + 50% qualidade)
                score = (taxa_conclusao_resp * 0.5) + (taxa_qualidade * 0.5)
                
                performance_data.append({
                    'Responsável': responsavel,
                    'Score': score,
                    'Conclusão': taxa_conclusao_resp,
                    'Qualidade': taxa_qualidade,
                    'Total': total
                })
            
            # Ordenar por score
            performance_df = pd.DataFrame(performance_data).sort_values('Score', ascending=False)
            
            for idx, row in performance_df.iterrows():
                contexto += f"- **{row['Responsável']}:** Score {row['Score']:.1f} (📈 {row['Conclusão']:.1f}% conclusão, 🎯 {row['Qualidade']:.1f}% qualidade) - {row['Total']} atividades\n"
        
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
        
        # 🆕 ANÁLISE DE RISCOS E ALERTAS
        contexto += f"\n#### ⚠️ Alertas e Riscos Identificados\n"
        
        # Risco 1: Módulos com alta taxa de falhas
        if 'Módulo' in df.columns and 'Falha/ Teste em Produção' in df.columns:
            modulos_risco = df[df['Falha/ Teste em Produção'] == 'Sim'].groupby('Módulo').size()
            if len(modulos_risco) > 0:
                modulo_mais_falhas = modulos_risco.idxmax()
                num_falhas = modulos_risco.max()
                contexto += f"- **Risco de Qualidade:** Módulo '{modulo_mais_falhas}' tem {num_falhas} falhas (maior incidência)\n"
        
        # Risco 2: Responsáveis com baixa produtividade
        if 'Responsável' in df.columns:
            resp_counts = df['Responsável'].value_counts()
            if len(resp_counts) > 2:
                resp_baixa_prod = resp_counts.nsmallest(2)
                contexto += f"- **Risco de Capacidade:** {', '.join(resp_baixa_prod.index)} com menor volume ({resp_baixa_prod.min()} atividades)\n"
        
        # Risco 3: Atividades pendentes críticas
        pendentes_criticas = len(df[df['Status'].isin(['Pendente', 'Em Andamento'])])
        if pendentes_criticas > 10:  # Threshold ajustável
            contexto += f"- **Risco de Acúmulo:** {pendentes_criticas} atividades pendentes/em andamento\n"
        
        # 🆕 ANÁLISE DE MELHORIA CONTÍNUA
        contexto += f"\n#### 📈 Oportunidades de Melhoria\n"
        
        # Tendência temporal de qualidade
        if 'Data Abertura' in df.columns and 'Falha/ Teste em Produção' in df.columns:
            df['Mês'] = df['Data Abertura'].dt.to_period('M')
            evolucao_falhas = df[df['Falha/ Teste em Produção'] == 'Sim'].groupby('Mês').size()
            
            if len(evolucao_falhas) > 1:
                variacao_falhas = ((evolucao_falhas.iloc[-1] - evolucao_falhas.iloc[-2]) / evolucao_falhas.iloc[-2]) * 100
                if variacao_falhas > 0:
                    contexto += f"- **Atenção à Qualidade:** Taxa de falhas aumentou {variacao_falhas:+.1f}% no último mês\n"
                else:
                    contexto += f"- **Melhoria em Qualidade:** Taxa de falhas reduziu {variacao_falhas:+.1f}% no último mês\n"
        
        # Identificar melhores práticas
        if 'Responsável' in df.columns and 'Falha/ Teste em Produção' in df.columns:
            resp_sem_falhas = df[df['Falha/ Teste em Produção'] == 'Não']['Responsável'].value_counts().head(2)
            if len(resp_sem_falhas) > 0:
                contexto += f"- **Benchmark Interno:** {', '.join(resp_sem_falhas.index)} são referências em qualidade (0 falhas)\n"
        
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
    
    # 🆕 SCORE GERAL DO TIME
    contexto += "\n### 🎖️ SCORE GERAL DO TIME\n"
    
    if not df_manutencao.empty:
        # Calcular score geral baseado em múltiplas métricas
        metricas = {
            'Taxa de Conclusão': taxa_conclusao,
            'Cumprimento de Prazo': taxa_dentro_prazo if 'taxa_dentro_prazo' in locals() else 0,
            'Qualidade': 100 - taxa_falhas_geral if 'taxa_falhas_geral' in locals() else 100,
            'Volume': min((total_atividades / 50) * 100, 100)  # Normalizado para benchmark
        }
        
        score_geral = sum(metricas.values()) / len(metricas)
        contexto += f"- **Score Geral:** {score_geral:.1f}/100\n"
        
        # Classificação do performance
        if score_geral >= 80:
            status = "🏆 Excelente"
        elif score_geral >= 60:
            status = "✅ Bom" 
        elif score_geral >= 40:
            status = "⚠️ Necessita Melhoria"
        else:
            status = "🔴 Crítico"
        
        contexto += f"- **Status:** {status}\n"
        
        # Detalhamento das métricas
        contexto += f"- **Detalhamento:** Conclusão {metricas['Taxa de Conclusão']:.1f}%, Prazo {metricas['Cumprimento de Prazo']:.1f}%, Qualidade {metricas['Qualidade']:.1f}%, Volume {metricas['Volume']:.1f}%\n"
    
    contexto += f"\n📅 **Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    contexto += f"\n📊 **Base de dados:** {len(df_manutencao)} atividades Manutenção"
    
    return contexto

def gerar_insights_automaticos(df_manutencao):
    """
    Gera insights automáticos baseados nos dados - VERSÃO MELHORADA
    """
    insights = "## 🎯 INSIGHTS AUTOMÁTICOS\n\n"
    
    if not df_manutencao.empty:
        df = df_manutencao.copy()
        
        # Insight 1: Módulo com mais atividades
        if 'Módulo' in df.columns:
            modulo_mais_atividades = df['Módulo'].value_counts().index[0]
            total_modulo = df['Módulo'].value_counts().iloc[0]
            percentual_modulo = (total_modulo / len(df)) * 100
            insights += f"🔧 **Módulo mais demandado:** {modulo_mais_atividades} ({total_modulo} atividades, {percentual_modulo:.1f}% do total)\n\n"
        
        # Insight 2: Responsável mais produtivo
        if 'Responsável' in df.columns:
            resp_mais_atividades = df['Responsável'].value_counts().index[0]
            total_resp = df['Responsável'].value_counts().iloc[0]
            percentual_resp = (total_resp / len(df)) * 100
            
            # Calcular qualidade do responsável mais produtivo
            df_resp = df[df['Responsável'] == resp_mais_atividades]
            falhas_resp = len(df_resp[df_resp['Falha/ Teste em Produção'] == 'Sim'])
            taxa_falhas_resp = (falhas_resp / total_resp) * 100 if total_resp > 0 else 0
            
            insights += f"👥 **Colaborador mais ativo:** {resp_mais_atividades} ({total_resp} atividades, {percentual_resp:.1f}% do total, {taxa_falhas_resp:.1f}% falhas)\n\n"
        
        # Insight 3: Taxa de falhas geral
        if 'Falha/ Teste em Produção' in df.columns:
            total_falhas = len(df[df['Falha/ Teste em Produção'] == 'Sim'])
            taxa_falhas = (total_falhas / len(df)) * 100
            
            if taxa_falhas > 20:
                status_falhas = "🔴 Crítico"
            elif taxa_falhas > 10:
                status_falhas = "🟡 Atenção"
            else:
                status_falhas = "🟢 Boa"
                
            insights += f"🔴 **Qualidade do trabalho:** {taxa_falhas:.1f}% de atividades com falha - {status_falhas}\n\n"
        
        # Insight 4: Status da sprint atual
        if 'Sprint' in df.columns and 'Status' in df.columns:
            if not df['Sprint'].empty:
                sprint_atual = df['Sprint'].value_counts().index[0]
                concluidas_sprint = len(df[(df['Sprint'] == sprint_atual) & (df['Status'] == 'Concluída')])
                total_sprint = len(df[df['Sprint'] == sprint_atual])
                taxa_sprint = (concluidas_sprint / total_sprint) * 100 if total_sprint > 0 else 0
                
                if taxa_sprint >= 80:
                    status_sprint = "🏆 Excelente"
                elif taxa_sprint >= 60:
                    status_sprint = "✅ Bom"
                elif taxa_sprint >= 40:
                    status_sprint = "⚠️ Em andamento"
                else:
                    status_sprint = "🔴 Atrasado"
                
                insights += f"🚀 **Progresso da {sprint_atual}:** {taxa_sprint:.1f}% concluída ({concluidas_sprint}/{total_sprint}) - {status_sprint}\n\n"
        
        # 🆕 Insight 5: Performance geral do time
        atividades_concluidas = len(df[df['Status'] == 'Concluída'])
        taxa_conclusao_geral = (atividades_concluidas / len(df)) * 100
        
        if taxa_conclusao_geral >= 80:
            status_geral = "🏆 Alta Produtividade"
        elif taxa_conclusao_geral >= 60:
            status_geral = "✅ Boa Produtividade"
        elif taxa_conclusao_geral >= 40:
            status_geral = "⚠️ Produtividade Moderada"
        else:
            status_geral = "🔴 Baixa Produtividade"
            
        insights += f"📊 **Performance Geral do Time:** {taxa_conclusao_geral:.1f}% de atividades concluídas - {status_geral}\n\n"
        
        # 🆕 Insight 6: Distribuição de trabalho
        if 'Responsável' in df.columns:
            distribuicao = df['Responsável'].value_counts()
            if len(distribuicao) > 1:
                maior_carga = distribuicao.iloc[0]
                menor_carga = distribuicao.iloc[-1]
                diferenca = maior_carga - menor_carga
                
                if diferenca > 10:
                    insights += f"⚖️ **Distribuição de trabalho:** Diferença de {diferenca} atividades entre maior e menor carga - Pode indicar necessidade de rebalanceamento\n\n"
                else:
                    insights += f"⚖️ **Distribuição de trabalho:** Balanceada - Diferença de apenas {diferenca} atividades entre colaboradores\n\n"
    
    else:
        insights += "📭 **Nenhum dado disponível** para gerar insights automáticos.\n\n"
    
    insights += "💡 **Dica:** Use o assistente IA para análises mais profundas e recomendações específicas!"
    
    return insights

# 🆕 FUNÇÃO AUXILIAR PARA ANÁLISES ESPECÍFICAS
def analisar_gargalos(df_manutencao):
    """
    Identifica gargalos específicos no processo
    """
    if df_manutencao.empty:
        return "Nenhum dado disponível para análise de gargalos"
    
    df = df_manutencao.copy()
    analise = "## 🔍 ANÁLISE DE GARGALOS\n\n"
    
    # Gargalo 1: Módulos com maior tempo de entrega
    if all(col in df.columns for col in ['Módulo', 'Data Abertura', 'Data Entrega', 'Status']):
        df_concluidas = df[df['Status'] == 'Concluída']
        mask = df_concluidas['Data Abertura'].notna() & df_concluidas['Data Entrega'].notna()
        
        if mask.any():
            df_validas = df_concluidas[mask]
            df_validas['Tempo Entrega'] = (df_validas['Data Entrega'] - df_validas['Data Abertura']).dt.days
            
            tempo_por_modulo = df_validas.groupby('Módulo')['Tempo Entrega'].mean().sort_values(ascending=False)
            
            if len(tempo_por_modulo) > 0:
                modulo_mais_lento = tempo_por_modulo.index[0]
                tempo_medio = tempo_por_modulo.iloc[0]
                analise += f"⏰ **Gargalo de Velocidade:** Módulo '{modulo_mais_lento}' tem maior tempo médio ({tempo_medio:.1f} dias)\n\n"
    
    # Gargalo 2: Responsáveis com maior taxa de falhas
    if 'Responsável' in df.columns and 'Falha/ Teste em Produção' in df.columns:
        falhas_por_resp = df[df['Falha/ Teste em Produção'] == 'Sim'].groupby('Responsável').size()
        total_por_resp = df.groupby('Responsável').size()
        
        if len(falhas_por_resp) > 0:
            taxa_falhas_resp = (falhas_por_resp / total_por_resp) * 100
            resp_mais_falhas = taxa_falhas_resp.idxmax()
            taxa_mais_falhas = taxa_falhas_resp.max()
            
            analise += f"🔴 **Gargalo de Qualidade:** {resp_mais_falhas} tem maior taxa de falhas ({taxa_mais_falhas:.1f}%)\n\n"
    
    # Gargalo 3: Módulos com mais atividades pendentes
    if 'Módulo' in df.columns and 'Status' in df.columns:
        pendentes_por_modulo = df[df['Status'].isin(['Pendente', 'Em Andamento'])].groupby('Módulo').size()
        
        if len(pendentes_por_modulo) > 0:
            modulo_mais_pendente = pendentes_por_modulo.idxmax()
            num_pendentes = pendentes_por_modulo.max()
            analise += f"📋 **Gargalo de Acúmulo:** Módulo '{modulo_mais_pendente}' tem {num_pendentes} atividades pendentes/em andamento\n\n"
    
    return analise