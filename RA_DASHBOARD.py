import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
from itertools import combinations
from collections import Counter
import zipfile
import io
import os
from streamlit_extras.stylable_container import stylable_container
import plotly.figure_factory as ff


# --- Configuration de la page ---
st.set_page_config(
    page_title="Reporting RA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Injection CSS----
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&display=swap');
        * { font-family: 'Inter', sans-serif; box-sizing: border-box; }
        .main { background: #f4f6f8; color: #333; }
        /* Sidebar avec gradient froid (bleu foncé) */
        .stSidebar { background: linear-gradient(135deg, #002F6C, #00509E); color: white; }
        /* Header avec une ambiance américaine et froide */
        .banking-header {
            background: linear-gradient(135deg, #002F6C 0%, #00509E 100%);
            padding: 2rem; 
            border-radius: 0 0 25px 25px;
            margin-bottom: 2rem;
            color: white;
            text-align: center;
        }
        .stPlotlyChart { border: none; }
        .dataframe { border-radius: 10px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)


# --- En-tête personnalisé ---
with stylable_container(key="header", css_styles=".banking-header { color: white !important; }"):
    st.markdown("""
        <div class='banking-header'>
            <h1 style='margin:0;'>Reporting Revenu Assurance</h1>
            <p style='opacity:0.8;'>Interface interactive des Opérations du revenu Assurance</p>
        </div>
    """, unsafe_allow_html=True)

# --- Fonction utilitaire pour créer des "metric cards" compactes ---
def metric_card(title, value, bg_color):
    html = f"""
    <div style="
        background-color: {bg_color};
        padding: 15px;
        border-radius: 8px;
        color: white;
        text-align: center;
        box-shadow: 0 3px 5px rgba(0,0,0,0.1);
        ">
        <h4 style="margin: 0; font-weight: 600; font-size: 1rem;">{title}</h4>
        <p style="font-size: 1.5rem; margin: 5px 0 0; font-weight: bold;">{value}</p>
    </div>
    """
    return html

# --- Chargement du fichier ---
file_path = st.sidebar.file_uploader("Choisir un fichier CSV", type="csv")
if file_path is not None:
    data = pd.read_csv(file_path, encoding="ISO-8859-1")
else:
    st.sidebar.write("Veuillez charger un fichier CSV.")
    st.stop()
        
# --- Nettoyage & transformation ---
def extractday(dated):
    parts=dated.split(' ')
    return parts[0]
data['Date']= data['created_at'].apply(extractday)

data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
data = data.drop_duplicates(subset='transaction_id', keep='first')
payin=data[data['operation_origin']=='payment']
payout=data[data['operation_origin']=='transfer']


# --- Filtres dans la barre latérale ---
# --- Filtres dans la barre latérale ---
st.sidebar.header("🔎 Filtres Stratégiques")

# Création d'un dataframe temporaire pour appliquer les filtres dynamiquement
filtered_data = data.copy()
# Sélection des dates (premier filtre, car il impacte toutes les autres données)
dated = st.sidebar.multiselect("Date", options=sorted(filtered_data["Date"].unique()))
if dated:
    filtered_data = filtered_data[filtered_data["Date"].isin(dated)]
# Mise à jour des options des autres filtres en fonction des données restantes
statuts = st.sidebar.multiselect("Statut", options=sorted(filtered_data["statut"].unique()))
if statuts:
    filtered_data = filtered_data[filtered_data["statut"].isin(statuts)]
operation = st.sidebar.multiselect("Operation", options=sorted(filtered_data["operation_origin"].unique()))
if operation:
    filtered_data = filtered_data[filtered_data["operation_origin"].isin(operation)]
pays = st.sidebar.multiselect("Pays", options=sorted(filtered_data["country"].unique()))
if pays:
    filtered_data = filtered_data[filtered_data["country"].isin(pays)]
partenaire = st.sidebar.multiselect("Provider Name", options=sorted(filtered_data["provider_name"].unique()))
if partenaire:
    filtered_data = filtered_data[filtered_data["provider_name"].isin(partenaire)]
# Mise à jour finale des données après filtrage
data = filtered_data

    
# --- Création des onglets ---
tabs = st.tabs(["📊 Vue Globale", "👥 Opérations", "🔄 Transactions"])

# Onglet Vision 360 (contenu à enrichir ultérieurement)

# =========================
    # Onglet 1 : Vue Globale
# =========================

with tabs[0]:
    st.subheader("Vue Globale")
        # Calcul des KPI
    montant_total = data["amount"].sum()
    nombre_transaction=data['transaction_id'].count()
    nombre_payin=payin['transaction_id'].count()
    Nombre_payout=payout['transaction_id'].count()
    montant_total_payin = payin["amount"].sum()
    montant_total_payout = payout["amount"].sum()

# Affichage dans des metric cards
    col1, col2= st.columns(2)
    col1.markdown(metric_card("Nombre Total Transaction", nombre_transaction, "#1E90FF"), unsafe_allow_html=True)
    col2.markdown(metric_card("Montant Total", f"{montant_total:,.2f} XOF", "#2E8B57"), unsafe_allow_html=True)

#affichage des graphes
    st.markdown("---")
    st.markdown("#### Evololutions des transactions par Opérateur")
    monthly_sales = data.groupby("provider_name")["amount"].sum().reset_index()
    fig_month = px.bar(monthly_sales, x="provider_name", y="amount",
        text_auto=True,
        color="amount",
        color_continuous_scale=["#1E90FF", "#4682B4"],
        template="plotly_white")
    fig_month.update_layout(height=330, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_month, use_container_width=True, config={"displayModeBar": False})
    
    chart1, chart2= st.columns((2))
    with chart1:
        st.subheader('Vue globale par Statut')
        fig=px.pie(data, values="amount",names="statut", template="plotly_dark")
        fig.update_traces(text=data["statut"], textposition="inside")
        st.plotly_chart(fig,use_container_width=True)
    
    with chart2:
        st.subheader('Vue globale par Pays')
        monthly_statut = data.groupby("country")["amount"].sum().reset_index()
        fig_month = px.bar(monthly_statut, x="country", y="amount",
            text_auto=True,
            color="amount",
            color_continuous_scale=["#1E90FF", "#4682B4"],
            template="plotly_white")
        fig_month.update_layout(height=330, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_month, use_container_width=True, config={"displayModeBar": False})
   

with tabs[1]:
    st.subheader("Opérations")
    # Calcul des KPI
    montant_total = data["amount"].sum()
    nombre_transaction=data['transaction_id'].count()
    nombre_payin=payin['transaction_id'].count()
    Nombre_payout=payout['transaction_id'].count()
    montant_total_payin = payin["amount"].sum()
    montant_total_payout = payout["amount"].sum()

# Affichage dans des metric cards
    col1, col2= st.columns(2)
    col1.markdown(metric_card("Nombre Total Transaction", nombre_transaction, "#1E90FF"), unsafe_allow_html=True)
    col2.markdown(metric_card("Montant Total", f"{montant_total:,.2f} XOF", "#2E8B57"), unsafe_allow_html=True)

    
#Affichages des data par pays et provider name
    success=data[data['statut']=='SUCCESS']
    cl1, cl2, cl3 =st.columns((3))
    with cl1:
        with st.expander("Transaction par Pays"):
            select_country= success.groupby(by=["country"], as_index=False)["amount"].sum()
            st.write(select_country.style.background_gradient(cmap="Blues"))
            csv= select_country.to_csv(index=False).encode('utf-8')
            st.download_button("Download Data", data= csv, file_name="country.csv", mime="text/csv",help='Cliquer ici pour télécharger le fichier en csv')
    
    with cl2:
        with st.expander("Transaction par provider name"):
            providername=success.groupby(by ="provider_name", as_index=False)["amount"].sum()
            st.write(providername.style.background_gradient(cmap="Oranges"))
            csv =providername.to_csv(index=False).encode('utf-8')
            st.download_button("Download Datas", data= csv, file_name="provider_name.csv", mime="text/csv",help='Cliquer ici pour télécharger le fichier en csv')

    with cl3:
        with st.expander("Transaction par marchand"):
            merchnname=success.groupby(by ="merchant_name", as_index=False)["amount"].sum()
            st.write(merchnname.style.background_gradient(cmap="Oranges"))
            csv =merchnname.to_csv(index=False).encode('utf-8')
            st.download_button("Download", data= csv, file_name="marchand.csv", mime="text/csv",help='Cliquer ici pour télécharger le fichier en csv')


    st.subheader(":point_right: Resumé des opérations par pays")
    with st.expander("Table Détails"):
        df_sample= data[0:10][["country","provider_name","operation_origin","operator","merchant_name"]]
        fig=ff.create_table(df_sample, colorscale="Cividis")
        st.plotly_chart(fig,use_container_width=True)
        










with tabs[2]:
    st.subheader("Transactions")
    # Calcul des KPI
    montant_total = data["amount"].sum()
    nombre_transaction=data['transaction_id'].count()
    nombre_payin=payin['transaction_id'].count()
    Nombre_payout=payout['transaction_id'].count()
    montant_total_payin = payin["amount"].sum()
    montant_total_payout = payout["amount"].sum()

# Affichage dans des metric cards
    col1, col2= st.columns(2)
    col1.markdown(metric_card("Nombre Total Transaction", nombre_transaction, "#1E90FF"), unsafe_allow_html=True)
    col2.markdown(metric_card("Montant Total", f"{montant_total:,.2f} XOF", "#2E8B57"), unsafe_allow_html=True)


























