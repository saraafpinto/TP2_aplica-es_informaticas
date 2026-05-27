import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

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

# --- 3. FILTROS DA BARRA LATERAL ---
st.sidebar.header("🎯 Filtros Globais")

# Filtro de Tópico
lista_topicos = ["Todos os Tópicos"] + sorted(df['Topic'].dropna().unique().tolist())
topico_selecionado = st.sidebar.selectbox("Tópico", lista_topicos)

# Filtro de Estado
lista_estados = ["Todos os Estados"] + sorted(df['LocationDesc'].dropna().unique().tolist())
estado_selecionado = st.sidebar.selectbox("Estado", lista_estados)

# Filtro de Ano
anos_disponiveis = sorted(df['Year'].dropna().unique().tolist())
ano_min, ano_max = int(min(anos_disponiveis)), int(max(anos_disponiveis))
anos_selecionados = st.sidebar.slider("Intervalo de Anos", ano_min, ano_max, (ano_min, ano_max))

# Aplicação dos Filtros Dinâmicos
mascara_ano = (df['Year'] >= anos_selecionados[0]) & (df['Year'] <= anos_selecionados[1])
mascara_topico = (df['Topic'] == topico_selecionado) if topico_selecionado != "Todos os Tópicos" and topico_selecionado != "Selecionar tudo" else True
mascara_estado = (df['LocationDesc'] == estado_selecionado) if estado_selecionado != "Todos os Estados" else True

df_filtrado = df[mascara_ano & mascara_topico & mascara_estado].copy()


# -----------------------------------------------------------------------------
# GRÁFICOS SUPERIORES (Evolução Temporal e Rankings por Estado/Tópico)
# -----------------------------------------------------------------------------
st.markdown("### 📈 Indicadores Gerais")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
with col_kpi1:
    st.metric("Total de Registos", f"{len(df_filtrado):,}")
with col_kpi2:
    media_val = df_filtrado['Data_Value'].mean()
    st.metric("Média do Indicador", f"{media_val:.2f}%" if pd.notnull(media_val) else "N/A")
with col_kpi3:
    st.metric("Estados Analisados", f"{df_filtrado['LocationAbbr'].nunique()}")

# --- SECÇÃO DE INSIGHTS (Requisito 3 do Enunciado) ---
with st.expander("💡 Insights e Recomendações Estratégicas", expanded=False):
    if not df_filtrado.empty:
        # Calcular os insights dinamicamente
        top_estado = df_filtrado.groupby('LocationDesc')['Data_Value'].mean().idxmax()
        val_top_estado = df_filtrado.groupby('LocationDesc')['Data_Value'].mean().max()
        
        anos = sorted(df_filtrado['Year'].dropna().unique())
        tendencia_txt = "manteve-se estável"
        if len(anos) > 1:
            val_inicio = df_filtrado[df_filtrado['Year'] == anos[0]]['Data_Value'].mean()
            val_fim = df_filtrado[df_filtrado['Year'] == anos[-1]]['Data_Value'].mean()
            tendencia_txt = f"**aumentou** (de {val_inicio:.1f} para {val_fim:.1f})" if val_fim > val_inicio else f"**diminuiu** (de {val_inicio:.1f} para {val_fim:.1f})"
            
        df_demog = df_filtrado[df_filtrado['Age_Group'] != 'Overall']
        idade_critica = df_demog.groupby('Age_Group')['Data_Value'].mean().idxmax() if not df_demog.empty else "N/A"

        st.info(f"""
        **Conclusões baseadas nos dados filtrados:**
        1. 📍 **Região Crítica:** O estado de **{top_estado}** regista a maior média (**{val_top_estado:.1f}%**). *Recomendação: Alocar mais recursos e focar campanhas de saúde preventiva nesta região.*
        2. 📈 **Evolução Temporal:** Ao longo dos anos selecionados, a média do indicador {tendencia_txt}. *Recomendação: Analisar as políticas públicas aplicadas nesse período para entender a variação.*
        3. 🎯 **Foco Demográfico:** A faixa etária mais afetada em média é **{idade_critica}**. *Recomendação: Direcionar rastreios e ações de sensibilização especificamente para este grupo etário.*
        """)
    else:
        st.warning("Não existem dados suficientes para gerar insights.")

st.markdown("---")

# Primeira Linha de Gráficos: Linha de Tempo e Média por Topic
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Média de Data_Value por Year**")
    df_ano = df_filtrado.groupby('Year', as_index=False)['Data_Value'].mean()
    fig_linha = px.line(df_ano, x='Year', y='Data_Value', markers=True)
    fig_linha.update_traces(line=dict(color='#0084FF', width=3), marker=dict(size=8))
    fig_linha.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickmode='linear'),
        yaxis=dict(showgrid=True),
        xaxis_title="Year", yaxis_title="Média de Data_Value"
    )
    st.plotly_chart(fig_linha, use_container_width=True)

with col2:
    st.markdown("**Média de Data_Value por Topic**")
    df_topic_chart = df_filtrado.groupby('Topic', as_index=False)['Data_Value'].mean().sort_values(by='Data_Value', ascending=False)
    fig_topic = px.bar(df_topic_chart, x='Topic', y='Data_Value', color_discrete_sequence=['#0084FF'])
    fig_topic.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True),
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
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=False, autorange="reversed"),
        showlegend=False, xaxis_title="Média de Data_Value", yaxis_title="LocationDesc"
    )
    st.plotly_chart(fig_risco, use_container_width=True)

