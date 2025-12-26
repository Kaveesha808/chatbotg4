import streamlit as st
import os
from PyPDF2 import PdfReader
from groq import Groq

# --- 1. පේජ් එකේ සැකසුම් (UI Config) ---
st.set_page_config(page_title="Ravindu Sir AI", page_icon="🎓", layout="centered")

# Custom CSS - පට්ට Dark ලස්සන UI එකක් සඳහා
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stChatInput { border-radius: 25px; }
    /* රවිඳු සර්ගේ මැසේජ් එකේ පාට */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1e293b;
        border: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. API Key එක ලබා ගැනීම (Streamlit Secrets වලින්) ---
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("අඩෝ... API Key එක සෙට් කරලා නෑ මල්ලි! (Secrets බලපන්)")
    st.stop()

# --- 3. PDF දැනුම කියවීම (RAG Optimization) ---
@st.cache_resource  # සර්වර් එක පටන් ගන්නකොට එක පාරක් විතරක් කියවන්න
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
                    if content:
                        combined_text += content + "\n"
            except Exception as e:
                print(f"Error reading {file}: {e}")
    return combined_text

knowledge_base = get_pdf_knowledge()

# --- 4. පර්සෝනා එක සැකසීම (Ravindu Sir Persona) ---
persona = f"""
නම: රවිඳු බණ්ඩාරනායක. ලංකාවේ විශාලතම ICT පන්තියේ හිමිකරු.
දැනුම (PDF): {knowledge_base}
විශේෂ කරුණු: PDFs වල තියෙන දේවල් copy කරලා දාන්න එපා ඒවා කියවන්න බෑ, ඒවා ලියලා තියෙන්නෙ unicode වලින්, දානවානම් ඒ unicodes සිංහලට පරිවර්තනය කරලා දාන්න.

නීති: 
1. පිළිතුරු දිය යුත්තේ රවිඳු බණ්ඩාරනායක සර්ගේ ස්වරූපයෙනි.
2. සිංග්ලිෂ් (Singlish) සහ සිංහල මිශ්‍ර කර භාවිතා කරන්න.
3. ඉතා සැරෙන්, අහංකාර ලෙස සහ මෝඩයන්ට බණින ලෙස පිළිතුරු දෙන්න.
4. "ස් ස් ස් මෙහේ බලපං මන් දිහා....", "අත් උස්සපන් පයින් ගහන්නේ තොපිට", "AL කරන්න එපා දෑතේ රස්සාවක් හොයාගනිල්ල දැන්මම", "මේවා අපි පුරුදු වෙන්න කරන වැඩ නෙවෙයිනෙ", "මේවා උබලා කපලා තැන් තැන් වල දාන්න එහෙනම් එපා", "අනික් උන් මෝඩයොද?", "බලපන් ඉතින් මං කියන දේ තේරෙන්නේ නැත්තම් ලොවෙත් තේරෙන්නේ නෑ", "ළමයි මේ බලන්න", "ඔයාලට මාව හාවෙක් වගේ පේනවද?", "අපේ කොන්ඩෙ අවුල් හරිද, ඒත් අපේ ඔලුව clear." වැනි වචන භාවිතා කරන්න.
"""

# --- 5. චැට් එක පාලනය කිරීම ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header එක
st.markdown("<h2 style='text-align: center; color: #3b82f6;'>රවිඳු සර් AI 🎓</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 12px; color: #888;'>ලංකාවේ විශාලතම ICT පන්තිය</p>", unsafe_allow_html=True)

# කලින් කරපු චැට් පෙන්වීම
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User ප්‍රශ්නය ඇසීම
if prompt := st.chat_input("මොකක්ද තොපිට තියෙන ප්‍රශ්නේ?"):
    # User message එක සේව් කිරීම
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Bot (Ravindu Sir) පිළිතුර ලබා ගැනීම
    with st.chat_message("assistant"):
        try:
            # Groq model එක භාවිතා කිරීම (Llama 3.3 70B - Sinhala වලට පට්ට)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": persona},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
            )
            
            # පිළිතුර Stream විදියට ලබා ගැනීම
            full_response = ""
            message_placeholder = st.empty()
            
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error එකක් ආවා මල්ලි: {str(e)}")

# Sidebar එකේ දැනුම ගැන විස්තර (Optional)
with st.sidebar:
    st.title("උබලා මගෙං කලින් අහපු දේවල්.")
    if knowledge_base:
        st.success("PDF දැනුම ඇතුළත් කර ඇත.")
    else:
        st.warning("PDFs කිසිවක් හමු නොවීය.")
    if st.button("කක්කා දාල හේදුවා වගේ චැට් එක මකන්න"):
        st.session_state.messages = []
        st.rerun()
