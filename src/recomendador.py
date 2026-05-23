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
            self.df = pd.read_csv(caminho_csv) # Colunas 'title' e 'genres'
            self.df.dropna(subset=['title', 'genres'], inplace=True)# Remove linhas vazias
            
            logger.info(f"Base carregada com sucesso. {len(self.df)} filmes disponíveis.")
            
        except FileNotFoundError:
            logger.error(f"Arquivo CSV não encontrado no caminho: {caminho_csv}")

            self.df = pd.DataFrame() # Cria um DataFrame vazio

    def buscar_similares(self, nome_filme: str, top_n: int = 5) -> list:
        """
        Método que recebe o nome de um filme e retorna uma lista de similares.
        Essa é a função que o Gemini chama no Tool Calling.
        """
        if self.df.empty:
            logger.warning("Tentativa de busca com a base de dados indisponível.")
            return ["[ERRO] Base de dados indisponível."]

        filme_alvo = self.df[self.df['title'].str.contains(nome_filme, case=False, na=False)] # Busca o filme na base
        
        if filme_alvo.empty:
            logger.info(f"Busca sem resultados para o filme: '{nome_filme}'")
            return [f"Infelizmente não achei '{nome_filme}' na nossa base."]
        
        genero_principal = filme_alvo.iloc[0]['genres'].split('|')[0] # Lógica inicial de Similaridade (Para o MVP)
        nome_filme_alvo = filme_alvo.iloc[0]['title'] # Pega o primeiro gênero do filme encontrado
        
        filmes_similares = self.df[ # Filtra filmes do mesmo gênero, excluindo o próprio filme que o usuário digitou
            (self.df['title'] != nome_filme_alvo) & 
            (self.df['genres'].str.contains(genero_principal, case=False, na=False))
        ]

        lista_resultados = filmes_similares.head(top_n)['title'].tolist() # Retorna apenas os nomes dos Top N filmes como uma lista
        
        logger.info(f"Recomendações geradas para '{nome_filme_alvo}' (Gênero: {genero_principal}): {lista_resultados}")
        
        return lista_resultados