with col4:
    st.markdown("**Volume de Notificações por Estado (Quantidade)**")
    df_estado_vol = df_filtrado.groupby('LocationDesc', as_index=False).size().sort_values(by='size', ascending=False).head(10)
    fig_vol = px.bar(df_estado_vol, x='size', y='LocationDesc', orientation='h', color_discrete_sequence=['#0084FF'])
    fig_vol.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=False, autorange="reversed"),
        showlegend=False, xaxis_title="Contagem de Data_Value", yaxis_title="LocationDesc"
    )
    st.plotly_chart(fig_vol, use_container_width=True)

st.markdown("---")
st.markdown("### 🔬 Panorama Geral: Risco vs Volume por Tópico")
st.markdown("Este gráfico ignora o filtro individual de Tópico para permitir comparar globalmente quais os problemas de saúde com mais dados (Volume) e com maiores taxas (Risco).")

# Usar apenas o filtro de Ano para garantir que vemos todos os tópicos
df_scatter_base = df[(df['Year'] >= anos_selecionados[0]) & (df['Year'] <= anos_selecionados[1])]

df_scatter = df_scatter_base.groupby('Topic').agg(
    Risco=('Data_Value', 'mean'),
    Volume=('Data_Value', 'count')
).reset_index()

fig_scatter = px.scatter(
    df_scatter, x='Volume', y='Risco', hover_name='Topic',
    color_discrete_sequence=['#0084FF'], size='Volume', size_max=25,
    labels={'Volume': 'Volume de Notificações', 'Risco': 'Média de Prevalência (%)'}
)
fig_scatter.update_layout(
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=True),
    yaxis=dict(showgrid=True)
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")
st.markdown("### 🗺️ Distribuição Geográfica")

df_mapa = df_filtrado.groupby('LocationAbbr', as_index=False)['Data_Value'].mean()
fig_mapa = px.choropleth(
    df_mapa, 
    locations='LocationAbbr', 
    locationmode="USA-states", 
    color='Data_Value',
    scope="usa",
    color_continuous_scale="Blues",
    title="Média de Data_Value por Estado"
)
fig_mapa.update_layout(
    plot_bgcolor='rgba(0,0,0,0)', 
    paper_bgcolor='rgba(0,0,0,0)',
    geo=dict(bgcolor='rgba(0,0,0,0)'),
    margin=dict(l=0, r=0, t=40, b=0)
)
st.plotly_chart(fig_mapa, use_container_width=True)

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
            textfont=dict(size=14, family='Arial'),
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
        
        fig_idade.update_xaxes(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=12))
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
            textfont=dict(size=14),
            marker=dict(line=dict(color='rgba(0,0,0,0)', width=0)) 
        )
        
        fig_genero.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(font=dict(size=12)),
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
            textfont=dict(size=13, family='Arial'),
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
        fig_etnia.update_yaxes(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=12))
        
        st.plotly_chart(fig_etnia, use_container_width=True)
    else:
        st.info("Sem dados de etnia para o tópico selecionado.")

# -----------------------------------------------------------------------------
# 4. INTEGRAÇÃO DE LLM (CHATBOT COM OLLAMA LOCAL) - Requisito 4 do Enunciado
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### Assistente de BI")
st.markdown("Fale com o assistente inteligente para extrair insights adicionais dos dados que está a visualizar.")

# Inicializar o histórico de chat na sessão do Streamlit
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"role": "assistant", "content": "Olá! Sou o teu assistente de dados. Podes perguntar-me sobre as tendências, os estados mais críticos ou a faixa etária mais afetada no dashboard atual!"}
    ]

# Renderizar as mensagens passadas no ecrã com o estilo "chat"
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Caixa de input de chat fixa em baixo (estilo ChatGPT)
if prompt := st.chat_input("Escreve a tua pergunta (ex: 'Qual é a região mais crítica e porquê?')"):
    # Guardar a mensagem do user no histórico e mostrar
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Lógica do Bot
    with st.chat_message("assistant"):
        with st.spinner("A analisar os dados..."):
            try:
                resumo_estados = df_filtrado.groupby('LocationDesc')['Data_Value'].mean().sort_values(ascending=False).head(5).to_dict()
                contexto_basico = (
                    f"O utilizador está a ver um dashboard com {len(df_filtrado)} linhas filtradas. "
                    f"Média global atual do indicador: {df_filtrado['Data_Value'].mean():.2f}%. "
                    f"Top 5 Estados mais críticos: {resumo_estados}."
                )
                
                prompt_completo = f"És um assistente de Business Intelligence empático. Contexto atual dos dados: {contexto_basico}\nPergunta: {prompt}\nResponde de forma muito concisa e em Português de Portugal."
                
                url_ollama = "http://localhost:11434/api/generate"
                payload = {
                    "model": "gemma2",
                    "prompt": prompt_completo,
                    "stream": False
                }
                
                resposta = requests.post(url_ollama, json=payload, timeout=60)
                
                if resposta.status_code == 200:
                    texto_resposta = resposta.json().get("response", "")
                    st.markdown(texto_resposta)
                    # Guardar a resposta do assistente no histórico
                    st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                else:
                    st.error(f"Erro no Ollama (Status {resposta.status_code}). Verifica se o modelo 'gemma2' está instalado.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Não foi possível ligar ao Ollama. Verifica se está a correr (http://localhost:11434).")
            except Exception as e:
                st.error(f"Erro inesperado: {str(e)}")