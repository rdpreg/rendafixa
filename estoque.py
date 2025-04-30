# === 1. Imports necessários ===
import pandas as pd
import streamlit as st
import io
import numpy as np
from datetime import datetime

# === 2. Funções auxiliares ===

# Formatar valores financeiros
def formatar_valor(valor):
    try:
        return f"{valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return valor

# Formatar taxas (em %)
def formatar_taxa(valor):
    try:
        return f"{valor * 100:.2f}".replace(".", ",")
    except:
        return valor

# Formatar moeda
def formatar_moeda(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except:
        return valor

# === 3. Definir Filtros Variáveis ===

# Widgets para o usuário definir critérios de avaliação
duration_max = widgets.FloatText(description="Duration máxima (anos):", value=None)
roi_minimo = widgets.FloatText(description="ROI Anualizado mínimo (%):", value=None)
rentabilidade_minima = widgets.FloatText(description="Rentabilidade mínima (%):", value=None)
emissor_nome = widgets.Text(description="Nome do Emissor:", placeholder="Parcial ou completo")
ativo_nome = widgets.Text(description="Nome do Ativo:", placeholder="Parcial ou completo")

print("🎯 Defina os critérios de avaliação de venda (deixe em branco se não quiser aplicar o filtro):")
display(duration_max, roi_minimo, rentabilidade_minima, emissor_nome, ativo_nome)

# === 4. Função Principal para Processar o Arquivo ===

def processar_arquivo_enviado(arquivo_enviado):
    if len(arquivo_enviado.value) == 0:
        print("⚠️ Por favor, envie um arquivo Excel.")
        return
    
    # Ler o conteúdo do arquivo
    info_arquivo = next(iter(arquivo_enviado.value.values()))
    conteudo = info_arquivo['content']
    df = pd.read_excel(io.BytesIO(conteudo), sheet_name='Export')
    
    # === 4.1 Filtrar apenas CRA, CRI e Debênture ===
    ativos_credito = ['Debênture', 'CRA', 'CRI']
    df_credito = df[df['Tipo'].isin(ativos_credito)].copy()
    
    # === 4.2 Corrigir tipos numéricos ===
    df_credito['Percentual Rentabilidade'] = pd.to_numeric(df_credito['Percentual Rentabilidade'], errors='coerce')
    df_credito['Percentual Carrego CDI'] = pd.to_numeric(df_credito['Percentual Carrego CDI'], errors='coerce')
    df_credito['Duration'] = pd.to_numeric(df_credito['Duration'], errors='coerce')
    df_credito['Percentual Ágio ou Deságio'] = pd.to_numeric(df_credito['Percentual Ágio ou Deságio'], errors='coerce')
    df_credito['Valor Total Mercado'] = pd.to_numeric(df_credito['Valor Total Mercado'], errors='coerce')
    df_credito['Rentabilidade'] = pd.to_numeric(df_credito['Rentabilidade'], errors='coerce')
    df_credito['Data Aquisição'] = pd.to_datetime(df_credito['Data Aquisição'], errors='coerce')

    # === 4.3 Gerar coluna de sugestão ===
    def gerar_sugestao(linha):
        if linha['Percentual Ágio ou Deságio'] > 0:
            return 'Vender'
        elif linha['Percentual Rentabilidade'] > 0.8:
            return 'Vender'
        elif linha['Duration'] <= 2:
            return 'Avaliar Venda'
        elif linha['Percentual Carrego CDI'] < 0.7:
            return 'Avaliar Venda'
        elif linha['Percentual Carrego CDI'] > 1:
            return 'Avaliar Realocação'
        else:
            return ''

    df_credito['Sugestão'] = df_credito.apply(gerar_sugestao, axis=1)
    
    # === 4.4 Calcular Dias Úteis e ROI Anualizado ===
    hoje = pd.to_datetime(datetime.today().date())
    df_credito['Dias Úteis'] = df_credito['Data Aquisição'].apply(lambda x: pd.bdate_range(x, hoje).shape[0] if pd.notnull(x) else np.nan)
    
    df_credito['ROI Anualizado'] = np.where(
        df_credito['Dias Úteis'] > 0,
        ((1 + df_credito['Percentual Rentabilidade']) ** (252 / df_credito['Dias Úteis']) - 1),
        np.nan
    )

    # Formatar ROI Anualizado como percentual
    df_credito['ROI Anualizado'] = df_credito['ROI Anualizado'].apply(lambda x: f"{x * 100:.2f}".replace(".", ",") if pd.notnull(x) else "")
    
    # Formatar Data Aquisição como dd/mm/yyyy
    df_credito['Data Aquisição'] = df_credito['Data Aquisição'].dt.strftime('%d/%m/%Y')

    # === 4.5 Selecionar colunas de saída ===
    colunas_saida = [
        'Conta', 'Tipo', 'Emissor', 'Ativo', 'Indexador', 'Taxa Compra',
        'Data Aquisição', 'Valor PU Mercado', 'Valor PU Custo ', 'Valor PU Curva',
        'Ágio ou Deságio', 'Percentual Ágio ou Deságio',
        'Valor Acumulado Proventos', 'Duration',
        'Rentabilidade', 'Percentual Rentabilidade', 'Percentual Carrego CDI', 
        'Valor Total Mercado', 'ROI Anualizado', 'Sugestão'
    ]
    
    df_saida = df_credito[colunas_saida]
    
    # === 4.6 Aplicar formatação ===
    colunas_valores = [
        'Valor PU Mercado', 'Valor PU Custo ', 'Valor PU Curva',
        'Ágio ou Deságio', 'Valor Acumulado Proventos', 'Valor Total Mercado'
    ]
    
    colunas_taxas = [
        'Taxa Compra', 'Percentual Ágio ou Deságio',
        'Percentual Rentabilidade', 'Percentual Carrego CDI'
    ]
    
    for coluna in colunas_valores:
        df_saida[coluna] = df_saida[coluna].apply(formatar_valor)
    
    for coluna in colunas_taxas:
        df_saida[coluna] = df_saida[coluna].apply(formatar_taxa)
    
    # === 4.7 Aplicar Filtros Variáveis ===
    df_filtros = df_saida.copy()

    # Filtro Duration
    if duration_max.value is not None and not np.isnan(duration_max.value):
        df_filtros['Duration'] = pd.to_numeric(df_filtros['Duration'], errors='coerce')
        df_filtros = df_filtros[df_filtros['Duration'] <= duration_max.value]

    # Filtro ROI Anualizado
    if roi_minimo.value is not None and not np.isnan(roi_minimo.value):
        df_filtros['ROI Anualizado Num'] = df_filtros['ROI Anualizado'].str.replace(',', '.').str.rstrip('%').astype(float)
        df_filtros = df_filtros[df_filtros['ROI Anualizado Num'] >= roi_minimo.value]

    # Filtro Rentabilidade Percentual
    if rentabilidade_minima.value is not None and not np.isnan(rentabilidade_minima.value):
        df_filtros['Percentual Rentabilidade Num'] = df_filtros['Percentual Rentabilidade'].str.replace(',', '.').astype(float)
        df_filtros = df_filtros[df_filtros['Percentual Rentabilidade Num'] >= rentabilidade_minima.value]

    # Filtro Emissor
    if emissor_nome.value:
        df_filtros = df_filtros[df_filtros['Emissor'].str.contains(emissor_nome.value, case=False, na=False)]

    # Filtro Ativo
    if ativo_nome.value:
        df_filtros = df_filtros[df_filtros['Ativo'].str.contains(ativo_nome.value, case=False, na=False)]

    # === 4.8 Exibir ativos filtrados ===
    print("\n🔍 Ativos filtrados de acordo com os critérios definidos:")
    display(df_filtros)

    # === 4.9 Exportar Excel dos ativos filtrados ===
    df_filtros.to_excel('ativos_filtrados.xlsx', index=False)
    print("\n✅ Arquivo 'ativos_filtrados.xlsx' gerado com os ativos filtrados.")

    # === 5.0 Gerar Resumo Final ===
    total_ativos = df_filtros.shape[0]
    volume_total = pd.to_numeric(df_filtros['Valor Total Mercado'].str.replace('.', '').str.replace(',', '.')).sum()
    
    print("\n📊 RESUMO FINAL:")
    print(f"Total de ativos para avaliar: {total_ativos}")
    print(f"Volume financeiro total: {formatar_moeda(volume_total)}")

# === 5. Upload de Arquivo e Botão de Processamento ===
uploader = widgets.FileUpload(accept='.xlsx', multiple=False)
botao_processar = widgets.Button(description="Processar Arquivo")

def ao_clicar_no_botao(botao):
    processar_arquivo_enviado(uploader)

botao_processar.on_click(ao_clicar_no_botao)

print("\n📂 Faça o upload do arquivo Excel:")
display(uploader, botao_processar)
