import ollama
import os
import logging
import requests
from recomendador import Recomendador

logger = logging.getLogger(__name__)

MODELO = "qwen2.5:1.5b"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


class Agente:
    def __init__(self, motor: Recomendador):
        """
        Inicializa o agente com o motor de busca e o cliente Ollama.
        O Ollama é usado apenas para gerar mini sinopses dos títulos recomendados.
        """
        self.motor = motor
        self.cliente = ollama.Client(host=OLLAMA_HOST)
        self.ultimo_relatorio = None
        logger.info(f"Agente inicializado. Modelo: {MODELO} | Host: {OLLAMA_HOST}")

    def conversar(self, mensagem_usuario: str) -> str:
        """
        1. Extrai título, quantidade e modo (similar/diferente) da mensagem
        2. Busca no CSV de acordo com o modo
        3. Monta resposta formatada + relatório pro PDF
        """
        titulos_encontrados = self.motor.extrair_titulos(mensagem_usuario)
        generos_encontrados = self.motor.extrair_generos_solicitados(mensagem_usuario)
        
        # Validação: o usuário não pode pedir comparações com mais de um título base ao mesmo tempo
        if len(titulos_encontrados) > 1:
            titulos_str = " e ".join([f"**{t}**" for t in titulos_encontrados])
            self.ultimo_relatorio = None
            return (
                f"Detectei que você mencionou mais de um conteúdo da nossa base ({titulos_str}).\n\n"
                f"Para que as recomendações fiquem bem precisas, **escolha somente um filme ou série por vez** na sua mensagem, por favor!"
            )
            
        # Validação: se não achou título, mas achou múltiplos gêneros
        if not titulos_encontrados and len(generos_encontrados) > 1:
            mapa_inverso = {g: sin[0].capitalize() for g, sin in self.motor.mapa_generos.items()}
            generos_pt = [mapa_inverso.get(g, g) for g in generos_encontrados]
            generos_str = " e ".join([f"**{g}**" for g in generos_pt])
            
            self.ultimo_relatorio = None
            return (
                f"Detectei que você pediu indicações misturando os gêneros {generos_str}.\n\n"
                f"Para que as recomendações fiquem bem precisas, **escolha somente um título ou um gênero por vez** na sua mensagem, por favor!"
            )
            
        # Validação: se misturou título específico com gênero
        if titulos_encontrados and generos_encontrados:
            titulo_str = titulos_encontrados[0]
            genero_str = generos_encontrados[0]
            
            mapa_inverso = {g: sin[0].capitalize() for g, sin in self.motor.mapa_generos.items()}
            genero_pt = mapa_inverso.get(genero_str, genero_str)
            
            self.ultimo_relatorio = None
            return (
                f"Detectei que você misturou um título específico (**{titulo_str}**) com um gênero (**{genero_pt}**).\n\n"
                f"Para que as recomendações fiquem bem precisas, **escolha somente um título ou um gênero por vez** na sua mensagem, por favor!"
            )
            
        titulo_extraido = titulos_encontrados[0] if titulos_encontrados else None
        genero_unico = generos_encontrados[0] if generos_encontrados else None
        
        pedidos = self.motor.extrair_pedidos(mensagem_usuario)
        
        # Validação: limite máximo de 10 conteúdos no total
        total_solicitado = sum(p["quantidade"] for p in pedidos)
        if total_solicitado > 10:
            self.ultimo_relatorio = None
            return (
                f"Você solicitou um total de **{total_solicitado} recomendações**.\n\n"
                f"Nosso sistema tem um **limite de segurança de 10 conteúdos por vez** para manter a precisão e a formatação do PDF. "
                f"Por favor, diminua a quantidade solicitada e tente novamente!"
            )
            
        detalhado_total = []
        titulos_adicionados = set()
        info_fonte = None

        if titulo_extraido:
            info_fonte = self.motor.buscar_info_fonte(titulo_extraido)
            logger.info(f"Fonte: {info_fonte} | Pedidos: {pedidos}")

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
        else:
            # Não encontrou título, tenta extrair gêneros diretamente
            if genero_unico:
                for pedido in pedidos:
                    itens = self.motor.buscar_por_genero(genero_unico, top_n=pedido["quantidade"], tipo_alvo=pedido["tipo"])
                    for item in itens:
                        if item["title"] not in titulos_adicionados:
                            titulos_adicionados.add(item["title"])
                            detalhado_total.append(item)

        if not detalhado_total:
            self.ultimo_relatorio = None
            
            # Formata a lista de gêneros disponíveis em português
            mapa_inverso = {g: sin[0].capitalize() for g, sin in self.motor.mapa_generos.items() if g in self.motor.generos_unicos}
            generos_str = ", ".join(sorted(mapa_inverso.values()))
            
            return (
                f"Não encontrei **'{mensagem_usuario}'** na nossa base de dados.\n\n"
                f"**Tente buscar por um título:** *Breaking Bad*, *The Batman*, *Stranger Things*...\n\n"
                f"**Ou busque por um desses gêneros:** _{generos_str}_"
            )

        # Monta a resposta de chat
        if titulo_extraido:
            titulo_fonte = info_fonte["titulo"]
            tipo_fonte = info_fonte["tipo"]
            genero_fonte = info_fonte["genero"].replace("|", ", ")
            ano_fonte = info_fonte.get("year", "")
            resposta = f"Com base em **{titulo_fonte}** ({ano_fonte} • {tipo_fonte} • {genero_fonte}), aqui estão suas recomendações:\n\n"
        else:
            mapa_inverso = {g: sin[0].capitalize() for g, sin in self.motor.mapa_generos.items()}
            nome_genero = mapa_inverso.get(genero_unico, genero_unico) if genero_unico else "Misto"
            
            resposta = f"Aqui estão as recomendações baseadas no gênero **{nome_genero}**:\n\n"
            titulo_fonte = f"Busca por Gênero ({nome_genero})"
            tipo_fonte = "-"
            genero_fonte = "-"
            ano_fonte = "-"

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

        # Se teve mais de um pedido misto ou buscou por gênero, ajusta título no PDF
        if not titulo_extraido or len(pedidos) > 1:
            modo_pdf = "solicitados" 
        else:
            modo_pdf = "diferentes" if pedidos[0]["modo"] == "diferente" else "similares"
        
        # Relatório pro PDF
        self.ultimo_relatorio = {
            "titulo_fonte": titulo_fonte,
            "tipo_fonte": tipo_fonte,
            "genero_fonte": genero_fonte,
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