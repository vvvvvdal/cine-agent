import streamlit as st
import logging
from recomendador import Recomendador
from assistente import Assistente

logger = logging.getLogger(__name__)

# Configuração visual da página
st.set_page_config(page_title="Cine Agent", page_icon="🎬", layout="centered")
st.title("🎬 Cine Agent")
st.caption("Converse com a IA para receber recomendações baseadas no nosso banco de dados.")

@st.cache_resource
def iniciar_sistema():
    logger.info("Iniciando componentes do sistema...")
    # Aqui assumimos que teremos um arquivo filmes.csv na raiz do projeto
    recomendador = Recomendador("filmes.csv")
    assistente = Assistente(recomendador)
    return assistente

try:
    assistente = iniciar_sistema()
except Exception as e:
    st.error("Erro crítico ao carregar o sistema. Verifique os logs e sua API KEY.")
    st.stop()

# Histórico salvo na "session_state"
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [{"role": "assistant", "content": "Olá! Me diga um filme que você gostou e eu te recomendo outros parecidos."}]

# Renderiza o histórico na tela
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Prompt de exemplo
prompt = st.chat_input("Ex: Gostei de The Batman, me sugira 5 filmes...")

if prompt:
    # 1. Mostra e salva a mensagem do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.mensagens.append({"role": "user", "content": prompt})

    # 2. Chama a IA e mostra um "Pensando..." enquanto o Pandas roda por baixo dos panos
    with st.chat_message("assistant"):
        with st.spinner("Vasculhando o banco de dados..."):
            resposta = assistente.conversar(prompt)
            st.markdown(resposta)
            
    # 3. Salva a resposta da IA no histórico
    st.session_state.mensagens.append({"role": "assistant", "content": resposta})