import google.generativeai as genai
import logging
import os
from dotenv import load_dotenv
from src.recomendador import MotorDeRecomendacao

# Carrega a GEMINI_API_KEY
load_dotenv()

logger = logging.getLogger(__name__)

class Assistente:
    def __init__(self, motor: Recomendador):
        """
        Inicializa o assistente, configura a chave da API e prepara as ferramentas.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY não encontrada. Verifique seu arquivo .env.")
            raise ValueError("Chave da API ausente.")
            
        genai.configure(api_key=api_key)
        self.motor = motor
        
        def buscar_filmes(nome_do_filme: str) -> list:
            """
            Usa o banco de dados interno para buscar filmes similares a um filme escolhido.
            Sempre chame esta função quando o usuário pedir recomendações de filmes.
            """
            logger.info(f"IA acionou a ferramenta de busca para: {nome_do_filme}")
            return self.motor.buscar_similares(nome_do_filme)

        # Configura o modelo passando a ferramenta
        self.modelo = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[buscar_filmes],
            system_instruction="Você é um assistente cinéfilo simpático. Use a ferramenta fornecida para buscar filmes e crie sinopses curtas e atrativas para os resultados."
        )
        
        # Inicia o chat com acionamento automático de funções habilitado
        self.chat = self.modelo.start_chat(enable_automatic_function_calling=True)
        logger.info("Assistente de IA inicializado com sucesso.")
        
    def conversar(self, mensagem_usuario: str) -> str:
        """
        Envia a mensagem do usuário para o Gemini.
        """
        try:
            logger.info(f"Processando mensagem do usuário: {mensagem_usuario}")
            resposta = self.chat.send_message(mensagem_usuario)
            return resposta.text
        except Exception as e:
            logger.error(f"Erro na comunicação com a API do Gemini: {e}")
            return "Desculpe, tive um problema ao processar sua requisição."