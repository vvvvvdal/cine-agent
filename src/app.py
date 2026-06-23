import streamlit as st
import uuid
import logging
from recomendador import Recomendador
from assistente import Assistente
from exportador import Exportador

logger = logging.getLogger(__name__)

# Configuração visual da página
st.set_page_config(page_title="Cine Agent", page_icon="🎬", layout="wide")

# Inicializa os componentes (cacheado)
@st.cache_resource
def iniciar_sistema():
    logger.info("Iniciando componentes do sistema...")
    recomendador = Recomendador("conteudo.csv")
    assistente = Assistente(recomendador)
    exportador = Exportador()
    return assistente, exportador

try:
    assistente, exportador = iniciar_sistema()
except Exception as e:
    st.error("Erro crítico ao carregar o sistema. Verifique os logs.")
    st.stop()


# Gerenciamento de múltiplos chats
def criar_chat():
    chat_id = str(uuid.uuid4())
    return chat_id, {
        "titulo": "Novo chat",
        "mensagens": [
            {"role": "assistant", "content": "Olá! Me diga um filme ou série que você gostou e eu te recomendo outros parecidos. 🎬"}
        ],
    }

if "chats" not in st.session_state:
    cid, cdata = criar_chat()
    st.session_state.chats = {cid: cdata}
    st.session_state.chat_ativo = cid

if "chat_ativo" not in st.session_state or st.session_state.chat_ativo not in st.session_state.chats:
    st.session_state.chat_ativo = list(st.session_state.chats.keys())[0]


# Sidebar com histórico de chats
with st.sidebar:
    st.markdown("## 🎬 Cine Agent")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("➕ Novo chat", use_container_width=True, type="secondary"):
        novo_id, novo_data = criar_chat()
        st.session_state.chats[novo_id] = novo_data
        st.session_state.chat_ativo = novo_id
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Recentes")

    chats_para_deletar = []
    for cid, chat_data in list(st.session_state.chats.items()):
        col_titulo, col_del = st.columns([5, 1])

        with col_titulo:
            titulo_exibido = chat_data["titulo"]
            if len(titulo_exibido) > 22:
                titulo_exibido = titulo_exibido[:22] + "..."

            # Botão invisível (tertiary) a menos que seja o ativo (secondary)
            btn_type = "secondary" if cid == st.session_state.chat_ativo else "tertiary"
            if st.button(titulo_exibido, key=f"sel_{cid}", use_container_width=True, type=btn_type):
                st.session_state.chat_ativo = cid
                st.rerun()

        with col_del:
            # Ícone de lixeira pequeno e discreto
            if st.button("✖", key=f"del_{cid}", help="Apagar este chat", type="tertiary"):
                chats_para_deletar.append(cid)

    for cid in chats_para_deletar:
        del st.session_state.chats[cid]
        if cid == st.session_state.chat_ativo:
            if st.session_state.chats:
                st.session_state.chat_ativo = list(st.session_state.chats.keys())[0]
            else:
                novo_id, novo_data = criar_chat()
                st.session_state.chats[novo_id] = novo_data
                st.session_state.chat_ativo = novo_id
        st.rerun()


# Área principal do chat
chat_atual = st.session_state.chats[st.session_state.chat_ativo]
mensagens = chat_atual["mensagens"]

st.title("🎬 Cine Agent")
st.caption("Converse para receber recomendações de filmes e séries baseadas no nosso banco de dados.")

# Renderiza o histórico
for idx, msg in enumerate(mensagens):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Botão PDF nas respostas do assistente (exceto a boas-vindas)
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
    mensagens.append({"role": "user", "content": prompt})

    # Atualiza o título do chat com a primeira pergunta
    if chat_atual["titulo"] == "Novo chat":
        chat_atual["titulo"] = prompt[:35] + "..." if len(prompt) > 35 else prompt

    # 2. Processa a resposta
    with st.chat_message("assistant"):
        with st.spinner("Vasculhando o banco de dados..."):
            resposta = assistente.conversar(prompt)
            st.markdown(resposta)

            # Gera PDF se tiver dados reais do CSV
            pdf_bytes = None
            if assistente.ultimo_relatorio:
                pdf_bytes = exportador.gerar_pdf_relatorio(assistente.ultimo_relatorio)
                st.download_button(
                    label="⬇️ Baixar recomendações em PDF",
                    data=pdf_bytes,
                    file_name="recomendacoes.pdf",
                    mime="application/pdf",
                    key="dl_new",
                )

    # 3. Salva no histórico do chat
    mensagens.append({
        "role": "assistant",
        "content": resposta,
        "pdf_bytes": pdf_bytes,
    })