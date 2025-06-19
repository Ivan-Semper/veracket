import streamlit as st
import pandas as pd
from components import beheer
from components.aanmeldingen import aanmeldingen_overzicht
from components.periode_beheer import periode_beheer
from components.auth import check_admin_access, login_form, show_admin_header, show_auth_log
from components.ronde_planning import ronde_planning_systeem

st.set_page_config(page_title="Tennis Training Inplanner - Admin Dashboard", layout="wide")

# Check authentication
if not check_admin_access():
    login_form()
    st.stop()

# Show admin header with logout option
show_admin_header()

# Admin sidebar
st.sidebar.markdown("### 🔐 Admin Dashboard")
st.sidebar.markdown("**Alleen voor Technische Commissie**")
st.sidebar.markdown("---")
st.sidebar.success("✅ Ingelogd als Admin")

pagina = st.sidebar.radio("📂 Kies een pagina", ["📋 Aanmeldingen", "🎯 Ronde Planning", "📅 Periode Beheer", "📅 Trainingsbeheer", "🔍 Login Geschiedenis"])

if pagina == "📋 Aanmeldingen":
    aanmeldingen_overzicht()

elif pagina == "🎯 Ronde Planning":
    ronde_planning_systeem()

elif pagina == "📅 Periode Beheer":
    periode_beheer()

elif pagina == "📅 Trainingsbeheer":
    beheer.trainingsbeheer_tab()

elif pagina == "🔍 Login Geschiedenis":
    st.title("🔍 Login Geschiedenis & Beveiliging")
    st.markdown("""
    Hier kun je alle login activiteit bekijken en beveiligingsinformatie controleren.
    """)
    show_auth_log()
