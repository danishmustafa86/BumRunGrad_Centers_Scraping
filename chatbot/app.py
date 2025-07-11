import streamlit as st
import os
from openai import OpenAI
from bs4 import BeautifulSoup
import html2text
import re
from langdetect import detect
import langdetect.lang_detect_exception

# Page configuration
st.set_page_config(
    page_title="Meko Clinic Rhinoplasty Chatbot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced language mapping with native names and ISO codes (Thai added)
LANGUAGES = {
    "English": {"code": "en", "name": "English", "native": "English"},
    "Spanish": {"code": "es", "name": "Español", "native": "Español"},
    "French": {"code": "fr", "name": "Français", "native": "Français"},
    "German": {"code": "de", "name": "Deutsch", "native": "Deutsch"},
    "Italian": {"code": "it", "name": "Italiano", "native": "Italiano"},
    "Portuguese": {"code": "pt", "name": "Português", "native": "Português"},
    "Russian": {"code": "ru", "name": "Русский", "native": "Русский"},
    "Chinese": {"code": "zh", "name": "中文", "native": "中文"},
    "Japanese": {"code": "ja", "name": "日本語", "native": "日本語"},
    "Korean": {"code": "ko", "name": "한국어", "native": "한국어"},
    "Arabic": {"code": "ar", "name": "العربية", "native": "العربية"},
    "Hindi": {"code": "hi", "name": "हिंदी", "native": "हिंदी"},
    "Urdu": {"code": "ur", "name": "اردو", "native": "اردو"},
    "Turkish": {"code": "tr", "name": "Türkçe", "native": "Türkçe"},
    "Thai": {"code": "th", "name": "ไทย", "native": "ไทย"}
}

# Enhanced language detection mapping (Thai added)
LANG_DETECT_MAP = {
    "en": "English",
    "es": "Spanish", 
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "zh-cn": "Chinese",
    "zh-tw": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "ur": "Urdu",
    "tr": "Turkish",
    "th": "Thai"
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

# Enhanced language detection function with Thai and Roman script support
def detect_language(text):
    try:
        # Clean text for better detection
        clean_text = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u0900-\u097F\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04FF\u0E00-\u0E7F]', ' ', text)
        
        # Convert to lowercase for pattern matching
        text_lower = text.lower()
        
        # First check for native scripts
        if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
            # Arabic/Urdu script detection
            urdu_patterns = [
                r'یہ', r'کیا', r'ہے', r'کے', r'میں', r'کو', r'سے', r'کہ', r'اور', 
                r'یار', r'ہا', r'کا', r'کی', r'نہیں', r'ہوں', r'ہیں', r'تھا', r'تھی',
                r'کریں', r'کرتے', r'کرنا', r'ہوا', r'ہوئی', r'گیا', r'گئی', r'دیا',
                r'لیا', r'آپ', r'میرا', r'تیرا', r'اس', r'اب', r'پہلے', r'بعد'
            ]
            
            arabic_patterns = [
                r'هذا', r'هذه', r'ذلك', r'التي', r'الذي', r'في', r'من', r'إلى',
                r'على', r'عن', r'مع', r'كان', r'كانت', r'يكون', r'تكون', r'لكن',
                r'أو', r'أم', r'ما', r'لا', r'نعم', r'كيف', r'متى', r'أين', r'لماذا'
            ]
            
            urdu_score = sum(1 for pattern in urdu_patterns if re.search(pattern, text))
            arabic_score = sum(1 for pattern in arabic_patterns if re.search(pattern, text))
            
            if urdu_score > arabic_score:
                return "Urdu"
            elif arabic_score > 0:
                return "Arabic"
            else:
                if any(word in text for word in ['یار', 'کیا', 'ہے', 'اور']):
                    return "Urdu"
                return "Arabic"
        
        # Check for Thai script (NEW)
        if re.search(r'[\u0E00-\u0E7F]', text):
            return "Thai"
        
        # Check for other native scripts
        if re.search(r'[\u0900-\u097F]', text):
            return "Hindi"
        if re.search(r'[\u4e00-\u9fff]', text):
            return "Chinese"
        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return "Japanese"
        if re.search(r'[\uac00-\ud7af]', text):
            return "Korean"
        if re.search(r'[\u0400-\u04FF]', text):
            return "Russian"
        
        # NEW: Check for Roman Thai (Thai written in Latin script)
        roman_thai_patterns = [
            # Common Thai words in Roman script
            r'\b(chai|mai|krub|krab|ka|kha|khun|nai|thi|ni|nan|kap|gap)\b',
            r'\b(arai|yang|ngai|thao|rai|dai|pen|mak|noi|yak|sabai|sanuk)\b',
            r'\b(gin|khao|nam|phom|chan|rao|khao|pai|ma|yu|nang|yen)\b',
            r'\b(rong|phaya|ban|baht|satang|saphan|thanon|mueang|krung|thep)\b',
            r'\b(doctor|mor|hospital|clinic|surgery|rhinoplasty|dang|jak)\b',
            r'\b(sawatdi|khob|khun|krub|krab|chai|mai|pen|yang|rai|dai)\b',
            r'\b(aroi|sabai|sanuk|suai|ngam|yak|noi|mak|maak|chob|phom)\b',
            r'\b(laew|yang|thao|rai|mueang|kap|gap|nai|thi|ni|nan|arai)\b'
        ]
        
        # Count Roman Thai pattern matches
        roman_thai_score = sum(1 for pattern in roman_thai_patterns if re.search(pattern, text_lower))
        
        # NEW: Check for Roman Urdu (Urdu written in Latin script)
        roman_urdu_patterns = [
            # Common Urdu words in Roman script
            r'\b(kya|hai|hain|ka|ki|ke|ko|se|me|main|mein|aur|ya|yaar|yar)\b',
            r'\b(ap|aap|tum|wo|woh|ye|yeh|is|us|iska|uska|mera|tera|humara)\b',
            r'\b(kaise|kahan|kab|kyun|kyunke|lekin|magar|phir|abhi|ab)\b',
            r'\b(kar|karna|karte|karta|karti|kiya|kiye|tha|thi|the)\b',
            r'\b(hona|hota|hoti|hote|hua|hui|huye|gaya|gayi|gaye)\b',
            r'\b(dena|deta|deti|dete|diya|diye|lena|leta|leti|lete|liya|liye)\b',
            r'\b(jana|jata|jati|jate|ghar|paisa|paise|kitna|kitne|kitni)\b',
            r'\b(accha|acha|bura|bhi|nahi|nahin|haan|han|ji|sahab|sahib)\b',
            r'\b(bhala|bhali|bhale|wala|wali|wale|pani|khana|kaam|kam)\b',
            r'\b(dost|doston|beta|beti|bhai|behan|ma|maa|papa|ammi|abbu)\b',
            r'\b(lagta|lagti|lagte|hota|hoti|hote|karta|karti|karte)\b',
            r'\b(surgery|doctor|hospital|clinic|treatment|medicine|dawai)\b'
        ]
        
        # Count Roman Urdu pattern matches
        roman_urdu_score = sum(1 for pattern in roman_urdu_patterns if re.search(pattern, text_lower))
        
        # NEW: Check for Roman Hindi (Hindi written in Latin script)
        roman_hindi_patterns = [
            r'\b(kya|hai|hain|ka|ki|ke|ko|se|me|main|mein|aur|ya)\b',
            r'\b(ap|aap|tum|wo|woh|ye|yeh|is|us|iska|uska|mera|tera|hamara)\b',
            r'\b(kaise|kahan|kab|kyun|kyunki|lekin|phir|abhi|ab|tab)\b',
            r'\b(kar|karna|karte|karta|karti|kiya|kiye|tha|thi|the)\b',
            r'\b(hona|hota|hoti|hote|hua|hui|huye|gaya|gayi|gaye)\b',
            r'\b(dena|deta|deti|dete|diya|diye|lena|leta|leti|lete|liya|liye)\b',
            r'\b(jana|jata|jati|jate|ghar|paisa|paise|kitna|kitne|kitni)\b',
            r'\b(accha|acha|bura|bhi|nahi|nahin|haan|han|ji|sahab|sahib)\b',
            r'\b(bhala|bhali|bhale|wala|wali|wale|pani|khana|kaam|kam)\b',
            r'\b(dost|doston|beta|beti|bhai|behan|ma|maa|papa|mata|pita)\b'
        ]
        
        # Count Roman Hindi pattern matches
        roman_hindi_score = sum(1 for pattern in roman_hindi_patterns if re.search(pattern, text_lower))
        
        # NEW: Check for Roman Arabic (Arabic written in Latin script)
        roman_arabic_patterns = [
            r'\b(ma|maa|hal|haal|fee|fi|min|ila|ala|an|anna|la|laa)\b',
            r'\b(wa|waa|aw|am|kam|kayf|mata|ayna|limatha|limaza)\b',
            r'\b(hatha|haza|tilka|allati|allathi|kana|kanat|yakun|takun)\b',
            r'\b(lakin|aw|ma|naam|kayf|shukran|ahlan|marhaba|allah)\b'
        ]
        
        # Count Roman Arabic pattern matches
        roman_arabic_score = sum(1 for pattern in roman_arabic_patterns if re.search(pattern, text_lower))
        
        # Determine language based on Roman script patterns
        if roman_thai_score > 0 or roman_urdu_score > 0 or roman_hindi_score > 0 or roman_arabic_score > 0:
            max_score = max(roman_thai_score, roman_urdu_score, roman_hindi_score, roman_arabic_score)
            if roman_thai_score == max_score:
                return "Thai"
            elif roman_urdu_score == max_score:
                return "Urdu"
            elif roman_hindi_score == max_score:
                return "Hindi"
            elif roman_arabic_score == max_score:
                return "Arabic"
        
        # Check for specific medical + local language combinations
        medical_terms = ['rhinoplasty', 'rhino', 'plasty', 'surgery', 'nose', 'job', 'operation', 'clinic', 'doctor']
        has_medical_terms = any(term in text_lower for term in medical_terms)
        
        if has_medical_terms:
            # If medical terms are mixed with local language words, prioritize the local language
            if any(word in text_lower for word in ['chai', 'mai', 'krub', 'krab', 'khun', 'arai', 'yang', 'ngai']):
                return "Thai"
            elif any(word in text_lower for word in ['kya', 'hai', 'hain', 'yaar', 'yar', 'lagta', 'hota', 'kaise']):
                # Check for Urdu-specific indicators
                if any(word in text_lower for word in ['yaar', 'yar', 'lagta', 'hota']):
                    return "Urdu"
                # Otherwise likely Hindi
                return "Hindi"
        
        # Try langdetect for other languages
        try:
            detected_lang = detect(clean_text)
            if detected_lang in LANG_DETECT_MAP:
                return LANG_DETECT_MAP[detected_lang]
        except:
            pass
        
        # Default to English if no patterns match
        return "English"
        
    except Exception as e:
        # Enhanced fallback detection
        text_lower = text.lower()
        
        # Check for Roman Thai in fallback
        if any(word in text_lower for word in ['chai', 'mai', 'krub', 'krab', 'khun', 'arai', 'yang', 'ngai', 'sabai', 'sanuk']):
            return "Thai"
        
        # Check for Roman Urdu/Hindi in fallback
        if any(word in text_lower for word in ['kya', 'hai', 'yaar', 'yar', 'kar', 'karna', 'hona', 'lagta', 'hota']):
            # Simple heuristic: if 'yaar' or 'yar' is present, likely Urdu
            if any(word in text_lower for word in ['yaar', 'yar', 'lagta', 'hota']):
                return "Urdu"
            # Otherwise, could be Hindi
            return "Hindi"
        
        # Check for native scripts in fallback
        if re.search(r'[\u0E00-\u0E7F]', text):
            return "Thai"
        elif re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
            return "Arabic"
        elif re.search(r'[\u0900-\u097F]', text):
            return "Hindi"
        elif re.search(r'[\u4e00-\u9fff]', text):
            return "Chinese"
        elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return "Japanese"
        elif re.search(r'[\uac00-\ud7af]', text):
            return "Korean"
        elif re.search(r'[\u0400-\u04FF]', text):
            return "Russian"
        else:
            return "English"

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

# Enhanced response generation with better language enforcement (Thai added)
def generate_response(user_message, detected_language, clinic_content):
    try:
        client = init_openai_client()
        
        # Get language info
        lang_info = LANGUAGES.get(detected_language, LANGUAGES["English"])
        lang_code = lang_info["code"]
        lang_name = lang_info["name"]
        native_name = lang_info["native"]
        
        # Create enhanced system prompt with stronger language enforcement
        system_prompt = f"""You are a helpful medical assistant for Meko Clinic specializing in rhinoplasty procedures.

CRITICAL LANGUAGE REQUIREMENT:
- The user has written in {detected_language} language (even if they used English/Latin letters)
- You MUST respond ONLY in {detected_language} language
- You MUST use the native script/writing system of {detected_language}: {native_name}
- DO NOT use English or any other language in your response
- DO NOT translate or explain in English
- If user wrote in Roman script (like "kya hai" or "chai mai"), respond in native script

SPECIFIC SCRIPT REQUIREMENTS:
- If {detected_language} is Thai: Write ONLY in Thai script (เขียนเป็นภาษาไทยเท่านั้น)
- If {detected_language} is Urdu: Write ONLY in Urdu script (اردو میں لکھیں)
- If {detected_language} is Arabic: Write ONLY in Arabic script (اكتب بالعربية فقط)
- If {detected_language} is Hindi: Write ONLY in Hindi script (हिंदी में लिखें)
- If {detected_language} is Chinese: Write ONLY in Chinese characters (用中文写)
- If {detected_language} is Japanese: Write ONLY in Japanese script (日本語で書く)
- If {detected_language} is Korean: Write ONLY in Korean script (한국어로 쓰기)
- If {detected_language} is Russian: Write ONLY in Cyrillic script (пишите на русском)
- If {detected_language} is any other language: Use its native script exclusively

IMPORTANT EXAMPLES:
- User input: "rhinoplasty arai krub" → Detected: Thai → Response: "ไรโนพลาสตี้เป็นการผ่าตัดเสริมจมูก..."
- User input: "rhinoplasty kya hai" → Detected: Urdu → Response: "رائنوپلاسٹی ایک جراحی کا طریقہ ہے..."
- User input: "nose job kitna paisa lagta hai" → Detected: Urdu → Response: "ناک کی جراحی کی لاگت..."
- User input: "surgery thao rai krub" → Detected: Thai → Response: "การผ่าตัดมีราคา..."

Use the following clinic information to answer questions:
{clinic_content}

Guidelines:
- Be professional and informative in {detected_language}
- Focus on rhinoplasty services offered by Meko Clinic
- If asked about something not in the clinic information, politely redirect to available services in {detected_language}
- Provide helpful and accurate information about rhinoplasty procedures in {detected_language}
- Always recommend consulting with the clinic directly for personalized advice in {detected_language}
- Maintain cultural sensitivity and appropriate medical terminology for {detected_language}
- Your entire response must be in {detected_language} language using {native_name} script
- Use respectful forms of address appropriate for {detected_language} culture"""
        
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
        # Return error message in detected language
        if detected_language == "Thai":
            return f"❌ เกิดข้อผิดพลาดในการสร้างการตอบกลับ: {str(e)}"
        elif detected_language == "Urdu":
            return f"❌ جواب بنانے میں خرابی: {str(e)}"
        elif detected_language == "Arabic":
            return f"❌ خطأ في إنشاء الاستجابة: {str(e)}"
        elif detected_language == "Hindi":
            return f"❌ प्रतिक्रिया उत्पन्न करने में त्रुटि: {str(e)}"
        else:
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
    
    # Language selection (now for display purposes and manual override)
    selected_language = st.selectbox(
        "🌐 Manual Language Override (Optional)",
        options=["Auto-detect"] + list(LANGUAGES.keys()),
        index=0,
        help="Language will be auto-detected from your message. Use this only to override."
    )
    
    st.markdown("---")
    
    # Auto-detection info
    st.markdown("### 🔍 Enhanced Auto-Detection")
    st.info("✅ Now supports Roman scripts!\n- 'kya hai' → Detected as Urdu\n- 'chai mai krub' → Detected as Thai\n- 'rhinoplasty arai' → Thai\n- Native scripts also supported")
    
    # Show recent detection
    if st.session_state.messages:
        last_user_msg = None
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "user" and "detected_language" in msg:
                last_user_msg = msg
                break
        
        if last_user_msg:
            detected_lang = last_user_msg["detected_language"]
            native_name = LANGUAGES.get(detected_lang, {}).get("native", detected_lang)
            st.success(f"Last detected: {detected_lang} ({native_name})")
    
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
    
    **Supported Languages:**
    - English, Spanish, French, German
    - Italian, Portuguese, Russian
    - Chinese, Japanese, Korean
    - Arabic, Hindi, Urdu, Turkish
    - **Thai** (new!)
    - **Roman scripts** (Urdu/Hindi/Thai/Arabic)
    
    *Please consult with medical professionals for personalized advice.*
    """)

# Main chat interface
st.title("💬 Meko Clinic Rhinoplasty Assistant")
st.markdown("**🌐 Multi-language Support with Enhanced Roman Script Detection + Thai**")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Show detected language for user messages
        if message["role"] == "user" and "detected_language" in message:
            detected_lang = message["detected_language"]
            native_name = LANGUAGES.get(detected_lang, {}).get("native", detected_lang)
            st.caption(f"🔍 Detected: {detected_lang} ({native_name})")

# Chat input with enhanced placeholder
if prompt := st.chat_input("Ask me about rhinoplasty procedures... | รายงานรายละเอียด rhinoplasty | rhinoplasty arai krub | rhinoplasty kya hai | प्रश्न पूछें | اسأل | 质问题"):
    # Detect language from user input
    if selected_language != "Auto-detect":
        detected_language = selected_language
    else:
        detected_language = detect_language(prompt)
    
    # Add user message to chat history with detected language
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        "detected_language": detected_language
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
        native_name = LANGUAGES.get(detected_language, {}).get("native", detected_language)
        st.caption(f"🔍 Detected: {detected_language} ({native_name})")
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(
                prompt, 
                detected_language, 
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
        🏥 Meko Clinic Rhinoplasty Chatbot | Powered by AIML API & OpenAI<br>
        🌐 Enhanced Auto-language Detection | Roman Script Support | 15+ Languages including Thai
    </div>
    """,
    unsafe_allow_html=True
)

