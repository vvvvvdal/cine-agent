FROM python:3.10-slim

LABEL project="cine_agent"
LABEL description="Sistema de Recomendação de Filmes/Séries com IA local via Ollama"

WORKDIR /app

ENV PROJECT_NAME="cine_agent"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Porta padrão onde o Streamlit vai rodar
EXPOSE 8501

# Comando de inicialização do Streamlit
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]