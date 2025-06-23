import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

# Set page config
st.set_page_config(page_title="Complete Planning", page_icon="🎾", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
RONDE_STATUS_PATH = BASE_DIR / "data" / "ronde_planning_status.json"

def load_ronde_status():
    """Load the current round planning status"""
    if RONDE_STATUS_PATH.exists():
        try:
            with open(RONDE_STATUS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "current_round": 1,
        "rounds_completed": [],
        "manual_assignments": {},
        "excluded_people": [],
        "planning_history": []
    }

def get_current_working_period():
    """Get information about the current working period"""
    try:
        from components.periode_beheer import get_current_working_period
        return get_current_working_period()
    except:
        return {"type": "live", "name": "Live Data", "folder": ""}

def main():
    st.title("🎾 Complete Planning Overzicht")
    
    # Get current working period info
    working_period = get_current_working_period()
    st.info(f"📊 **Data bron:** {working_period['type'].title()} - {working_period['name']}")
    
    # Load planning status
    status = load_ronde_status()
    
    if not status.get("planning_history"):
        st.warning("⚠️ Nog geen planning beschikbaar. Start eerst met plannen in het hoofdsysteem.")
        st.markdown("---")
        st.markdown("### 💡 Hoe te gebruiken:")
        st.markdown("1. Ga naar de hoofdpagina en start met plannen")
        st.markdown("2. Plan alle rondes en wijs mensen handmatig toe")
        st.markdown("3. Kom terug naar deze pagina voor het complete overzicht")
        return
    
    # Check if planning is complete (no more people need manual assignment)
    all_people_assigned = True
    total_people_needing_manual = 0
    
    for round_data in status.get("planning_history", []):
        round_num = round_data["round"]
        manual_assignments = status.get("manual_assignments", {}).get(str(round_num), [])
        
        # Get people who still need manual assignment for this round
        manual_needed = round_data.get("manual_needed", [])
        already_assigned_names = {assignment["name"] for assignment in manual_assignments}
        
        # Filter out people who have already been manually assigned
        filtered_manual_needed = []
        for person_data in manual_needed:
            person_name = person_data[0] if len(person_data) > 0 else ""
            if person_name not in already_assigned_names:
                filtered_manual_needed.append(person_data)
        
        if filtered_manual_needed:
            total_people_needing_manual += len(filtered_manual_needed)
            all_people_assigned = False
    
    # Collect all assignments from all rounds
    all_training_groups = {}
    all_assignments_for_export = []
    
    for round_data in status["planning_history"]:
        round_num = round_data["round"]
        
        # Add automatic assignments
        for training, people in round_data.get("assigned_by_training", {}).items():
            if training not in all_training_groups:
                all_training_groups[training] = []
            for name, level in people:
                # Convert float level to int if it's a whole number
                if isinstance(level, float) and level.is_integer():
                    level = int(level)
                member_data = {
                    "Naam": str(name),
                    "Niveau": str(level),
                    "Ronde": str(round_num),
                    "Type": "Automatisch",
                    "Training": str(training)
                }
                all_training_groups[training].append(member_data)
                all_assignments_for_export.append(member_data)
        
        # Add manual assignments
        manual_assignments = status.get("manual_assignments", {}).get(str(round_num), [])
        for assignment in manual_assignments:
            training = assignment["training"]
            if training not in all_training_groups:
                all_training_groups[training] = []
            # Use stored level if available, otherwise use "Handmatig"
            level = assignment.get("level", "Handmatig")
            if isinstance(level, float) and level.is_integer():
                level = int(level)
            member_data = {
                "Naam": str(assignment["name"]),
                "Niveau": str(level),
                "Ronde": str(round_num),
                "Type": "Handmatig",
                "Training": str(training)
            }
            all_training_groups[training].append(member_data)
            all_assignments_for_export.append(member_data)
    
    if not all_assignments_for_export:
        st.warning("⚠️ Nog geen toewijzingen gevonden in de planning.")
        return
    
    # Show completion status
    if all_people_assigned:
        st.success("✅ **Planning Status:** Alle deelnemers zijn succesvol ingepland!")
    else:
        st.warning(f"⏳ **Planning Status:** Er zijn nog {total_people_needing_manual} mensen die handmatig toegewezen moeten worden.")
    
    # Summary statistics
    st.markdown("---")
    st.subheader("📊 Planning Statistieken")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_people = len(all_assignments_for_export)
        st.metric("👥 Totaal Deelnemers", total_people)
    with col2:
        total_trainings = len(all_training_groups)
        st.metric("🎾 Aantal Trainingen", total_trainings)
    with col3:
        auto_count = len([a for a in all_assignments_for_export if a["Type"] == "Automatisch"])
        st.metric("🤖 Automatisch", auto_count)
    with col4:
        manual_count = len([a for a in all_assignments_for_export if a["Type"] == "Handmatig"])
        st.metric("👤 Handmatig", manual_count)
    
    # Training groups overview with beautiful tables
    st.markdown("---")
    st.subheader("🎾 Trainingsgroepen Overzicht")
    
    # Sort trainings by day and time for logical order
    def sort_training_key(training_name):
        days_order = {'Maandag': 1, 'Dinsdag': 2, 'Woensdag': 3, 'Donderdag': 4, 'Vrijdag': 5, 'Zaterdag': 6, 'Zondag': 7}
        day = training_name.split()[0]
        return days_order.get(day, 8)
    
    sorted_trainings = sorted(all_training_groups.items(), key=lambda x: sort_training_key(x[0]))
    
    for training, members in sorted_trainings:
        if members:  # Only show trainings that have people
            # Create a beautiful header for each training
            st.markdown(f"### 🎾 {training}")
            
            # Create DataFrame for this training group
            df_group = pd.DataFrame(members)
            df_group = df_group.sort_values('Naam')
            
            # Create columns for layout
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Display beautiful table with custom styling
                display_df = df_group[["Naam", "Niveau", "Type", "Ronde"]].copy()
                
                # Add emoji indicators for type
                display_df['Type'] = display_df['Type'].apply(
                    lambda x: f"🤖 {x}" if x == "Automatisch" else f"👤 {x}"
                )
                
                # Rename columns for better display
                display_df.columns = ["👤 Naam", "📊 Niveau", "⚙️ Toewijzing", "🔄 Ronde"]
                
                st.dataframe(
                    display_df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "👤 Naam": st.column_config.TextColumn("👤 Naam", width="medium"),
                        "📊 Niveau": st.column_config.TextColumn("📊 Niveau", width="small"),
                        "⚙️ Toewijzing": st.column_config.TextColumn("⚙️ Toewijzing", width="medium"),
                        "🔄 Ronde": st.column_config.NumberColumn("🔄 Ronde", width="small")
                    }
                )
            
            with col2:
                # Training statistics in a nice box
                st.markdown("**📊 Training Stats**")
                
                auto_count = len([m for m in members if m["Type"] == "Automatisch"])
                manual_count = len([m for m in members if m["Type"] == "Handmatig"])
                total_count = len(members)
                
                # Create metrics in a container
                with st.container():
                    st.metric("👥 Totaal", total_count)
                    st.metric("🤖 Automatisch", auto_count)
                    st.metric("👤 Handmatig", manual_count)
                    
                    # Calculate percentage
                    if total_count > 0:
                        auto_percentage = (auto_count / total_count) * 100
                        st.metric("📈 % Automatisch", f"{auto_percentage:.1f}%")
            
            st.markdown("---")
    
    # Summary table at the bottom
    st.subheader("📊 Samenvatting per Training")
    
    # Create summary statistics table
    summary_data = []
    for training, members in sorted_trainings:
        if members:
            auto_count = len([m for m in members if m["Type"] == "Automatisch"])
            manual_count = len([m for m in members if m["Type"] == "Handmatig"])
            total_count = len(members)
            
            summary_data.append({
                "🎾 Training": training,
                "👥 Totaal": total_count,
                "🤖 Automatisch": auto_count,
                "👤 Handmatig": manual_count,
                "📈 % Automatisch": f"{(auto_count/total_count*100):.1f}%" if total_count > 0 else "0%"
            })
    
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        
        st.dataframe(
            df_summary, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "🎾 Training": st.column_config.TextColumn("🎾 Training", width="large"),
                "👥 Totaal": st.column_config.NumberColumn("👥 Totaal", width="small"),
                "🤖 Automatisch": st.column_config.NumberColumn("🤖 Automatisch", width="small"),
                "👤 Handmatig": st.column_config.NumberColumn("👤 Handmatig", width="small"),
                "📈 % Automatisch": st.column_config.TextColumn("📈 % Automatisch", width="small")
            }
        )
    
    # Export section with beautiful styling
    st.markdown("---")
    st.subheader("📥 Complete Planning Downloaden")
    
    # Create complete export DataFrame
    df_complete_export = pd.DataFrame(all_assignments_for_export)
    df_complete_export = df_complete_export.sort_values(['Training', 'Naam'])
    
    # Reorder columns for better export
    export_columns = ["Training", "Naam", "Niveau", "Type", "Ronde"]
    df_complete_export = df_complete_export[export_columns]
    
    # Add emojis to export data for better readability
    df_export_display = df_complete_export.copy()
    df_export_display['Type'] = df_export_display['Type'].apply(
        lambda x: f"🤖 {x}" if x == "Automatisch" else f"👤 {x}"
    )
    
    # Rename columns for display
    df_export_display.columns = ["🎾 Training", "👤 Naam", "📊 Niveau", "⚙️ Toewijzing", "🔄 Ronde"]
    
    # Create layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**Download de complete planning van alle trainingsgroepen:**")
        
        # Create CSV with proper encoding
        csv_complete_export = df_complete_export.to_csv(index=False, encoding='utf-8-sig', sep=';')
        
        # Download button for complete planning
        st.download_button(
            label="🎾 Download Complete Planning (CSV)",
            data=csv_complete_export,
            file_name=f"complete_planning_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            type="primary",
            help="Download alle trainingsgroepen in één CSV bestand",
            use_container_width=True
        )
    
    with col2:
        st.markdown("**📊 Export Samenvatting:**")
        with st.container():
            st.metric("📄 Regels", len(df_complete_export))
            st.metric("🎾 Trainingen", len(all_training_groups))
            st.metric("👥 Unieke Deelnemers", len(set(df_complete_export['Naam'])))
    
    # Show beautiful preview of the complete data
    st.markdown("---")
    st.markdown("**👀 Preview van Export Data:**")
    
    # Display preview with beautiful styling
    preview_rows = min(15, len(df_export_display))
    st.dataframe(
        df_export_display.head(preview_rows), 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "🎾 Training": st.column_config.TextColumn("🎾 Training", width="large"),
            "👤 Naam": st.column_config.TextColumn("👤 Naam", width="medium"),
            "📊 Niveau": st.column_config.TextColumn("📊 Niveau", width="small"),
            "⚙️ Toewijzing": st.column_config.TextColumn("⚙️ Toewijzing", width="medium"),
            "🔄 Ronde": st.column_config.NumberColumn("🔄 Ronde", width="small")
        }
    )
    
    if len(df_export_display) > preview_rows:
        st.info(f"... en nog {len(df_export_display) - preview_rows} regels meer in de volledige export.")

if __name__ == "__main__":
    main() 