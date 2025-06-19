import streamlit as st
import pandas as pd
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TRAINING1_PATH = BASE_DIR / "data" / "training1_inschrijvingen.csv"
TRAINING2_PATH = BASE_DIR / "data" / "training2_inschrijvingen.csv"
TRAINING3_PATH = BASE_DIR / "data" / "training3_inschrijvingen.csv"

def clean_duplicates_manually():
    """Admin tool to manually clean duplicates based on phone number"""
    st.subheader("🧹 Duplicaten Opruimen")
    st.markdown("""
    **Let op**: Deze functie verwijdert automatisch alle duplicaten op basis van telefoonnummer. 
    Voor elke persoon wordt alleen de meest recente aanmelding behouden.
    """)
    
    training_files = [
        (TRAINING1_PATH, "Training 1 (Eerste keuze)"),
        (TRAINING2_PATH, "Training 2 (Tweede keuze)"),
        (TRAINING3_PATH, "Training 3 (Derde keuze)")
    ]
    
    duplicates_found = False
    
    for file_path, training_name in training_files:
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                
                if 'Telefoon' in df.columns and 'Inschrijfdatum' in df.columns:
                    # Count duplicates
                    duplicate_phones = df[df.duplicated(subset=['Telefoon'], keep=False)]['Telefoon'].unique()
                    
                    if len(duplicate_phones) > 0:
                        duplicates_found = True
                        st.warning(f"**{training_name}**: {len(duplicate_phones)} personen met duplicaten gevonden")
                        
                        # Show duplicate details
                        for phone in duplicate_phones:
                            phone_entries = df[df['Telefoon'] == phone].sort_values('Inschrijfdatum', ascending=False)
                            st.write(f"📞 {phone}: {len(phone_entries)} aanmeldingen")
                            for idx, entry in phone_entries.iterrows():
                                is_newest = idx == phone_entries.index[0]
                                status = "✅ Behouden" if is_newest else "❌ Wordt verwijderd"
                                st.write(f"  - {entry['Naam']} ({entry['Inschrijfdatum']}) {status}")
                    else:
                        st.success(f"**{training_name}**: Geen duplicaten gevonden")
                
            except Exception as e:
                st.error(f"Fout bij controleren {training_name}: {e}")
    
    if duplicates_found:
        if st.button("🧹 Duplicaten Opruimen", type="primary"):
            cleaned_count = 0
            
            for file_path, training_name in training_files:
                if file_path.exists():
                    try:
                        df = pd.read_csv(file_path)
                        
                        if 'Telefoon' in df.columns and 'Inschrijfdatum' in df.columns:
                            # Convert date column to datetime for proper sorting
                            df['Inschrijfdatum'] = pd.to_datetime(df['Inschrijfdatum'])
                            
                            # Keep only the most recent entry for each phone number
                            original_count = len(df)
                            df_cleaned = df.sort_values('Inschrijfdatum', ascending=False).drop_duplicates(subset=['Telefoon'], keep='first')
                            removed_count = original_count - len(df_cleaned)
                            
                            if removed_count > 0:
                                # Convert back to string format for saving
                                df_cleaned['Inschrijfdatum'] = df_cleaned['Inschrijfdatum'].dt.strftime('%Y-%m-%d %H:%M')
                                df_cleaned.to_csv(file_path, index=False)
                                cleaned_count += removed_count
                                st.success(f"**{training_name}**: {removed_count} duplicaten verwijderd")
                    
                    except Exception as e:
                        st.error(f"Fout bij opruimen {training_name}: {e}")
            
            if cleaned_count > 0:
                st.success(f"✅ Totaal {cleaned_count} duplicaten verwijderd!")
                st.balloons()
                st.rerun()
    else:
        st.success("✅ Geen duplicaten gevonden in alle bestanden!")

def aanmeldingen_overzicht():
    st.title("📋 Aanmeldingen Overzicht")
    st.markdown("""
    Hier kun je alle binnenkomende aanmeldingen bekijken, gesorteerd per training prioriteit.
    De aanmeldingen komen automatisch binnen via het publieke aanmeldformulier.
    """)
    
    # Add admin tools section
    with st.expander("🔧 Admin Tools"):
        clean_duplicates_manually()
    
    # Tabs voor verschillende trainingen
    tab1, tab2, tab3, tab_combined = st.tabs(["🥇 Training 1 (Eerste keuze)", "🥈 Training 2 (Tweede keuze)", "🥉 Training 3 (Derde keuze)", "📊 Gecombineerd overzicht"])
    
    with tab1:
        st.subheader("🥇 Eerste keuze trainingen")
        display_training_registrations(TRAINING1_PATH, "Training 1", "success")
    
    with tab2:
        st.subheader("🥈 Tweede keuze trainingen")
        display_training_registrations(TRAINING2_PATH, "Training 2", "info")
    
    with tab3:
        st.subheader("🥉 Derde keuze trainingen")
        display_training_registrations(TRAINING3_PATH, "Training 3", "warning")
    
    with tab_combined:
        st.subheader("📊 Gecombineerd overzicht alle aanmeldingen")
        display_combined_overview()

