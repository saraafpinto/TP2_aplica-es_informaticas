import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuração Básica da Página do Streamlit
st.set_page_config(page_title="Dashboard de Prevalência", layout="wide")
st.title("📊 Dashboard Demográfico Interativo")

# 2. Carregamento dos Dados com tratamento
@st.cache_data
def carregar_e_tratar_dados():
    # Carrega o CSV original
    df = pd.read_csv("dataset.csv")
    
    # --- PASSO DE TRATAMENTO DE DADOS (Igual ao que fizeste no Power BI) ---
    # Criar a coluna Age_Group
    df['Age_Group'] = np.where(
        df['Break_Out_Category'].str.lower().str.contains('age', na=False),
        df['Break_out'],
        'Overall'
    )
    
    # Criar a coluna Gender
    df['Gender'] = np.where(
        df['Break_Out_Category'].str.lower().str.contains('gender', na=False),
        df['Break_out'],
        'Overall'
    )
    
    # Criar a coluna Race_Ethnicity
    df['Race_Ethnicity'] = np.where(
        df['Break_Out_Category'].str.lower().str.contains('race|ethnicity', na=False),
        df['Break_out'],
        'Overall'
    )
    
    return df

# Chamar a função para ter o DataFrame limpo
df = carregar_e_tratar_dados()

# --- 3. CRIAR O FILTRO POR TOPIC (IGUAL AO SLICER DO POWER BI) ---
st.sidebar.header("🎯 Filtros Globais")
lista_topicos = ["Selecionar tudo"] + sorted(df['Topic'].dropna().unique().tolist())
topico_selecionado = st.sidebar.selectbox("Topic", lista_topicos)

# Aplicação do Filtro do Slicer sobre os dados
if topico_selecionado == "Selecionar tudo":
    df_filtrado = df.copy()
else:
    df_filtrado = df[df['Topic'] == topico_selecionado]


# -----------------------------------------------------------------------------
# GRÁFICOS SUPERIORES (Evolução Temporal e Rankings por Estado/Tópico)
# -----------------------------------------------------------------------------
st.markdown("### 📈 Indicadores Gerais")

# Primeira Linha de Gráficos: Linha de Tempo e Média por Topic
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Média de Data_Value por Year**")
    df_ano = df_filtrado.groupby('Year', as_index=False)['Data_Value'].mean()
    fig_linha = px.line(df_ano, x='Year', y='Data_Value', markers=True)
    fig_linha.update_traces(line=dict(color='#0084FF', width=3), marker=dict(size=8))
    fig_linha.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickmode='linear', tickfont=dict(color='white')),
        yaxis=dict(showgrid=True, gridcolor='#262730', tickfont=dict(color='white')),
        xaxis_title="Year", yaxis_title="Média de Data_Value"
    )
    st.plotly_chart(fig_linha, use_container_width=True)

with col2:
    st.markdown("**Média de Data_Value por Topic**")
    df_topic_chart = df_filtrado.groupby('Topic', as_index=False)['Data_Value'].mean().sort_values(by='Data_Value', ascending=False)
    fig_topic = px.bar(df_topic_chart, x='Topic', y='Data_Value', color_discrete_sequence=['#0084FF'])
    fig_topic.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(color='white', size=10)),
        yaxis=dict(showgrid=True, gridcolor='#262730', tickfont=dict(color='white')),
        showlegend=False, xaxis_title="Topic", yaxis_title="Média de Data_Value"
    )
    st.plotly_chart(fig_topic, use_container_width=True)


# Segunda Linha de Gráficos: Rankings de Estados (Risco vs Volume)
col3, col4 = st.columns(2)

with col3:
    st.markdown("**Top 10 Estados por Risco Médio (Valor)**")
    df_estado_risco = df_filtrado.groupby('LocationDesc', as_index=False)['Data_Value'].mean().sort_values(by='Data_Value', ascending=False).head(10)
    fig_risco = px.bar(df_estado_risco, x='Data_Value', y='LocationDesc', orientation='h', color_discrete_sequence=['#0084FF'])
    fig_risco.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='#262730', tickfont=dict(color='white')),
        yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(color='white')),
        showlegend=False, xaxis_title="Média de Data_Value", yaxis_title="LocationDesc"
    )
    st.plotly_chart(fig_risco, use_container_width=True)

with col4:
    st.markdown("**Volume de Notificações por Estado (Quantidade)**")
    df_estado_vol = df_filtrado.groupby('LocationDesc', as_index=False).size().sort_values(by='size', ascending=False).head(10)
    fig_vol = px.bar(df_estado_vol, x='size', y='LocationDesc', orientation='h', color_discrete_sequence=['#0084FF'])
    fig_vol.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='#262730', tickfont=dict(color='white')),
        yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(color='white')),
        showlegend=False, xaxis_title="Contagem de Data_Value", yaxis_title="LocationDesc"
    )
    st.plotly_chart(fig_vol, use_container_width=True)


st.markdown("---")
st.markdown("### 👥 Segmentação Demográfica Filtrada")

