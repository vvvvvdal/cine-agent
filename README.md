## Cine Agent: Sistema de Recomendação de Filmes e Séries

**Integrantes:**
* Felipe Gonçalves Vidal
* Rafael José de Souza Marques
* João Henrique Emiliano Bittencourt
* Paulo de Tarso Rezende Lôbo

---

## Fundamentação teórica e Decisões de projeto

Este projeto foi estruturado seguindo rigorosamente os seguintes pilares acadêmicos e técnicos:

* **Paradigma de Programação Orientada a Objetos (POO):** Todo o sistema é organizado em classes com responsabilidades bem definidas. A classe `Recomendador` é responsável pelo carregamento e processamento dos dados, a `Agente` orquestra a camada de IA e a `Exportador` cuida da geração de relatórios. A comunicação entre elas acontece por **composição**: o `Agente` recebe uma instância de `Recomendador` no seu construtor, aplicando **injeção de dependência**.
* **Processamento de Dados com Pandas:** O coração do motor de recomendação é a biblioteca **Pandas**, utilizada para ler, limpar e filtrar o dataset CSV semi-estruturado (`conteudo.csv`). As buscas por similaridade de gêneros são feitas inteiramente via operações vetorizadas do DataFrame, sem loops manuais.
* **Inteligência Artificial (LLM Local - Ollama):** O sistema utiliza o modelo local **qwen2.5:1.5b** como cérebro de processamento de linguagem natural (NLP). A IA atua na classificação inteligente da intenção do usuário, descobrindo com precisão se a requisição busca obras "SIMILARES" ou "DIFERENTES" baseada no contexto da mensagem.
* **Tecnologias (Python + Streamlit + Docker):** O **Python** atua como linguagem principal, o **Streamlit** fornece a interface web conversacional sem necessidade de frontend separado, e o **Docker** garante portabilidade total para deploy em qualquer ambiente.

---

## Sobre o sistema

Um sistema de recomendação via interface web conversacional, desenvolvido em Python com Streamlit. O projeto permite que o usuário descreva seus gostos em linguagem natural e receba sugestões personalizadas e cruzadas de filmes e séries baseadas em seus gêneros preferidos.

### Funcionalidades

**1. Motor de Recomendação (`Recomendador`)**
* **Carregamento do Dataset:** Leitura automática do arquivo `conteudo.csv` contendo dezenas de títulos com seus respectivos gêneros e anos de lançamento.
* **Limpeza de Dados:** Remoção automática de linhas com campos vazios (`title` ou `genres`) via `dropna()` do Pandas.
* **Lógica de Intersecção:** Utiliza a teoria dos conjuntos para encontrar obras similares (com ao menos um gênero em comum) e diferentes (com zero gêneros em comum).
* **Processamento de Multicamadas:** Consegue ler requisições compostas, separando "me de 3 parecidos e 3 diferentes" em múltiplas pipelines de execução autônoma.
* **Travas de Segurança e Validação:** Bloqueia automaticamente requisições confusas com mais de um título pivô ou múltiplos gêneros na mesma frase e impõe um limite de 10 recomendações por vez, garantindo precisão nos resultados e na quebra de página do PDF.
* **Busca Direta por Gêneros e Fuzzy Matching:** Permite buscar recomendações baseadas inteiramente em gêneros (ex: "5 filmes de terror"), utilizando a biblioteca `thefuzz` para interpretar e tolerar pequenos erros de digitação (ex: "ficao cientifica" -> Sci-Fi).
* **Aleatoriedade Dinâmica:** Utiliza `.sample()` do Pandas combinado com pesos matemáticos para garantir que as indicações sejam embaralhadas, oferecendo sugestões frescas a cada interação.

**2. Agente de IA (`Agente`)**
* **Configuração da IA Local:** Utiliza a biblioteca oficial do Ollama para inferir diretamente a partir do host da máquina.
* **Classificação NLP:** Aplica a Inteligência Artificial exclusivamente como classificador lógico, impedindo alucinações de texto e mantendo o processamento direto e veloz.
* **Gerenciamento Inteligente de Chats:** Mantém um histórico interativo da conversa atual no Streamlit (Session State), permitindo que o bot lembre do contexto da sessão.

**3. Exportação de Relatórios (`Exportador`)**
* **Geração de PDF em Memória:** Constrói documentos formatados usando a biblioteca `fpdf2` e devolve os bytes diretamente para o navegador do usuário, dispensando a gravação física no disco.
* **Estruturação Visual:** Aplica automaticamente cabeçalhos e formatações ricas (negritos, cores em cinza, itálicos) com tratamento nativo de _encoding_ (`latin-1`) para caracteres especiais e acentos.

