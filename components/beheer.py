import streamlit as st
import pandas as pd
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TRAINING_CSV_PATH = BASE_DIR / "data" / "trainings.csv"

def trainingsbeheer_tab():
    st.title("📅 Trainingsbeheer")
    st.markdown("""
    Hier kun je trainingen toevoegen, bewerken of verwijderen. Geef per training aan:
    - Dag en tijd
    - Min/max niveau
    - Capaciteit
    - Trainer
    """)

    # Laad bestaande trainingen uit CSV (indien aanwezig)
    if "trainingen" not in st.session_state:
        if os.path.exists(TRAINING_CSV_PATH):
            df_existing = pd.read_csv(TRAINING_CSV_PATH)
            # Remove Training Naam column if it exists (backward compatibility)
            if "Training Naam" in df_existing.columns:
                df_existing = df_existing.drop(columns=["Training Naam"])
            st.session_state.trainingen = df_existing
        else:
            st.session_state.trainingen = pd.DataFrame(columns=["Dag", "Tijd", "MinNiveau", "MaxNiveau", "Capaciteit", "Trainer"])

    df = st.session_state.trainingen
    st.subheader("📋 Huidige trainingen")

    # Bewerken
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")
    if st.button("💾 Wijzigingen opslaan"):
        st.session_state.trainingen = edited_df
        st.session_state.trainingen.to_csv(TRAINING_CSV_PATH, index=False)
        st.success("Wijzigingen opgeslagen!")
        st.rerun()

    # Verwijderen
    if len(df) > 0:
        st.write("### 🗑 Verwijder training")
        index_to_delete = st.selectbox("Selecteer een training om te verwijderen:", df.index, format_func=lambda i: f"{df.at[i, 'Dag']} {df.at[i, 'Tijd']} - Niveau {df.at[i, 'MinNiveau']}-{df.at[i, 'MaxNiveau']}")
        if st.button("Verwijder geselecteerde training"):
            st.session_state.trainingen = df.drop(index=index_to_delete).reset_index(drop=True)
            st.session_state.trainingen.to_csv(TRAINING_CSV_PATH, index=False)
            st.success("Training verwijderd!")
            st.rerun()

    # Toevoegen
    with st.form("Nieuwe training toevoegen"):
        st.write("### ➕ Voeg nieuwe training toe")
        dag = st.selectbox("Dag", ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag"])
        tijd = st.text_input("Tijd (bijv. 17:30 - 18:45)")
        min_niveau = st.number_input("Minimum niveau", min_value=1, max_value=10, value=5)
        max_niveau = st.number_input("Maximum niveau", min_value=1, max_value=10, value=9)
        capaciteit = st.number_input("Capaciteit (max. aantal spelers)", min_value=1, value=24)
        trainer = st.text_input("Trainer")
        toevoegen = st.form_submit_button("➕ Toevoegen")

        if toevoegen:
            nieuwe_training = {
                "Dag": dag,
                "Tijd": tijd,
                "MinNiveau": min_niveau,
                "MaxNiveau": max_niveau,
                "Capaciteit": capaciteit,
                "Trainer": trainer
            }
            st.session_state.trainingen = pd.concat([
                st.session_state.trainingen, pd.DataFrame([nieuwe_training])
            ], ignore_index=True)
            st.session_state.trainingen.to_csv(TRAINING_CSV_PATH, index=False)
            st.success("Training toegevoegd!")
            st.rerun()
