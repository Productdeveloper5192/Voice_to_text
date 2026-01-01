import streamlit as st
import speech_recognition as sr
from googletrans import Translator


def main():
    st.set_page_config(page_title="Multilingual Voice to Text", page_icon="🎙️")
    
    st.title("🎙️ Multilingual Voice to Text")
    st.write("Speak in your native language, and I will transcribe and translate it to English.")

    # Initialize session state for the note if not exists
    if 'voice_note' not in st.session_state:
        st.session_state['voice_note'] = ""
    if 'last_result' not in st.session_state:
        st.session_state['last_result'] = None

    # Initialize recognizer
    r = sr.Recognizer()
    translator = Translator()

    # Language selection
    languages = {
        "English": "en-US",
        "Hindi (हिंदी)": "hi-IN",
        "Telugu (తెలుగు)": "te-IN",
        "Tamil (தமிழ்)": "ta-IN",
        "Kannada (ಕನ್ನಡ)": "kn-IN",
        "Malayalam (മലയാളം)": "ml-IN",
        "Marathi (मराठी)": "mr-IN",
        "Gujarati (ગુજરાતી)": "gu-IN",
        "Bengali (বাংলা)": "bn-IN",
        "Spanish": "es-ES",
        "French": "fr-FR",
        "German": "de-DE",
        "Japanese": "ja-JP"
    }
    
    # Sidebar for Settings
    with st.sidebar:
        st.header("⚙️ Audio Settings")
        
        # Microphone selection
        try:
            mic_list = sr.Microphone.list_microphone_names()
            # Filter out duplicates and keep indices
            unique_mics = {}
            for i, name in enumerate(mic_list):
                if name not in unique_mics:
                    unique_mics[name] = i
            
            # Default to first one or a known good one if possible
            mic_options = list(unique_mics.keys())
            selected_mic_name = st.selectbox(
                "Select Microphone", 
                mic_options, 
                index=0 if mic_options else None
            )
            selected_mic_index = unique_mics[selected_mic_name] if selected_mic_name else None
        except:
             st.error("Could not list microphones.")
             selected_mic_index = None

        st.caption("Adjust these if recognition is poor:")
        energy_threshold = st.slider("Background Noise Level", 0, 1000, 300, help="Higher = less sensitive to noise. Lower = more sensitive.")
        pause_threshold = st.slider("Pause Threshold", 0.5, 3.0, 0.8, help="Seconds of silence to consider the phrase complete.")
        dynamic_energy = st.checkbox("Auto-Adjust for Noise", value=True)

        with st.expander("🛠️ Diagnostics (Debug)"):
            st.write("Session State:", st.session_state)
            if 'last_error' in st.session_state:
                st.error(f"Last Error: {st.session_state['last_error']}")


    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("💡 Tip: If recognition fails, try selecting a specific microphone in the sidebar or adjusting the noise level.")
        
        selected_lang_name = st.selectbox("Speaking Language:", list(languages.keys()))
        selected_lang_code = languages[selected_lang_name]
        
        # Display the LAST success result here, so it persists even if the button isn't clicked this run
        if st.session_state['last_result']:
            res = st.session_state['last_result']
            st.markdown("### Last Capture:")
            st.success(f"**Original:** {res['original']}")
            if res['translated']:
                st.info(f"**Translated:** {res['translated']}")

        if st.button("🎙️ Start Recording", type="primary"):
            message_placeholder = st.empty()
            
            with message_placeholder.container():
                st.info(f"Listening in {selected_lang_name}... Speak now.")
                
            try:
                # Use the selected microphone
                with sr.Microphone(device_index=selected_mic_index) as source:
                    # Apply settings
                    r.energy_threshold = energy_threshold
                    r.pause_threshold = pause_threshold
                    r.dynamic_energy_threshold = dynamic_energy
                    
                    if dynamic_energy:
                         with st.spinner("Calibrating background noise... (Don't speak yet)"):
                             r.adjust_for_ambient_noise(source, duration=1)
                         
                         # Warning for high noise levels
                         if r.energy_threshold > 1000:
                             st.warning(f"⚠️ Very noisy environment (Level {r.energy_threshold:.0f}). Uncheck 'Auto-Adjust'.")
                         else:
                             # Lower sensitivity slightly to catch quieter speech
                             r.energy_threshold *= 0.8
                             st.caption(f"Sensitivity set to {r.energy_threshold:.0f}")
                    
                    # VISUAL CUE - Critical for timing
                    message_placeholder.warning("🔴 SPEAK NOW! (Listening...)")
                    
                    # Listen
                    audio = r.listen(source, timeout=10, phrase_time_limit=15)
                    
                message_placeholder.info("Processing...")
                
                # Playback
                wav_data = audio.get_wav_data()
                st.audio(wav_data, format="audio/wav")
                
                # Check for empty/short audio (approx bytes check, 1 sec mono 16khz ~ 32k bytes)
                if len(wav_data) < 32000:
                     st.warning("⚠️ Audio was very short. Did you speak *after* seeing the red 'SPEAK NOW'?")
                
                # Recognize speech
                try:
                    original_text = r.recognize_google(audio, language=selected_lang_code)
                    
                    # Translate if not English
                    translated_text = None
                    if selected_lang_code != "en-US":
                        translated = translator.translate(original_text, dest='en')
                        translated_text = translated.text
                        final_text = translated_text
                    else:
                        final_text = original_text
                    
                    # Store in session state so it persists
                    st.session_state['last_result'] = {
                        "original": original_text, 
                        "translated": translated_text
                    }
                    
                    # Append to note
                    st.session_state['voice_note'] += final_text + " "
                    
                    # Force sync
                    if 'note_area' in st.session_state:
                         st.session_state['note_area'] = st.session_state['voice_note']
                         
                    message_placeholder.success("Added to note!")
                    st.rerun() # Force immediate update to show the persistent result above
                    
                except sr.UnknownValueError:
                    st.error("❌ Audio capture failed.")
                    
                    tips = [
                        "**Silence:** The microphone didn't pick up your voice. Did you hear yourself in the playback above?",
                        "**Noise:** Background noise drowned out your voice."
                    ]
                    
                    if r.energy_threshold > 500:
                         tips.append(f"**Sensitivity Issue:** Your noise level is very high ({r.energy_threshold:.0f}). **Uncheck 'Auto-Adjust'** and lower the slider to **300**.")
                    else:
                         tips.append("**Settings:** Try lowering the 'Background Noise Level' slider further.")
                         
                    st.warning("**Why this happens:**\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(tips)]))
                except sr.RequestError as e:
                    st.error(f"❌ Connection error to Google Service. Check your internet: {e}")
                    
            except sr.WaitTimeoutError:
                st.warning("Listening timed out. No speech detected. Try asking louder or checking your mic.")
            except Exception as e:
                st.session_state['last_error'] = str(e)
                st.error(f"Error: {e}")

        if st.button("🗑️ Clear Note"):
            st.session_state['voice_note'] = ""
            st.rerun()

    with col2:
        st.markdown("### 📝 Your Notes")
        # Text area to edit/view the accumulated text
        note_content = st.text_area(
            "Captured Text (English)", 
            value=st.session_state['voice_note'], 
            height=400,
            key="note_area",
            on_change=lambda: st.session_state.update({'voice_note': st.session_state.note_area})
        )
        
        st.download_button(
            label="💾 Download Note",
            data=note_content,
            file_name="voice_note.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
