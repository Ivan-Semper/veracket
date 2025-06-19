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
                return json.load(f)
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
    """)
    
    # Load current status
    status = load_ronde_status()
    current_round = status["current_round"]
    
    # Check if training files exist
    if not TRAININGEN_PATH.exists():
        st.error("❌ Trainingen bestand niet gevonden in 'data/' map.")
        return
    
    trainingen = pd.read_csv(TRAININGEN_PATH)
    
    # Show current status
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
        
        # Get available people for this round
        available_people = get_available_people_for_round(current_round, status)
        
        if len(available_people) == 0:
            st.warning(f"⚠️ Geen beschikbare mensen voor Ronde {current_round}")
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
                    display_cols = ['Naam', 'Telefoon', 'Speelsterkte', 'Trainingen_per_week', 'Voorkeur_1', 'Voorkeur_2', 'Voorkeur_3']
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
                        
                        # Store results
                        round_result = {
                            "round": current_round,
                            "timestamp": datetime.now().isoformat(),
                            "assigned_by_training": planning,
                            "manual_needed": handmatig,
                            "assigned": []
                        }
                        
                        # Convert planning to assigned list
                        for training, people in planning.items():
                            for name, level in people:
                                round_result["assigned"].append({
                                    "name": name,
                                    "level": level,
                                    "training": training
                                })
                        
                        # Update status
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
            
            with st.expander(f"🎯 Ronde {round_num} Resultaten", expanded=(round_num == current_round)):
                
                # Show successful assignments
                if round_data.get("assigned_by_training"):
                    st.markdown("### ✅ Succesvol Toegewezen")
                    for training, people in round_data["assigned_by_training"].items():
                        st.markdown(f"**{training}** ({len(people)} mensen)")
                        df = pd.DataFrame(people, columns=["Naam", "Niveau"])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Show manual cases
                if round_data.get("manual_needed"):
                    st.markdown("### ❌ Handmatige Inplanning Nodig")
                    df_manual = pd.DataFrame(round_data["manual_needed"], columns=["Naam", "Niveau", "Reden"])
                    st.dataframe(df_manual, use_container_width=True, hide_index=True)
                    
                    # Manual assignment interface
                    st.markdown("#### 🔧 Handmatige Toewijzing")
                    
                    for i, (naam, niveau, reden) in enumerate(round_data["manual_needed"]):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**{naam}** (Niveau: {niveau})")
                            st.caption(f"Reden: {reden}")
                        
                        with col2:
                            # Training selection for manual assignment
                            training_options = ["Niet toewijzen"]
                            for _, row in trainingen.iterrows():
                                if 'Training Naam' in row and pd.notna(row['Training Naam']):
                                    option = f"{row['Dag']} {row['Tijd']} - {row['Training Naam']}"
                                else:
                                    trainer_text = f" - {row['Trainer']}" if pd.notna(row['Trainer']) and row['Trainer'].strip() else ""
                                    option = f"{row['Dag']} {row['Tijd']}{trainer_text}"
                                training_options.append(option)
                            selected_training = st.selectbox(
                                "Toewijzen aan:",
                                training_options,
                                key=f"manual_{round_num}_{i}_{naam}"
                            )
                        
                        with col3:
                            if st.button("✅ Toewijzen", key=f"assign_{round_num}_{i}_{naam}"):
                                if selected_training != "Niet toewijzen":
                                    # Add to manual assignments
                                    if str(round_num) not in status["manual_assignments"]:
                                        status["manual_assignments"][str(round_num)] = []
                                    
                                    status["manual_assignments"][str(round_num)].append({
                                        "name": naam,
                                        "level": niveau,
                                        "training": selected_training,
                                        "timestamp": datetime.now().isoformat()
                                    })
                                    
                                    save_ronde_status(status)
                                    st.success(f"✅ {naam} toegewezen aan {selected_training}")
                                    st.rerun()
                
                # Show manual assignments
                manual_assignments = status.get("manual_assignments", {}).get(str(round_num), [])
                if manual_assignments:
                    st.markdown("### 🔧 Handmatig Toegewezen")
                    df_manual_assigned = pd.DataFrame(manual_assignments)[['name', 'level', 'training']]
                    df_manual_assigned.columns = ['Naam', 'Niveau', 'Training']
                    st.dataframe(df_manual_assigned, use_container_width=True, hide_index=True)
                
                # Round completion
                if round_num == current_round and round_num not in status["rounds_completed"]:
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(f"✅ Ronde {round_num} Voltooien", type="primary"):
                            status["rounds_completed"].append(round_num)
                            if round_num < 3:
                                status["current_round"] = round_num + 1
                            save_ronde_status(status)
                            st.success(f"✅ Ronde {round_num} voltooid!")
                            st.rerun()
                    
                    with col2:
                        if st.button(f"🔄 Ronde {round_num} Opnieuw Plannen"):
                            # Remove this round from history
                            status["planning_history"] = [r for r in status["planning_history"] if r["round"] != round_num]
                            if str(round_num) in status["manual_assignments"]:
                                del status["manual_assignments"][str(round_num)]
                            save_ronde_status(status)
                            st.info(f"🔄 Ronde {round_num} reset voor herplanning")
                            st.rerun()
    
    # Final results and reset
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Finale Planning Downloaden"):
            # Combine all results
            all_assignments = []
            
            # Add automatic assignments
            for round_data in status.get("planning_history", []):
                for person in round_data.get("assigned", []):
                    all_assignments.append({
                        "Naam": person["name"],
                        "Niveau": person["level"],
                        "Training": person["training"],
                        "Ronde": round_data["round"],
                        "Type": "Automatisch"
                    })
            
            # Add manual assignments
            for round_num, assignments in status.get("manual_assignments", {}).items():
                for assignment in assignments:
                    all_assignments.append({
                        "Naam": assignment["name"],
                        "Niveau": assignment["level"],
                        "Training": assignment["training"],
                        "Ronde": int(round_num),
                        "Type": "Handmatig"
                    })
            
            if all_assignments:
                df_final = pd.DataFrame(all_assignments)
                csv_data = df_final.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Finale Planning CSV",
                    data=csv_data,
                    file_name=f"finale_planning_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Geen planning om te downloaden")
    
    with col2:
        if st.button("🔄 Volledige Reset", help="Reset alle rondes en begin opnieuw"):
            if st.session_state.get("confirm_reset"):
                # Reset everything
                status = {
                    "current_round": 1,
                    "rounds_completed": [],
                    "manual_assignments": {},
                    "excluded_people": [],
                    "planning_history": []
                }
                save_ronde_status(status)
                st.session_state["confirm_reset"] = False
                st.success("🔄 Systeem volledig gereset!")
                st.rerun()
            else:
                st.session_state["confirm_reset"] = True
                st.warning("⚠️ Klik nogmaals om te bevestigen") 