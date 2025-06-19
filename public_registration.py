import streamlit as st
from components.registration_form_simple import registration_form

# Configure the public registration page as standalone (no multipage)
st.set_page_config(
    page_title="Tennis Training Aanmelding", 
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar
)

# Remove any multipage functionality by clearing the pages
import streamlit.web.bootstrap as bootstrap
if hasattr(st, '_get_main_script_director'):
    # Clear any registered pages to prevent sidebar navigation
    try:
        st.session_state.clear()
    except:
        pass

# Custom CSS to hide Streamlit branding and create dark professional theme
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hide hamburger menu button */
    .css-14xtw13.e8zbici0 {display: none !important;}
    .css-vk3wp9 {display: none !important;}
    .css-1rs6os {display: none !important;}
    .css-17ziqus {display: none !important;}
    button[kind="header"] {display: none !important;}
    button[data-testid="collapsedControl"] {display: none !important;}
    .stButton[data-testid="collapsedControl"] {display: none !important;}
    
    /* Hide sidebar completely for public users - multiple selectors for different Streamlit versions */
    .css-1d391kg {display: none !important;}
    .css-1cypcdb {display: none !important;}
    .css-17eq0hr {display: none !important;}
    .css-1lcbmhc {display: none !important;}
    .css-1y4p8pa {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    .stSidebar {display: none !important;}
    
    /* Also hide any navigation elements */
    .css-10trblm {display: none !important;}
    .css-1inwz65 {display: none !important;}
    
    /* Dark theme for main app */
    .stApp {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    
    /* Custom styling for main content */
    .main > div {
        padding-top: 2rem;
        background-color: #1e1e1e;
    }
    
    /* Soft dark form styling */
    .stForm {
        border: 1px solid #404040;
        border-radius: 15px;
        padding: 2.5rem;
        margin: 1.5rem 0;
        background-color: #2d2d2d;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    /* Form input styling */
    .stTextInput > div > div > input {
        background-color: #3a3a3a;
        color: #e0e0e0;
        border: 1px solid #555555;
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 5px rgba(76, 175, 80, 0.3);
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        background-color: #3a3a3a;
        color: #e0e0e0;
        border: 1px solid #555555;
        border-radius: 8px;
    }
    
    /* Select box styling */
    .stSelectbox > div > div > select {
        background-color: #3a3a3a;
        color: #e0e0e0;
        border: 1px solid #555555;
    }
    
    /* Slider styling */
    .stSlider > div > div > div > div {
        background-color: #4CAF50;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        color: #e0e0e0;
    }
    
    /* Headers styling */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    
    /* Markdown text styling */
    .stMarkdown {
        color: #d0d0d0;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #1b4332;
        border: 1px solid #4CAF50;
        color: #a8e6cf;
    }
    
    .stError {
        background-color: #4a1e1e;
        border: 1px solid #f44336;
        color: #ffcdd2;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #1e3a5f;
        border: 1px solid #2196F3;
        color: #bbdefb;
    }
</style>

<script>
// Force hide sidebar on page load
document.addEventListener('DOMContentLoaded', function() {
    function hideSidebar() {
        // Hide sidebar by various selectors
        const sidebarSelectors = [
            '.css-1d391kg',
            '.css-1cypcdb', 
            '.css-17eq0hr',
            '.css-1lcbmhc',
            '.css-1y4p8pa',
            'section[data-testid="stSidebar"]',
            '.stSidebar'
        ];
        
        // Hide hamburger menu button selectors
        const hamburgerSelectors = [
            '.css-14xtw13.e8zbici0',
            '.css-vk3wp9',
            '.css-1rs6os',
            '.css-17ziqus',
            'button[kind="header"]',
            'button[data-testid="collapsedControl"]',
            '.stButton[data-testid="collapsedControl"]'
        ];
        
        // Hide sidebar elements
        sidebarSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
            });
        });
        
        // Hide hamburger menu button
        hamburgerSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
            });
        });
    }
    
    // Hide immediately and also on any DOM changes
    hideSidebar();
    
    // Create observer to hide sidebar if it appears
    const observer = new MutationObserver(hideSidebar);
    observer.observe(document.body, { childList: true, subtree: true });
});
</script>
""", unsafe_allow_html=True)

# Main content - only the registration form
def main():
    # Header with club information
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1>🎾 Tennis Training Aanmelding</h1>
        <p style="font-size: 1.2em; color: #666;">
            Welkom! Meld je hier aan voor onze tennis trainingen.
        </p>

    </div>
    """, unsafe_allow_html=True)
    
    # Show the registration form
    registration_form()
    
    # Footer with contact information
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #666;">
        <p><strong>Tennis Club Contact</strong></p>
        <p>📧 info@tennisclub.nl | 📞 +31 (0)12 345 6789</p>
        <p>🏢 Sportlaan 123, 1234 AB Tennisstad</p>
        <p style="margin-top: 1rem; font-size: 0.9em;">
            🌐 Language support: Nederlands & English
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 