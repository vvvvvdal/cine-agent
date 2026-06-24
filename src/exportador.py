from fpdf import FPDF
import logging

logger = logging.getLogger(__name__)

class Exportador:
    def __init__(self):
        """
        Construtor. O exportador opera 100% em memória, devolvendo bytes diretamente.
        Não é necessário criar ou manter pastas de exportação.
        """
        logger.info("Exportador inicializado. Modo de operação: em memória.")

    def gerar_pdf_relatorio(self, relatorio: dict) -> bytes:
        """
        Gera um PDF estruturado a partir dos dados do CSV + sinopses do Ollama.
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(20, 20, 20)

            # Cabeçalho
            pdf.set_font("Helvetica", style="B", size=16)
            pdf.cell(0, 10, text=self._lat("Cine Agent"), ln=True, align="C")
            pdf.set_font("Helvetica", size=11)
            pdf.cell(0, 7, text=self._lat("Relatório de Recomendações"), ln=True, align="C")
            pdf.ln(4)

            # Linha separadora
            pdf.set_draw_color(180, 180, 180)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)

            # Bloco da fonte
            titulo_fonte = relatorio.get("titulo_fonte", "")
            tipo_fonte = relatorio.get("tipo_fonte", "")
            genero_fonte = relatorio.get("genero_fonte", "")
            ano_fonte = relatorio.get("ano_fonte", "")

            pdf.set_font("Helvetica", style="B", size=12)
            pdf.cell(40, 8, text=self._lat("Conteúdo fonte:"))
            pdf.set_font("Helvetica", size=12)
            pdf.cell(0, 8, text=self._lat(f"{titulo_fonte} ({ano_fonte})"), ln=True)

            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(100, 100, 100)
            generos_formatados = genero_fonte.replace("|", ", ") if genero_fonte else ""
            pdf.cell(0, 6, text=self._lat(f"Tipo: {tipo_fonte}  |  Gêneros: {generos_formatados}"), ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(6)

            # Cabeçalho da lista com modo
            recomendacoes = relatorio.get("recomendacoes", [])
            modo = relatorio.get("modo", "similares")
            
            if modo == "solicitados":
                texto_cabecalho = "Conteúdos mistos solicitados:"
            else:
                texto_cabecalho = f"Conteúdos {modo} solicitados:"

            pdf.set_font("Helvetica", style="B", size=13)
            pdf.cell(0, 8, text=self._lat(texto_cabecalho), ln=True)
            pdf.ln(3)

            # Cada recomendação
            for i, item in enumerate(recomendacoes, start=1):
                titulo_rec = item.get("titulo", "")
                tipo_rec = item.get("tipo", "")
                generos_rec = item.get("generos", "").replace("|", ", ")
                ano_rec = item.get("year", "")
                sinopse = item.get("sinopse", "")

                # Título em negrito
                pdf.set_font("Helvetica", style="B", size=11)
                pdf.cell(0, 7, text=self._lat(f"{i}. {titulo_rec} ({ano_rec})"), ln=True)

                # Tipo e gêneros em cinza
                pdf.set_font("Helvetica", size=10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 6, text=self._lat(f"   {tipo_rec}  |  {generos_rec}"), ln=True)

                # Sinopse
                if sinopse:
                    pdf.set_font("Helvetica", style="I", size=10)
                    pdf.set_text_color(60, 60, 60)
                    pdf.multi_cell(0, 5, text=self._lat(f"   {sinopse}"))

                pdf.set_text_color(0, 0, 0)
                pdf.ln(3)

            logger.info(f"Relatório PDF gerado com {len(recomendacoes)} recomendações.")
            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"Erro ao gerar relatorio PDF: {e}")
            return b""

    def _lat(self, texto: str) -> str:
        """
        Substitui caracteres problemáticos (como aspas duplas inteligentes geradas por LLMs)
        e converte para latin-1 para compatibilidade com fpdf2 sem fontes customizadas.
        """
        t = texto.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        t = t.replace("–", "-").replace("—", "-")
        return t.encode('latin-1', 'replace').decode('latin-1')