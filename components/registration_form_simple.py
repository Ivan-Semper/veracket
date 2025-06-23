import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TRAININGEN_PATH = BASE_DIR / "data" / "trainings.csv"
TRAINING1_PATH = BASE_DIR / "data" / "training1_inschrijvingen.csv"
TRAINING2_PATH = BASE_DIR / "data" / "training2_inschrijvingen.csv"
TRAINING3_PATH = BASE_DIR / "data" / "training3_inschrijvingen.csv"
PERIODE_STATUS_PATH = BASE_DIR / "data" / "periode_status.json"

def check_registration_status():
    """Check if registrations are currently open"""
    if PERIODE_STATUS_PATH.exists():
        try:
            with open(PERIODE_STATUS_PATH, 'r', encoding='utf-8') as f:
                status = json.load(f)
                return status.get("is_open", True), status.get("current_period", None)
        except:
            pass
    return True, None  # Default: open

def load_available_trainings():
    """Load available training sessions from the CSV file"""
    if os.path.exists(TRAININGEN_PATH):
        trainings_df = pd.read_csv(TRAININGEN_PATH)
        training_options = []
        for _, row in trainings_df.iterrows():
            # Create training name based on level range
            if row['MinNiveau'] == row['MaxNiveau']:
                level_text = f"Niveau {row['MinNiveau']}"
            else:
                level_text = f"Niveau {row['MinNiveau']}-{row['MaxNiveau']}"
            
            # Use trainer name if available, otherwise use generic name
            trainer_text = f" - {row['Trainer']}" if pd.notna(row['Trainer']) and row['Trainer'].strip() else ""
            
            option = f"{row['Dag']} {row['Tijd']}{trainer_text} ({level_text})"
            training_options.append(option)
        return training_options
    return []

