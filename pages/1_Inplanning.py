import streamlit as st
import pandas as pd
from pathlib import Path
from utils.logic import plan_spelers

BASE_DIR = Path(__file__).resolve().parent.parent
TRAINING1_PATH = BASE_DIR / "data" / "training1_inschrijvingen.csv"
TRAINING2_PATH = BASE_DIR / "data" / "training2_inschrijvingen.csv"
TRAINING3_PATH = BASE_DIR / "data" / "training3_inschrijvingen.csv"
TRAININGEN_PATH = BASE_DIR / "data" / "trainings.csv"

st.title("📊 Automatische Inplanning")

st.info("""
🎯 **Nieuw: Ronde-gebaseerde Planning**

Voor meer controle over het planningsproces is er nu een nieuw ronde-gebaseerd systeem beschikbaar in het admin dashboard.
Dit systeem laat je stap voor stap door de planningsrondes gaan en handmatig edge cases oplossen.

**Voordelen van het nieuwe systeem:**
- Stap-voor-stap planning per training prioriteit
- Handmatige controle na elke ronde
- Geen verlies van plekken door technische problemen
- Volledige audit trail van alle beslissingen

Ga naar **Admin Dashboard → 🎯 Ronde Planning** om het nieuwe systeem te gebruiken.
""")

st.markdown("---")
st.markdown("### 📊 Klassieke Automatische Planning")
st.markdown("*Dit is het originele systeem dat alle trainingen in één keer plant.*")

if not TRAININGEN_PATH.exists():
    st.error("❌ Trainingen bestand niet gevonden in 'data/' map.")
    st.stop()

# Load en combineer alle training inschrijvingen
inschrijvingen_list = []

# Laad training 1 (hoogste prioriteit)
if TRAINING1_PATH.exists():
    df1 = pd.read_csv(TRAINING1_PATH)
    df1['Training_prioriteit'] = 1
    inschrijvingen_list.append(df1)
    st.info(f"📋 Training 1: {len(df1)} inschrijvingen geladen")

# Laad training 2
if TRAINING2_PATH.exists():
    df2 = pd.read_csv(TRAINING2_PATH)
    df2['Training_prioriteit'] = 2
    inschrijvingen_list.append(df2)
    st.info(f"📋 Training 2: {len(df2)} inschrijvingen geladen")

# Laad training 3
if TRAINING3_PATH.exists():
    df3 = pd.read_csv(TRAINING3_PATH)
    df3['Training_prioriteit'] = 3
    inschrijvingen_list.append(df3)
    st.info(f"📋 Training 3: {len(df3)} inschrijvingen geladen")

if not inschrijvingen_list:
    st.warning("⚠️ Geen inschrijvingen gevonden. Zorg dat er minstens één training CSV bestand bestaat.")
    st.stop()

# Combineer alle inschrijvingen
inschrijvingen = pd.concat(inschrijvingen_list, ignore_index=True)
trainingen = pd.read_csv(TRAININGEN_PATH)

st.success(f"✅ Totaal {len(inschrijvingen)} inschrijvingen geladen uit {len(inschrijvingen_list)} training(en)")

# Plan spelers in
planning, handmatig = plan_spelers(inschrijvingen, trainingen)

# ✅ Per training gegroepeerd
st.subheader("✅ Verdeling per training")
for training, spelers in planning.items():
    st.markdown(f"**{training}**")
    df = pd.DataFrame(spelers, columns=["Naam", "Niveau"])
    df.index += 1
    st.dataframe(df, use_container_width=True)

# ❌ Handmatige inplanning
if handmatig:
    st.subheader("❌ Handmatige inplanning nodig")
    df_fail = pd.DataFrame(handmatig, columns=["Naam", "Niveau", "Reden"])
    df_fail.index += 1
    st.dataframe(df_fail, use_container_width=True)

# 💾 Download resultaat
alle_resultaten = [
    {"Naam": naam, "Niveau": niveau, "Toegewezen training": training}
    for training, spelers in planning.items()
    for naam, niveau in spelers
] + [
    {"Naam": naam, "Niveau": niveau, "Toegewezen training": reden}
    for naam, niveau, reden in handmatig
]

csv_output = pd.DataFrame(alle_resultaten).to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Download volledige planning als CSV",
    data=csv_output,
    file_name="volledige_inplanning.csv",
    mime="text/csv"
)
