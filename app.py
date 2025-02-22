import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
from datetime import timedelta

# Função para alocar clientes nos apartamentos (sem troca de apartamento)
def alocar_clientes_fixos(df):
    # Criar um dicionário para armazenar a ocupação dos apartamentos
    ocupacao = {1: {}, 2: {}, 3: {}}  # {apartamento: {data: cliente}}

    # Iterar sobre cada reserva
    for _, reserva in df.iterrows():
        check_in = reserva['Check-in']
        check_out = reserva['Check-out']
        cliente = reserva['Nome do hóspede']

        # Verificar se o cliente já foi alocado em algum apartamento
        quarto_alocado = None
        for quarto in ocupacao:
            if cliente in ocupacao[quarto].values():
                quarto_alocado = quarto
                break

        # Se o cliente já foi alocado, usar o mesmo apartamento
        if quarto_alocado is not None:
            for data in pd.date_range(check_in, check_out - timedelta(days=1)):
                data = data.date()
                ocupacao[quarto_alocado][data] = cliente
        else:
            # Se o cliente não foi alocado, encontrar o primeiro apartamento disponível
            for quarto in ocupacao:
                disponivel = True
                for data in pd.date_range(check_in, check_out - timedelta(days=1)):
                    data = data.date()
                    if data in ocupacao[quarto]:
                        disponivel = False
                        break
                if disponivel:
                    for data in pd.date_range(check_in, check_out - timedelta(days=1)):
                        data = data.date()
                        ocupacao[quarto][data] = cliente
                    break
            else:
                st.warning(f"Não há apartamentos disponíveis para {cliente} entre {check_in} e {check_out}.")

    return ocupacao

# Título da aplicação
st.title("Gestão de Alojamento Local")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Carregue o arquivo CSV com as reservas", type="csv")

# Verificar se um arquivo foi carregado
if uploaded_file is not None:
    try:
        # Ler o arquivo CSV
        df = pd.read_csv(uploaded_file)

        # Converter colunas de datas para o tipo datetime
        df['Check-in'] = pd.to_datetime(df['Check-in']).dt.date  # Remover horas
        df['Check-out'] = pd.to_datetime(df['Check-out']).dt.date  # Remover horas
        if 'Reservado em' in df.columns:
            df['Reservado em'] = pd.to_datetime(df['Reservado em'])  # Manter horas aqui

        # Remover "EUR" dos preços e comissões e converter para numérico
        if 'Preço' in df.columns:
            df['Preço'] = df['Preço'].replace({' EUR': ''}, regex=True).astype(float)
        if 'Valor da comissão' in df.columns:
            df['Valor da comissão'] = df['Valor da comissão'].replace({' EUR': ''}, regex=True).astype(float)

        # Mostrar tabela de reservas
        st.write("Reservas:", df)

        # Cálculos e estatísticas
        st.write("Estatísticas e Métricas:")

        # Receita Total
        receita_total = df['Preço'].sum()
        st.write(f"Receita Total: {receita_total:.2f} EUR")

        # Valor Líquido (Receita Total - Comissões Totais)
        if 'Valor da comissão' in df.columns:
            comissao_total = df['Valor da comissão'].sum()
            valor_liquido = receita_total - comissao_total
            st.write(f"Valor Líquido: {valor_liquido:.2f} EUR")

        # Valor Líquido por Cliente
        if 'Valor da comissão' in df.columns:
            df['Valor Líquido'] = df['Preço'] - df['Valor da comissão']
            st.write("Valor Líquido por Cliente:")
            st.write(df[['Nome do hóspede', 'Valor Líquido']])

        # Duração Média das Reservas
        if 'Duração (noites)' in df.columns:
            duracao_media = df['Duração (noites)'].mean()
            st.write(f"Duração Média das Reservas: {duracao_media:.2f} noites")

        # Taxa de Ocupação (considerando 3 quartos)
        dias_totais = (df['Check-out'].max() - df['Check-in'].min()).days
        if 'Duração (noites)' in df.columns:
            dias_ocupados = df['Duração (noites)'].sum()
            taxa_ocupacao = (dias_ocupados / (3 * dias_totais)) * 100  # 3 quartos
            st.write(f"Taxa de Ocupação: {taxa_ocupacao:.2f}%")

        # Número Médio de Pessoas por Reserva
        if 'Pessoas' in df.columns:
            media_pessoas = df['Pessoas'].mean()
            st.write(f"Número Médio de Pessoas por Reserva: {media_pessoas:.2f}")

        # Distribuição de Motivos de Viagem
        if 'Motivo da viagem' in df.columns:
            st.write("Distribuição de Motivos de Viagem:")
            motivo_viagem_counts = df['Motivo da viagem'].value_counts()
            st.bar_chart(motivo_viagem_counts)

        # Métodos de Pagamento Mais Usados
        if 'Método de pagamento' in df.columns:
            st.write("Métodos de Pagamento Mais Usados:")
            metodo_pagamento_counts = df['Método de pagamento'].value_counts()
            st.bar_chart(metodo_pagamento_counts)

        # Alocar clientes nos apartamentos (sem troca de apartamento)
        ocupacao = alocar_clientes_fixos(df)

        # Criar a tabela de ocupação
        st.write("Tabela de Ocupação dos Apartamentos:")

        # Criar um DataFrame para a tabela de ocupação
        datas = pd.date_range(df['Check-in'].min(), df['Check-out'].max(), freq='D').date
        tabela_ocupacao = pd.DataFrame(index=[1, 2, 3], columns=datas)

        for quarto in ocupacao:
            for data in ocupacao[quarto]:
                tabela_ocupacao.at[quarto, data] = ocupacao[quarto][data]

        st.write(tabela_ocupacao)

        # Adicionar cores e interatividade
        st.write("Tabela de Ocupação com Cores:")

        # Criar um DataFrame para o gráfico de calor
        dados_grafico = []
        for quarto in ocupacao:
            for data in ocupacao[quarto]:
                dados_grafico.append({
                    "Data": data,
                    "Quarto": quarto,
                    "Cliente": ocupacao[quarto][data]
                })

        df_grafico = pd.DataFrame(dados_grafico)

        # Criar o gráfico de calor
        fig = px.timeline(
            df_grafico,
            x_start="Data",
            x_end="Data",
            y="Quarto",
            color="Cliente",
            title="Tabela de Ocupação",
            labels={"Data": "Data", "Quarto": "Quarto"}
        )
        fig.update_yaxes(type='category')
        st.plotly_chart(fig)

        # Detalhes da Reserva ao clicar no nome
        st.write("Detalhes da Reserva:")
        reserva_selecionada = st.selectbox(
            "Selecione uma reserva pelo nome do hóspede:",
            df['Nome do hóspede'].unique()
        )
        detalhes_reserva = df[df['Nome do hóspede'] == reserva_selecionada].iloc[0]
        st.write(detalhes_reserva)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
else:
    st.warning("Por favor, carregue um arquivo CSV.")