# Display sample questions in multiple languages (Thai added)
if len(st.session_state.messages) == 0:
    st.markdown("### 💡 Sample Questions / นลคำถาม / نمونہ سوالات / नमूना प्रश्न / أسئلة عينة / 샘플 질문")
    
    # Create tabs for different languages (Thai added)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["English", "ไทย (Thai)", "Roman Thai", "اردو (Urdu)", "Roman Urdu", "हिंदी (Hindi)"])
    
    with tab1:
        questions = [
            "What rhinoplasty procedures do you offer?",
            "What is the recovery time for rhinoplasty?",
            "How much does rhinoplasty cost?",
            "What should I expect during consultation?"
        ]
        for i, question in enumerate(questions):
            if st.button(question, key=f"en_{i}"):
                st.session_state.messages.append({"role": "user", "content": question, "detected_language": "English"})
                st.rerun()
    
    with tab2:
        questions = [
            "คุณมีการผ่าตัดไรโนพลาสตี้แบบใดบ้าง?",
            "ระยะเวลาฟื้นฟูสำหรับไรโนพลาสตี้เป็นเวลาเท่าไร?",
            "ไรโนพลาสตี้มีค่าใช้จ่ายเท่าไร?",
            "ฉันควรคาดหวังอะไรระหว่างการปรึกษา?"
        ]
        for i, question in enumerate(questions):
            if st.button(question, key=f"th_{i}"):
                st.session_state.messages.append({"role": "user", "content": question, "detected_language": "Thai"})
                st.rerun()

    with tab3:
        questions = [
            "rhinoplasty arai krub",
            "surgery thao rai krub",
            "rhinoplasty sabai mai",
            "consultation pai nai"
        ]
        for i, question in enumerate(questions):
            if st.button(question, key=f"roman_th_{i}"):
                st.session_state.messages.append({"role": "user", "content": question, "detected_language": "Thai"})
                st.rerun()

    with tab4:
        questions = [
            "آپ کے کلینک میں رائنو پلاسٹی کے کون سے طریقے ہیں؟",
            "رائنو پلاسٹی کے بعد صحتیابی کا وقت کیا ہے؟",
            "رائنو پلاسٹی کی قیمت کتنی ہے؟",
            "مشاورت کے دوران مجھے کیا توقع رکھنی چاہیے؟"
        ]
        for i, question in enumerate(questions):
            if st.button(question, key=f"ur_{i}"):
                st.session_state.messages.append({"role": "user", "content": question, "detected_language": "Urdu"})
                st.rerun()

    with tab5:
        questions = [
            "rhinoplasty kya hai?",
            "recovery time kitna hota hai?",
            "cost kitni hoti hai?",
            "consultation me kya hota hai?"
        ]
        for i, question in enumerate(questions):
            if st.button(question, key=f"roman_ur_{i}"):
                st.session_state.messages.append({"role": "user", "content": question, "detected_language": "Urdu"})
                st.rerun()

    with tab6:
        questions = [
            "आप कौन-कौन सी राइनोप्लास्टी प्रक्रियाएँ करते हैं?",
            "राइनोप्लास्टी के लिए रिकवरी टाइम क्या होता है?",
            "राइनोप्लास्टी की कीमत कितनी है?",
            "परामर्श के दौरान क्या उम्मीद की जा सकती है?"
        ]
        for i, question in enumerate(questions):
            if st.button(question, key=f"hi_{i}"):
                st.session_state.messages.append({"role": "user", "content": question, "detected_language": "Hindi"})
                st.rerun()
    
