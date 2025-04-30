import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Ferramenta Crédito Privado", layout="wide")

# === Funções auxiliares ===
def formatar_valor(valor):
    try:
        return f"{valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return valor

def formatar_taxa(valor):
    try:
        return f"{valor * 100:.2f}".replace(".", ",")
    except:
        return valor

def formatar_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return valor

# === Função da aba Trade Ideia ===
def trade_ideia_tab(df_credito):
    st.subheader("💡 Trade Ideia – Simulação de Troca de Ativo")

    # Entrada do novo ativo
    col1, col2, col3 = st.columns(3)
    with col1:
        indexador_novo = st.selectbox("Indexador do novo ativo", ["IPCA+", "CDI+", "PRE"])
    with col2:
        taxa_nova = st.number_input("Taxa bruta do novo ativo (%)", min_value=0.0, step=0.01)
    with col3:
        duration_novo = st.number_input("Duration estimada (anos)", min_value=0.0, step=0.1)

    if st.button("Simular troca"):
        df = df_credito.copy()
        df['Desagio'] = df['Valor PU Curva'] - df['Valor PU Mercado']
        df = df[df['Desagio'] > 0]

        df['Diferenca Rentabilidade'] = taxa_nova - df['Taxa Compra'] * 100
        df['Diferenca Rentabilidade R$'] = df['Diferenca Rentabilidade'] / 100 * 1000

        df['Tempo Recuperacao (anos)'] = df['Desagio'] / df['Diferenca Rentabilidade R$']
        df['Tempo Recuperacao (anos)'] = df['Tempo Recuperacao (anos)'].apply(lambda x: round(x, 2) if x > 0 else np.nan)

        df_resultado = df[['Ativo', 'Indexador', 'Taxa Compra', 'Valor PU Curva', 'Valor PU Mercado',
                           'Desagio', 'Diferenca Rentabilidade', 'Tempo Recuperacao (anos)']]
        df_resultado.columns = ['Ativo', 'Indexador', 'Taxa Atual', 'PU Curva', 'PU Mercado',
                                'Deságio (R$)', 'Δ Rentabilidade (%)', 'Tempo p/ Recuperar (anos)']

        st.write("Ativos com deságio e estimativa de recuperação ao trocar pelo novo ativo:")
        st.dataframe(df_resultado, use_container_width=True)

# === Interface do app ===
st.title("📊 Ferramenta de Crédito Privado")

# Upload de planilha
uploaded_file = st.file_uploader("📂 Faça o upload da planilha Excel (.xlsx)", type="xlsx")