def extract_training_level_range(training_text):
    """Extract min and max level from training text like 'Maandag 19:00 - Beginners Training (Niveau 6-9)'"""
    import re
    match = re.search(r'Niveau (\d+)-(\d+)', training_text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def check_permission_needed(speelsterkte, training_choices, toestemming_hoger_niveau):
    """Check if user needs permission for higher level trainings"""
    permission_warnings = []
    
    for training in training_choices:
        if training and "Selecteer" not in training and "No training" not in training:
            min_level, max_level = extract_training_level_range(training)
            if min_level and max_level:
                # Check if user's level is too high (lower number = better)
                if speelsterkte < min_level and not toestemming_hoger_niveau:
                    permission_warnings.append(f"Voor '{training}' (niveau {min_level}-{max_level}) heb je toestemming nodig omdat jouw niveau ({speelsterkte}) hoger is dan het minimum niveau ({min_level})")
    
    return permission_warnings

def save_multiple_registrations(registrations_list):
    """Save registrations to separate CSV files per training, removing duplicates based on phone number"""
    os.makedirs("data", exist_ok=True)
    
    # Get the phone number from the first registration (all have same phone)
    phone_number = registrations_list[0]['Telefoon'] if registrations_list else None
    duplicate_found = False
    
    # Group registrations by training number
    training_groups = {}
    for registration in registrations_list:
        training_num = registration['Training_nummer']
        if training_num not in training_groups:
            training_groups[training_num] = []
        training_groups[training_num].append(registration)
    
    # Save each training to its own file
    training_paths = {
        1: TRAINING1_PATH,
        2: TRAINING2_PATH,
        3: TRAINING3_PATH
    }
    
    for training_num, registrations in training_groups.items():
        if training_num in training_paths:
            file_path = training_paths[training_num]
            
            # Remove Training_nummer column as it's not needed in separate files
            for reg in registrations:
                reg.pop('Training_nummer', None)
            
            # Convert to DataFrame
            df_new = pd.DataFrame(registrations)
            
            # If file exists, remove existing registrations with same phone number
            if os.path.exists(file_path):
                df_existing = pd.read_csv(file_path)
                
                # Check if duplicate exists
                if phone_number and 'Telefoon' in df_existing.columns:
                    existing_count = len(df_existing[df_existing['Telefoon'] == phone_number])
                    if existing_count > 0:
                        duplicate_found = True
                    df_existing = df_existing[df_existing['Telefoon'] != phone_number]
                
                # Combine with new registrations
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = df_new
            
            # Save to CSV
            df_combined.to_csv(file_path, index=False)
    
    return duplicate_found

def get_translations():
    """Return dictionary with all text translations"""
    return {
        'nl': {
            'title': '🎾 Tennis Training Aanmelding',
            'welcome': '**Welkom bij de tennis training aanmelding!**\n\nVul onderstaand formulier in om je aan te melden voor tennis trainingen.',
            'language_select': 'Taal / Language:',
            'personal_info': '👤 Persoonlijke Gegevens',
            'first_name': 'Voornaam *',
            'first_name_placeholder': 'Bijv. Jan',
            'last_name': 'Achternaam *',
            'last_name_placeholder': 'Bijv. de Vries',
            'phone': 'Telefoonnummer *',
            'phone_placeholder': '06-12345678',
            'tennis_level': '🎾 Tennis Niveau',
            'skill_level': 'Speelsterkte (1-9) *',
            'skill_help': '1 = Beste niveau/gevorderd, 9 = Beginner',
            'permission_checkbox': 'Ik heb toestemming van een trainer gekregen om een niveau hoger te trainen',
            'permission_help': 'Vink dit alleen aan als je al toestemming hebt gevraagd en gekregen van een trainer om een niveau boven je eigen speelsterkte te trainen',
            'training_preferences': '📅 Training Voorkeuren',
            'frequency_question': 'Hoe vaak wil je per week trainen? *',
            'frequency_help': 'Geef aan hoe vaak je wilt/kunt trainen (maximaal 3x per week)',
            'frequency_1': '1x per week',
            'frequency_2': '2x per week',
            'frequency_3': '3x per week',
            'select_preferences': '**Selecteer je trainingsvoorkeuren voor elke training:**',
            'training_1_prefs': '**Training 1 voorkeuren:**',
            'training_2_prefs': '**Training 2 voorkeuren:**',
            'training_3_prefs': '**Training 3 voorkeuren:**',
            'choice_1': '1e keuze *',
            'choice_2': '2e keuze *',
            'choice_3': '3e keuze',
            'choice_1_help': 'Je meest gewenste training voor training {}',
            'choice_2_help': 'Je tweede keuze voor training {}',
            'choice_3_help': 'Je derde keuze voor training {} (optioneel)',
            'select_training': 'Selecteer een training...',
            'no_third_choice': 'Geen derde keuze',
            'additional_info': '💬 Aanvullende Informatie',
            'extra_message': 'Extra bericht (optioneel)',
            'extra_message_placeholder': 'Eventuele vragen of opmerkingen, of je mag wat leuks tegen de TC zeggen...',
            'submit_button': '📝 Inschrijving Versturen',
            'validation_error': '❌ Controleer je invoer:',
            'name_required': 'Voornaam en achternaam zijn verplicht',
            'phone_required': 'Telefoonnummer is verplicht',
            'training_required': 'Selecteer een training voor {}',
            'success_message': '✅ **Inschrijving succesvol verzonden!**\n\nBedankt voor je aanmelding. Je wordt binnenkort gecontacteerd over de indeling.',
            'duplicate_replaced': '🔄 **Vorige aanmelding vervangen**\n\nJe had je eerder al aangemeld. Je oude aanmelding is vervangen door deze nieuwe aanmelding.',
            'no_trainings': '⚠️ Er zijn momenteel geen trainingen beschikbaar. Neem contact op met de beheerder.',
            'error_saving': 'Er is een fout opgetreden bij het opslaan van je inschrijving. Probeer het opnieuw of neem contact op met de beheerder.',
            'info_section': 'ℹ️ Informatie over Trainingen',
            'available_trainings': '**Beschikbare trainingen:**',
            'skill_indication': '**Speelsterkte indicatie:**',
            'level_1_2': '**Niveau 1-2:** Zeer gevorderd, competitie niveau',
            'level_3_4': '**Niveau 3-4:** Gevorderd, wedstrijdspelers',
            'level_5_6': '**Niveau 5-6:** Goede basis, langere rallies, tactiek',
            'level_7_8': '**Niveau 7-8:** Basis technieken leren, korte rallies',
            'level_9': '**Niveau 9:** Complete beginner, nog nooit gespeeld',
            'contact_info': '**Contact:**\nVoor vragen over de aanmelding kun je contact opnemen via info@tennisclub.nl',
            'registration_closed': '🔒 **Aanmeldingen Momenteel Gesloten**',
            'closed_message': 'De aanmeldingsperiode is momenteel gesloten. Nieuwe aanmeldingen zijn tijdelijk niet mogelijk.',
            'check_back': 'Kom later terug of neem contact op voor meer informatie.',
            'current_period': 'Huidige periode:',
            'not_assigned_warning': '🚫 **Je wordt NIET ingedeeld:** {}',
            'solution_message': '💡 **Oplossing:** Vink de checkbox hierboven aan als je al toestemming hebt van een trainer, of kies een training voor jouw niveau.',
            'summary_title': '📋 Samenvatting van je aanmelding',
            'summary_name': 'Naam',
            'summary_phone': 'Telefoon',
            'summary_skill': 'Speelsterkte',
            'summary_permission': 'Toestemming hoger niveau',
            'summary_frequency': 'Trainingen per week',
            'summary_training_prefs': 'Training {} voorkeuren',
            'summary_choice_1': '1e keuze',
            'summary_choice_2': '2e keuze',
            'summary_choice_3': '3e keuze',
            'summary_extra_message': 'Extra bericht',
            'summary_registered_on': 'Aangemeld op'
        },
        'en': {
            'title': '🎾 Tennis Training Registration',
            'welcome': '**Welcome to tennis training registration!**\n\nPlease fill out the form below to register for tennis training sessions.',
            'language_select': 'Taal / Language:',
            'personal_info': '👤 Personal Information',
            'first_name': 'First Name *',
            'first_name_placeholder': 'E.g. John',
            'last_name': 'Last Name *',
            'last_name_placeholder': 'E.g. Smith',
            'phone': 'Phone Number *',
            'phone_placeholder': '+31-6-12345678',
            'tennis_level': '🎾 Tennis Level',
            'skill_level': 'Skill Level (1-9) *',
            'skill_help': '1 = Best level/advanced, 9 = Beginner',
            'permission_checkbox': 'I have received permission from a trainer to train at a higher level',
            'permission_help': 'Only check this if you have already asked and received permission from a trainer to train above your own skill level',
            'training_preferences': '📅 Training Preferences',
            'frequency_question': 'How often do you want to train per week? *',
            'frequency_help': 'Indicate how often you want/can train (maximum 3x a week)',
            'frequency_1': '1x a week',
            'frequency_2': '2x a week',
            'frequency_3': '3x a week',
            'select_preferences': '**Select your training preferences for each training:**',
            'training_1_prefs': '**Training 1 preferences:**',
            'training_2_prefs': '**Training 2 preferences:**',
            'training_3_prefs': '**Training 3 preferences:**',
            'choice_1': '1st choice *',
            'choice_2': '2nd choice *',
            'choice_3': '3rd choice',
            'choice_1_help': 'Your most preferred training for training {}',
            'choice_2_help': 'Your second choice for training {}',
            'choice_3_help': 'Your third choice for training {} (optional)',
            'select_training': 'Select a training...',
            'no_third_choice': 'No third choice',
            'additional_info': '💬 Additional Information',
            'extra_message': 'Extra message (optional)',
            'extra_message_placeholder': 'Any questions or comments, or feel free to say something nice to the TC...',
            'submit_button': '📝 Submit Registration',
            'validation_error': '❌ Please check your input:',
            'name_required': 'First name and last name are required',
            'phone_required': 'Phone number is required',
            'training_required': 'Select a training for {}',
            'success_message': '✅ **Registration successfully submitted!**\n\nThank you for your registration. You will be contacted soon about the placement.',
            'duplicate_replaced': '🔄 **Previous registration replaced**\n\nYou had already registered before. Your old registration has been replaced with this new registration.',
            'no_trainings': '⚠️ There are currently no trainings available. Please contact the administrator.',
            'error_saving': 'An error occurred while saving your registration. Please try again or contact the administrator.',
            'info_section': 'ℹ️ Training Information',
            'available_trainings': '**Available trainings:**',
            'skill_indication': '**Skill level indication:**',
            'level_1_2': '**Level 1-2:** Very advanced, competition level',
            'level_3_4': '**Level 3-4:** Advanced, match players',
            'level_5_6': '**Level 5-6:** Good foundation, longer rallies, tactics',
            'level_7_8': '**Level 7-8:** Learning basic techniques, short rallies',
            'level_9': '**Level 9:** Complete beginner, never played before',
            'contact_info': '**Contact:**\nFor questions about registration, please contact info@tennisclub.nl',
            'registration_closed': '🔒 **Registration Currently Closed**',
            'closed_message': 'The registration period is currently closed. New registrations are temporarily not possible.',
            'check_back': 'Please check back later or contact us for more information.',
            'current_period': 'Current period:',
            'not_assigned_warning': '🚫 **You will NOT be assigned:** {}',
            'solution_message': '💡 **Solution:** Check the checkbox above if you already have permission from a trainer, or choose a training for your level.',
            'summary_title': '📋 Registration Summary',
            'summary_name': 'Name',
            'summary_phone': 'Phone',
            'summary_skill': 'Skill Level',
            'summary_permission': 'Higher Level Permission',
            'summary_frequency': 'Trainings a week',
            'summary_training_prefs': 'Training {} preferences',
            'summary_choice_1': '1st choice',
            'summary_choice_2': '2nd choice',
            'summary_choice_3': '3rd choice',
            'summary_extra_message': 'Extra message',
            'summary_registered_on': 'Registered on'
        }
    }

def registration_form():
    # Language selector at the top
    translations = get_translations()
    
    # Language selection in sidebar or main area
    col1, col2 = st.columns([3, 1])
    with col2:
        language = st.selectbox(
            "🌐 Language / Taal:",
            ["nl", "en"],
            format_func=lambda x: "🇳🇱 Nederlands" if x == "nl" else "🇬🇧 English",
            key="language_selector"
        )
    
    # Get current language texts
    t = translations[language]
    
    st.title(t['title'])
    st.markdown(t['welcome'])
    
    # Check if registrations are open
    is_open, current_period = check_registration_status()
    
    if not is_open:
        # Show closed message
        st.error(t['registration_closed'])
        st.markdown(t['closed_message'])
        
        if current_period:
            st.info(f"{t['current_period']} {current_period}")
        
        st.markdown(t['check_back'])
        st.markdown("---")
        st.markdown(t['contact_info'])
        return
    
    # Load available trainings
    available_trainings = load_available_trainings()
    
    if not available_trainings:
        st.warning(t['no_trainings'])
        return
    
    # === PERSOONLIJKE GEGEVENS ===
    st.subheader(t['personal_info'])
    
    col1, col2 = st.columns(2)
    with col1:
        voornaam = st.text_input(t['first_name'], placeholder=t['first_name_placeholder'])
    with col2:
        achternaam = st.text_input(t['last_name'], placeholder=t['last_name_placeholder'])
    
    telefoon = st.text_input(t['phone'], placeholder=t['phone_placeholder'])
    
    # === TENNIS NIVEAU ===
    st.subheader(t['tennis_level'])
    
    # Custom CSS for better slider and checkbox styling
    st.markdown("""
    <style>
    /* Slider styling - larger but stable */
    .stSlider > div > div > div {
        height: 10px !important;
    }
    .stSlider > div > div > div > div {
        height: 24px !important;
        width: 24px !important;
        border: 3px solid #FF6B6B !important;
        background-color: white !important;
    }
    .stSlider > div > div > div > div:hover {
        border-color: #FF4757 !important;
        box-shadow: 0 0 8px rgba(255, 107, 107, 0.4) !important;
    }
    
    /* Checkbox styling - softer colors */
    .permission-checkbox {
        background-color: #F8F9FA !important;
        border: 1px solid #DEE2E6 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin: 15px 0 !important;
        border-left: 4px solid #6C757D !important;
    }
    .permission-checkbox label {
        font-weight: 600 !important;
        color: #343A40 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Show skill level with clear markers
    if language == "nl":
        level_overview = """
        📊 <strong>KNLTB Speelsterktes (korte uitleg):</strong>
        - <strong>1-2</strong>: 🏆 Nationaal/internationaal niveau
        - <strong>3-4</strong>: 🎾 Regionale top / clubtopper
        - <strong>5-6</strong>: ⚽ Vergevorderd clubniveau / actieve speler
        - <strong>7-8</strong>: 🌱 Gevorderde beginner / recreant
        - <strong>9</strong>: 🆕 Absolute beginner
        """
    else:  # English
        level_overview = """
        📊 <strong>KNLTB Skill Levels (short explanation):</strong>
        - <strong>1-2</strong>: 🏆 National/international level
        - <strong>3-4</strong>: 🎾 Regional top / club champion
        - <strong>5-6</strong>: ⚽ Advanced club level / active player
        - <strong>7-8</strong>: 🌱 Advanced beginner / recreational
        - <strong>9</strong>: 🆕 Absolute beginner
        """
    
    st.markdown(f"<strong>{t['skill_level']}</strong>", unsafe_allow_html=True)
    st.markdown(level_overview, unsafe_allow_html=True)
    
    speelsterkte = st.slider(
        "Jouw speelsterkte:", 
        min_value=1, 
        max_value=9, 
        value=5,
        step=1,
        help=t['skill_help']
    )
    
    # Show current level description with detailed KNLTB info
    if language == "nl":
        level_descriptions = {
            1: "🏆 **Niveau 1 - Internationaal/professioneel niveau**\nATP/WTA-speler of ex-professional. Technisch en fysiek op het hoogste niveau.",
            2: "🏆 **Niveau 2 - Nationale top**\nTop 50 Nederland. Technisch en fysiek zeer sterk, kan op nationaal niveau meedoen.",
            3: "🎾 **Niveau 3 - Top van de regio**\nNationale subtop niveau. Kan op nationaal niveau meedoen, regionale topper.",
            4: "🎾 **Niveau 4 - Zeer sterk clubniveau**\nClubtopper/regionale subtop. Consistentie, kracht, spin en strategie zijn aanwezig.",
            5: "⚽ **Niveau 5 - Vergevorderd clubniveau**\nSterke competitie-/selectiespeler. Goede techniek en tactisch inzicht.",
            6: "⚽ **Niveau 6 - Actieve clubspeler**\nKan goed meedoen in wedstrijden. Heeft controle over basistechnieken en positie.",
            7: "🌱 **Niveau 7 - Gevorderde beginner**\nRecreant die competitie begint. Kan korte rally's spelen, basis slagen aanwezig.",
            8: "🌱 **Niveau 8 - Beginner met ervaring**\nBeginnerscursus afgerond. Kan bal in het spel houden met forehand/backhand.",
            9: "🆕 **Niveau 9 - Absolute beginner**\nStarter/recreatief niveau. Kent de regels nog nauwelijks, heeft moeite met rally's."
        }
        level_text = f"**Jouw gekozen niveau: {speelsterkte}/9**\n\n{level_descriptions[speelsterkte]}"
    else:  # English
        level_descriptions = {
            1: "🏆 **Level 1 - International/professional level**\nATP/WTA player or ex-professional. Technical and physical at the highest level.",
            2: "🏆 **Level 2 - National top**\nTop 50 Netherlands. Technically and physically very strong, can compete at national level.",
            3: "🎾 **Level 3 - Regional top**\nNational sub-top level. Can compete at national level, regional champion.",
            4: "🎾 **Level 4 - Very strong club level**\nClub champion/regional sub-top. Consistency, power, spin and strategy are present.",
            5: "⚽ **Level 5 - Advanced club level**\nStrong competition/selection player. Good technique and tactical insight.",
            6: "⚽ **Level 6 - Active club player**\nCan compete well in matches. Has control over basic techniques and position.",
            7: "🌱 **Level 7 - Advanced beginner**\nRecreational player starting competition. Can play short rallies, basic strokes present.",
            8: "🌱 **Level 8 - Beginner with experience**\nBeginner course completed. Can keep ball in play with forehand/backhand.",
            9: "🆕 **Level 9 - Absolute beginner**\nStarter/recreational level. Barely knows the rules, has trouble with rallies."
        }
        level_text = f"**Your chosen level: {speelsterkte}/9**\n\n{level_descriptions[speelsterkte]}"
    
    st.info(level_text)
    
    # Enhanced permission checkbox with better styling
    toestemming_hoger_niveau = st.checkbox(
        "🎾 " + t['permission_checkbox'],
        help=t['permission_help']
    )
    
    # Clear explanation about permission requirement - exact same styling as st.info()
    if language == "nl":
        permission_explanation = """
        <div style="margin-top: 12px; padding: 0.75rem 1rem; background-color: rgb(231, 243, 255); border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; color: rgb(49, 51, 63);">
        <strong>💡 Belangrijk:</strong> Als het trainingniveau <strong>beter</strong> is dan jouw eigen niveau (lager getal = beter niveau), 
        dan heb je toestemming van een trainer nodig.<br><br>
        
        <strong>Voorbeeld:</strong><br>
        • Jij bent niveau <strong>7</strong><br>
        • Training is voor niveau <strong>6</strong><br>
        • Dan moet je deze checkbox aanvinken, anders word je <strong>niet ingedeeld</strong><br><br>
        
        <strong>Let op:</strong> Als de TC twijfels heeft over je niveau, 
        wordt dit nagevraagd bij de trainers voordat je wordt ingedeeld.
        </div>
        """
    else:  # English
        permission_explanation = """
        <div style="margin-top: 12px; padding: 0.75rem 1rem; background-color: rgb(231, 243, 255); border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; color: rgb(49, 51, 63);">
        <strong>💡 Important:</strong> If your level is <strong>better</strong> than the training (lower number = better level), 
        you need permission from a trainer.<br><br>
        
        <strong>Example:</strong><br>
        • You are level <strong>7</strong> (beginner)<br>
        • Training is for level <strong>6</strong> (active club player)<br>
        • Then you must check this checkbox, otherwise you will <strong>not be assigned</strong><br><br>
        
        <strong>Note:</strong> If the TC has doubts about your level, 
        this will be checked with the trainers before you are assigned.
        </div>
        """
    
    st.markdown(permission_explanation, unsafe_allow_html=True)
    
    # === TRAINING VOORKEUREN ===
    st.subheader(t['training_preferences'])
    
    trainingen_per_week = st.selectbox(
        t['frequency_question'],
        [t['frequency_1'], t['frequency_2'], t['frequency_3']],
        help=t['frequency_help']
    )
    
    # Bepaal aantal training sets
    if trainingen_per_week == t['frequency_1']:
        aantal_sets = 1
    elif trainingen_per_week == t['frequency_2']:
        aantal_sets = 2
    else:  # frequency_3
        aantal_sets = 3
    
    st.markdown(t['select_preferences'])
    
    # === DYNAMISCHE TRAINING VOORKEUREN ===
    alle_voorkeuren = []
    
    # Training 1 (altijd zichtbaar)
    st.markdown(t['training_1_prefs'])
    col1, col2, col3 = st.columns(3)
    with col1:
        voorkeur_1_set_1 = st.selectbox(
            t['choice_1'],
            [t['select_training']] + available_trainings,
            key="voorkeur_1_set_1",
            help=t['choice_1_help'].format(1)
        )
    
    remaining_1 = [opt for opt in available_trainings if opt != voorkeur_1_set_1]
    with col2:
        voorkeur_2_set_1 = st.selectbox(
            t['choice_2'],
            [t['select_training']] + remaining_1,
            key="voorkeur_2_set_1",
            help=t['choice_2_help'].format(1)
        )
    
    remaining_1 = [opt for opt in remaining_1 if opt != voorkeur_2_set_1]
    with col3:
        voorkeur_3_set_1 = st.selectbox(
            t['choice_3'],
            [t['no_third_choice']] + remaining_1,
            key="voorkeur_3_set_1",
            help=t['choice_3_help'].format(1)
        )
    
    alle_voorkeuren.append({
        'voorkeur_1': voorkeur_1_set_1,
        'voorkeur_2': voorkeur_2_set_1,
        'voorkeur_3': voorkeur_3_set_1
    })
    
    # Real-time permission check for Training 1
    training_1_choices = [voorkeur_1_set_1, voorkeur_2_set_1, voorkeur_3_set_1]
    permission_warnings_1 = check_permission_needed(speelsterkte, training_1_choices, toestemming_hoger_niveau)
    if permission_warnings_1:
        for warning in permission_warnings_1:
            st.error(t['not_assigned_warning'].format(warning))
            st.info(t['solution_message'])
    
    # Training 2 (alleen bij 2x of 3x per week)
    if aantal_sets >= 2:
        st.markdown("---")
        st.markdown(t['training_2_prefs'])
        
        # Filter uit eerste keuze van training 1
        al_gekozen = [voorkeur_1_set_1] if voorkeur_1_set_1 != t['select_training'] else []
        beschikbaar_2 = [opt for opt in available_trainings if opt not in al_gekozen]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            voorkeur_1_set_2 = st.selectbox(
                t['choice_1'],
                [t['select_training']] + beschikbaar_2,
                key="voorkeur_1_set_2",
                help=t['choice_1_help'].format(2)
            )
        
        remaining_2 = [opt for opt in beschikbaar_2 if opt != voorkeur_1_set_2]
        with col2:
            voorkeur_2_set_2 = st.selectbox(
                t['choice_2'],
                [t['select_training']] + remaining_2,
                key="voorkeur_2_set_2",
                help=t['choice_2_help'].format(2)
            )
        
        remaining_2 = [opt for opt in remaining_2 if opt != voorkeur_2_set_2]
        with col3:
            voorkeur_3_set_2 = st.selectbox(
                t['choice_3'],
                [t['no_third_choice']] + remaining_2,
                key="voorkeur_3_set_2",
                help=t['choice_3_help'].format(2)
            )
        
        alle_voorkeuren.append({
            'voorkeur_1': voorkeur_1_set_2,
            'voorkeur_2': voorkeur_2_set_2,
            'voorkeur_3': voorkeur_3_set_2
        })
        
        # Real-time permission check for Training 2
        training_2_choices = [voorkeur_1_set_2, voorkeur_2_set_2, voorkeur_3_set_2]
        permission_warnings_2 = check_permission_needed(speelsterkte, training_2_choices, toestemming_hoger_niveau)
        if permission_warnings_2:
            for warning in permission_warnings_2:
                st.error(t['not_assigned_warning'].format(warning))
                st.info(t['solution_message'])
    
    # Training 3 (alleen bij 3x per week)
    if aantal_sets >= 3:
        st.markdown("---")
        st.markdown(t['training_3_prefs'])
        
        # Filter uit eerste keuzes van training 1 en 2
        al_gekozen = []
        if voorkeur_1_set_1 != t['select_training']:
            al_gekozen.append(voorkeur_1_set_1)
        if voorkeur_1_set_2 != t['select_training']:
            al_gekozen.append(voorkeur_1_set_2)
        beschikbaar_3 = [opt for opt in available_trainings if opt not in al_gekozen]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            voorkeur_1_set_3 = st.selectbox(
                t['choice_1'],
                [t['select_training']] + beschikbaar_3,
                key="voorkeur_1_set_3",
                help=t['choice_1_help'].format(3)
            )
        
        remaining_3 = [opt for opt in beschikbaar_3 if opt != voorkeur_1_set_3]
        with col2:
            voorkeur_2_set_3 = st.selectbox(
                t['choice_2'],
                [t['select_training']] + remaining_3,
                key="voorkeur_2_set_3",
                help=t['choice_2_help'].format(3)
            )
        
        remaining_3 = [opt for opt in remaining_3 if opt != voorkeur_2_set_3]
        with col3:
            voorkeur_3_set_3 = st.selectbox(
                t['choice_3'],
                [t['no_third_choice']] + remaining_3,
                key="voorkeur_3_set_3",
                help=t['choice_3_help'].format(3)
            )
        
        alle_voorkeuren.append({
            'voorkeur_1': voorkeur_1_set_3,
            'voorkeur_2': voorkeur_2_set_3,
            'voorkeur_3': voorkeur_3_set_3
        })
        
        # Real-time permission check for Training 3
        training_3_choices = [voorkeur_1_set_3, voorkeur_2_set_3, voorkeur_3_set_3]
        permission_warnings_3 = check_permission_needed(speelsterkte, training_3_choices, toestemming_hoger_niveau)
        if permission_warnings_3:
            for warning in permission_warnings_3:
                st.error(t['not_assigned_warning'].format(warning))
                st.info(t['solution_message'])
    
    # === AANVULLENDE INFORMATIE ===
    st.subheader(t['additional_info'])
    
    extra_bericht = st.text_area(
        t['extra_message'],
        placeholder=t['extra_message_placeholder'],
        height=100
    )
    
    # === SUBMIT BUTTON ===
    st.markdown("---")
    if st.button(t['submit_button'], type="primary"):
        # Validation
        errors = []
        
        if not voornaam.strip():
            errors.append(t['name_required'].split(' en ')[0])  # First name required
        if not achternaam.strip():
            errors.append(t['name_required'].split(' en ')[1])  # Last name required
        if not telefoon.strip():
            errors.append(t['phone_required'])
        
        # Validatie voor alle training sets
        for i, voorkeuren_set in enumerate(alle_voorkeuren, 1):
            if voorkeuren_set['voorkeur_1'] == t['select_training']:
                errors.append(t['training_required'].format(f"{i}: {t['choice_1']}"))
            if voorkeuren_set['voorkeur_2'] == t['select_training']:
                errors.append(t['training_required'].format(f"{i}: {t['choice_2']}"))
        
        # Check permission for higher level trainings
        all_training_choices = []
        for voorkeuren_set in alle_voorkeuren:
            all_training_choices.extend([
                voorkeuren_set['voorkeur_1'],
                voorkeuren_set['voorkeur_2'], 
                voorkeuren_set['voorkeur_3']
            ])
        
        permission_warnings = check_permission_needed(speelsterkte, all_training_choices, toestemming_hoger_niveau)
        errors.extend(permission_warnings)
        
        if errors:
            st.error(t['validation_error'])
            for error in errors:
                st.write(f"• {error}")
        else:
            # Prepare registration data - één rij per gewenste training
            alle_registraties = []
            
            basis_data = {
                "Naam": f"{voornaam.strip()} {achternaam.strip()}",
                "Telefoon": telefoon.strip(),
                "Inschrijfdatum": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Speelsterkte": speelsterkte,
                "Toestemming_hoger_niveau": "Ja" if toestemming_hoger_niveau else "Nee",
                "Trainingen_per_week": trainingen_per_week,
                "Extra_bericht": extra_bericht.strip(),
                "Taal": "Nederlands" if language == "nl" else "English",
                # Keep compatible fields for existing planning system
                "Niveau": speelsterkte,  # For compatibility with planning logic
                "Ervaring": "Niet opgegeven"
            }
            
            # Maak een registratie voor elke gewenste training
            for i, voorkeuren_set in enumerate(alle_voorkeuren, 1):
                training_data = basis_data.copy()
                training_data.update({
                    "Training_nummer": i,
                    "Voorkeur_1": voorkeuren_set['voorkeur_1'] if voorkeuren_set['voorkeur_1'] != t['select_training'] else "",
                    "Voorkeur_2": voorkeuren_set['voorkeur_2'] if voorkeuren_set['voorkeur_2'] != t['select_training'] else "",
                    "Voorkeur_3": voorkeuren_set['voorkeur_3'] if voorkeuren_set['voorkeur_3'] != t['no_third_choice'] else "",
                })
                alle_registraties.append(training_data)
            
            try:
                # Sla alle registraties op in één keer
                duplicate_found = save_multiple_registrations(alle_registraties)
                
                if duplicate_found:
                    st.info(t['duplicate_replaced'])
                st.success(t['success_message'])
                st.balloons()
                
                # Show summary
                with st.expander(t['summary_title']):
                    eerste_registratie = alle_registraties[0]
                    st.write(f"**{t['summary_name']}:** {eerste_registratie['Naam']}")
                    st.write(f"**{t['summary_phone']}:** {eerste_registratie['Telefoon']}")
                    st.write(f"**{t['summary_skill']}:** {eerste_registratie['Speelsterkte']}/9")
                    st.write(f"**{t['summary_permission']}:** {eerste_registratie['Toestemming_hoger_niveau']}")
                    st.write(f"**{t['summary_frequency']}:** {eerste_registratie['Trainingen_per_week']}")
                    
                    # Toon alle training voorkeuren
                    for i, registratie in enumerate(alle_registraties, 1):
                        st.write(f"**{t['summary_training_prefs'].format(i)}:**")
                        st.write(f"  • {t['summary_choice_1']}: {registratie['Voorkeur_1']}")
                        st.write(f"  • {t['summary_choice_2']}: {registratie['Voorkeur_2']}")
                        if registratie['Voorkeur_3']:
                            st.write(f"  • {t['summary_choice_3']}: {registratie['Voorkeur_3']}")
                    
                    if eerste_registratie['Extra_bericht']:
                        st.write(f"**{t['summary_extra_message']}:** {eerste_registratie['Extra_bericht']}")
                    st.write(f"**{t['summary_registered_on']}:** {eerste_registratie['Inschrijfdatum']}")
            
            except Exception as e:
                st.error(t['error_saving'])
                st.write(f"Error details: {str(e)}")

    # Additional information section
    st.markdown("---")
    st.subheader(t['info_section'])
    
    if available_trainings:
        st.markdown(t['available_trainings'])
        for training in available_trainings:
            st.write(f"• {training}")
    
    st.markdown("")
    st.markdown(t['contact_info']) 