# 4. Criação de Separadores Visuais (Tabs) para não misturar os gráficos demográficos
tab_idade, tab_genero, tab_etnia = st.tabs([
    "🧓 Por Faixa Etária", 
    "👩‍🦰 Por Género", 
    "🌍 Por Etnia / Raça"
])

# --- SEPARADOR 1: GRÁFICO DE IDADE (COLUNAS LIMPAS) ---
with tab_idade:
    st.subheader("Análise por Grupos Etários")
    
    # Filtro para isolar a Idade usando o DataFrame que já passou pelo filtro do Topic
    df_idade = df_filtrado[
        (df_filtrado['Gender'] == 'Overall') & 
        (df_filtrado['Race_Ethnicity'] == 'Overall') & 
        (df_filtrado['Age_Group'] != 'Overall')
    ]
    
    if not df_idade.empty:
        df_idade_agrupado = df_idade.groupby('Age_Group', as_index=False)['Data_Value'].mean()
        
        fig_idade = px.bar(
            df_idade_agrupado,
            x='Age_Group',
            y='Data_Value',
            color='Age_Group',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig_idade.update_traces(
            text=df_idade_agrupado['Data_Value'].round(1).astype(str) + '%',
            textposition='outside',        
            textfont=dict(size=14, color='white', family='Arial'),
            marker_line_width=0,           
            marker_pattern_shape=""        
        )
        
        fig_idade.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',  
            paper_bgcolor='rgba(0,0,0,0)', 
            xaxis_title="Faixa Etária",
            yaxis_title="",                
            showlegend=False,
            yaxis=dict(range=[0, df_idade_agrupado['Data_Value'].max() * 1.15]),
            margin=dict(t=60, b=40, l=40, r=40),
            height=500
        )
        
        fig_idade.update_xaxes(showgrid=False, showline=False, zeroline=False, tickfont=dict(color='white', size=12))
        fig_idade.update_yaxes(showgrid=False, showline=False, zeroline=False, showticklabels=False) 
        
        st.plotly_chart(fig_idade, use_container_width=True)
    else:
        st.info("Sem dados de idade para o tópico selecionado.")


# --- SEPARADOR 2: GRÁFICO DE GÉNERO (CIRCULAR / PIE) ---
with tab_genero:
    st.subheader("Análise por Género")
    
    df_genero = df_filtrado[
        (df_filtrado['Age_Group'] == 'Overall') & 
        (df_filtrado['Race_Ethnicity'] == 'Overall') & 
        (df_filtrado['Gender'] != 'Overall')
    ]
    
    if not df_genero.empty:
        df_genero_agrupado = df_genero.groupby('Gender', as_index=False)['Data_Value'].mean()
        
        fig_genero = px.pie(
            df_genero_agrupado,
            values='Data_Value',
            names='Gender',
            color='Gender',
            color_discrete_sequence=['#91CC75', '#5470C6'] 
        )
        
        fig_genero.update_traces(
            textposition='inside',
            textinfo='percent+label', 
            textfont=dict(size=14, color='white'),
            marker=dict(line=dict(color='rgba(0,0,0,0)', width=0)) 
        )
        
        fig_genero.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(font=dict(color='white', size=12)),
            margin=dict(t=40, b=40, l=40, r=40),
            height=500
        )
        
        st.plotly_chart(fig_genero, use_container_width=True)
    else:
        st.info("Sem dados de género para o tópico selecionado.")


# --- SEPARADOR 3: GRÁFICO DE ETNIA (BARRAS HORIZONTAIS LIMPAS) ---
with tab_etnia:
    st.subheader("Análise por Etnia e Raça")
    
    df_etnia = df_filtrado[
        (df_filtrado['Age_Group'] == 'Overall') & 
        (df_filtrado['Gender'] == 'Overall') & 
        (df_filtrado['Race_Ethnicity'] != 'Overall')
    ]
    
    if not df_etnia.empty:
        df_etnia_agrupado = df_etnia.groupby('Race_Ethnicity', as_index=False)['Data_Value'].mean()
        
        fig_etnia = px.bar(
            df_etnia_agrupado,
            x='Data_Value',
            y='Race_Ethnicity',
            orientation='h',
            color='Race_Ethnicity',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig_etnia.update_traces(
            text=df_etnia_agrupado['Data_Value'].round(1).astype(str) + '%',
            textposition='outside',        
            textfont=dict(size=13, color='white', family='Arial'),
            marker_line_width=0,
            marker_pattern_shape=""
        )
        
        fig_etnia.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="",
            yaxis_title="Etnia / Raça",
            showlegend=False,
            xaxis=dict(range=[0, df_etnia_agrupado['Data_Value'].max() * 1.20]), 
            margin=dict(t=40, b=40, l=40, r=100), 
            height=600
        )
        
        fig_etnia.update_xaxes(showgrid=False, showline=False, zeroline=False, showticklabels=False)
        fig_etnia.update_yaxes(showgrid=False, showline=False, zeroline=False, tickfont=dict(color='white', size=12))
        
        st.plotly_chart(fig_etnia, use_container_width=True)
    else:
        st.info("Sem dados de etnia para o tópico selecionado.")