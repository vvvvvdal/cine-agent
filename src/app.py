import streamlit as st
import logging
from recomendador import Recomendador
from agente import Agente
from exportador import Exportador

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Cine Agent", page_icon="🎬", layout="wide")

# Inicializa os componentes (cacheado)
@st.cache_resource
def iniciar_sistema():
    logger.info("Iniciando componentes do sistema...")
    recomendador = Recomendador("conteudo.csv")
    agente = Agente(recomendador)
    exportador = Exportador()
    return agente, exportador

try:
    agente, exportador = iniciar_sistema()
except Exception as e:
    st.error("Erro crítico ao carregar o sistema. Verifique os logs.")
    st.stop()


# Inicializa o chat único na sessão
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"role": "assistant", "content": "Olá! Me diga um filme ou série que você gostou e eu te recomendo outros parecidos. 🎬"}
    ]

# Área principal do chat
col1, col2 = st.columns([0.85, 0.15])

with col1:
    st.title("🎬 Cine Agent")
    st.caption("Converse para receber recomendações de filmes e séries baseadas no nosso banco de dados.")

with col2:
    st.write("")
    st.write("")
    if st.button("Limpar conversa", use_container_width=True):
        st.session_state.mensagens = [
            {"role": "assistant", "content": "Olá! Me diga um filme ou série que você gostou e eu te recomendo outros parecidos. 🎬"}
        ]
        st.rerun()

st.divider()

# Renderiza o histórico
for idx, msg in enumerate(st.session_state.mensagens):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Botão PDF nas respostas do agente (exceto a boas-vindas)
        if msg["role"] == "assistant" and msg.get("pdf_bytes"):
            st.download_button(
                label="⬇️ Baixar recomendações em PDF",
                data=msg["pdf_bytes"],
                file_name="recomendacoes.pdf",
                mime="application/pdf",
                key=f"dl_{idx}",
            )

# Prompt de entrada
prompt = st.chat_input("Ex: Gostei de Better Call Saul, me sugira séries parecidas...")

if prompt:
    # 1. Mostra e salva a mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.mensagens.append({"role": "user", "content": prompt})

    # 2. Processa a resposta
    with st.chat_message("assistant"):
        with st.spinner("Vasculhando o banco de dados..."):
            resposta = agente.conversar(prompt)
            st.markdown(resposta)

            # Gera PDF se tiver dados reais do CSV
            pdf_bytes = None
            if agente.ultimo_relatorio:
                pdf_bytes = exportador.gerar_pdf_relatorio(agente.ultimo_relatorio)
                st.download_button(
                    label="⬇️ Baixar recomendações em PDF",
                    data=pdf_bytes,
                    file_name="recomendacoes.pdf",
                    mime="application/pdf",
                    key="dl_new",
                )

    # 3. Salva no histórico do chat
    st.session_state.mensagens.append({
        "role": "assistant",
        "content": resposta,
        "pdf_bytes": pdf_bytes,
    })