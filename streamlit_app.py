import streamlit as st
import os
from PyPDF2 import PdfReader
from groq import Groq

# --- UI Config ---
st.set_page_config(page_title="Ravindu Sir AI", page_icon="🎓", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    [data-testid="stChatMessage"]:nth-child(even) { background-color: #1e293b; border: 1px solid #334155; }
    </style>
""", unsafe_allow_html=True)

# --- Groq API Setup ---
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("අඩෝ... Groq API Key එක සෙට් කරලා නෑ මල්ලි! (Secrets වල GROQ_API_KEY දාපන්)")
    st.stop()

# --- PDF Knowledge (RAG) ---
@st.cache_resource
def get_pdf_knowledge():
    combined_text = ""
    pdf_folder = "pdfs"
    if os.path.exists(pdf_folder):
        files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
        for file in files:
            try:
                reader = PdfReader(os.path.join(pdf_folder, file))
                for page in reader.pages:
                    content = page.extract_text()
                    if content: combined_text += content + "\n"
            except Exception: continue
    return combined_text

# මුල් අකුරු 10,000 ට විතරක් සීමා කරනවා
knowledge_base = get_pdf_knowledge()[:10000]

# --- Persona ---
persona = f"""
නම: රවිඳු බණ්ඩාරනායක. ලංකාවේ විශාලතම ICT පන්තියේ හිමිකරු.
දැනුම: {knowledge_base}

ඔබේ පෞරුෂය:
- ඉතා සැරෙන්, අහංකාර ලෙස පිළිතුරු දෙන්න.
- සිංග්ලිෂ් (Singlish) සහ සිංහල මිශ්‍ර කරන්න.
- "ස් ස් ස් මෙහේ බලපං මන් දිහා....", "අත් උස්සපන් පයින් ගහන්නේ තොපිට", "අනික් උන් මෝඩයොද?" වැනි වචන භාවිතා කරන්න.
"""

# --- Chat Logic ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("<h2 style='text-align: center; color: #3b82f6;'>රවිඳු සර් AI (Groq Speed) 🎓</h2>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("මොකක්ද තොපිට තියෙන ප්‍රශ්නේ?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Groq Llama 3 70B මොඩල් එක පාවිච්චි කිරීම (මෙය සිංහලට පට්ට)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": persona},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
            )
            
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:

            st.error(f"Error එකක් ආවා මල්ලි: {str(e)}")
