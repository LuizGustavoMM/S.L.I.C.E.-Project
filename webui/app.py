import os
import streamlit as st
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
from crewai_tools import DirectoryReadTool, FileReadTool
from langchain.tools import tool

os.environ["OTEL_SDK_DISABLED"] = "true"

@tool("Escritor de Arquivos")
def custom_file_writer(file_path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Arquivo salvo com sucesso em: {file_path}"
    except Exception as e:
        return f"Erro ao escrever o arquivo: {str(e)}"

st.set_page_config(page_title="MAS Interface", layout="wide")
st.title("Interface de Comando - Multi-Agent System")

groq_api_key = os.environ.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("GROQ_API_KEY nao encontrada nas variaveis de ambiente.")
    st.stop()

llm_researcher = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=groq_api_key
)

llm_coder = ChatGroq(
    temperature=0,
    model_name="llama-3.1-70b-versatile",
    api_key=groq_api_key
)

base_path = "/workspace"
project_folder = st.text_input("Nome da pasta do projeto dentro de /workspace:", "meu-projeto")
user_task = st.text_area("Descreva a tarefa de programacao:")

if st.button("Iniciar MAS"):
    full_path = os.path.join(base_path, project_folder)
    
    if not os.path.exists(full_path):
        st.error(f"O diretorio {full_path} nao foi encontrado.")
    elif not user_task.strip():
        st.warning("Forneca uma descricao da tarefa.")
    else:
        st.info(f"Iniciando agentes no diretorio: {full_path}")
        
        directory_tool = DirectoryReadTool(directory=full_path)
        file_read_tool = FileReadTool()
        
        researcher = Agent(
            role="Pesquisador de Codigo",
            goal="Analisar a estrutura do projeto e entender os arquivos existentes.",
            backstory="Analista focado em arquitetura. Le apenas os arquivos estritamente necessarios para a tarefa.",
            verbose=True,
            allow_delegation=False,
            tools=[directory_tool, file_read_tool],
            llm=llm_researcher
        )

        coder = Agent(
            role="Programador",
            goal="Escrever codigo funcional com base na pesquisa.",
            backstory="Desenvolvedor senior que escreve codigo e o salva no disco usando a ferramenta correta.",
            verbose=True,
            allow_delegation=False,
            tools=[directory_tool, file_read_tool, custom_file_writer],
            llm=llm_coder
        )

        reviewer = Agent(
            role="Validador Senior",
            goal="Revisar o codigo gerado e aplicar correcoes.",
            backstory="Arquiteto criterioso. Corrige falhas logicas e valida a execucao da tarefa.",
            verbose=True,
            allow_delegation=False,
            tools=[directory_tool, file_read_tool, custom_file_writer],
            llm=llm_coder
        )

        task1 = Task(
            description=f"Liste o diretorio {full_path}. Leia o conteudo apenas dos arquivos fundamentais para esta exigencia: {user_task}. Nao leia arquivos desnecessarios para poupar o limite de tokens.",
            expected_output="Relatorio de arquivos e trechos de codigo relevantes.",
            agent=researcher
        )

        task2 = Task(
            description=f"Implemente a solucao baseada no relatorio anterior para: {user_task}. Obrigatoriamente use o Escritor de Arquivos para salvar em {full_path}.",
            expected_output="Resumo das alteracoes feitas em disco.",
            agent=coder
        )

        task3 = Task(
            description=f"Inspecione os arquivos alterados em {full_path}. Valide a logica para: {user_task}. Se achar erro, sobrescreva o arquivo corrigindo.",
            expected_output="Veredito final aprovando as mudancas.",
            agent=reviewer
        )

        crew = Crew(
            agents=[researcher, coder, reviewer],
            tasks=[task1, task2, task3],
            process=Process.sequential,
            verbose=2
        )

        with st.spinner("Agentes processando na Groq... acompanhe o terminal."):
            try:
                result = crew.kickoff()
                st.success("Tarefa concluida!")
                st.markdown("### Resultado Final:")
                st.write(result)
            except Exception as e:
                st.error("Falha na execucao.")
                st.write(e)