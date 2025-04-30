import streamlit as st

st.set_page_config(page_title="Teste de Simulação de Troca", layout="centered")
st.title("💡 Simulador de Recuperação de Deságio")

st.markdown("""
Insira os dados abaixo para calcular em quanto tempo (em anos) você recuperaria o **deságio realizado** ao vender um ativo e reinvestir em um novo com maior rentabilidade.

A simulação considera que:
- O valor investido no novo ativo é o PU Mercado do ativo antigo (valor recebido na venda)
- Ambos os ativos são isentos de IR
""")

st.header("Dados do ativo atual (que será vendido)")
pu_mercado = st.number_input("PU Mercado (preço de venda)", min_value=0.0, value=980.0, step=1.0)
pu_curva = st.number_input("PU Curva (valor ideal no vencimento)", min_value=0.0, value=1000.0, step=1.0)
taxa_atual = st.number_input("Taxa bruta atual (% a.a.)", min_value=0.0, value=9.5, step=0.1)

st.header("Dados do novo ativo (compra)")
taxa_nova = st.number_input("Taxa bruta do novo ativo (% a.a.)", min_value=0.0, value=11.0, step=0.1)

if st.button("Calcular tempo de recuperação"):
    desagio = pu_curva - pu_mercado
    delta_taxa = taxa_nova - taxa_atual

    if delta_taxa <= 0:
        st.warning("A taxa do novo ativo é igual ou menor que a atual. Não compensa a troca.")
    else:
        ganho_anual = (delta_taxa / 100) * pu_mercado
        tempo_recuperacao = desagio / ganho_anual if ganho_anual > 0 else float('inf')

        st.subheader("Resultado da Simulação")
        st.markdown(f"- Deságio realizado: **R$ {desagio:,.2f}**")
        st.markdown(f"- Ganho anual estimado com novo ativo: **R$ {ganho_anual:,.2f}**")
        st.markdown(f"- Tempo estimado para recuperar o deságio: **{tempo_recuperacao:.2f} anos**")

        if tempo_recuperacao > 5:
            st.info("Pode demorar mais de 5 anos para recuperar o deságio. Avalie com cautela.")
        else:
            st.success("A troca pode ser vantajosa. O tempo de recuperação é razoável.")
