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

pagina = st.sidebar.radio("📂 Kies een pagina", ["📋 Aanmeldingen", "🎯 Ronde Planning", "📅 Periode Beheer", "Upload Inschrijvingen", "📅 Trainingsbeheer", "🔍 Login Geschiedenis"])

if pagina == "📋 Aanmeldingen":
    aanmeldingen_overzicht()

elif pagina == "🎯 Ronde Planning":
    ronde_planning_systeem()

elif pagina == "📅 Periode Beheer":
    periode_beheer()

elif pagina == "Upload Inschrijvingen":
    st.title("🎾 Tennis Training Inplanner")
    st.markdown("Gebruik dit dashboard om automatisch spelers in te plannen voor trainingen op basis van voorkeuren en inschrijftijd.")
    
    uploaded_file = st.file_uploader("📤 Upload het CSV-bestand met inschrijvingen", type=["csv"])

    if uploaded_file:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            # Clean up column names
            df.columns = [col.strip() for col in df.columns]  # Remove leading/trailing spaces
            df.columns = [col.replace(' ', '_') for col in df.columns]  # Replace spaces with underscores
            
            st.success("Bestand succesvol geladen!")
            st.subheader("📋 Inschrijvingen voorbeeld")
            st.dataframe(df.head())

            if st.button("Ga door naar inplanning"):
                import os
                os.makedirs("data", exist_ok=True)
                st.session_state["df"] = df
                df.to_csv("data/inschrijvingen.csv", index=False)
                st.success("Bestand succesvol opgeslagen! Ga naar de Inplanning pagina via het menu links.")

        except Exception as e:
            st.error(f"Fout bij het inladen van bestand: {e}")
    else:
        st.info("Wacht op upload van CSV-bestand...")

elif pagina == "📅 Trainingsbeheer":
    beheer.trainingsbeheer_tab()

elif pagina == "🔍 Login Geschiedenis":
    st.title("🔍 Login Geschiedenis & Beveiliging")
    st.markdown("""
    Hier kun je alle login activiteit bekijken en beveiligingsinformatie controleren.
    """)
    show_auth_log()
