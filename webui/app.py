import os
import re
import streamlit as st
from groq import Groq

# Desabilita telemetria do Streamlit
os.environ["OTEL_SDK_DISABLED"] = "true"

st.set_page_config(page_title="Editor LLM Direto", layout="wide")
st.title("Editor de Arquivos LLM - Modo Cirúrgico")

# Inicializacao do cliente Groq
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY nao encontrada nas variaveis de ambiente (.env).")
    st.stop()

client = Groq(api_key=api_key)

base_path = "/workspace"

st.markdown("### Configuração da Tarefa")
col1, col2 = st.columns([1, 2])

with col1:
    project_folder = st.text_input("Pasta do Projeto:", "meu-projeto")
    target_file = st.text_input("Arquivo Alvo (ex: src/main.py):", "main.py")

with col2:
    user_task = st.text_area("O que deve ser alterado neste arquivo?", height=130)

def extrair_codigo(resposta_llm):
    """
    Usa Regex para extrair apenas o bloco de codigo da resposta, 
    ignorando textos conversacionais que quebram a compilacao.
    """
    padrao = r"```[\w]*\n(.*?)```"
    match = re.search(padrao, resposta_llm, re.DOTALL)
    if match:
        return match.group(1).strip()
    return resposta_llm.strip() # Fallback se a LLM nao usar markdown

if st.button("Executar Modificação"):
    full_file_path = os.path.join(base_path, project_folder, target_file)
    
    if not os.path.exists(full_file_path):
        st.error(f"Arquivo nao encontrado em: {full_file_path}")
    elif not user_task.strip():
        st.warning("Descreva o que precisa ser feito.")
    else:
        # 1. Leitura do arquivo original
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                codigo_original = f.read()
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
            st.stop()

        st.info(f"Processando {target_file} via Groq (Llama 3.1 70B)...")
        
        # 2. Engenharia de Prompt Estrita
        system_prompt = """Você é um Engenheiro de Software Sênior atuando como um compilador e editor de código.
Sua única função é receber um código-fonte existente e uma instrução de alteração, e retornar o CÓDIGO COMPLETO reescrito e atualizado.
REGRAS ABSOLUTAS:
1. NÃO explique o que você fez.
2. NÃO use frases como "Aqui está o código" ou "Espero que isso ajude".
3. Envolva toda a sua resposta em UM ÚNICO bloco de markdown (```).
4. Retorne o arquivo inteiro, não apenas a parte modificada, para que o sistema possa sobrescrever o arquivo original diretamente."""

        user_prompt = f"INSTRUÇÃO DE ALTERAÇÃO:\n{user_task}\n\nCÓDIGO ORIGINAL:\n```\n{codigo_original}\n```"

        # 3. Chamada de API Direta
        try:
            with st.spinner("LLM reescrevendo o arquivo..."):
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model="llama-3.1-70b-versatile",
                    temperature=0.1, # Temperatura baixa para garantir determinismo e reduzir alucinacoes
                )
            
            resposta_bruta = chat_completion.choices[0].message.content
            
            # 4. Extracao e Salvamento
            codigo_final = extrair_codigo(resposta_bruta)
            
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(codigo_final)
                
            st.success("Arquivo sobrescrito com sucesso!")
            
            with st.expander("Ver Código Atualizado"):
                st.code(codigo_final)
                
        except Exception as e:
            st.error(f"Falha na comunicacao com a API ou no processamento: {e}")