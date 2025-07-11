import streamlit as st
import os
from openai import OpenAI
from bs4 import BeautifulSoup
import html2text
import re

# Page configuration
st.set_page_config(
    page_title="Meko Clinic Rhinoplasty Chatbot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Language options
LANGUAGES = {
    "English": "en",
    "Spanish": "es", 
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Hindi": "hi",
    "Urdu": "ur",
    "Turkish": "tr"
}

# Initialize OpenAI client
@st.cache_resource
def init_openai_client():
    api_key = st.secrets.get("AIML_API_KEY", "")
    if not api_key:
        st.error("⚠️ AIML API Key not found. Please add it to your Streamlit secrets.")
        st.stop()
    
    return OpenAI(
        base_url="https://api.aimlapi.com/v1",
        api_key=api_key
    )

# Load and parse HTML content
@st.cache_data
def load_html_content():
    try:
        with open(os.path.join(os.path.dirname(__file__), "meko_clinic_rhinoplasty.html"), "r", encoding="utf-8") as file:
            html_content = file.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Convert to text
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        text_content = h.handle(str(soup))
        
        # Clean up the text
        text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
        text_content = re.sub(r'\s+', ' ', text_content)
        
        return text_content.strip()
        
    except FileNotFoundError:
        st.error("❌ HTML file 'meko_clinic_rhinoplasty.html' not found in the current directory.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading HTML file: {str(e)}")
        st.stop()

# Generate response using AIML API
def generate_response(user_message, language, clinic_content):
    try:
        client = init_openai_client()
        
        # Create system prompt based on selected language
        system_prompt = f"""You are a helpful medical assistant for Meko Clinic specializing in rhinoplasty procedures. 
        
        Please respond in {language} language. Use the following clinic information to answer questions:
        
        {clinic_content}
        
        Guidelines:
        - Always respond in {language} and in same script of selected {language} language
        - Be professional and informative
        - Focus on the rhinoplasty services offered by Meko Clinic
        - If asked about something not in the clinic information, politely redirect to available services
        - Provide helpful and accurate information about rhinoplasty procedures
        - Always recommend consulting with the clinic directly for personalized advice
        """
        
        response = client.chat.completions.create(
            model="x-ai/grok-3-mini-beta",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error generating response: {str(e)}"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "clinic_content" not in st.session_state:
    st.session_state.clinic_content = load_html_content()

# Sidebar
with st.sidebar:
    st.title("🏥 Meko Clinic")
    st.markdown("### Rhinoplasty Chatbot")
    
    # Language selection
    selected_language = st.selectbox(
        "🌐 Select Language",
        options=list(LANGUAGES.keys()),
        index=0
    )
    
    st.markdown("---")
    
    # API Key input (if not in secrets)
    if not st.secrets.get("AIML_API_KEY"):
        api_key = st.text_input(
            "🔑 AIML API Key",
            type="password",
            help="Enter your AIML API key"
        )
        if api_key:
            st.session_state.api_key = api_key
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # Info section
    st.markdown("### ℹ️ About")
    st.markdown("""
    This chatbot can help you with information about:
    - Rhinoplasty procedures
    - Clinic services
    - Pre and post-operative care
    - Consultation booking
    
    *Please consult with medical professionals for personalized advice.*
    """)

# Main chat interface
st.title("💬 Meko Clinic Rhinoplasty Assistant")
st.markdown(f"**Current Language:** {selected_language}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about rhinoplasty procedures..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(
                prompt, 
                selected_language, 
                st.session_state.clinic_content
            )
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 14px;'>
        🏥 Meko Clinic Rhinoplasty Chatbot | Powered by AIML API & OpenAI
    </div>
    """,
    unsafe_allow_html=True
)

# Display sample questions based on language
if len(st.session_state.messages) == 0:
    st.markdown("### 💡 Sample Questions")
    
    sample_questions = {
        "English": [
            "What rhinoplasty procedures do you offer?",
            "What is the recovery time for rhinoplasty?",
            "How much does rhinoplasty cost?",
            "What should I expect during consultation?"
        ],
        "Spanish": [
            "¿Qué procedimientos de rinoplastia ofrecen?",
            "¿Cuál es el tiempo de recuperación de la rinoplastia?",
            "¿Cuánto cuesta la rinoplastia?",
            "¿Qué debo esperar durante la consulta?"
        ],
        "French": [
            "Quelles procédures de rhinoplastie proposez-vous?",
            "Quel est le temps de récupération pour la rhinoplastie?",
            "Combien coûte la rhinoplastie?",
            "À quoi dois-je m'attendre lors de la consultation?"
        ],
        "German": [
            "Welche Nasenoperationen bieten Sie an?",
            "Wie lange ist die Heilungszeit nach einer Nasenoperation?",
            "Was kostet eine Nasenoperation?",
            "Was erwartet mich bei der Beratung?"
        ]
    }
    
    questions = sample_questions.get(selected_language, sample_questions["English"])
    
    cols = st.columns(2)
    for i, question in enumerate(questions):
        with cols[i % 2]:
            if st.button(question, key=f"sample_{i}"):
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()