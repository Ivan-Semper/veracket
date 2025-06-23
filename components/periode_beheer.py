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

def restore_archived_period_for_planning(archive_name):
    """Restore an archived period to data folder for planning purposes"""
    try:
        archive_path = ARCHIVE_DIR / archive_name
        
        if not archive_path.exists():
            return False, "Archief map niet gevonden"
        
        # Clear current data first
        clear_success, cleared_files = clear_current_registrations()
        if not clear_success:
            return False, f"Fout bij wissen huidige data: {cleared_files}"
        
        # Copy archived files back to data folder
        files_restored = []
        
        for file_name in ["training1_inschrijvingen.csv", "training2_inschrijvingen.csv", "training3_inschrijvingen.csv"]:
            archive_file = archive_path / file_name
            if archive_file.exists():
                shutil.copy2(archive_file, DATA_DIR / file_name)
                files_restored.append(file_name)
        
        return True, files_restored
    
    except Exception as e:
        return False, str(e)

def get_current_working_period():
    """Get information about the current working period (for planning)"""
    # Check if we're working with an archived period
    if os.path.exists(DATA_DIR / "working_period.json"):
        try:
            with open(DATA_DIR / "working_period.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Default to current period
    status = load_periode_status()
    return {
        "type": "current", 
        "name": status.get("current_period", "Huidige periode"),
        "source": "live"
    }

def set_working_period(period_info):
    """Set the current working period for planning"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_DIR / "working_period.json", 'w', encoding='utf-8') as f:
        json.dump(period_info, f, indent=2, ensure_ascii=False)

def periode_beheer():
    st.title("📅 Periode Beheer")
    st.markdown("""
    **Verbeterde workflow:**
    - **Inschrijvingen** kunnen open/gesloten worden (voor het publiek)
    - **Planning** kan altijd worden uitgevoerd (ook bij gesloten inschrijvingen)
    - **Archief** kan worden geselecteerd voor herplanning
    """)
    
    # Load current status
    status = load_periode_status()
    counts = get_registration_counts()
    working_period = get_current_working_period()
    
    # Current period status
    st.subheader("📊 Huidige Periode Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if status["is_open"]:
            st.success("🟢 **INSCHRIJVINGEN OPEN**")
            st.write("Publiek kan zich aanmelden")
        else:
            st.error("🔴 **INSCHRIJVINGEN GESLOTEN**")
            st.write("Publiek kan zich niet aanmelden")
    
    with col2:
        if working_period["type"] == "current":
            st.info("📊 **LIVE DATA**")
        else:
            st.info("📁 **ARCHIEF DATA**")
        st.write("Voor planning/admin")
    
    with col3:
        st.metric("Totaal Aanmeldingen", counts["total"])
    
    with col4:
        st.metric("Training 1", counts["training1"])
        st.write(f"Training 2+3: {counts['training2'] + counts['training3']}")
    
    # Working period information
    st.info(f"🎯 **Werkende periode voor planning:** {working_period['name']}")
    if working_period["type"] == "archive":
        st.warning("⚠️ Je werkt nu met gearchiveerde data voor planning doeleinden")
    
    # Period information
    if status["current_period"]:
        st.write(f"📋 **Inschrijvings periode:** {status['current_period']}")
    
    if status["opened_date"]:
        st.write(f"🕐 **Inschrijvingen geopend:** {status['opened_date']}")
    
    if status["closed_date"]:
        st.write(f"🕐 **Inschrijvingen gesloten:** {status['closed_date']}")
    
    st.markdown("---")
    
    # Archive selection section
    st.subheader("📁 Selecteer Werkende Periode")
    
    archived_periods = get_archived_periods()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Huidige Live Data**")
        if st.button("🔄 Schakel naar Live Data", disabled=(working_period["type"] == "current")):
            set_working_period({"type": "current", "name": status.get("current_period", "Huidige periode"), "source": "live"})
            st.success("✅ Geschakeld naar live data")
            st.rerun()
    
    with col2:
        if archived_periods:
            st.write("**Gearchiveerde Periodes**")
            selected_archive = st.selectbox(
                "Selecteer archief voor planning:",
                options=["-- Kies een archief --"] + [p["name"] for p in archived_periods],
                key="archive_selector"
            )
            
            if selected_archive != "-- Kies een archief --":
                if st.button(f"📁 Laad '{selected_archive}' voor planning"):
                    with st.spinner(f"Laden van archief '{selected_archive}'..."):
                        success, result = restore_archived_period_for_planning(selected_archive)
                        
                        if success:
                            # Update working period
                            set_working_period({
                                "type": "archive",
                                "name": selected_archive,
                                "source": "archive",
                                "loaded_date": datetime.now().isoformat()
                            })
                            
                            st.success(f"✅ Archief '{selected_archive}' geladen voor planning!")
                            st.info(f"📁 Herstelde bestanden: {', '.join(result)}")
                            st.rerun()
                        else:
                            st.error(f"❌ Fout bij laden archief: {result}")
        else:
            st.info("Geen gearchiveerde periodes beschikbaar")
    
    st.markdown("---")
    
    # Registration management (separate from planning)
    st.subheader("🌐 Inschrijvingen Beheer")
    st.write("*Dit beïnvloedt alleen of het publiek zich kan aanmelden, niet de planning functionaliteit*")
    
    # Actions based on current status
    if status["is_open"]:
        # Period is open - show close option
        st.write("### 🔒 Inschrijvingen Sluiten")
        st.warning("⚠️ **Let op:** Dit sluit alleen de inschrijvingen af, je kunt nog steeds plannen!")
        
        if counts["total"] > 0:
            st.info(f"📊 Er zijn momenteel **{counts['total']} aanmeldingen** die gearchiveerd kunnen worden.")
            
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
                
                archive_option = st.radio(
                    "Wat wil je doen met de huidige data?",
                    ["Archiveren en doorwerken met live data", "Alleen archiveren (huidige data blijft beschikbaar)"]
                )
                
                close_confirm = st.checkbox("Ik bevestig dat ik de inschrijvingen wil sluiten")
                
                submit_close = st.form_submit_button("🔒 Inschrijvingen Sluiten", type="primary")
                
                if submit_close:
                    if not period_name.strip():
                        st.error("❌ Periode naam is verplicht!")
                    elif not close_confirm:
                        st.error("❌ Bevestig dat je de inschrijvingen wilt sluiten!")
                    else:
                        # Archive current period
                        with st.spinner("Archiveren van huidige periode..."):
                            success, result = archive_current_period(period_name.strip())
                            
                            if success:
                                if archive_option == "Archiveren en doorwerken met live data":
                                    # Clear current registrations
                                    clear_success, cleared_files = clear_current_registrations()
                                    if not clear_success:
                                        st.error(f"❌ Fout bij het wissen van huidige bestanden: {cleared_files}")
                                        return
                                    
                                    # Reset to live data
                                    set_working_period({
                                        "type": "current", 
                                        "name": "Nieuwe periode", 
                                        "source": "live"
                                    })
                                    info_msg = f"🗑️ Huidige bestanden gewist: {', '.join(cleared_files)}"
                                else:
                                    info_msg = "📊 Huidige data blijft beschikbaar voor planning"
                                
                                # Update status
                                new_status = {
                                    "is_open": False,
                                    "current_period": period_name.strip(),
                                    "opened_date": status.get("opened_date"),
                                    "closed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                save_periode_status(new_status)
                                
                                st.success(f"✅ **Inschrijvingen gesloten en periode '{period_name.strip()}' gearchiveerd!**")
                                st.info(f"📁 Gearchiveerde bestanden: {', '.join(result)}")
                                st.info(info_msg)
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ Fout bij archiveren: {result}")
        else:
            st.info("📝 Er zijn geen aanmeldingen om te archiveren.")
            
            if st.button("🔒 Inschrijvingen Sluiten (zonder archiveren)", type="secondary"):
                new_status = {
                    "is_open": False,
                    "current_period": "Gesloten",
                    "opened_date": status.get("opened_date"),
                    "closed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_periode_status(new_status)
                st.success("✅ Inschrijvingen gesloten!")
                st.rerun()
    
    else:
        # Period is closed - show open option
        st.write("### 🔓 Nieuwe Inschrijvingsperiode Starten")
        st.success("✅ Klaar om een nieuwe inschrijvingsperiode te starten!")
        
        with st.form("open_period_form"):
            st.write("### 📅 Nieuwe Inschrijvingsperiode")
            
            new_period_name = st.text_input(
                "Naam voor nieuwe periode (optioneel)",
                placeholder="Bijv. 2025 Periode 2, Lente 2025, etc.",
                help="Laat leeg voor automatische naamgeving"
            )
            
            submit_open = st.form_submit_button("🔓 Inschrijvingen Openen", type="primary")
            
            if submit_open:
                period_name = new_period_name.strip() if new_period_name.strip() else f"Periode gestart {datetime.now().strftime('%Y-%m-%d')}"
                
                new_status = {
                    "is_open": True,
                    "current_period": period_name,
                    "opened_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "closed_date": None
                }
                save_periode_status(new_status)
                
                st.success(f"✅ **Nieuwe inschrijvingsperiode '{period_name}' gestart!**")
                st.info("🎾 Aanmeldingen zijn nu weer mogelijk via het publieke formulier.")
                st.balloons()
                st.rerun()
    
    # Archived periods overview
    st.markdown("---")
    st.subheader("📁 Gearchiveerde Periodes")
    
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
                    
                    # Quick action buttons
                    if st.button(f"🔄 Gebruik voor planning", key=f"use_{period['name']}"):
                        with st.spinner(f"Laden van archief '{period['name']}'..."):
                            success, result = restore_archived_period_for_planning(period['name'])
                            
                            if success:
                                set_working_period({
                                    "type": "archive",
                                    "name": period['name'],
                                    "source": "archive",
                                    "loaded_date": datetime.now().isoformat()
                                })
                                
                                st.success(f"✅ Archief '{period['name']}' geladen!")
                                st.rerun()
                            else:
                                st.error(f"❌ Fout: {result}")
                
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
    
    # Status summary
    st.markdown("---")
    st.subheader("📊 Status Samenvatting")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🌐 Publiek Formulier:**")
        if status["is_open"]:
            st.success("✅ Inschrijvingen OPEN")
            st.write("→ http://localhost:8501")
        else:
            st.error("❌ Inschrijvingen GESLOTEN")
            st.write("→ Publiek kan zich niet aanmelden")
    
    with col2:
        st.write("**🎯 Planning Functionaliteit:**")
        st.success("✅ Altijd beschikbaar")
        st.write(f"→ Werkend met: {working_period['name']}")
        if working_period["type"] == "archive":
            st.write("→ Gearchiveerde data geladen") 