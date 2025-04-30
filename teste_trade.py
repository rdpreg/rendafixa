import streamlit as st
import math

st.set_page_config(page_title="Teste de Simulação de Troca", layout="centered")
st.title("💡 Simulador de Recuperação de Deságio")

st.markdown("""
Insira os dados abaixo para calcular em quanto tempo (em anos e número de cupons) você recuperaria o **deságio realizado** ao vender um ativo e reinvestir em um novo com maior rentabilidade.

A simulação considera que:
- O valor investido no novo ativo é o PU Mercado do ativo antigo (valor recebido na venda)
- Ambos os ativos são isentos de IR
- Os cupons são pagos de forma regular, com valor fixo por pagamento
""")

st.header("Dados do ativo atual (que será vendido)")
pu_mercado = st.number_input("PU Mercado (preço de venda)", min_value=0.0, value=980.0, step=1.0)
pu_curva = st.number_input("PU Curva (valor ideal no vencimento)", min_value=0.0, value=1000.0, step=1.0)
taxa_atual = st.number_input("Taxa bruta atual (% a.a.)", min_value=0.0, value=9.5, step=0.1)

st.header("Dados do novo ativo (compra)")
taxa_nova = st.number_input("Taxa bruta do novo ativo (% a.a.)", min_value=0.0, value=11.0, step=0.1)
cupom_valor = st.number_input("Valor do cupom por pagamento (R$)", min_value=0.0, value=30.0, step=1.0)
cupom_freq = st.selectbox("Frequência de pagamento de cupons", ["Mensal", "Trimestral", "Semestral", "Anual"])

frequencia_meses = {"Mensal": 1, "Trimestral": 3, "Semestral": 6, "Anual": 12}

if st.button("Calcular tempo de recuperação"):
    desagio = pu_curva - pu_mercado
    delta_taxa = taxa_nova - taxa_atual

    st.subheader("Resultado da Simulação")
    st.markdown(f"- Deságio realizado: **R$ {desagio:,.2f}**")

    if delta_taxa <= 0:
        st.warning("A taxa do novo ativo é igual ou menor que a atual. Não compensa a troca.")
    elif cupom_valor <= 0:
        st.warning("Informe um valor positivo para o cupom.")
    else:
        num_cupons = math.ceil(desagio / cupom_valor)
        meses_para_recuperar = num_cupons * frequencia_meses[cupom_freq]
        anos_para_recuperar = round(meses_para_recuperar / 12, 2)

        st.markdown(f"- Valor do cupom: **R$ {cupom_valor:,.2f}**")
        st.markdown(f"- Frequência: **{cupom_freq}**")
        st.markdown(f"- Cupons necessários para recuperar o deságio: **{num_cupons}**")
        st.markdown(f"- Tempo estimado para recuperar o deságio: **{anos_para_recuperar} anos** ou **{meses_para_recuperar} meses**")

        if anos_para_recuperar > 5:
            st.info("Pode demorar mais de 5 anos para recuperar o deságio. Avalie com cautela.")
        else:
            st.success("A troca pode ser vantajosa. O tempo de recuperação é razoável.")
