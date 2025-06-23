import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
from utils.logic import plan_spelers

BASE_DIR = Path(__file__).resolve().parent.parent
TRAINING1_PATH = BASE_DIR / "data" / "training1_inschrijvingen.csv"
TRAINING2_PATH = BASE_DIR / "data" / "training2_inschrijvingen.csv"
TRAINING3_PATH = BASE_DIR / "data" / "training3_inschrijvingen.csv"
TRAININGEN_PATH = BASE_DIR / "data" / "trainings.csv"
RONDE_STATUS_PATH = BASE_DIR / "data" / "ronde_planning_status.json"

def load_ronde_status():
    """Load the current round planning status"""
    if RONDE_STATUS_PATH.exists():
        try:
            with open(RONDE_STATUS_PATH, 'r', encoding='utf-8') as f:
                status = json.load(f)
                
                # Clean up duplicate entries in planning history
                if "planning_history" in status:
                    seen_rounds = {}
                    cleaned_history = []
                    
                    for round_data in status["planning_history"]:
                        round_num = round_data.get("round")
                        if round_num not in seen_rounds:
                            cleaned_history.append(round_data)
                            seen_rounds[round_num] = True
                        else:
                            # Keep the most recent timestamp for this round
                            existing_index = next(i for i, r in enumerate(cleaned_history) if r.get("round") == round_num)
                            existing_timestamp = cleaned_history[existing_index].get("timestamp", "")
                            current_timestamp = round_data.get("timestamp", "")
                            
                            if current_timestamp > existing_timestamp:
                                cleaned_history[existing_index] = round_data
                    
                    status["planning_history"] = cleaned_history
                    
                    # Save cleaned status
                    with open(RONDE_STATUS_PATH, 'w', encoding='utf-8') as f:
                        json.dump(status, f, indent=2, ensure_ascii=False)
                
                return status
        except:
            pass
    
    # Default status
    return {
        "current_round": 1,
        "rounds_completed": [],
        "manual_assignments": {},
        "excluded_people": [],
        "planning_history": []
    }

