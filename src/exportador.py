from fpdf import FPDF
import os
import logging

logger = logging.getLogger(__name__)

class Exportador:
    def __init__(self, pasta_saida: str = "exports"):
        """
        Construtor. Garante que a pasta de exportação exista no sistema.
        """
        self.pasta_saida = pasta_saida
        os.makedirs(self.pasta_saida, exist_ok=True)
        logger.info(f"Exportador inicializado. Pasta de destino: {self.pasta_saida}")

    def gerar_txt(self, conteudo: str, nome_arquivo: str = "recomendacoes.txt") -> str:
        """
        Salva o conteúdo em um arquivo .txt e retorna o caminho.
        """
        caminho_completo = os.path.join(self.pasta_saida, nome_arquivo)
        try:
            with open(caminho_completo, "w", encoding="utf-8") as f:
                f.write(conteudo)
            logger.info(f"TXT gerado com sucesso em: {caminho_completo}")
            return caminho_completo
        except Exception as e:
            logger.error(f"Erro ao gerar TXT: {e}")
            return ""

    def gerar_pdf(self, conteudo: str, nome_arquivo: str = "recomendacoes.pdf") -> str:
        """
        Gera um arquivo PDF com o conteúdo e retorna o caminho.
        """
        caminho_completo = os.path.join(self.pasta_saida, nome_arquivo)
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            texto_tratado = conteudo.encode('latin-1', 'replace').decode('latin-1') # Tratamento de encoding para não quebrar acentos no PDF
            
            pdf.multi_cell(0, 10, txt=texto_tratado) # "multi_cell" permite quebra de linha automática para textos longos (como sinopses)
            
            pdf.output(caminho_completo)
            logger.info(f"PDF gerado com sucesso em: {caminho_completo}")
            return caminho_completo
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            return ""