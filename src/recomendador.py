import re
import pandas as pd
import logging

# Data/Hora - Nome - Nível - Mensagem
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Recomendador:
    def __init__(self, caminho_csv: str):
        """
        Construtor da classe. Carrega o dataset na memória assim que o objeto é instanciado.
        """
        try:
            self.df = pd.read_csv(caminho_csv) # Colunas 'title', 'type' e 'genres'
            self.df.dropna(subset=['title', 'genres'], inplace=True) # Remove linhas vazias
            
            logger.info(f"Base carregada com sucesso. {len(self.df)} títulos disponíveis.")
            
        except FileNotFoundError:
            logger.error(f"Arquivo CSV não encontrado no caminho: {caminho_csv}")
            self.df = pd.DataFrame() # Cria um DataFrame vazio

    def extrair_titulo(self, mensagem: str) -> str:
        """
        Varre a mensagem do usuário procurando qual título do CSV aparece nela.
        Ordena por comprimento (maior primeiro) pra evitar match parcial.
        """
        if self.df.empty:
            return mensagem

        mensagem_lower = mensagem.lower()
        titulos_ordenados = sorted(self.df['title'].tolist(), key=len, reverse=True)

        for titulo in titulos_ordenados:
            if titulo.lower() in mensagem_lower:
                logger.info(f"Título extraído da mensagem: '{titulo}'")
                return titulo

        logger.info(f"Nenhum título do CSV encontrado na mensagem: '{mensagem}'")
        return mensagem

    def extrair_quantidade(self, mensagem: str) -> int:
        """
        Extrai a quantidade solicitada da mensagem do usuário.
        Procura por números escritos ou por algarismos. Padrão: 5.
        """
        # Mapa de números escritos por extenso
        numeros_extenso = {
            "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
            "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8,
            "nove": 9, "dez": 10,
        }

        mensagem_lower = mensagem.lower()

        # Tenta achar um número antes de palavras como "filme", "serie", "parecid", "diferent", "recomend"
        padrao = r'(\d+)\s*(?:filme|serie|série|parecid|diferent|recomend|sugest)'
        match = re.search(padrao, mensagem_lower)
        if match:
            qtd = int(match.group(1))
            logger.info(f"Quantidade extraída (algarismo): {qtd}")
            return min(qtd, 10)  # Limita a 10

        # Tenta achar número por extenso
        for palavra, valor in numeros_extenso.items():
            padrao_extenso = rf'\b{palavra}\b\s*(?:filme|serie|série|parecid|diferent|recomend|sugest)'
            if re.search(padrao_extenso, mensagem_lower):
                logger.info(f"Quantidade extraída (extenso): {valor}")
                return valor

        # Tenta achar qualquer número solto na mensagem
        numeros = re.findall(r'\d+', mensagem_lower)
        if numeros:
            # Pega o último número assumindo que anos de filme (ex 2022) estariam atrelados ao nome e a qtd no pedido final
            # Filtra números maiores que 10 para evitar pegar anos como 2022
            for n in reversed(numeros):
                if int(n) <= 10:
                    logger.info(f"Quantidade extraída (fallback iterativo): {n}")
                    return int(n)
            logger.info(f"Quantidade extraída (fallback direto): {min(int(numeros[0]), 10)}")
            return min(int(numeros[0]), 10)

        logger.info("Quantidade não especificada, usando padrão: 5")
        return 5

    def extrair_modo(self, mensagem: str) -> str:
        """
        Detecta se o usuário quer títulos similares ou diferentes.
        """
        mensagem_lower = mensagem.lower()
        
        # Palavras que indicam explicitamente que quer algo diferente
        palavras_diferente = [
            "diferent", "nadaver", "nada a ver", "nao parecid", "não parecid",
            "nao sao parecid", "não são parecid", "outro estilo", "outro genero",
            "outro gênero", "oposto", "não se parecem", "nao se parecem", "não parecem", "nao parecem"
        ]

        negacoes_parecido = [
            "nao parecid", "não parecid", "nao sao parecid", "não são parecid",
            "não se parecem", "nao se parecem", "não parecem", "nao parecem"
        ]

        # Se ele pediu explicitamente "parecido" ou "similar", a prioridade é similar
        if ("parecid" in mensagem_lower or "parece" in mensagem_lower or "similar" in mensagem_lower) and not any(p in mensagem_lower for p in negacoes_parecido):
            logger.info("Modo detectado: similar (explícito)")
            return "similar"

        for palavra in palavras_diferente:
            if palavra in mensagem_lower:
                logger.info(f"Modo detectado: diferente (match: '{palavra}')")
                return "diferente"

        if ("nao gostei" in mensagem_lower or "não gostei" in mensagem_lower or "odiei" in mensagem_lower):
            logger.info("Modo detectado: diferente (sentimento negativo base)")
            return "diferente"

        logger.info("Modo detectado: similar (padrão)")
        return "similar"

    def extrair_tipo_alvo(self, mensagem: str) -> str:
        """
        Detecta se o usuário pediu especificamente Filmes, Séries ou Qualquer.
        """
        msg = mensagem.lower()
        quer_filme = "filme" in msg
        quer_serie = "serie" in msg or "série" in msg

        if quer_filme and not quer_serie:
            return "Filme"
        elif quer_serie and not quer_filme:
            return "Série"
        return "Qualquer"

    def extrair_pedidos(self, mensagem: str) -> list:
        """
        Divide a mensagem em sub-pedidos para suportar "2 filmes e 2 series".
        """
        msg = mensagem.lower().replace(',', ' e ').replace('.', ' e ').replace(' mas ', ' e ').replace(' e tambem ', ' e ')
        partes = msg.split(' e ')
        
        pedidos = []
        contexto_negativo = ('nao gostei' in mensagem.lower() or 'não gostei' in mensagem.lower() or 'odiei' in mensagem.lower())

        for parte in partes:
            if not parte.strip(): continue
            
            # Ignora partes que são só "gostei de X" sem um pedido atrelado
            if ('gostei' in parte or 'odiei' in parte) and not any(p in parte for p in ['indica', 'recomenda', 'sugere', 'manda', 'parecid', 'similar', 'diferent', 'filme', 'serie']):
                continue
                
            qtd = self.extrair_quantidade(parte)
            tipo = self.extrair_tipo_alvo(parte)
            
            parte_para_modo = parte
            if contexto_negativo and 'parecid' not in parte and 'similar' not in parte and 'diferent' not in parte and 'parecem' not in parte:
                parte_para_modo = 'nao gostei ' + parte
                
            modo = self.extrair_modo(parte_para_modo)
            
            # Se a parte não tem nada útil que diferencie de um "vazio", pula
            if qtd == 5 and tipo == 'Qualquer' and 'parecid' not in parte and 'similar' not in parte and 'diferent' not in parte and 'parecem' not in parte:
                continue
                
            pedidos.append({
                'quantidade': qtd,
                'tipo': tipo,
                'modo': modo,
                'original': parte
            })
            
        if not pedidos:
            pedidos.append({
                'quantidade': self.extrair_quantidade(mensagem),
                'tipo': self.extrair_tipo_alvo(mensagem),
                'modo': self.extrair_modo(mensagem),
                'original': mensagem
            })
            
        return pedidos

    def buscar_similares(self, nome_filme: str, top_n: int = 5) -> list:
        """
        Retorna uma lista de nomes de títulos similares (mesmo gênero principal).
        """
        if self.df.empty:
            logger.warning("Tentativa de busca com a base de dados indisponível.")
            return ["[ERRO] Base de dados indisponível."]

        filme_alvo = self.df[self.df['title'].str.contains(nome_filme, case=False, na=False)]
        
        if filme_alvo.empty:
            logger.info(f"Busca sem resultados para o filme: '{nome_filme}'")
            return [f"Infelizmente não achei '{nome_filme}' na nossa base."]
        
        generos_fonte = set(filme_alvo.iloc[0]['genres'].split('|'))
        nome_filme_alvo = filme_alvo.iloc[0]['title']
        
        def tem_genero_comum(genres_str):
            generos_titulo = set(genres_str.split('|'))
            return len(generos_titulo & generos_fonte) > 0

        filmes_similares = self.df[
            (self.df['title'] != nome_filme_alvo) & 
            (self.df['genres'].apply(tem_genero_comum))
        ]

        lista_resultados = filmes_similares.head(top_n)['title'].tolist()
        
        logger.info(f"Similares para '{nome_filme_alvo}' (Gênero: {genero_principal}): {lista_resultados}")
        return lista_resultados

    def buscar_similares_detalhado(self, nome_filme: str, top_n: int = 5, tipo_alvo: str = "Qualquer") -> list:
        """
        Retorna dicts com título, tipo e gêneros de títulos similares (mesmo gênero).
        """
        if self.df.empty:
            return []

        filme_alvo = self.df[self.df['title'].str.contains(nome_filme, case=False, na=False)]
        if filme_alvo.empty:
            return []

        generos_fonte = set(filme_alvo.iloc[0]['genres'].split('|'))
        nome_filme_alvo = filme_alvo.iloc[0]['title']

        def tem_genero_comum(genres_str):
            generos_titulo = set(genres_str.split('|'))
            return len(generos_titulo & generos_fonte) > 0

        filtro = (self.df['title'] != nome_filme_alvo) & (self.df['genres'].apply(tem_genero_comum))
        if tipo_alvo != "Qualquer":
            filtro = filtro & (self.df['type'] == tipo_alvo)

        filmes_similares = self.df[filtro]
        resultado = filmes_similares.head(top_n)[['title', 'type', 'genres', 'year']]
        return resultado.to_dict('records')

    def buscar_diferentes_detalhado(self, nome_filme: str, top_n: int = 5, tipo_alvo: str = "Qualquer") -> list:
        """
        Retorna dicts com título, tipo e gêneros de títulos com gêneros DIFERENTES.
        Exclui qualquer título que compartilhe algum gênero com o título fonte.
        """
        if self.df.empty:
            return []

        filme_alvo = self.df[self.df['title'].str.contains(nome_filme, case=False, na=False)]
        if filme_alvo.empty:
            return []

        nome_filme_alvo = filme_alvo.iloc[0]['title']
        generos_fonte = set(filme_alvo.iloc[0]['genres'].split('|'))

        def sem_genero_comum(genres_str):
            generos_titulo = set(genres_str.split('|'))
            return len(generos_titulo & generos_fonte) == 0

        filtro = (self.df['title'] != nome_filme_alvo) & (self.df['genres'].apply(sem_genero_comum))
        if tipo_alvo != "Qualquer":
            filtro = filtro & (self.df['type'] == tipo_alvo)

        diferentes = self.df[filtro]

        if diferentes.empty:
            logger.info("Nenhum título totalmente diferente encontrado, buscando os menos similares.")
            def contar_generos_comuns(genres_str):
                return len(set(genres_str.split('|')) & generos_fonte)

            candidatos = self.df[(self.df['title'] != nome_filme_alvo)]
            if tipo_alvo != "Qualquer":
                candidatos = candidatos[candidatos['type'] == tipo_alvo]
                
            candidatos = candidatos.copy()
            candidatos['score'] = candidatos['genres'].apply(contar_generos_comuns)
            diferentes = candidatos.sort_values('score').drop(columns='score')

        resultado = diferentes.head(top_n)[['title', 'type', 'genres', 'year']]
        logger.info(f"Diferentes de '{nome_filme_alvo}': {resultado['title'].tolist()}")
        return resultado.to_dict('records')

    def buscar_info_fonte(self, nome_titulo: str) -> dict:
        """
        Retorna metadados do título buscado: nome exato, tipo (Filme/Série) e gênero principal.
        """
        if self.df.empty:
            return {"titulo": nome_titulo, "tipo": "Título", "genero": "", "year": ""}

        resultado = self.df[self.df['title'].str.contains(nome_titulo, case=False, na=False)]
        if resultado.empty:
            return {"titulo": nome_titulo, "tipo": "Título", "genero": "", "year": ""}

        linha = resultado.iloc[0]
        return {
            "titulo": linha['title'],
            "tipo": linha['type'],
            "genero": linha['genres'],
            "year": linha['year'],
        }