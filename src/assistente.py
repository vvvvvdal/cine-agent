import ollama
import os
import logging
import requests
from recomendador import Recomendador

logger = logging.getLogger(__name__)

MODELO = "qwen2.5:1.5b"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


class Assistente:
    def __init__(self, motor: Recomendador):
        """
        Inicializa o assistente com o motor de busca e o cliente Ollama.
        O Ollama é usado apenas para gerar mini sinopses dos títulos recomendados.
        """
        self.motor = motor
        self.cliente = ollama.Client(host=OLLAMA_HOST)
        self.ultimo_relatorio = None
        logger.info(f"Assistente inicializado. Modelo: {MODELO} | Host: {OLLAMA_HOST}")

    def conversar(self, mensagem_usuario: str) -> str:
        """
        1. Extrai título, quantidade e modo (similar/diferente) da mensagem
        2. Busca no CSV de acordo com o modo
        3. Gera mini sinopses via Ollama
        4. Monta resposta formatada + relatório pro PDF
        """
        titulo_extraido = self.motor.extrair_titulo(mensagem_usuario)
        info_fonte = self.motor.buscar_info_fonte(titulo_extraido)
        
        pedidos = self.motor.extrair_pedidos(mensagem_usuario)
        logger.info(f"Fonte: {info_fonte} | Pedidos: {pedidos}")

        detalhado_total = []
        titulos_adicionados = set()
        
        for pedido in pedidos:
            # IA interpreta a real intenção em vez de depender apenas de heurísticas
            texto_original = pedido.get("original", pedido.get("texto_original", mensagem_usuario))
            modo_ia = self._classificar_modo_com_ia(texto_original, pedido["modo"])
            pedido["modo"] = modo_ia
            
            qtd = pedido["quantidade"]
            modo = pedido["modo"]
            tipo_alvo = pedido["tipo"]
            
            if modo == "diferente":
                itens = self.motor.buscar_diferentes_detalhado(titulo_extraido, top_n=qtd, tipo_alvo=tipo_alvo)
            else:
                itens = self.motor.buscar_similares_detalhado(titulo_extraido, top_n=qtd, tipo_alvo=tipo_alvo)
                
            for item in itens:
                if item["title"] not in titulos_adicionados:
                    titulos_adicionados.add(item["title"])
                    detalhado_total.append(item)

        if not detalhado_total:
            self.ultimo_relatorio = None
            return (
                f"Não encontrei **'{mensagem_usuario}'** na nossa base de dados. 😕\n\n"
                f"Tente outro título! Exemplos: *Breaking Bad*, *Inception*, *Stranger Things*..."
            )

        # Monta a resposta de chat
        titulo_fonte = info_fonte["titulo"]
        tipo_fonte = info_fonte["tipo"]
        genero_fonte = info_fonte["genero"].replace("|", ", ")
        ano_fonte = info_fonte.get("year", "")

        resposta = f"Com base em **{titulo_fonte}** ({ano_fonte} • {tipo_fonte} • {genero_fonte}), "
        resposta += f"aqui estão suas recomendações:\n\n"

        recomendacoes_relatorio = []
        for i, item in enumerate(detalhado_total):
            titulo = item["title"]
            tipo = item["type"]
            generos = item["genres"].replace("|", ", ")
            ano = item.get("year", "")

            # Formatação ajustada sem sinopses
            resposta += f"**{i + 1}. {titulo}** ({ano})\n\n"
            resposta += f"_{tipo} • {generos}_\n\n"
            resposta += "---\n\n"

            recomendacoes_relatorio.append({
                "titulo": titulo,
                "tipo": tipo,
                "generos": item["genres"],
                "year": ano,
                "sinopse": "", # Removido
            })

        # Se teve mais de um pedido misto, usa 'solicitados' no PDF
        modo_pdf = "solicitados" if len(pedidos) > 1 else ("diferentes" if pedidos[0]["modo"] == "diferente" else "similares")
        
        # Relatório pro PDF (dados do CSV + sinopses do Ollama)
        self.ultimo_relatorio = {
            "titulo_fonte": titulo_fonte,
            "tipo_fonte": tipo_fonte,
            "genero_fonte": info_fonte["genero"],
            "ano_fonte": ano_fonte,
            "modo": modo_pdf,
            "recomendacoes": recomendacoes_relatorio,
        }

        return resposta

    def _classificar_modo_com_ia(self, texto: str, modo_padrao: str) -> str:
        """
        Usa o agente de IA para interpretar exclusivamente se o usuário quer
        títulos SIMILARES ou DIFERENTES baseado no trecho da mensagem.
        """
        prompt = (
            f"Analise a seguinte frase e classifique se a intenção do usuário é buscar "
            f"obras SIMILARES (parecidas, na mesma pegada, gosta do estilo) ou "
            f"DIFERENTES (nada a ver, oposto, não gosta do estilo).\n\n"
            f"Frase: '{texto}'\n\n"
            f"Responda APENAS com uma única palavra: SIMILAR ou DIFERENTE."
        )
        try:
            resposta = self.cliente.chat(
                model=MODELO,
                messages=[{"role": "user", "content": prompt}],
            )
            resp = resposta["message"]["content"].strip().lower()
            if "diferente" in resp:
                return "diferente"
            if "similar" in resp:
                return "similar"
        except Exception as e:
            logger.warning(f"Erro ao classificar com IA: {e}")
        return modo_padrao