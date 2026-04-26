# Multi-Agent System (MAS) - Engenheiro de Software Local

Este projeto implementa uma equipe de agentes de inteligência artificial autônomos utilizando CrewAI e Ollama para automação de tarefas de programação. O sistema é composto por três agentes (Pesquisador, Programador e Validador) que trabalham de forma sequencial para analisar, implementar e revisar código em repositórios locais.

### Otimização de Hardware

A stack foi configurada para extrair o máximo desempenho da seguinte configuração:
* **GPU:** NVIDIA GeForce RTX 4060 (8GB VRAM) - Utilizada para inferência acelerada via CUDA.
* **CPU:** AMD Ryzen 5 5600X.
* **RAM:** 16GB DDR4 3200 MHz (Configurado para operar dentro do limite de 15GB-16GB disponível).
* **SO:** Windows 11 com Docker Desktop e WSL2 habilitado.

O uso do modelo Gemma via Ollama com aceleração de GPU permite que o processamento dos agentes ocorra localmente com alta velocidade de geração de tokens, mantendo a privacidade dos dados do repositório.

### Pré-requisitos

* Docker Desktop instalado com a opção "Use the WSL 2 based engine" ativada.
* Drivers da NVIDIA atualizados no Windows (Game Ready ou Studio).
* Integração do Docker com a sua distro WSL padrão habilitada nas configurações do Docker Desktop.

### Estrutura do Projeto

```text
mas-project/
├── docker-compose.yml       # Orquestração dos containers e automação de modelos
├── workspace/               # Volume montado para seus repositórios
│   └── .gitignore           # Configurado para ignorar conteúdos dentro do workspace
└── webui/
    ├── Dockerfile           # Build da imagem da interface
    ├── requirements.txt     # Bibliotecas Python (CrewAI, Streamlit, etc)
    └── app.py               # Lógica de orquestração dos agentes
```

### Instalação e Execução

1. Certifique-se de que a pasta `workspace` existe na raiz do projeto.
2. Abra o PowerShell na pasta raiz `mas-project`.
3. Suba os serviços:
   ```powershell
   docker compose up -d
   ```
4. O sistema iniciará o download automático do modelo Gemma no primeiro boot através do container `ollama-pull`.
5. Verifique o status da GPU no container:
   ```powershell
   docker exec -it mas-ollama nvidia-smi
    ```

### Como Comandar a MAS

A interação é feita exclusivamente pela Web UI para garantir dinamismo entre diferentes repositórios sem reiniciar containers.

1. Acesse `http://localhost:8501` no navegador.
2. No campo **Nome da pasta do projeto**, digite o nome do diretório que você colocou dentro de `workspace/`.
3. No campo **Tarefa**, descreva a implementação ou correção desejada (ex: "Adicione um método de busca por ID na classe ProdutoService").
4. Clique em **Iniciar MAS**.
5. O console do navegador e os logs do Docker mostrarão o pensamento dos agentes:
   - **Agente Pesquisador:** Varre o diretório e lê os arquivos necessários.
   - **Agente Programador:** Realiza as alterações nos arquivos físicos.
   - **Agente Validador:** Revisa o código escrito e aplica correções se encontrar erros.

### Fluxo de Revisão e Commit

Para garantir a segurança do seu código, a MAS não possui permissão para realizar commits automáticos. 

1. Após a finalização da tarefa na Web UI, abra o seu editor de código (IDE).
2. Revise as alterações feitas diretamente nos arquivos dentro da pasta `workspace`.
3. Utilize o seu terminal Git local para realizar o `git add`, `git commit` e `git push` manualmente após validar a solução.

### Gerenciamento de Modelos

Para adicionar outros modelos mini à stack:
```powershell
docker exec -it mas-ollama ollama pull [nome-do-modelo]
```