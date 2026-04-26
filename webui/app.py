import os
import streamlit as st
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama
from crewai_tools import DirectoryReadTool, FileReadTool
from langchain.tools import tool

os.environ["OTEL_SDK_DISABLED"] = "true"

# 1. Criando nossa Custom Tool para escrever arquivos
@tool("Escritor de Arquivos")
def custom_file_writer(file_path: str, content: str) -> str:
    """
    Ferramenta util para criar ou sobrescrever arquivos de codigo.
    Recebe o caminho completo do arquivo (file_path) e o codigo fonte (content).
    """
    try:
        # Garante que a pasta exista antes de criar o arquivo
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Arquivo salvo com sucesso em: {file_path}"
    except Exception as e:
        return f"Erro ao escrever o arquivo: {str(e)}"

st.set_page_config(page_title="MAS Interface", layout="wide")
st.title("Interface de Comando - Multi-Agent System")

llm = Ollama(
    model="llama3", 
    base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
    num_ctx=8192
)

base_path = "/workspace"
project_folder = st.text_input("Nome da pasta do projeto dentro de /workspace:", "meu-projeto")
user_task = st.text_area("Descreva a tarefa de programação:")

if st.button("Iniciar MAS"):
    full_path = os.path.join(base_path, project_folder)
    
    if not os.path.exists(full_path):
        st.error(f"O diretório {full_path} não foi encontrado.")
    elif not user_task.strip():
        st.warning("Forneça uma descrição da tarefa.")
    else:
        st.info(f"Iniciando agentes no diretório: {full_path}")
        
        # 2. Instanciando as ferramentas de leitura
        directory_tool = DirectoryReadTool(directory=full_path)
        file_read_tool = FileReadTool()
        
        researcher = Agent(
            role="Pesquisador de Codigo",
            goal="Analisar a estrutura do projeto e entender os arquivos existentes.",
            backstory="Um analista focado em entender a arquitetura, ler os arquivos corretos e planejar onde as mudancas devem ocorrer.",
            verbose=True,
            allow_delegation=False,
            tools=[directory_tool, file_read_tool],
            llm=llm
        )

        coder = Agent(
            role="Programador",
            goal="Escrever codigo funcional e limpo com base na pesquisa e nos requisitos solicitados.",
            backstory="Um desenvolvedor experiente que escreve codigo de alta qualidade. Modifica arquivos existentes ou cria novos usando as ferramentas apropriadas.",
            verbose=True,
            allow_delegation=False,
            # 3. Entregando a nossa Custom Tool para o programador
            tools=[directory_tool, file_read_tool, custom_file_writer],
            llm=llm
        )

        reviewer = Agent(
            role="Validador Sênior",
            goal="Revisar o codigo gerado, garantir a integridade e sugerir ou aplicar correcoes finais.",
            backstory="Um arquiteto de software criterioso. Verifica padroes, logica e evita bugs antes de considerar a tarefa concluida.",
            verbose=True,
            allow_delegation=False,
            # 4. Entregando a nossa Custom Tool para o validador
            tools=[directory_tool, file_read_tool, custom_file_writer],
            llm=llm
        )

        task1 = Task(
            description=f"Leia o diretorio do projeto localizado em {full_path}. Identifique quais arquivos precisam ser lidos e modificados para cumprir a seguinte exigencia: {user_task}",
            expected_output="Um relatorio listando os arquivos relevantes e o contexto atual do codigo.",
            agent=researcher
        )

        task2 = Task(
            description=f"Usando o relatorio do pesquisador, implemente a solucao para: {user_task}. Use a ferramenta 'Escritor de Arquivos' para criar ou alterar arquivos em {full_path}. O codigo deve estar completo e funcional.",
            expected_output="Os arquivos modificados ou criados salvos no disco e um resumo das alteracoes feitas.",
            agent=coder
        )

        task3 = Task(
            description=f"Revise as alteracoes feitas no diretorio {full_path} pela tarefa anterior. Valide se a logica atende a solicitacao original: {user_task}. Se houver erros, use a ferramenta 'Escritor de Arquivos' para corrigir os arquivos.",
            expected_output="Um veredito final atestando que o codigo esta correto e os arquivos finais em disco.",
            agent=reviewer
        )

        crew = Crew(
            agents=[researcher, coder, reviewer],
            tasks=[task1, task2, task3],
            process=Process.sequential,
            verbose=2
        )

        with st.spinner("Agentes trabalhando... acompanhe o terminal para detalhes completos."):
            result = crew.kickoff()
            
        st.success("Tarefa concluida!")
        st.markdown("### Resultado Final do Validador:")
        st.write(result)