def display_training_registrations(file_path, training_name, status_type):
    """Display registrations for a specific training priority"""
    
    if not file_path.exists():
        st.info(f"📝 Nog geen aanmeldingen voor {training_name}")
        return
    
    try:
        df = pd.read_csv(file_path)
        
        if len(df) == 0:
            st.info(f"📝 Nog geen aanmeldingen voor {training_name}")
            return
        
        # Show summary
        col1, col2, col3 = st.columns(3)
        with col1:
            if status_type == "success":
                st.success(f"**{len(df)}** aanmeldingen")
            elif status_type == "info":
                st.info(f"**{len(df)}** aanmeldingen")
            else:
                st.warning(f"**{len(df)}** aanmeldingen")
        
        with col2:
            avg_strength = df['Speelsterkte'].mean() if 'Speelsterkte' in df.columns else 0
            st.metric("Gem. speelsterkte", f"{avg_strength:.1f}")
        
        with col3:
            recent_count = len(df[df['Inschrijfdatum'] == df['Inschrijfdatum'].max()]) if 'Inschrijfdatum' in df.columns else 0
            st.metric("Vandaag", recent_count)
        
        # Show detailed table
        st.markdown("### 📋 Gedetailleerd overzicht")
        
        # Select which columns to display
        display_columns = ['Naam', 'Telefoon', 'Speelsterkte', 'Voorkeur_1', 'Voorkeur_2', 'Voorkeur_3', 
                          'Trainingen_per_week', 'Toestemming_hoger_niveau', 'Inschrijfdatum']
        
        # Filter existing columns
        available_columns = [col for col in display_columns if col in df.columns]
        df_display = df[available_columns].copy()
        
        # Format the display
        if 'Inschrijfdatum' in df_display.columns:
            df_display['Inschrijfdatum'] = pd.to_datetime(df_display['Inschrijfdatum']).dt.strftime('%d-%m-%Y %H:%M')
        
        # Sort by registration date (newest first)
        if 'Inschrijfdatum' in df_display.columns:
            df_display = df_display.sort_values('Inschrijfdatum', ascending=False)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Download button
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Download {training_name} CSV",
            data=csv_data,
            file_name=f"{training_name.lower().replace(' ', '_')}_aanmeldingen.csv",
            mime="text/csv"
        )
        
        # Show extra messages if available
        if 'Extra_bericht' in df.columns:
            messages = df[df['Extra_bericht'].notna() & (df['Extra_bericht'] != '')]
            if len(messages) > 0:
                st.markdown("### 💬 Extra berichten van deelnemers")
                for idx, row in messages.iterrows():
                    st.info(f"**{row['Naam']}**: {row['Extra_bericht']}")
        
    except Exception as e:
        st.error(f"Fout bij het laden van {training_name}: {e}")

def display_combined_overview():
    """Display combined overview of all registrations"""
    
    all_data = []
    
    # Load all training files
    training_files = [
        (TRAINING1_PATH, "Eerste keuze", "🥇"),
        (TRAINING2_PATH, "Tweede keuze", "🥈"), 
        (TRAINING3_PATH, "Derde keuze", "🥉")
    ]
    
    for file_path, priority_name, icon in training_files:
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                df['Training_Prioriteit'] = priority_name
                df['Prioriteit_Icon'] = icon
                all_data.append(df)
            except Exception as e:
                st.error(f"Fout bij laden {priority_name}: {e}")
    
    if not all_data:
        st.info("📝 Nog geen aanmeldingen gevonden")
        return
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Summary statistics
    st.markdown("### 📊 Overzicht statistieken")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Totaal aanmeldingen", len(combined_df))
    
    with col2:
        unique_people = combined_df['Naam'].nunique() if 'Naam' in combined_df.columns else 0
        st.metric("Unieke personen", unique_people)
    
    with col3:
        avg_strength = combined_df['Speelsterkte'].mean() if 'Speelsterkte' in combined_df.columns else 0
        st.metric("Gem. speelsterkte", f"{avg_strength:.1f}")
    
    with col4:
        with_permission = len(combined_df[combined_df['Toestemming_hoger_niveau'] == 'Ja']) if 'Toestemming_hoger_niveau' in combined_df.columns else 0
        st.metric("Met toestemming", with_permission)
    
    # Show breakdown per priority
    st.markdown("### 📈 Verdeling per prioriteit")
    priority_counts = combined_df['Training_Prioriteit'].value_counts()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        count1 = priority_counts.get('Eerste keuze', 0)
        st.success(f"🥇 Eerste keuze: **{count1}**")
    with col2:
        count2 = priority_counts.get('Tweede keuze', 0)
        st.info(f"🥈 Tweede keuze: **{count2}**")
    with col3:
        count3 = priority_counts.get('Derde keuze', 0)
        st.warning(f"🥉 Derde keuze: **{count3}**")
    
    # Detailed combined table
    st.markdown("### 📋 Alle aanmeldingen")
    
    # Select display columns
    display_columns = ['Prioriteit_Icon', 'Training_Prioriteit', 'Naam', 'Telefoon', 'Speelsterkte', 
                      'Voorkeur_1', 'Trainingen_per_week', 'Inschrijfdatum']
    
    available_columns = [col for col in display_columns if col in combined_df.columns]
    df_display = combined_df[available_columns].copy()
    
    # Format dates
    if 'Inschrijfdatum' in df_display.columns:
        df_display['Inschrijfdatum'] = pd.to_datetime(df_display['Inschrijfdatum']).dt.strftime('%d-%m-%Y %H:%M')
    
    # Sort by registration date (newest first)
    if 'Inschrijfdatum' in df_display.columns:
        df_display = df_display.sort_values('Inschrijfdatum', ascending=False)
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Download combined data
    csv_data = combined_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download alle aanmeldingen CSV",
        data=csv_data,
        file_name="alle_aanmeldingen_gecombineerd.csv",
        mime="text/csv"
    ) 