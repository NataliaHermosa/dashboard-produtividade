import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

def testar_planilha():
    st.title("📊 Teste de Conexão com Planilha Produtividade")
    
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha "Produtividade"
        planilha = client.open("Produtividade")
        st.success(f"✅ Planilha '{planilha.title}' conectada!")
        
        # Acessa as abas específicas
        st.subheader("📑 Abas da planilha:")
        
        # Aba Manutenção
        try:
            aba_manutencao = planilha.worksheet("Manutenção")
            st.success(f"✅ Aba 'Manutenção' - {len(aba_manutencao.get_all_values())} linhas")
        except Exception as e:
            st.error(f"❌ Erro na aba 'Manutenção': {e}")
        
        # Aba Controlador
        try:
            aba_controlador = planilha.worksheet("Controlador")
            st.success(f"✅ Aba 'Controlador' - {len(aba_controlador.get_all_values())} linhas")
        except Exception as e:
            st.error(f"❌ Erro na aba 'Controlador': {e}")
        
        # Lista todas as abas disponíveis
        st.subheader("📋 Todas as abas disponíveis:")
        todas_abas = planilha.worksheets()
        for aba in todas_abas:
            st.write(f"- {aba.title} ({aba.row_count} linhas × {aba.col_count} colunas)")
            
    except Exception as e:
        st.error(f"❌ Erro geral: {e}")

testar_planilha()