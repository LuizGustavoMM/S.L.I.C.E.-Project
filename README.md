# S.L.I.C.E. - Surgical LLM Interface for Code Editing

O **S.L.I.C.E.** é uma interface leve, rápida e cirúrgica para criação e edição automatizada de código utilizando Inteligência Artificial. Ele conecta o seu repositório local diretamente aos modelos mais avançados e rápidos do mercado através da API da Groq (Llama 3.3 70B).

Este projeto nasceu de um pivô arquitetural. Inicialmente concebido como um Sistema Multi-Agente (MAS) rodando localmente, esbarramos nos altos custos computacionais e limitações de memória (VRAM) exigidos por frameworks de agentes. A solução foi **democratizar o projeto**: removemos as camadas de abstração, eliminamos a necessidade de uma GPU dedicada (como uma RTX 4060 ou 4090) e criamos um script Python puro com tratamento de resiliência. Qualquer desenvolvedor, em qualquer máquina, pode rodar esta ferramenta.

## ✨ Como Funciona (Os Três Modos)

A interface é inteligente e define a sua intenção automaticamente com base nos campos que você preenche:

1. **Modo Edição (Cirúrgico):** Você aponta um arquivo existente e diz o que quer mudar. A ferramenta lê o arquivo, envia para a IA reescrever com as novas regras e sobrescreve o arquivo no seu disco local automaticamente.
2. **Modo Criação (Scaffolding):** Você digita o nome de um arquivo que *ainda não existe* e dá a instrução. A ferramenta gera o código do zero e já salva o novo arquivo na pasta correta do seu projeto.
3. **Modo Criação Livre:** Você não aponta nenhum arquivo, apenas faz um pedido de código solto. A ferramenta atua como um chat avançado, exibindo o código na tela para você copiar sem poluir seus diretórios.

## 🚀 Resiliência de API (Rate Limit Handling)

Como utilizamos a tier gratuita da Groq, o sistema possui **Backoff Exponencial** nativo. Se você pedir alterações gigantescas que estourem os limites de "Tokens Por Minuto" (TPM) da API, o S.L.I.C.E. não vai crashar. Ele interceptará o erro HTTP 429, pausará a execução silenciosamente por 60 segundos e tentará novamente de forma automática.

## 🛠️ Estrutura do Projeto

A arquitetura atual é 100% conteinerizada e enxuta, consumindo mínimos recursos da máquina host.

```text
slice-project/
├── .env                     # Variáveis de ambiente (sua chave da Groq)
├── docker-compose.yml       # Orquestração do container Web
├── workspace/               # Volume montado para colocar os seus repositórios reais
│   └── .gitignore           # Configurado para ignorar o rastreio do código injetado
└── webui/
    ├── Dockerfile           # Imagem da interface
    ├── requirements.txt     # Dependências (Streamlit, Groq)
    └── app.py               # Lógica de extração e UI
```

## ⚙️ Pré-requisitos e Instalação

1. Você precisa ter o **Docker** e o **Docker Compose** instalados (no Windows, o Docker Desktop com WSL2 funciona perfeitamente).
2. Crie uma conta no [Groq Console](https://console.groq.com) e gere uma API Key.
3. Na raiz do projeto, crie um arquivo chamado `.env` e adicione a sua chave:

```env
GROQ_API_KEY=sua_chave_secreta_aqui
```

## ▶️ Como Rodar

1. Coloque o código-fonte que você deseja trabalhar dentro da pasta `workspace`.
2. Abra o terminal na raiz do projeto e suba o serviço:

```bash
docker compose up -d --build
```

3. Acesse a interface web pelo navegador: `http://localhost:8501`.
4. Preencha os campos de "Pasta do Projeto", "Arquivo Alvo" e a "Instrução" e clique em **Executar Tarefa**.
5. Revise as alterações feitas pela IA no seu editor de código favorito (ex: VS Code) e faça os commits manualmente para garantir a segurança.

## 🛑 Para Parar a Aplicação

```bash
docker compose down
```
