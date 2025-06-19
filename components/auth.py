import streamlit as st
from datetime import datetime
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_LOG_PATH = BASE_DIR / "data" / "auth_log.json"

# Admin access code
ADMIN_CODE = "legends"

def log_auth_attempt(success, ip_address=None, timestamp=None):
    """Log authentication attempts for audit trail"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = {
        "timestamp": timestamp,
        "success": success,
        "ip_address": ip_address or "Unknown",
        "user_agent": "Admin Dashboard"
    }
    
    # Load existing log
    auth_log = []
    if AUTH_LOG_PATH.exists():
        try:
            with open(AUTH_LOG_PATH, 'r', encoding='utf-8') as f:
                auth_log = json.load(f)
        except:
            auth_log = []
    
    # Add new entry
    auth_log.append(log_entry)
    
    # Keep only last 100 entries
    auth_log = auth_log[-100:]
    
    # Save log
    os.makedirs(AUTH_LOG_PATH.parent, exist_ok=True)
    with open(AUTH_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(auth_log, f, indent=2, ensure_ascii=False)

def check_admin_access():
    """Check if user is authenticated as admin"""
    return st.session_state.get('admin_authenticated', False)

def login_form():
    """Display login form and handle authentication"""
    st.title("🔐 Admin Login")
    st.markdown("""
    **Toegang tot Admin Dashboard**
    
    Voer de toegangscode in om toegang te krijgen tot de admin functies.
    """)
    
    with st.form("login_form"):
        st.markdown("### 🔑 Authenticatie")
        
        access_code = st.text_input(
            "Toegangscode:",
            type="password",
            placeholder="Voer toegangscode in...",
            help="Voer de juiste toegangscode in voor admin toegang"
        )
        
        submit_login = st.form_submit_button("🚪 Inloggen", type="primary")
        
        if submit_login:
            if access_code == ADMIN_CODE:
                # Successful login
                st.session_state['admin_authenticated'] = True
                st.session_state['login_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Log successful attempt
                log_auth_attempt(success=True)
                
                st.success("✅ **Login succesvol!**")
                st.info("🔄 Pagina wordt vernieuwd...")
                st.balloons()
                st.rerun()
                
            else:
                # Failed login
                log_auth_attempt(success=False)
                
                st.error("❌ **Ongeldige toegangscode!**")
                st.warning("⚠️ Zorg ervoor dat je de juiste code invoert.")
                
                # Show recent failed attempts (security info)
                if AUTH_LOG_PATH.exists():
                    try:
                        with open(AUTH_LOG_PATH, 'r', encoding='utf-8') as f:
                            auth_log = json.load(f)
                        
                        failed_attempts = [entry for entry in auth_log[-10:] if not entry['success']]
                        if len(failed_attempts) >= 3:
                            st.warning(f"⚠️ {len(failed_attempts)} recente mislukte pogingen gedetecteerd.")
                    except:
                        pass
    
    # Security information
    st.markdown("---")
    st.markdown("""
    ### 🛡️ Beveiligingsinformatie
    
    - Alle login pogingen worden gelogd voor audit doeleinden
    - Bij herhaalde mislukte pogingen wordt dit geregistreerd
    - Alleen geautoriseerde personen hebben toegang tot deze code
    
    **Contact:** Bij problemen met inloggen, neem contact op met de technische commissie.
    """)

def logout():
    """Handle user logout"""
    if 'admin_authenticated' in st.session_state:
        del st.session_state['admin_authenticated']
    if 'login_timestamp' in st.session_state:
        del st.session_state['login_timestamp']
    
    st.success("✅ **Succesvol uitgelogd!**")
    st.info("🔄 Pagina wordt vernieuwd...")
    st.rerun()

def show_admin_header():
    """Show admin header with logout option"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        login_time = st.session_state.get('login_timestamp', 'Onbekend')
        st.success(f"🔐 **Admin toegang actief** - Ingelogd: {login_time}")
    
    with col3:
        if st.button("🚪 Uitloggen", type="secondary"):
            logout()

def get_auth_log():
    """Get authentication log for admin view"""
    if not AUTH_LOG_PATH.exists():
        return []
    
    try:
        with open(AUTH_LOG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def show_auth_log():
    """Display authentication log in admin dashboard"""
    st.subheader("🔍 Login Geschiedenis")
    
    auth_log = get_auth_log()
    
    if not auth_log:
        st.info("📝 Geen login geschiedenis beschikbaar.")
        return
    
    # Statistics
    total_attempts = len(auth_log)
    successful_logins = len([entry for entry in auth_log if entry['success']])
    failed_attempts = total_attempts - successful_logins
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Totaal Pogingen", total_attempts)
    with col2:
        st.metric("Succesvol", successful_logins)
    with col3:
        st.metric("Mislukt", failed_attempts)
    
    # Recent activity
    st.markdown("### 📋 Recente Activiteit")
    
    # Show last 20 entries
    recent_log = auth_log[-20:]
    recent_log.reverse()  # Most recent first
    
    for entry in recent_log:
        timestamp = entry['timestamp']
        success = entry['success']
        ip_address = entry.get('ip_address', 'Onbekend')
        
        if success:
            st.success(f"✅ **{timestamp}** - Succesvol ingelogd (IP: {ip_address})")
        else:
            st.error(f"❌ **{timestamp}** - Mislukte poging (IP: {ip_address})")
    
    # Download log
    if st.button("📥 Download Volledige Log"):
        log_data = json.dumps(auth_log, indent=2, ensure_ascii=False)
        st.download_button(
            label="💾 Download auth_log.json",
            data=log_data.encode('utf-8'),
            file_name=f"auth_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        ) 