**4. Interface Web (`app.py`)**
* **Chat Interativo:** Interface conversacional via Streamlit com campo de input e histórico de mensagens renderizado em tempo real.
* **Estado da Sessão:** Utiliza `st.session_state` para persistir o histórico de mensagens entre interações.
* **Cache de Recursos:** O sistema é inicializado uma única vez via `@st.cache_resource`, evitando recarregamento desnecessário do modelo e dataset.

---

## Conceitos de POO aplicados

| Conceito | Aplicação no Projeto |
|---|---|
| **Classe e Objeto** | `Recomendador`, `Agente` e `Exportador` são classes instanciadas em `app.py` |
| **Encapsulamento** | Atributos como `self.df`, `self.modelo` e `self.chat` são internos às classes |
| **Composição** | `Agente` contém uma instância de `Recomendador` (relação "tem-um") |
| **Construtores** | Cada classe inicializa seu estado no construtor (conexão API, leitura CSV, criação de pasta) |
| **Tratamento de Exceções** | `try/except` em todas as operações críticas (API, leitura de arquivo, geração de PDF) |
| **Responsabilidade Única** | Cada classe resolve exatamente um problema do domínio |

---

## Arquitetura e Estrutura de Arquivos

* **Paradigma:** Orientado a Objetos com separação em camadas (Apresentação → IA → Dados → Exportação).
* **Agente de IA:** O Ollama atua como processador NLP (Natural Language Processing) interpretando e classificando a intenção do usuário isoladamente.
* **Observabilidade:** Sistema de logging estruturado com `logging` do Python (Data/Hora, Módulo, Nível, Mensagem) em todas as classes.

```text
cine-agent/
├── src/
│   ├── app.py                  # Ponto de entrada: Interface Streamlit e fluxo do chat
│   ├── agente.py               # Classe Agente: Agente com IA Local (Ollama)
│   ├── recomendador.py         # Classe Recomendador: Carregamento CSV e algoritmo de similaridade
│   └── exportador.py           # Classe Exportador: Geração de relatórios PDF estruturados
│
├── exports/                    # Pasta contendo exemplos de PDFs já gerados
├── conteudo.csv                # Dataset semi-estruturado (65 títulos de filmes e séries)
├── requirements.txt            # Dependências Python do projeto
├── Dockerfile                  # Imagem Docker (Python 3.10-slim)
├── docker-compose.yml          # Orquestração de containers com variáveis de ambiente
└── .gitignore                  # Arquivos ignorados pelo Git
```

---

## Dataset (`conteudo.csv`)

O arquivo CSV semi-estruturado contém o catálogo utilizado pelo motor de recomendação:

| Coluna | Tipo | Descrição | Exemplo |
|---|---|---|---|
| `title` | `string` | Nome do título | `Better Call Saul` |
| `type` | `string` | Classificação do conteúdo | `Filme` ou `Série` |
| `genres` | `string` | Gêneros separados por pipe (`\|`) | `Crime\|Drama\|Thriller` |

O dataset contém 65 títulos, entre filmes e séries. Para expandir a base, basta adicionar novas linhas seguindo o mesmo formato CSV.

---

## Como executar o projeto

**Pré-requisitos Iniciais:** 
* Ter o [Docker](https://www.docker.com/) e Docker Compose instalados.
* Ter o [Ollama](https://ollama.com/) instalado na sua máquina host.

**Passo 1: Clonar o repositório**
Baixe o código-fonte e entre na pasta do projeto:
```bash
git clone https://github.com/seu-usuario/cine-agent.git
cd cine-agent
```

**Passo 2: Baixar e rodar o modelo de IA**
O sistema utiliza o modelo `qwen2.5:1.5b` rodando localmente na sua máquina. Para garantir que ele está disponível, abra um terminal no seu computador e execute:
```bash
ollama run qwen2.5:1.5b
```
*Obs: Após o modelo baixar e aparecer no terminal, você pode digitar `/bye` para fechar, pois ele ficará disponível em background.*

**Passo 3: Executar via Docker**
Com o Ollama pronto e o modelo baixado, inicie os containers da aplicação:
```bash
docker compose up --build
```

**Passo 4: Acessar o sistema**
Abra o seu navegador e acesse:
**http://localhost:8501**
