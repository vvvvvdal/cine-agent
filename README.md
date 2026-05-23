# Cine Agent - Sistema de Recomendação de Filmes e Séries
### Trabalho de Programação Orientada à Objetos

Um Sistema de Recomendação inteligente construído com Python, aplicando o paradigma de **Orientação a Objetos (POO)**. O sistema utiliza a biblioteca Pandas para processamento de dados semiestruturados e integra um Agente de Inteligência Artificial (Google Gemini) via *Tool Calling* para gerar sinopses e recomendações personalizadas.

## Arquitetura do Projeto

O projeto foi desenhado focando na separação de responsabilidades (Clean Code) e modularidade:

* **`MotorDeRecomendacao` (Pandas):** Classe responsável por carregar o *dataset* CSV, higienizar os dados e aplicar o algoritmo de filtragem para encontrar títulos similares.
* **`AssistenteIA` (LLM/Gemini):** Orquestra a comunicação com a API do Gemini. Utiliza a técnica de *Function Calling* para acionar as classes internas do sistema de forma autônoma.
* **`ExportadorDeDocumentos`:** Classe utilitária dedicada à geração de arquivos físicos (PDF e TXT) a partir dos resultados gerados.
* **Frontend (Streamlit):** Interface conversacional fluida e reativa que isola a camada de visualização da lógica de negócios.

## Estrutura de Diretórios

```text
/cine-agent
├── .github/workflows/
│   └── pipeline.yml       # CI/CD com Pytest
├── src/
│   ├── app.py             # Interface visual (Streamlit)
│   ├── assistente.py      # Agente LLM
│   ├── exportador.py      # Geração de PDF/TXT
│   └── recomendador.py    # Lógica estrutural de busca (Pandas)
├── exports/               # Arquivos gerados pelo usuário (Ignorado no Git)
├── filmes.csv             # Base de dados (Mock de testes)
├── .env                   # Chave de API (Não versionado)
├── .dockerignore          # Otimização do container
├── docker-compose.yml     # Orquestração do ambiente
├── Dockerfile             # Receita da imagem
├── requirements.txt       # Dependências
└── README.md              # Documentação
```

## Como rodar

### 1. Pré-requisitos
Antes de começar, você vai precisar ter instalado na sua máquina:
* [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/)
* Uma chave de API válida do [Google AI Studio](https://aistudio.google.com/) (Gemini API)

### 2. Configurando o Ambiente
Clone este repositório e navegue até a pasta do projeto:
```bash
git clone [https://github.com/seu-usuario/cine-agent.git](https://github.com/seu-usuario/cine-agent.git)
cd cine-agent

```

Na raiz do projeto, crie um arquivo chamado `.env` e insira a sua chave da API do Google. O exemplar dele é o `.env.example`:

```env
GEMINI_API_KEY=sua_chave_aqui_gerada_no_google

```

Certifique-se também de que o arquivo de dados `filmes.csv` está na raiz do projeto contendo as colunas `title` e `genres` (esse é o banco de dados de filmes e séries que a IA vai consultar).

### 3. Subindo a Aplicação

Com o `.env` configurado, abra o terminal na raiz do projeto e execute o comando abaixo para construir a imagem e subir o container:

```bash
docker compose up -d --build

```

> **Nota:** O parâmetro `-d` roda o sistema em background (modo *detached*), deixando seu terminal livre. O `--build` garante que o Docker leia as últimas alterações do seu código.

### 4. Acessando o Sistema

Assim que o container estiver rodando, abra o seu navegador e acesse:
👉 **http://localhost:8501**

### 5. Comandos Úteis (Manutenção)

* **Ver os logs do sistema e da IA em tempo real:**
```bash
docker logs -f cine_agent

```

* **Derrubar o sistema e desligar o container:**
```bash
docker compose down

```