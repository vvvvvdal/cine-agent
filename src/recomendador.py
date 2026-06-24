import re
import pandas as pd
import logging
import random
from thefuzz import fuzz

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
            
            todos_generos_str = "|".join(self.df['genres'].dropna().tolist())
            self.generos_unicos = set(todos_generos_str.split('|'))
            
            # Mapas para traduções
            self.mapa_generos = {
                'Action': ['ação', 'acao', 'action', 'porrada', 'luta'],
                'Adventure': ['aventura', 'adventure', 'exploracao', 'exploração'],
                'Sci-Fi': ['ficção científica', 'ficcao cientifica', 'sci-fi', 'sci fi', 'ciencia', 'espaço', 'espaco', 'alien'],
                'Drama': ['drama', 'emocionante', 'triste'],
                'Comedy': ['comédia', 'comedia', 'engraçado', 'engracado', 'risada', 'comedy', 'rir'],
                'Horror': ['terror', 'horror', 'assustador', 'medo'],
                'Crime': ['crime', 'policial', 'investigacao', 'investigação', 'roubo', 'assassino', 'investigativo'],
                'Thriller': ['suspense', 'thriller', 'tenso', 'tensão', 'tensao'],
                'Romance': ['romance', 'amor', 'romantico', 'romântico', 'apaixonado'],
                'Mystery': ['mistério', 'misterio', 'mystery', 'enigma'],
                'Fantasy': ['fantasia', 'fantasy', 'mágica', 'magia'],
                'Animation': ['animação', 'animacao', 'desenho', 'animation', 'animado'],
                'Family': ['família', 'familia', 'family', 'infantil', 'crianca', 'criança'],
                'Biography': ['biografia', 'biography', 'história real', 'historia real'],
                'History': ['história', 'historia', 'history', 'época', 'historico'],
                'Documentary': ['documentário', 'documentario', 'documentary'],
                'Music': ['música', 'musica', 'musical', 'music'],
                'Western': ['faroeste', 'western', 'bang bang', 'cowboy']
            }
            
            logger.info(f"Base carregada com sucesso. {len(self.df)} títulos disponíveis.")
            
        except FileNotFoundError:
            logger.error(f"Arquivo CSV não encontrado no caminho: {caminho_csv}")
            self.df = pd.DataFrame() # Cria um DataFrame vazio

    def extrair_titulos(self, mensagem: str) -> list:
        """
        Retorna uma lista com todos os títulos do CSV encontrados na mensagem.
        """
        if self.df.empty:
            return []

        mensagem_lower = mensagem.lower()
        titulos_ordenados = sorted(self.df['title'].tolist(), key=len, reverse=True)
        encontrados = []

        for titulo in titulos_ordenados:
            if titulo.lower() in mensagem_lower:
                encontrados.append(titulo)
                # Remove o título da mensagem para não dar match duplo (ex: 'The Batman' e 'Batman')
                mensagem_lower = mensagem_lower.replace(titulo.lower(), "")

        return encontrados

    def extrair_titulo(self, mensagem: str) -> str:
        """
        Retorna o primeiro título encontrado (apenas por retrocompatibilidade).
        """
        titulos = self.extrair_titulos(mensagem)
        if titulos:
            logger.info(f"Título extraído da mensagem: '{titulos[0]}'")
            return titulos[0]

        logger.info(f"Nenhum título do CSV encontrado na mensagem: '{mensagem}'")
        return mensagem

    def extrair_quantidade(self, mensagem: str) -> int:
        """
        Extrai a quantidade solicitada (ex: "5 filmes" ou "duas séries").
        Retorna 5 por padrão.
        """
        mensagem_lower = mensagem.lower()
        
        numeros_extenso = {
            "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
            "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8,
            "nove": 9, "dez": 10
        }

        # Primeiro procura por palavras escritas (um, dois, tres...)
        for palavra, valor in numeros_extenso.items():
            if re.search(rf'\b{palavra}\b', mensagem_lower):
                return valor

        # Depois procura por algarismos (1, 2, 3...)
        numeros = re.findall(r'\d+', mensagem_lower)
        for n in numeros:
            if int(n) <= 100: # Evita pegar anos de filmes (ex: 2022)
                return int(n)

        return 5 # Valor padrão se não achar nada

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

    def extrair_generos_solicitados(self, mensagem: str) -> list:
        """
        Retorna uma lista de gêneros oficiais em inglês que o usuário pediu.
        Usa thefuzz para tolerar erros de digitação e mapeia português para inglês.
        """
        mensagem_lower = mensagem.lower()
        encontrados = set()
        
        # Ignora se ele estiver negando (ex: 'nao gosto de terror')
        if 'nao gosto' in mensagem_lower or 'não gosto' in mensagem_lower or 'odeio' in mensagem_lower:
            return []
        
        for genero_oficial, sinonimos in self.mapa_generos.items():
            if genero_oficial not in self.generos_unicos:
                continue
                
            for sinonimo in sinonimos:
                score = fuzz.partial_ratio(sinonimo, mensagem_lower)
                threshold = 85 if len(sinonimo) > 4 else 90
                
                if score >= threshold:
                    encontrados.add(genero_oficial)
                    break # já achou esse gênero, vai pro próximo
                    
        if encontrados:
            logger.info(f"Gêneros extraídos por fuzzy match: {list(encontrados)}")
            
        return list(encontrados)

    def buscar_por_genero(self, genero: str, top_n: int = 5, tipo_alvo: str = "Qualquer") -> list:
        """
        Busca títulos que contenham o gênero especificado.
        """
        if self.df.empty:
            return []
            
        filtro = self.df['genres'].str.contains(genero, case=False, na=False)
        if tipo_alvo != "Qualquer":
            filtro &= (self.df['type'] == tipo_alvo)
            
        resultados = self.df[filtro]
        if resultados.empty:
            return []
            
        # Embaralha os resultados
        resultados = resultados.sample(frac=1, random_state=None)
        
        return resultados.head(top_n)[['title', 'type', 'genres', 'year']].to_dict('records')

    def extrair_tipo_alvo(self, mensagem: str) -> str:
        """
        Detecta se o usuário pediu especificamente Filmes, Séries ou Qualquer.
        """
        msg = mensagem.lower()
        if "filme" in msg and "serie" not in msg and "série" not in msg:
            return "Filme"
        if ("serie" in msg or "série" in msg) and "filme" not in msg:
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
        if filmes_similares.empty:
            return []
            
        # Embaralha os resultados para trazer sugestões dinâmicas
        filmes_similares = filmes_similares.sample(frac=1, random_state=None)
        
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
            
            # Embaralha preservando a ordenação pelo score
            candidatos['random'] = [random.random() for _ in range(len(candidatos))]
            diferentes = candidatos.sort_values(['score', 'random']).drop(columns=['score', 'random'])
        else:
            # Embaralha os totalmente diferentes
            diferentes = diferentes.sample(frac=1, random_state=None)

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