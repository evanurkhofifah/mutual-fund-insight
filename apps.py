import os
import fitz
import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Bikin judul
st.title("Mutual Fund Fact Sheet Analyzer")

# Cek apakah API key sudah ada
if "GOOGLE_API_KEY" not in os.environ:
    # Jika belum, minta user buat masukin API key
    google_api_key = st.text_input("Google API Key", type="password")
    # User harus klik Start untuk save API key
    start_button = st.button("Start")
    if start_button:
        os.environ["GOOGLE_API_KEY"] = google_api_key
        st.rerun()
    # Jangan tampilkan chat dulu kalau belum pencet start
    st.stop()

# Status eksekusi analisis
if "analysis_started" not in st.session_state:
    st.session_state["analysis_started"] = False

# Input profil risiko user
if "user_risk_profile" not in st.session_state:
    st.session_state["user_risk_profile"] = None

# Input profil risiko dan upload file hanya tampil jika analisis belum dimulai
if not st.session_state["analysis_started"]:
    # Pilih profil risiko
    risk_profile = st.selectbox(
        "Select your risk profile:",
        ["Conservative", "Moderate", "Aggressive"]
    )
    # Simpan pilihan user ke session state
    st.session_state["user_risk_profile"] = risk_profile

    # Upload file
    uploaded_pdf = st.file_uploader("Upload Fund Fact Sheet (PDF)", type="pdf")
    if uploaded_pdf:
        # Jika ada fund fact sheet yang diupload, load PDF-nya
        pdf_bytes = uploaded_pdf.read()
        # Buka PDF dengan fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        # Extract text dari PDF
        text = "\n".join([page.get_text() for page in doc])
        # Simpan text PDF ke session state
        st.session_state["fund_fact_sheet"] = text

    # Tombol untuk memulai chat
    start_analysis = st.button("Start Chat")
    if start_analysis:
        # Cek apakah user sudah upload file dan pilih profil resiko
        if "fund_fact_sheet" in st.session_state and st.session_state["user_risk_profile"]:
            st.session_state["analysis_started"] = True # Tandai chat/analisis sudah dimulai
            st.stop()  # reload UI agar input hilang dan chat muncul
        else:
            st.warning("Please upload a PDF and select your risk profile first.") # warning jika belum lengkap


# Jika analisis sudah dimulai, tampilkan chat
if st.session_state["analysis_started"]:
    # Ambil data dari session state
    report = st.session_state["fund_fact_sheet"]
    risk_profile = st.session_state["user_risk_profile"]

    # Inisiasi client LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.1
    )

    # Cek apakah data sebelumnya tentang message history sudah ada
    if "messages_history" not in st.session_state:
        # Jika belum, bikin datanya, isinya hanya system message dulu, dengan fund fact sheet dan profil resiko sebagai context
        st.session_state["messages_history"] = [
            SystemMessage(
                f"You are a mutual fund fact sheet analyst. Analyze the uploaded fund fact sheet and extract key information. "
                f"Also consider the user's risk profile ({risk_profile}) for educational guidance (do not give investment advice). "
                f"Fact Sheet Context:\n{report}"
            )
        ]
    # Jika messages_history sudah ada, tinggal di load aja
    messages_history = st.session_state["messages_history"]

    # Tampilkan messages history selama ini
    for message in messages_history:
        # Tidak perlu tampilkan system message
        if type(message) is SystemMessage:
            continue
        # Pilih role, apakah user/AI
        role = "User" if type(message) is HumanMessage else "AI"
        # Tampikan chatnya!
        with st.chat_message(role):
            st.markdown(message.content)

    # Input pertanyaan user
    prompt = st.chat_input("Ask something about the fund fact sheet")
    if prompt:
        # Jika user ada prompt, tampilkan promptnya langsung
        with st.chat_message("User"):
            st.markdown(prompt)
        # Masukin prompt ke message history, dan kirim ke LLM
        messages_history.append(HumanMessage(prompt))
        response = llm.invoke(messages_history)

        # Simpan jawaban LLKM ke message history
        messages_history.append(response)
        # Tampilkan langsung jawaban LLM
        with st.chat_message("AI"):
            st.markdown(response.content)
