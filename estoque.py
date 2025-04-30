import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Ajustar layout com CSS
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    </style>
""", unsafe_allow_html=True)


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

# === Interface do usuário ===
st.title("📊 Ferramenta de Avaliação de Crédito Privado")
st.markdown("Faça o upload de uma planilha `.xlsx` com os dados da aba `Export` para começar.")

uploaded_file = st.file_uploader("📂 Upload do arquivo Excel", type="xlsx")

# === Filtros ===
st.sidebar.header("🎯 Filtros de Análise")
duration_max = st.sidebar.number_input("Duration máxima (anos):", value=0.0, step=0.1)
roi_minimo = st.sidebar.number_input("ROI Anualizado mínimo (%):", value=0.0, step=0.1)
rentabilidade_minima = st.sidebar.number_input("Rentabilidade mínima (%):", value=0.0, step=0.1)
emissor_nome = st.sidebar.text_input("Nome do Emissor (parcial):")
ativo_nome = st.sidebar.text_input("Nome do Ativo (parcial):")

# === Processamento do arquivo ===
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name='Export')

    # Filtrar apenas CRA, CRI e Debêntures
    ativos_credito = ['Debênture', 'CRA', 'CRI']
    df = df[df['Tipo'].isin(ativos_credito)].copy()

    # Conversões
    df['Percentual Rentabilidade'] = pd.to_numeric(df['Percentual Rentabilidade'], errors='coerce')
    df['Percentual Carrego CDI'] = pd.to_numeric(df['Percentual Carrego CDI'], errors='coerce')
    df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')
    df['Percentual Ágio ou Deságio'] = pd.to_numeric(df['Percentual Ágio ou Deságio'], errors='coerce')
    df['Valor Total Mercado'] = pd.to_numeric(df['Valor Total Mercado'], errors='coerce')
    df['Rentabilidade'] = pd.to_numeric(df['Rentabilidade'], errors='coerce')
    df['Data Aquisição'] = pd.to_datetime(df['Data Aquisição'], errors='coerce')

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

    # Aplicar filtros
    df_filtrado = df.copy()

    if duration_max > 0:
        df_filtrado = df_filtrado[df_filtrado['Duration'] <= duration_max]

    if roi_minimo > 0:
        df_filtrado = df_filtrado[df_filtrado['ROI Anualizado Num'] >= roi_minimo]

    if rentabilidade_minima > 0:
        df_filtrado = df_filtrado[df_filtrado['Percentual Rentabilidade'] >= (rentabilidade_minima / 100)]

    if emissor_nome:
        df_filtrado = df_filtrado[df_filtrado['Emissor'].str.contains(emissor_nome, case=False, na=False)]

    if ativo_nome:
        df_filtrado = df_filtrado[df_filtrado['Ativo'].str.contains(ativo_nome, case=False, na=False)]

    # Formatar colunas para exibição
    col_format_valores = ['Ágio ou Deságio', 'Valor Acumulado Proventos', 'Valor Total Mercado']
    for col in col_format_valores:
        df_filtrado[col] = df_filtrado[col].apply(formatar_valor)

    col_format_taxas = ['Taxa Compra', 'Percentual Ágio ou Deságio',
                        'Percentual Rentabilidade', 'Percentual Carrego CDI']
    for col in col_format_taxas:
        df_filtrado[col] = df_filtrado[col].apply(formatar_taxa)

    # Seleção final de colunas
    colunas_final = [
        'Tipo', 'Emissor', 'Ativo', 'Indexador', 'Taxa Compra',
        'Data Aquisição',
        'Ágio ou Deságio', 'Percentual Ágio ou Deságio',
        'Valor Acumulado Proventos', 'Duration',
        'Rentabilidade', 'Percentual Rentabilidade', 'Percentual Carrego CDI',
        'Valor Total Mercado', 'ROI Anualizado', 'Sugestão'
    ]

    df_final = df_filtrado[colunas_final]

    # === RESUMO FINAL ===
    total_contas = df_final.shape[0]
    total_ativos_unicos = df_final['Ativo'].nunique()
    df_final['Valor Total Mercado Num'] = df_final['Valor Total Mercado'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    volume_total = df_final['Valor Total Mercado Num'].sum()

    st.subheader("📊 Resumo Final")
    st.markdown(f"- **Total de contas para avaliar:** {total_contas}")
    st.markdown(f"- **Total de ativos únicos:** {total_ativos_unicos}")
    st.markdown(f"- **Volume financeiro total:** {formatar_moeda(volume_total)}")

    # === TABELA ===
    st.subheader("🔍 Ativos selecionados:")
    st.dataframe(df_final.drop(columns=['Valor Total Mercado Num']), use_container_width=True)

    # === DOWNLOAD ===
    def converter_para_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.drop(columns=['Valor Total Mercado Num']).to_excel(writer, index=False, sheet_name='Análise')
        return output.getvalue()

    st.download_button(
        label="📥 Baixar Excel filtrado",
        data=converter_para_excel(df_final),
        file_name="ativos_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
