import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime, date
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARCHIVE_DIR = BASE_DIR / "archive"
TRAINING1_PATH = DATA_DIR / "training1_inschrijvingen.csv"
TRAINING2_PATH = DATA_DIR / "training2_inschrijvingen.csv"
TRAINING3_PATH = DATA_DIR / "training3_inschrijvingen.csv"
PERIODE_STATUS_PATH = DATA_DIR / "periode_status.json"

def load_periode_status():
    """Load current period status"""
    if PERIODE_STATUS_PATH.exists():
        try:
            with open(PERIODE_STATUS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Default status
    return {
        "is_open": True,
        "current_period": None,
        "opened_date": None,
        "closed_date": None
    }

def save_periode_status(status):
    """Save period status"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PERIODE_STATUS_PATH, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

def get_registration_counts():
    """Get current registration counts"""
    counts = {"training1": 0, "training2": 0, "training3": 0, "total": 0}
    
    if TRAINING1_PATH.exists():
        try:
            df1 = pd.read_csv(TRAINING1_PATH)
            counts["training1"] = len(df1)
        except:
            pass
    
    if TRAINING2_PATH.exists():
        try:
            df2 = pd.read_csv(TRAINING2_PATH)
            counts["training2"] = len(df2)
        except:
            pass
    
    if TRAINING3_PATH.exists():
        try:
            df3 = pd.read_csv(TRAINING3_PATH)
            counts["training3"] = len(df3)
        except:
            pass
    
    counts["total"] = counts["training1"] + counts["training2"] + counts["training3"]
    return counts

def archive_current_period(period_name):
    """Archive current registrations to a named period folder"""
    try:
        # Create archive directory structure
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        period_dir = ARCHIVE_DIR / period_name
        os.makedirs(period_dir, exist_ok=True)
        
        # Archive registration files
        files_archived = []
        
        if TRAINING1_PATH.exists():
            shutil.copy2(TRAINING1_PATH, period_dir / "training1_inschrijvingen.csv")
            files_archived.append("training1_inschrijvingen.csv")
        
        if TRAINING2_PATH.exists():
            shutil.copy2(TRAINING2_PATH, period_dir / "training2_inschrijvingen.csv")
            files_archived.append("training2_inschrijvingen.csv")
        
        if TRAINING3_PATH.exists():
            shutil.copy2(TRAINING3_PATH, period_dir / "training3_inschrijvingen.csv")
            files_archived.append("training3_inschrijvingen.csv")
        
        # Create archive metadata
        metadata = {
            "period_name": period_name,
            "archived_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_archived": files_archived,
            "registration_counts": get_registration_counts()
        }
        
        with open(period_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return True, files_archived
    
    except Exception as e:
        return False, str(e)

def clear_current_registrations():
    """Clear current registration files"""
    try:
        files_cleared = []
        
        if TRAINING1_PATH.exists():
            os.remove(TRAINING1_PATH)
            files_cleared.append("training1_inschrijvingen.csv")
        
        if TRAINING2_PATH.exists():
            os.remove(TRAINING2_PATH)
            files_cleared.append("training2_inschrijvingen.csv")
        
        if TRAINING3_PATH.exists():
            os.remove(TRAINING3_PATH)
            files_cleared.append("training3_inschrijvingen.csv")
        
        return True, files_cleared
    
    except Exception as e:
        return False, str(e)

def get_archived_periods():
    """Get list of archived periods"""
    if not ARCHIVE_DIR.exists():
        return []
    
    periods = []
    for item in ARCHIVE_DIR.iterdir():
        if item.is_dir():
            metadata_path = item / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    periods.append({
                        "name": item.name,
                        "metadata": metadata
                    })
                except:
                    periods.append({
                        "name": item.name,
                        "metadata": {"period_name": item.name, "archived_date": "Onbekend"}
                    })
    
    return sorted(periods, key=lambda x: x["metadata"].get("archived_date", ""), reverse=True)

def periode_beheer():
    st.title("📅 Periode Beheer")
    st.markdown("""
    Hier kun je trainingsperiodes openen en sluiten. Wanneer je een periode sluit, 
    worden alle huidige aanmeldingen gearchiveerd en kan er een nieuwe periode beginnen.
    """)
    
    # Load current status
    status = load_periode_status()
    counts = get_registration_counts()
    
    # Current period status
    st.subheader("📊 Huidige Periode Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if status["is_open"]:
            st.success("🟢 **OPEN**")
            st.write("Aanmeldingen mogelijk")
        else:
            st.error("🔴 **GESLOTEN**")
            st.write("Aanmeldingen geblokkeerd")
    
    with col2:
        st.metric("Totaal Aanmeldingen", counts["total"])
    
    with col3:
        st.metric("Training 1", counts["training1"])
    
    with col4:
        st.metric("Training 2 + 3", counts["training2"] + counts["training3"])
    
    # Period information
    if status["current_period"]:
        st.info(f"📋 **Huidige periode:** {status['current_period']}")
    
    if status["opened_date"]:
        st.write(f"🕐 **Geopend op:** {status['opened_date']}")
    
    if status["closed_date"]:
        st.write(f"🕐 **Gesloten op:** {status['closed_date']}")
    
    st.markdown("---")
    
    # Actions based on current status
    if status["is_open"]:
        # Period is open - show close option
        st.subheader("🔒 Periode Sluiten")
        st.warning("⚠️ **Let op:** Sluiten van de periode archiveert alle huidige aanmeldingen!")
        
        if counts["total"] > 0:
            st.info(f"📊 Er zijn momenteel **{counts['total']} aanmeldingen** die gearchiveerd zullen worden.")
            
            with st.form("close_period_form"):
                st.write("### 📁 Archief Instellingen")
                
                # Suggest period name based on current date
                current_year = datetime.now().year
                suggested_name = f"{current_year} Periode {datetime.now().month//4 + 1}"
                
                period_name = st.text_input(
                    "Naam voor deze periode *",
                    value=suggested_name,
                    placeholder="Bijv. 2025 Periode 1, Winter 2025, etc.",
                    help="Geef een duidelijke naam voor deze trainingsperiode"
                )
                
                close_confirm = st.checkbox("Ik bevestig dat ik deze periode wil sluiten en archiveren")
                
                submit_close = st.form_submit_button("🔒 Periode Sluiten en Archiveren", type="primary")
                
                if submit_close:
                    if not period_name.strip():
                        st.error("❌ Periode naam is verplicht!")
                    elif not close_confirm:
                        st.error("❌ Bevestig dat je de periode wilt sluiten!")
                    else:
                        # Archive current period
                        with st.spinner("Archiveren van huidige periode..."):
                            success, result = archive_current_period(period_name.strip())
                            
                            if success:
                                # Clear current registrations
                                clear_success, cleared_files = clear_current_registrations()
                                
                                if clear_success:
                                    # Update status
                                    new_status = {
                                        "is_open": False,
                                        "current_period": period_name.strip(),
                                        "opened_date": status.get("opened_date"),
                                        "closed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    }
                                    save_periode_status(new_status)
                                    
                                    st.success(f"✅ **Periode '{period_name.strip()}' succesvol gesloten en gearchiveerd!**")
                                    st.info(f"📁 Gearchiveerde bestanden: {', '.join(result)}")
                                    st.info(f"🗑️ Huidige bestanden gewist: {', '.join(cleared_files)}")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Fout bij het wissen van huidige bestanden: {cleared_files}")
                            else:
                                st.error(f"❌ Fout bij archiveren: {result}")
        else:
            st.info("📝 Er zijn geen aanmeldingen om te archiveren. Je kunt de periode direct sluiten.")
            
            if st.button("🔒 Periode Sluiten (zonder archiveren)", type="secondary"):
                new_status = {
                    "is_open": False,
                    "current_period": "Leeg",
                    "opened_date": status.get("opened_date"),
                    "closed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_periode_status(new_status)
                st.success("✅ Periode gesloten!")
                st.rerun()
    
    else:
        # Period is closed - show open option
        st.subheader("🔓 Nieuwe Periode Starten")
        st.success("✅ Klaar om een nieuwe trainingsperiode te starten!")
        
        with st.form("open_period_form"):
            st.write("### 📅 Nieuwe Periode")
            
            new_period_name = st.text_input(
                "Naam voor nieuwe periode (optioneel)",
                placeholder="Bijv. 2025 Periode 2, Lente 2025, etc.",
                help="Laat leeg voor automatische naamgeving"
            )
            
            submit_open = st.form_submit_button("🔓 Nieuwe Periode Starten", type="primary")
            
            if submit_open:
                period_name = new_period_name.strip() if new_period_name.strip() else f"Periode gestart {datetime.now().strftime('%Y-%m-%d')}"
                
                new_status = {
                    "is_open": True,
                    "current_period": period_name,
                    "opened_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "closed_date": None
                }
                save_periode_status(new_status)
                
                st.success(f"✅ **Nieuwe periode '{period_name}' gestart!**")
                st.info("🎾 Aanmeldingen zijn nu weer mogelijk via het publieke formulier.")
                st.balloons()
                st.rerun()
    
    # Archived periods overview
    st.markdown("---")
    st.subheader("📁 Gearchiveerde Periodes")
    
    archived_periods = get_archived_periods()
    
    if archived_periods:
        st.write(f"**{len(archived_periods)} gearchiveerde periode(s) gevonden:**")
        
        for period in archived_periods:
            with st.expander(f"📁 {period['name']} - {period['metadata'].get('archived_date', 'Onbekend')[:10]}"):
                metadata = period['metadata']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Periode naam:** {metadata.get('period_name', 'Onbekend')}")
                    st.write(f"**Gearchiveerd op:** {metadata.get('archived_date', 'Onbekend')}")
                    
                    if 'registration_counts' in metadata:
                        counts = metadata['registration_counts']
                        st.write(f"**Totaal aanmeldingen:** {counts.get('total', 0)}")
                
                with col2:
                    if 'files_archived' in metadata:
                        st.write("**Gearchiveerde bestanden:**")
                        for file in metadata['files_archived']:
                            st.write(f"• {file}")
                
                # Download archived files
                archive_path = ARCHIVE_DIR / period['name']
                if archive_path.exists():
                    st.write("**Download bestanden:**")
                    
                    for file_name in ["training1_inschrijvingen.csv", "training2_inschrijvingen.csv", "training3_inschrijvingen.csv"]:
                        file_path = archive_path / file_name
                        if file_path.exists():
                            try:
                                with open(file_path, 'rb') as f:
                                    st.download_button(
                                        label=f"📥 {file_name}",
                                        data=f.read(),
                                        file_name=f"{period['name']}_{file_name}",
                                        mime="text/csv",
                                        key=f"download_{period['name']}_{file_name}"
                                    )
                            except:
                                st.write(f"❌ Fout bij laden {file_name}")
    else:
        st.info("📝 Nog geen gearchiveerde periodes gevonden.")
    
    # Registration status for public form
    st.markdown("---")
    st.subheader("🌐 Publiek Formulier Status")
    
    if status["is_open"]:
        st.success("✅ Het publieke aanmeldformulier is **ACTIEF**")
        st.write("Mensen kunnen zich aanmelden via: http://localhost:8502")
    else:
        st.error("❌ Het publieke aanmeldformulier is **GEBLOKKEERD**")
        st.write("Mensen kunnen zich momenteel niet aanmelden.") 