def save_ronde_status(status):
    """Save the round planning status"""
    os.makedirs("data", exist_ok=True)
    with open(RONDE_STATUS_PATH, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

def get_available_people_for_round(round_num, status):
    """Get people available for planning in the current round"""
    
    # Load the appropriate CSV based on round
    if round_num == 1:
        csv_path = TRAINING1_PATH
    elif round_num == 2:
        csv_path = TRAINING2_PATH
    elif round_num == 3:
        csv_path = TRAINING3_PATH
    else:
        return pd.DataFrame()
    
    if not csv_path.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(csv_path)
    
    # Only filter out manually excluded people
    # Don't filter based on previous round assignments because:
    # - Each round reads from a different CSV file
    # - People who want 2x/3x per week should appear in multiple rounds
    # - The CSV files already contain the correct people for each round
    excluded = status.get("excluded_people", [])
    
    # Filter out only excluded people (not previously assigned people)
    available = df[~df["Naam"].isin(excluded)].copy()
    
    return available

def get_people_already_assigned_to_trainings(status, current_round):
    """Get a dictionary of people already assigned to specific trainings in previous rounds"""
    people_training_map = {}  # person_name -> [list of training names]
    
    for round_data in status.get("planning_history", []):
        if round_data["round"] < current_round:
            # From automatic assignments
            for training_name, people in round_data.get("assigned_by_training", {}).items():
                for name, level in people:
                    if name not in people_training_map:
                        people_training_map[name] = []
                    people_training_map[name].append(training_name)
            
            # From manual assignments
            manual_assignments = status.get("manual_assignments", {}).get(str(round_data["round"]), [])
            for assignment in manual_assignments:
                name = assignment["name"]
                training = assignment["training"]
                if name not in people_training_map:
                    people_training_map[name] = []
                people_training_map[name].append(training)
    
    return people_training_map

def filter_people_for_available_trainings(people_df, trainingen_df, people_training_map):
    """Filter people based on which trainings they can still be assigned to"""
    if len(people_df) == 0:
        return people_df
    
    # Create list of all available training names
    available_training_names = []
    for _, row in trainingen_df.iterrows():
        # Create training name based on available columns
        if 'Training Naam' in row and pd.notna(row['Training Naam']):
            training_name = f"{row['Dag']} {row['Tijd']} - {row['Training Naam']}"
        else:
            trainer_text = f" - {row['Trainer']}" if pd.notna(row['Trainer']) and row['Trainer'].strip() else ""
            training_name = f"{row['Dag']} {row['Tijd']}{trainer_text}"
        available_training_names.append(training_name)
    
    # Filter people who can still be assigned to at least one training
    filtered_people = []
    
    for idx, person in people_df.iterrows():
        person_name = person['Naam']
        already_assigned_trainings = people_training_map.get(person_name, [])
        
        # Check if person can be assigned to any remaining training
        can_be_assigned = False
        for training_name in available_training_names:
            if training_name not in already_assigned_trainings:
                can_be_assigned = True
                break
        
        if can_be_assigned:
            filtered_people.append(person)
    
    if filtered_people:
        return pd.DataFrame(filtered_people)
    else:
        return pd.DataFrame()

def plan_single_round(people_df, trainingen_df, round_num, status):
    """Plan a single round using the existing logic, but prevent duplicate training assignments"""
    if len(people_df) == 0:
        return {}, []
    
    # Get people already assigned to trainings in previous rounds
    people_training_map = get_people_already_assigned_to_trainings(status, round_num)
    
    # Filter people who can still be assigned to available trainings
    filtered_people = filter_people_for_available_trainings(people_df, trainingen_df, people_training_map)
    
    if len(filtered_people) == 0:
        return {}, []
    
    # Use the existing planning logic with filtered people
    planning, handmatig = plan_spelers(filtered_people, trainingen_df)
    
    # Additional check: remove people from planning if they're already assigned to that training
    cleaned_planning = {}
    additional_manual = []
    
    for training_name, people_list in planning.items():
        cleaned_people = []
        for name, level in people_list:
            already_assigned_trainings = people_training_map.get(name, [])
            if training_name not in already_assigned_trainings:
                cleaned_people.append((name, level))
            else:
                additional_manual.append((name, level, f"Al toegewezen aan {training_name} in vorige ronde"))
        
        if cleaned_people:
            cleaned_planning[training_name] = cleaned_people
    
    # Add additional manual cases
    handmatig.extend(additional_manual)
    
    return cleaned_planning, handmatig

def ronde_planning_systeem():
    st.title("🎯 Ronde-gebaseerde Planning")
    
    # Import periode management functions
    from components.periode_beheer import get_current_working_period, load_periode_status
    
    # Get current working period and registration status
    working_period = get_current_working_period()
    registration_status = load_periode_status()
    
    # Show current working period
    if working_period["type"] == "archive":
        st.info(f"🎯 **Planning met gearchiveerde periode:** {working_period['name']}")
        st.warning("⚠️ Je werkt nu met gearchiveerde data. Alle planning wordt gedaan op basis van deze data.")
    else:
        st.info(f"🎯 **Planning met live data:** {working_period['name']}")
    
    # Show registration status (separate from planning)
    if registration_status["is_open"]:
        st.success("✅ **Inschrijvingen zijn open** - Planning kan worden uitgevoerd")
    else:
        st.error("❌ **Inschrijvingen zijn gesloten** - Planning kan nog steeds worden uitgevoerd")
    
    st.markdown("""
    **Stapsgewijze planning systeem:**
    - **Ronde 1**: Plan mensen die 1x, 2x of 3x per week willen trainen - hun EERSTE training
    - **Ronde 2**: Plan mensen die 2x of 3x per week willen trainen - hun TWEEDE training  
    - **Ronde 3**: Plan mensen die 3x per week willen trainen - hun DERDE training
    
    **Voorbeeld:** Als Jan 2x per week wil trainen:
    - Ronde 1: Jan wordt ingepland voor zijn eerste training (uit training1_inschrijvingen.csv)
    - Ronde 2: Jan wordt ingepland voor zijn tweede training (uit training2_inschrijvingen.csv)
    
    **Belangrijk:** Mensen die 2x of 3x per week willen trainen verschijnen in meerdere rondes!
    Dit is normaal omdat ze meerdere trainingen nodig hebben.
    
    Na elke ronde kun je handmatig edge cases oplossen voordat je naar de volgende ronde gaat.
    
    **💡 Tip:** Planning werkt altijd, ongeacht of inschrijvingen open of gesloten zijn!
    """)
    
    # Load current status
    status = load_ronde_status()
    current_round = status["current_round"]
    
    # Check if training files exist
    if not TRAININGEN_PATH.exists():
        st.error("❌ Trainingen bestand niet gevonden in 'data/' map.")
        st.info("💡 Zorg ervoor dat je trainingen hebt gedefinieerd in de Trainingsbeheer sectie.")
        return
    
    trainingen = pd.read_csv(TRAININGEN_PATH)
    
    # Quick status overview
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Werkende Periode", working_period["type"].title())
        st.write(working_period["name"][:20] + "..." if len(working_period["name"]) > 20 else working_period["name"])
    
    with col2:
        if registration_status["is_open"]:
            st.metric("Inschrijvingen", "Open")
        else:
            st.metric("Inschrijvingen", "Gesloten")
    
    with col3:
        st.metric("Huidige Ronde", current_round)
        completed = len(status["rounds_completed"])
        st.write(f"{completed}/3 rondes voltooid")
    
    with col4:
        # Count total registrations
        total_regs = 0
        for path in [TRAINING1_PATH, TRAINING2_PATH, TRAINING3_PATH]:
            if path.exists():
                try:
                    df = pd.read_csv(path)
                    total_regs += len(df)
                except:
                    pass
        st.metric("Totaal Registraties", total_regs)
    
    # Show current status
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if 1 in status["rounds_completed"]:
            st.success("✅ Ronde 1 Voltooid")
        elif current_round == 1:
            st.info("🔄 Ronde 1 Actief")
        else:
            st.warning("⏳ Ronde 1 Wachtend")
    
    with col2:
        if 2 in status["rounds_completed"]:
            st.success("✅ Ronde 2 Voltooid")
        elif current_round == 2:
            st.info("🔄 Ronde 2 Actief")
        else:
            st.warning("⏳ Ronde 2 Wachtend")
    
    with col3:
        if 3 in status["rounds_completed"]:
            st.success("✅ Ronde 3 Voltooid")
        elif current_round == 3:
            st.info("🔄 Ronde 3 Actief")
        else:
            st.warning("⏳ Ronde 3 Wachtend")
    
    st.markdown("---")
    
    # Show current round planning
    if current_round <= 3:
        round_descriptions = {
            1: "🎯 Ronde 1 Planning - Eerste Training (iedereen)",
            2: "🎯 Ronde 2 Planning - Tweede Training (2x/3x per week)",
            3: "🎯 Ronde 3 Planning - Derde Training (3x per week)"
        }
        st.subheader(round_descriptions[current_round])
        
        # Show which files are being used
        round_files = {
            1: "training1_inschrijvingen.csv",
            2: "training2_inschrijvingen.csv", 
            3: "training3_inschrijvingen.csv"
        }
        
        current_file = round_files[current_round]
        if working_period["type"] == "archive":
            st.info(f"📁 **Gebruikt bestand:** {current_file} (uit archief: {working_period['name']})")
        else:
            st.info(f"📊 **Gebruikt bestand:** {current_file} (live data)")
        
        # Get available people for this round
        available_people = get_available_people_for_round(current_round, status)
        
        if len(available_people) == 0:
            st.warning(f"⚠️ Geen beschikbare mensen voor Ronde {current_round}")
            
            # Show helpful message based on working period
            if working_period["type"] == "archive":
                st.info("💡 Mogelijk heeft dit archief geen data voor deze ronde, of zijn alle mensen al ingepland.")
            else:
                st.info("💡 Mogelijk zijn er geen aanmeldingen voor deze ronde, of zijn alle mensen al ingepland.")
            
            if current_round < 3:
                if st.button(f"⏭️ Ga naar Ronde {current_round + 1}"):
                    status["rounds_completed"].append(current_round)
                    status["current_round"] = current_round + 1
                    save_ronde_status(status)
                    st.rerun()
        else:
            # Filter people based on their training frequency for this round
            if current_round == 1:
                # Ronde 1: Iedereen (1x, 2x, 3x per week)
                filtered_people = available_people.copy()
                round_info = "Alle mensen die zich hebben aangemeld (1x, 2x of 3x per week)"
            elif current_round == 2:
                # Ronde 2: Alleen mensen die 2x of 3x per week willen
                if 'Trainingen_per_week' in available_people.columns:
                    filtered_people = available_people[
                        available_people['Trainingen_per_week'].isin(['2x per week', '3x per week'])
                    ]
                else:
                    filtered_people = available_people.copy()
                round_info = "Mensen die 2x of 3x per week willen trainen"
            else:  # current_round == 3
                # Ronde 3: Alleen mensen die 3x per week willen
                if 'Trainingen_per_week' in available_people.columns:
                    filtered_people = available_people[
                        available_people['Trainingen_per_week'] == '3x per week'
                    ]
                else:
                    filtered_people = available_people.copy()
                round_info = "Mensen die 3x per week willen trainen"
            
            if len(filtered_people) == 0:
                st.info(f"📋 Geen mensen beschikbaar voor deze ronde ({round_info})")
                if current_round < 3:
                    if st.button(f"⏭️ Ga naar Ronde {current_round + 1}"):
                        status["rounds_completed"].append(current_round)
                        status["current_round"] = current_round + 1
                        save_ronde_status(status)
                        st.rerun()
            else:
                st.info(f"📋 {len(filtered_people)} mensen beschikbaar voor planning ({round_info})")
                
                # Show preview of people to be planned
                with st.expander("👥 Mensen in deze ronde"):
                    display_cols = ['Naam', 'Telefoon', 'Niveau', 'Trainingen_per_week', 'Voorkeur_1', 'Voorkeur_2', 'Voorkeur_3']
                    available_cols = [col for col in display_cols if col in filtered_people.columns]
                    st.dataframe(filtered_people[available_cols], use_container_width=True, hide_index=True)
                
                # Plan this round
                if st.button(f"🚀 Start Ronde {current_round} Planning", type="primary"):
                    with st.spinner(f"Planning Ronde {current_round}..."):
                        # Make a copy of trainingen for this round
                        trainingen_copy = trainingen.copy()
                        
                        # Apply previous round capacity reductions
                        for round_data in status.get("planning_history", []):
                            if round_data["round"] < current_round:
                                for training_name, people in round_data.get("assigned_by_training", {}).items():
                                    # Find matching training and reduce capacity
                                    for idx, row in trainingen_copy.iterrows():
                                        # Create training label based on available columns
                                        if 'Training Naam' in row and pd.notna(row['Training Naam']):
                                            training_label = f"{row['Dag']} {row['Tijd']} - {row['Training Naam']}"
                                        else:
                                            trainer_text = f" - {row['Trainer']}" if pd.notna(row['Trainer']) and row['Trainer'].strip() else ""
                                            training_label = f"{row['Dag']} {row['Tijd']}{trainer_text}"
                                        
                                        if training_label == training_name:
                                            trainingen_copy.at[idx, 'Capaciteit'] = max(0, trainingen_copy.at[idx, 'Capaciteit'] - len(people))
                        
                        # Plan this round with filtered people
                        planning, handmatig = plan_single_round(filtered_people, trainingen_copy, current_round, status)
                        
                        # Check if this round already exists in planning history
                        existing_round_index = None
                        for i, round_data in enumerate(status.get("planning_history", [])):
                            if round_data["round"] == current_round:
                                existing_round_index = i
                                break
                        
                        # Store results
                        round_result = {
                            "round": current_round,
                            "timestamp": datetime.now().isoformat(),
                            "assigned_by_training": planning,
                            "manual_needed": handmatig,
                            "assigned": [],
                            "working_period": working_period["name"],
                            "period_type": working_period["type"]
                        }
                        
                        # Convert planning to assigned list
                        for training, people in planning.items():
                            for name, level in people:
                                round_result["assigned"].append({
                                    "name": name,
                                    "level": level,
                                    "training": training
                                })
                        
                        # Update status - replace existing round or add new one
                        if existing_round_index is not None:
                            status["planning_history"][existing_round_index] = round_result
                        else:
                            status["planning_history"].append(round_result)
                        
                        save_ronde_status(status)
                        
                        st.success(f"✅ Ronde {current_round} planning voltooid!")
                        st.rerun()
    
    # Show results of current/completed rounds
    if status.get("planning_history"):
        st.markdown("---")
        st.subheader("📊 Planning Resultaten")
        
        for round_data in status["planning_history"]:
            round_num = round_data["round"]
            period_info = ""
            
            # Show which period this round was planned with
            if "working_period" in round_data:
                period_type = round_data.get("period_type", "current")
                if period_type == "archive":
                    period_info = f" (Archief: {round_data['working_period']})"
                else:
                    period_info = f" (Live: {round_data['working_period']})"
            
            with st.expander(f"🎯 Ronde {round_num} Resultaten{period_info}", expanded=(round_num == current_round)):
                
                # Show successful assignments
                if round_data.get("assigned_by_training"):
                    st.write("### ✅ Automatisch Ingepland")
                    for training, people in round_data["assigned_by_training"].items():
                        st.write(f"**{training}** ({len(people)} mensen)")
                        if people:
                            df_assigned = pd.DataFrame(people, columns=["Naam", "Niveau"])
                            st.dataframe(df_assigned, use_container_width=True, hide_index=True)
                
                # Show manual assignments if any
                manual_assignments = status.get("manual_assignments", {}).get(str(round_num), [])
                if manual_assignments:
                    st.write("### 🔧 Handmatig Ingepland")
                    df_manual = pd.DataFrame(manual_assignments)[['name', 'training']]
                    df_manual.columns = ['Naam', 'Training']
                    st.dataframe(df_manual, use_container_width=True, hide_index=True)
                
                # Show people needing manual assignment (filter out already assigned people)
                if round_data.get("manual_needed"):
                    # Get list of people already manually assigned in this round
                    manual_assignments = status.get("manual_assignments", {}).get(str(round_num), [])
                    assigned_names = set(assignment["name"] for assignment in manual_assignments)
                    
                    # Filter out people who are already manually assigned
                    manual_needed_data = round_data["manual_needed"]
                    filtered_manual_needed = []
                    for entry in manual_needed_data:
                        person_name = entry[0]  # First element is always the name
                        if person_name not in assigned_names:
                            filtered_manual_needed.append(entry)
                    
                    if filtered_manual_needed:  # Only show if there are still people needing assignment
                        st.write("### ⚠️ Handmatige Inplanning Nodig")
                        
                        # Handle backwards compatibility (old format has 3 columns, new format has 4)
                        if filtered_manual_needed and len(filtered_manual_needed[0]) == 3:
                            # Old format: (naam, niveau, reden) - add empty opgaves column
                            df_manual_needed = pd.DataFrame(filtered_manual_needed, columns=["Naam", "Niveau", "Reden"])
                            df_manual_needed.insert(2, "Opgaves", "Niet beschikbaar (oude data)")
                        else:
                            # New format: (naam, niveau, opgaves, reden)
                            df_manual_needed = pd.DataFrame(filtered_manual_needed, columns=["Naam", "Niveau", "Opgaves", "Reden"])
                        
                        st.dataframe(df_manual_needed, use_container_width=True, hide_index=True)
                
                # Manual assignment form - only show if there are people needing assignment
                if round_data.get("manual_needed"):
                    # Get list of people already manually assigned in this round
                    manual_assignments = status.get("manual_assignments", {}).get(str(round_num), [])
                    assigned_names = set(assignment["name"] for assignment in manual_assignments)
                    
                    # Filter out people who are already manually assigned
                    manual_needed_data = round_data["manual_needed"]
                    filtered_manual_needed = []
                    for entry in manual_needed_data:
                        person_name = entry[0]  # First element is always the name
                        if person_name not in assigned_names:
                            filtered_manual_needed.append(entry)
                    
                    if filtered_manual_needed:  # Only show form if there are people needing assignment
                        st.write("### 🔧 Handmatige Inplanning")
                        
                        # Get available trainings
                        available_trainings = []
                        for _, row in trainingen.iterrows():
                            if 'Training Naam' in row and pd.notna(row['Training Naam']):
                                training_name = f"{row['Dag']} {row['Tijd']} - {row['Training Naam']}"
                            else:
                                trainer_text = f" - {row['Trainer']}" if pd.notna(row['Trainer']) and row['Trainer'].strip() else ""
                                training_name = f"{row['Dag']} {row['Tijd']}{trainer_text}"
                            available_trainings.append(training_name)
                        
                        # Manual assignment form
                        form_key = f"manual_assignment_round_{round_num}_{hash(str(round_data.get('timestamp', '')))}"
                        with st.form(form_key):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Handle backwards compatibility for person selection
                                if filtered_manual_needed and len(filtered_manual_needed[0]) == 3:
                                    # Old format: (naam, niveau, reden)
                                    person_options = [f"{name} (niveau {level})" for name, level, reason in filtered_manual_needed]
                                else:
                                    # New format: (naam, niveau, opgaves, reden)
                                    person_options = [f"{name} (niveau {level}) - {opgaves}" for name, level, opgaves, reason in filtered_manual_needed]
                                
                                person_to_assign = st.selectbox(
                                    "Selecteer persoon:",
                                    options=["-- Selecteer --"] + person_options,
                                    key=f"person_{round_num}_{hash(str(round_data.get('timestamp', '')))}"
                                )
                            
                            with col2:
                                training_to_assign = st.selectbox(
                                    "Selecteer training:",
                                    options=["-- Selecteer --"] + available_trainings,
                                    key=f"training_{round_num}_{hash(str(round_data.get('timestamp', '')))}"
                                )
                            
                            if st.form_submit_button("➕ Handmatig Toewijzen"):
                                if person_to_assign != "-- Selecteer --" and training_to_assign != "-- Selecteer --":
                                    # Extract person name (format: "Name (niveau X) - preferences")
                                    person_name = person_to_assign.split(" (niveau")[0]
                                    
                                    # Get person level for adding to assigned_by_training
                                    person_level = None
                                    manual_needed_data = round_data["manual_needed"]
                                    for entry in manual_needed_data:
                                        if entry[0] == person_name:  # entry[0] is the name
                                            person_level = entry[1]  # entry[1] is the level
                                            break
                                    
                                    # Find the round in planning history and update it
                                    for i, round_data_item in enumerate(status["planning_history"]):
                                        if round_data_item["round"] == round_num:
                                            # Remove person from manual_needed list
                                            new_manual_needed = []
                                            for entry in round_data_item["manual_needed"]:
                                                if entry[0] != person_name:  # Keep everyone except the assigned person
                                                    new_manual_needed.append(entry)
                                            status["planning_history"][i]["manual_needed"] = new_manual_needed
                                            
                                            # Add person to assigned_by_training
                                            if training_to_assign not in status["planning_history"][i]["assigned_by_training"]:
                                                status["planning_history"][i]["assigned_by_training"][training_to_assign] = []
                                            status["planning_history"][i]["assigned_by_training"][training_to_assign].append([person_name, person_level])
                                            
                                            # Add to assigned list
                                            status["planning_history"][i]["assigned"].append({
                                                "name": person_name,
                                                "level": person_level,
                                                "training": training_to_assign
                                            })
                                            break
                                    
                                    # Add to manual assignments for tracking
                                    if str(round_num) not in status["manual_assignments"]:
                                        status["manual_assignments"][str(round_num)] = []
                                    
                                    status["manual_assignments"][str(round_num)].append({
                                        "name": person_name,
                                        "level": person_level,  # Store the actual level
                                        "training": training_to_assign,
                                        "assigned_by": "manual",
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    
                                    save_ronde_status(status)
                                    st.success(f"✅ {person_name} toegewezen aan {training_to_assign}")
                                    st.rerun()
                
                # Export results
                if round_data.get("assigned") or manual_assignments:
                    st.write("### 📥 Exporteren")
                    
                    # Combine automatic and manual assignments
                    all_assignments = []
                    
                    # Add automatic assignments
                    for assignment in round_data.get("assigned", []):
                        # Convert float level to int if it's a whole number
                        level = assignment["level"]
                        if isinstance(level, float) and level.is_integer():
                            level = int(level)
                        all_assignments.append({
                            "Naam": str(assignment["name"]),
                            "Niveau": str(level),
                            "Training": str(assignment["training"]),
                            "Type": "Automatisch",
                            "Ronde": str(round_num)
                        })
                    
                    # Add manual assignments
                    for assignment in manual_assignments:
                        # Use stored level if available, otherwise use "Handmatig"
                        level = assignment.get("level", "Handmatig")
                        if isinstance(level, float) and level.is_integer():
                            level = int(level)
                        all_assignments.append({
                            "Naam": str(assignment["name"]),
                            "Niveau": str(level),
                            "Training": str(assignment["training"]),
                            "Type": "Handmatig",
                            "Ronde": str(round_num)
                        })
                    
                    if all_assignments:
                        df_export = pd.DataFrame(all_assignments)
                        
                        # Create CSV with proper encoding
                        csv_export = df_export.to_csv(index=False, encoding='utf-8-sig', sep=';')
                        
                        # Show preview of the data
                        st.write("**Preview van de export data:**")
                        st.dataframe(df_export, use_container_width=True, hide_index=True)
                        
                        st.download_button(
                            label=f"📥 Download Ronde {round_num} Resultaten",
                            data=csv_export,
                            file_name=f"ronde_{round_num}_planning_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            key=f"export_{round_num}_{hash(str(round_data.get('timestamp', '')))}"
                        )

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
    
    # Show Final Planning section only if everything is planned
    if status.get("planning_history") and all_people_assigned:
        st.markdown("---")
        st.header("🎉 Final Planning - Alle Trainingsgroepen")
        st.success("✅ Alle deelnemers zijn succesvol ingepland!")
        
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
        
        if all_training_groups:
            # Summary statistics
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
            
            st.markdown("---")
            
            # Show each training group in a nice format
            for training, members in all_training_groups.items():
                if members:  # Only show trainings that have people
                    with st.expander(f"🎾 {training} ({len(members)} deelnemers)", expanded=True):
                        # Create DataFrame for this training group
                        df_group = pd.DataFrame(members)
                        
                        # Sort by name for better readability
                        df_group = df_group.sort_values('Naam')
                        
                        # Display only relevant columns
                        display_df = df_group[["Naam", "Niveau", "Type", "Ronde"]]
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Final export section
            st.subheader("📥 Complete Planning Downloaden")
            st.write("Download hier de complete planning van alle trainingsgroepen:")
            
            # Create complete export DataFrame
            df_complete_export = pd.DataFrame(all_assignments_for_export)
            df_complete_export = df_complete_export.sort_values(['Training', 'Naam'])
            
            # Reorder columns for better export
            export_columns = ["Training", "Naam", "Niveau", "Type", "Ronde"]
            df_complete_export = df_complete_export[export_columns]
            
            # Create CSV with proper encoding
            csv_complete_export = df_complete_export.to_csv(index=False, encoding='utf-8-sig', sep=';')
            
            # Show preview of the complete data
            st.write("**Preview van de complete planning:**")
            st.dataframe(df_complete_export, use_container_width=True, hide_index=True)
            
            # Download button for complete planning
            st.download_button(
                label="🎾 Download Complete Planning",
                data=csv_complete_export,
                file_name=f"complete_planning_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                type="primary",
                help="Download alle trainingsgroepen in één bestand"
            )
        else:
            st.info("📋 Nog geen trainingsgroepen ingepland")
    
    elif status.get("planning_history") and not all_people_assigned:
        # Show progress if planning is in progress but not complete
        st.markdown("---")
        st.subheader("📊 Planning Voortgang")
        st.info(f"⏳ Planning nog niet compleet. Er zijn nog {total_people_needing_manual} mensen die handmatig toegewezen moeten worden.")
        
        # Show progress bar
        total_people = 0
        assigned_people = 0
        
        # Count total people from all CSV files
        working_period = get_current_working_period()
        if working_period["type"] == "live":
            data_path = "data"
        else:
            data_path = f"archive/{working_period['folder']}"
        
        for i in range(1, 4):
            csv_file = f"{data_path}/training{i}_inschrijvingen.csv"
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                total_people += len(df)
        
        assigned_people = len(all_assignments_for_export) if 'all_assignments_for_export' in locals() else 0
        
        if total_people > 0:
            progress = assigned_people / total_people
            st.progress(progress, text=f"Voortgang: {assigned_people}/{total_people} mensen ingepland ({progress:.1%})")
        
        st.write("💡 **Tip:** Wijs alle mensen handmatig toe om de 'Final Planning' sectie te zien met het complete overzicht en download mogelijkheid.")

    # Round completion and navigation
    st.markdown("---")
    st.subheader("🔄 Planning Beheer")
    
    # Check if current round has any planning
    current_round_has_planning = any(r["round"] == current_round for r in status.get("planning_history", []))
    
    if current_round_has_planning:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if current_round < 3:
                if st.button(f"✅ Ronde {current_round} Voltooid - Ga naar Ronde {current_round + 1}", 
                           type="primary", 
                           help="Markeer deze ronde als voltooid en ga naar de volgende ronde"):
                    status["rounds_completed"].append(current_round)
                    status["current_round"] = current_round + 1
                    save_ronde_status(status)
                    st.success(f"✅ Ronde {current_round} voltooid! Nu bezig met ronde {current_round + 1}")
                    st.rerun()
            else:
                st.success("🎉 Alle rondes voltooid!")
        
        with col2:
            if st.button("🔄 Reset Huidige Ronde", help="Reset de huidige ronde planning"):
                # Remove current round from history
                status["planning_history"] = [r for r in status["planning_history"] if r["round"] != current_round]
                
                # Reset manual assignments for current round
                if str(current_round) in status.get("manual_assignments", {}):
                    del status["manual_assignments"][str(current_round)]
                
                save_ronde_status(status)
                st.success(f"✅ Ronde {current_round} reset!")
                st.rerun()
        
        with col3:
            # Session state for reset confirmation
            if "confirm_full_reset" not in st.session_state:
                st.session_state.confirm_full_reset = False
            
            if not st.session_state.confirm_full_reset:
                if st.button("🗑️ Reset Alle Planning", help="Reset alle planning en start opnieuw"):
                    st.session_state.confirm_full_reset = True
                    st.rerun()
            else:
                st.warning("⚠️ Weetje zeker dat je alle planning wilt resetten?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Ja, Reset Alles", type="primary"):
                        # Reset everything
                        new_status = {
                            "current_round": 1,
                            "rounds_completed": [],
                            "manual_assignments": {},
                            "excluded_people": [],
                            "planning_history": []
                        }
                        save_ronde_status(new_status)
                        st.session_state.confirm_full_reset = False
                        st.success("✅ Alle planning gereset!")
                        st.rerun()
                with col_no:
                    if st.button("❌ Annuleren"):
                        st.session_state.confirm_full_reset = False
                        st.rerun()
    else:
        st.info("💡 Start eerst een planning voor deze ronde om ronde beheer opties te zien.")
    
    # Show working period reminder
    st.markdown("---")
    st.info(f"💡 **Herinnering:** Je werkt momenteel met {working_period['type']} data: {working_period['name']}. "
            f"Je kunt dit wijzigen in de Periode Beheer sectie.") 