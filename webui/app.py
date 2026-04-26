import os
import re
import time
import streamlit as st
from groq import Groq, RateLimitError

os.environ["OTEL_SDK_DISABLED"] = "true"

st.set_page_config(page_title="Editor LLM Direto", layout="wide")
st.title("Editor de Arquivos LLM - Modo Cirurgico")

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY nao encontrada nas variaveis de ambiente (.env).")
    st.stop()

client = Groq(api_key=api_key)

base_path = "/workspace"

st.markdown("### Configuracao da Tarefa")
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
    return resposta_llm.strip()

def chamar_llm_com_espera(client, system_prompt, user_prompt, max_tentativas=3):
    """
    Tenta chamar a API. Se bater no limite de uso da Groq (Rate Limit),
    pausa a execucao, aguarda 60 segundos e tenta de novo.
    """
    tentativa = 0
    while tentativa < max_tentativas:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
            )
            return chat_completion.choices[0].message.content
            
        except RateLimitError as e:
            tentativa += 1
            st.warning(f"Limite de velocidade da Groq atingido! Pausando por 60 segundos... (Tentativa {tentativa}/{max_tentativas})")
            time.sleep(60)
            
        except Exception as e:
            st.error(f"Erro inesperado na API: {e}")
            break
            
    return None


if st.button("Executar Modificacao"):
    full_file_path = os.path.join(base_path, project_folder, target_file)
    
    if not os.path.exists(full_file_path):
        st.error(f"Arquivo nao encontrado em: {full_file_path}")
    elif not user_task.strip():
        st.warning("Descreva o que precisa ser feito.")
    else:
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                codigo_original = f.read()
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
            st.stop()

        st.info(f"Processando {target_file} via Groq (Llama 3.1 70B)...")
        
        system_prompt = """Voce e um Engenheiro de Software Senior atuando como um compilador e editor de codigo.
Sua unica funcao e receber um codigo-fonte existente e uma instrucao de alteracao, e retornar o CODIGO COMPLETO reescrito e atualizado.
REGRAS ABSOLUTAS:
1. NAO explique o que voce fez.
2. NAO use frases como "Aqui esta o codigo" ou "Espero que isso ajude".
3. Envolva toda a sua resposta em UM UNICO bloco de markdown (```).
4. Retorne o arquivo inteiro, nao apenas a parte modificada, para que o sistema possa sobrescrever o arquivo original diretamente."""

        user_prompt = f"INSTRUCAO DE ALTERACAO:\n{user_task}\n\nCODIGO ORIGINAL:\n```\n{codigo_original}\n```"

        with st.spinner("LLM reescrevendo o arquivo (isso pode pausar se o limite for atingido)..."):
            resposta_bruta = chamar_llm_com_espera(client, system_prompt, user_prompt)

        if resposta_bruta:
            codigo_final = extrair_codigo(resposta_bruta)
            
            try:
                with open(full_file_path, 'w', encoding='utf-8') as f:
                    f.write(codigo_final)
                    
                st.success("Arquivo sobrescrito com sucesso!")
                
                with st.expander("Ver Codigo Atualizado"):
                    st.code(codigo_final)
            except Exception as e:
                st.error(f"Erro ao salvar o arquivo no disco: {e}")
        else:
            st.error("Falha ao gerar o codigo apos esgotar as tentativas de API.")