# Rodar após upload
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name='Export')
    ativos_credito = ['Debênture', 'CRA', 'CRI']
    df = df[df['Tipo'].isin(ativos_credito)].copy()

    # Conversões
    df['Percentual Rentabilidade'] = pd.to_numeric(df['Percentual Rentabilidade'], errors='coerce')
    df['Percentual Carrego CDI'] = pd.to_numeric(df['Percentual Carrego CDI'], errors='coerce')
    df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')
    df['Percentual Ágio ou Deságio'] = pd.to_numeric(df['Percentual Ágio ou Deságio'], errors='coerce')
    df['Valor Total Mercado'] = pd.to_numeric(df['Valor Total Mercado'], errors='coerce')
    df['Rentabilidade'] = pd.to_numeric(df['Rentabilidade'], errors='coerce')
    df['Taxa Compra'] = pd.to_numeric(df['Taxa Compra'], errors='coerce')
    df['Valor PU Mercado'] = pd.to_numeric(df['Valor PU Mercado'], errors='coerce')
    df['Valor PU Curva'] = pd.to_numeric(df['Valor PU Curva'], errors='coerce')
    df['Data Aquisição'] = pd.to_datetime(df['Data Aquisição'], errors='coerce')

    # Tabs
    aba = st.radio("Selecione a aba:", ["📦 Estoque", "💡 Trade Ideia"])

    if aba == "📦 Estoque":
        # === Filtros ===
        st.sidebar.header("🎯 Filtros de Análise")
        duration_max = st.sidebar.number_input("Duration máxima (anos):", value=0.0, step=0.1)
        roi_minimo = st.sidebar.number_input("ROI Anualizado mínimo (%):", value=0.0, step=0.1)
        rentabilidade_minima = st.sidebar.number_input("Rentabilidade mínima (%):", value=0.0, step=0.1)
        indexador_tipo = st.sidebar.selectbox("Indexador:", ["Todos", "CDI+", "IPCA+", "PRE"], index=0)
        emissor_nome = st.sidebar.text_input("Nome do Emissor (parcial):")
        ativo_nome = st.sidebar.text_input("Nome do Ativo (parcial):")

        # ROI Anualizado
        hoje = pd.to_datetime(datetime.today().date())
        df['Dias Úteis'] = df['Data Aquisição'].apply(lambda x: pd.bdate_range(x, hoje).shape[0] if pd.notnull(x) else np.nan)
        df['ROI Anualizado Num'] = np.where(
            df['Dias Úteis'] > 0,
            ((1 + df['Percentual Rentabilidade']) ** (252 / df['Dias Úteis']) - 1),
            np.nan
        )
        df['ROI Anualizado'] = df['ROI Anualizado Num'].apply(lambda x: f"{x * 100:.2f}".replace(".", ",") if pd.notnull(x) else "")
        df['Data Aquisição'] = df['Data Aquisição'].dt.strftime('%d/%m/%Y')

        # Sugestão
        def gerar_sugestao(row):
            if row['Percentual Ágio ou Deságio'] > 0:
                return 'Vender'
            elif row['Percentual Rentabilidade'] > 0.8:
                return 'Vender'
            elif row['Duration'] <= 2:
                return 'Avaliar Venda'
            elif row['Percentual Carrego CDI'] < 0.7:
                return 'Avaliar Venda'
            elif row['Percentual Carrego CDI'] > 1:
                return 'Avaliar Realocação'
            else:
                return ''
        df['Sugestão'] = df.apply(gerar_sugestao, axis=1)

        # Aplicar filtros
        df_filtros = df.copy()
        if duration_max > 0:
            df_filtros = df_filtros[df_filtros['Duration'] <= duration_max]
        if roi_minimo > 0:
            df_filtros = df_filtros[df_filtros['ROI Anualizado Num'] >= roi_minimo]
        if rentabilidade_minima > 0:
            df_filtros = df_filtros[df_filtros['Percentual Rentabilidade'] >= (rentabilidade_minima / 100)]
        if indexador_tipo != "Todos":
            df_filtros = df_filtros[df_filtros['Indexador'].str.contains(indexador_tipo, case=False, na=False)]
        if emissor_nome:
            df_filtros = df_filtros[df_filtros['Emissor'].str.contains(emissor_nome, case=False, na=False)]
        if ativo_nome:
            df_filtros = df_filtros[df_filtros['Ativo'].str.contains(ativo_nome, case=False, na=False)]

        # Formatar colunas
        col_valores = ['Ágio ou Deságio', 'Valor Acumulado Proventos', 'Valor Total Mercado']
        for col in col_valores:
            df_filtros[col] = df_filtros[col].apply(formatar_valor)
        col_taxas = ['Taxa Compra', 'Percentual Ágio ou Deságio',
                     'Percentual Rentabilidade', 'Percentual Carrego CDI']
        for col in col_taxas:
            df_filtros[col] = df_filtros[col].apply(formatar_taxa)

        colunas_final = [
            'Tipo', 'Emissor', 'Ativo', 'Indexador', 'Taxa Compra',
            'Data Aquisição', 'Ágio ou Deságio', 'Percentual Ágio ou Deságio',
            'Valor Acumulado Proventos', 'Duration', 'Rentabilidade',
            'Percentual Rentabilidade', 'Percentual Carrego CDI',
            'Valor Total Mercado', 'ROI Anualizado', 'Sugestão'
        ]

        df_final = df_filtros[colunas_final]
        df_final['Valor Total Mercado Num'] = df_final['Valor Total Mercado'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

        st.subheader("📊 Resumo Final")
        st.markdown(f"- **Total de contas para avaliar:** {df_final.shape[0]}")
        st.markdown(f"- **Total de ativos únicos:** {df_final['Ativo'].nunique()}")
        st.markdown(f"- **Volume financeiro total:** {formatar_moeda(df_final['Valor Total Mercado Num'].sum())}")

        st.subheader("🔍 Ativos selecionados:")
        st.dataframe(df_final.drop(columns=['Valor Total Mercado Num']), use_container_width=True)

        def converter_para_excel(df):
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.drop(columns=['Valor Total Mercado Num']).to_excel(writer, index=False)
            return output.getvalue()

        st.download_button("📥 Baixar Excel", data=converter_para_excel(df_final), file_name="ativos_filtrados.xlsx")

    elif aba == "💡 Trade Ideia":
        trade_ideia_tab(df)
