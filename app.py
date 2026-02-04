import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fredy Furtado Salon", layout="wide", page_icon="✂️")

# --- BANCO DE DATOS ---
def init_db():
    conn = sqlite3.connect('salon.db')
    c = conn.cursor()
    # Clientes
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY, nome TEXT, sobrenome TEXT, nascimento TEXT, cpf TEXT, telefone TEXT, email TEXT)''')
    # Agenda
    c.execute('''CREATE TABLE IF NOT EXISTS agenda 
                 (id INTEGER PRIMARY KEY, data TEXT, horario TEXT, cliente TEXT, servico TEXT, funcionario TEXT)''')
    # Financeiro
    c.execute('''CREATE TABLE IF NOT EXISTS financeiro 
                 (id INTEGER PRIMARY KEY, data TEXT, cliente TEXT, valor REAL, metodo TEXT)''')
    # Serviços e Funcionários
    c.execute('''CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY, nome TEXT)''')
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
menu = st.sidebar.selectbox("Navegação", ["Agenda", "Clientes", "Financeiro", "Serviços e Equipe"])

# --- MÓDULO CLIENTES ---
if menu == "Clientes":
    st.header("👥 Gestão de Clientes")
    
    with st.expander("Cadastrar Novo Cliente"):
        with st.form("form_cliente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome*")
            sobrenome = col2.text_input("Sobrenome")
            nasc = col1.date_input("Data de Nascimento", min_value=date(1940, 1, 1))
            cpf = col2.text_input("CPF")
            tel = col1.text_input("Telefone")
            email = col2.text_input("E-mail")
            
            if st.form_submit_button("Salvar Cliente"):
                if nome:
                    run_query("INSERT INTO clientes (nome, sobrenome, nascimento, cpf, telefone, email) VALUES (?,?,?,?,?,?)", 
                             (nome, sobrenome, str(nasc), cpf, tel, email), fetch=False)
                    st.success("Cliente cadastrado com sucesso!")
                else:
                    st.error("O campo Nome é obrigatório.")

    st.subheader("Clientes Cadastrados")
    df_c = run_query("SELECT * FROM clientes")
    st.dataframe(df_c, use_container_width=True)

# --- MÓDULO AGENDA ---
elif menu == "Agenda":
    st.header("📅 Agenda de Atendimentos")
    
    clientes = run_query("SELECT nome || ' ' || sobrenome as nome FROM clientes")['nome'].tolist()
    servicos = run_query("SELECT nome FROM servicos")['nome'].tolist()
    equipe = run_query("SELECT nome FROM funcionarios")['nome'].tolist()

    with st.expander("Novo Agendamento"):
        with st.form("form_agenda"):
            col1, col2 = st.columns(2)
            d = col1.date_input("Data")
            h = col2.time_input("Horário")
            c = col1.selectbox("Cliente", clientes if clientes else ["Cadastre um cliente primeiro"])
            s = col2.selectbox("Serviço", servicos if servicos else ["Cadastre serviços"])
            f = col1.selectbox("Profissional", equipe if equipe else ["Cadastre funcionários"])
            
            if st.form_submit_button("Confirmar Agendamento"):
                run_query("INSERT INTO agenda (data, horario, cliente, servico, funcionario) VALUES (?,?,?,?,?)",
                          (str(d), str(h), c, s, f), fetch=False)
                st.success("Agendado!")

    st.subheader("Compromissos")
    df_a = run_query("SELECT * FROM agenda ORDER BY data, horario")
    st.dataframe(df_a, use_container_width=True)

# --- MÓDULO FINANCEIRO ---
elif menu == "Financeiro":
    st.header("💰 Módulo Financeiro")
    
    t1, t2 = st.tabs(["Lançar Recebimento", "Relatórios Financeiros"])
    
    with t1:
        with st.form("form_fin"):
            clientes = run_query("SELECT nome || ' ' || sobrenome as nome FROM clientes")['nome'].tolist()
            valor = st.number_input("Valor Recebido (R$)", min_value=0.0, step=0.5)
            metodo = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"])
            cli = st.selectbox("Cliente", clientes)
            dt_fin = st.date_input("Data do Pagamento")
            
            if st.form_submit_button("Registrar Entrada"):
                run_query("INSERT INTO financeiro (data, cliente, valor, metodo) VALUES (?,?,?,?)",
                          (str(dt_fin), cli, valor, metodo), fetch=False)
                st.success(f"Entrada de R$ {valor} registrada!")

    with t2:
        periodo = st.radio("Filtro de Relatório", ["Diário", "Semanal", "Mensal", "Anual"], horizontal=True)
        df_f = run_query("SELECT * FROM financeiro")
        df_f['data'] = pd.to_datetime(df_f['data'])
        hoje = datetime.now()

        if periodo == "Diário":
            df_filtro = df_f[df_f['data'].dt.date == hoje.date()]
        elif periodo == "Semanal":
            df_filtro = df_f[df_f['data'] > (hoje - timedelta(days=7))]
        elif periodo == "Mensal":
            df_filtro = df_f[df_f['data'].dt.month == hoje.month]
        else:
            df_filtro = df_f[df_f['data'].dt.year == hoje.year]

        col1, col2 = st.columns(2)
        col1.metric("Faturamento no Período", f"R$ {df_filtro['valor'].sum():.2f}")
        col2.metric("Qtd. Atendimentos", len(df_filtro))
        
        st.dataframe(df_filtro, use_container_width=True)

# --- MÓDULO CONFIGURAÇÕES ---
elif menu == "Serviços e Equipe":
    st.header("⚙️ Configurações do Salão")
    
    col_s, col_f = st.columns(2)
    
    with col_s:
        st.subheader("Tipos de Serviços")
        novo_s = st.text_input("Nome do Serviço (ex: Corte)")
        if st.button("Adicionar Serviço"):
            run_query("INSERT INTO servicos (nome) VALUES (?)", (novo_s,), fetch=False)
        
        df_s = run_query("SELECT nome FROM servicos")
        st.table(df_s)

    with col_f:
        st.subheader("Funcionários")
        novo_f = st.text_input("Nome do Funcionário")
        if st.button("Adicionar Funcionário"):
            run_query("INSERT INTO funcionarios (nome) VALUES (?)", (novo_f,), fetch=False)
            
        df_func = run_query("SELECT nome FROM funcionarios")
        st.table(df_func)