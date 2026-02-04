import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fredy Furtado Salon", layout="wide", page_icon="✂️")

# --- BANCO DE DATOS (ESTRUTURA ATUALIZADA) ---
def init_db():
    conn = sqlite3.connect('salon.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY, nome TEXT, sobrenome TEXT, nascimento TEXT, cpf TEXT, telefone TEXT, email TEXT)''')
    
    # Nova tabela de serviços com PREÇO
    c.execute('''CREATE TABLE IF NOT EXISTS servicos 
                 (id INTEGER PRIMARY KEY, nome TEXT, preco REAL)''')
    
    # Tabela de Atendimentos (Histórico e Financeiro integrados)
    c.execute('''CREATE TABLE IF NOT EXISTS atendimentos 
                 (id INTEGER PRIMARY KEY, data TEXT, cliente_id INTEGER, servico TEXT, 
                  valor REAL, metodo_pagamento TEXT, funcionario TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS funcionarios (id INTEGER PRIMARY KEY, nome TEXT)''')
    conn.commit()
    conn.close()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect('salon.db')
    if fetch:
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    else:
        conn.execute(query, params)
        conn.commit()
        conn.close()

init_db()

# --- BARRA LATERAL ---
st.sidebar.title("Fredy Furtado Salon")
menu = st.sidebar.selectbox("Ir para:", ["Atendimento / Ficha", "Clientes", "Serviços", "Equipe", "Financeiro"])

# --- MÓDULO 1: SERVIÇOS (COM VALORES) ---
if menu == "Serviços":
    st.header("📋 Lista de Serviços e Preços")
    
    with st.form("novo_servico"):
        col1, col2 = st.columns(2)
        nome_s = col1.text_input("Nome do Serviço")
        preco_s = col2.number_input("Valor (R$)", min_value=0.0, step=5.0)
        if st.form_submit_button("Cadastrar Serviço"):
            run_query("INSERT INTO servicos (nome, preco) VALUES (?,?)", (nome_s, preco_s), fetch=False)
            st.success("Serviço adicionado!")

    df_s = run_query("SELECT id, nome as 'Serviço', preco as 'Preço (R$)' FROM servicos")
    st.dataframe(df_s, use_container_width=True, hide_index=True)

# --- MÓDULO 2: CLIENTES ---
elif menu == "Clientes":
    st.header("👥 Gestão de Clientes")
    with st.expander("Cadastrar Novo Cliente"):
        with st.form("form_cliente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome*")
            sobrenome = c2.text_input("Sobrenome")
            cpf = c1.text_input("CPF")
            tel = c2.text_input("Telefone")
            if st.form_submit_button("Salvar"):
                run_query("INSERT INTO clientes (nome, sobrenome, cpf, telefone) VALUES (?,?,?,?)", 
                         (nome, sobrenome, cpf, tel), fetch=False)
                st.success("Cliente cadastrado!")
    
    df_c = run_query("SELECT id, nome, sobrenome, cpf, telefone FROM clientes")
    st.dataframe(df_c, use_container_width=True, hide_index=True)

# --- MÓDULO 3: ATENDIMENTO / FICHA DO CLIENTE (O CORAÇÃO DO APP) ---
elif menu == "Atendimento / Ficha":
    st.header("📑 Ficha de Atendimento")

    # 1. Selecionar Cliente
    df_clientes = run_query("SELECT id, nome || ' ' || sobrenome as full_name FROM clientes")
    if not df_clientes.empty:
        cliente_opcoes = {row['full_name']: row['id'] for _, row in df_clientes.iterrows()}
        nome_selecionado = st.selectbox("Buscar Cliente", options=list(cliente_opcoes.keys()))
        cliente_id = cliente_opcoes[nome_selecionado]

        # Exibir Dados do Cliente
        cliente_info = run_query("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).iloc[0]
        st.info(f"**Cliente:** {cliente_info['nome']} {cliente_info['sobrenome']} | **Tel:** {cliente_info['telefone']} | **CPF:** {cliente_info['cpf']}")

        col_lançar, col_historia = st.columns([1, 1])

        with col_lançar:
            st.subheader("Novo Atendimento")
            # Buscar serviços para pegar o preço automático
            df_serv = run_query("SELECT nome, preco FROM servicos")
            if not df_serv.empty:
                lista_serv = df_serv['nome'].tolist()
                serv_escolhido = st.selectbox("Selecione o Serviço", lista_serv)
                
                # Preencher valor automático
                valor_auto = df_serv[df_serv['nome'] == serv_escolhido]['preco'].values[0]
                valor_final = st.number_input("Confirmar Valor (R$)", value=float(valor_auto))
                
                metodo = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito"])
                func_lista = run_query("SELECT nome FROM funcionarios")['nome'].tolist()
                func = st.selectbox("Profissional", func_lista if func_lista else ["Padrão"])

                if st.button("Finalizar Atendimento"):
                    run_query('''INSERT INTO atendimentos (data, cliente_id, servico, valor, metodo_pagamento, funcionario) 
                                 VALUES (?,?,?,?,?,?)''', 
                              (str(date.today()), cliente_id, serv_escolhido, valor_final, metodo, func), fetch=False)
                    st.success("Atendimento registrado com sucesso!")
                    st.rerun()
            else:
                st.warning("Cadastre serviços primeiro no módulo 'Serviços'.")

        with col_historia:
            st.subheader("📜 Histórico (Atendimentos Anteriores)")
            hist = run_query('''SELECT data as Data, servico as Serviço, valor as Valor, metodo_pagamento as Pagamento 
                                FROM atendimentos WHERE cliente_id = ? ORDER BY id DESC''', (cliente_id,))
            if not hist.empty:
                st.dataframe(hist, use_container_width=True, hide_index=True)
            else:
                st.write("Nenhum atendimento anterior encontrado.")
    else:
        st.warning("Nenhum cliente cadastrado. Vá ao módulo Clientes.")

# --- MÓDULO 4: EQUIPE ---
elif menu == "Equipe":
    st.header("💇‍♂️ Profissionais")
    novo_f = st.text_input("Nome do Funcionário")
    if st.button("Adicionar"):
        run_query("INSERT INTO funcionarios (nome) VALUES (?)", (novo_f,), fetch=False)
    
    df_f = run_query("SELECT nome as Nome FROM funcionarios")
    st.table(df_f)

# --- MÓDULO 5: FINANCEIRO ---
elif menu == "Financeiro":
    st.header("💰 Relatório Financeiro")
    
    df_f = run_query('''SELECT a.data, c.nome || ' ' || c.sobrenome as cliente, a.servico, a.valor, a.metodo_pagamento 
                        FROM atendimentos a JOIN clientes c ON a.cliente_id = c.id''')
    
    if not df_f.empty:
        df_f['data'] = pd.to_datetime(df_f['data'])
        filtro = st.radio("Filtro", ["Diário", "Mensal", "Anual"], horizontal=True)
        hoje = datetime.now()

        if filtro == "Diário":
            df_res = df_f[df_f['data'].dt.date == hoje.date()]
        elif filtro == "Mensal":
            df_res = df_f[df_f['data'].dt.month == hoje.month]
        else:
            df_res = df_f

        st.metric("Faturamento Total no Período", f"R$ {df_res['valor'].sum():.2f}")
        st.dataframe(df_res, use_container_width=True)
    else:
        st.write("Sem movimentações financeiras.")