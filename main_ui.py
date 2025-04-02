import os
import tempfile

import streamlit as st
from groq import Groq

from services.analyze_speech import AnalyzeSpeech

# @st.cache_resource
# def load_model():
#     torch.set_default_device("cuda")
#     return whisper.load_model("small")
#
# model = load_model()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
# print(next(model.parameters()).device)

st.header("SpeakSmart")
st.subheader("AI-Powered Communication Coach")

choice = st.selectbox("", options=("Upload Audio", "Record Audio"))

if choice:
    print(choice)
    audio_bytes = None
    if choice == "Record Audio":
        audio_bytes = st.audio_input("Say Something")
    else:
        audio_bytes = st.file_uploader("Upload Audio", type=["mp3", "wav", "flac", "aac", "ogg", "m4a", "wma"], accept_multiple_files=False)

    if audio_bytes:

        with tempfile.NamedTemporaryFile(delete=False, suffix=audio_bytes.name) as temp_file:
            temp_file.write(audio_bytes.read())
            temp_file.flush()
            temp_file_path = temp_file.name

        print(temp_file_path)
        print(os.path.exists(temp_file_path))

        # result = model.transcribe(
        #     temp_file_path,
        #     # word_timestamps=True,
        #     fp16=True
        # )

        analyze_speech = AnalyzeSpeech()

        st.divider()
        st.title("Analysis Report:")
        st.subheader("Speech:-")
        st.audio(audio_bytes)

        st.text(analyze_speech.get_transcription(temp_file_path))

        analyze_speech.load_audio(temp_file_path)
        st.markdown(f"**Duration:** {analyze_speech.duration:.2f} sec")

        st.markdown("#### Speech rate:")
        analyze_speech.get_speech_rate()
        st.markdown(f"**Avg:** {analyze_speech.speech_rate.avg_speech_rate:.2f} wpm")
        st.markdown(f"**Score:** {analyze_speech.speech_rate.percent:.0f} % ({analyze_speech.speech_rate.category})")
        st.markdown(f"**Suggestion:** {analyze_speech.speech_rate.remark}")
        st.pyplot(analyze_speech.speech_rate.get_graph())

        st.markdown("#### Intonation:")
        analyze_speech.get_intonation()
        st.markdown(f"**Avg:** {analyze_speech.intonation.mean_pitch:.2f} Hz")
        st.markdown(f"**Score:** {analyze_speech.intonation.percent:.0f} % ({analyze_speech.intonation.category})")
        st.markdown(f"**Suggestion:** {analyze_speech.intonation.remark}")
        st.pyplot(analyze_speech.intonation.get_graph())

        st.markdown("#### Energy:")
        analyze_speech.get_energy()
        st.markdown(f"**Avg:** {analyze_speech.energy.avg_energy:.5f}")
        st.markdown(f"**Score:** {analyze_speech.energy.percent:.0f} % ({analyze_speech.energy.category})")
        st.markdown(f"**Suggestion:** {analyze_speech.energy.remark}")

        st.markdown("#### Confidence:")
        st.markdown(f"**Score:** {analyze_speech.get_pauses().percent:.0f} % ({analyze_speech.pauses.category})")
        st.markdown(f"**Suggestion:** {analyze_speech.pauses.remark}")

        st.markdown("## Conversation score:")
        st.text(f"{analyze_speech.get_conversation_score():.0f} %")

        st.subheader("LLM output:")

        analyze_speech.get_vocab_analysis()

        st.markdown("#### Repeated Words:")
        if len(analyze_speech.vocab_analysis.repeated_words) == 0:
            st.text("None")
        else:
            for i in analyze_speech.vocab_analysis.repeated_words:
                st.write(f"- {i['word']} \t {i['count']}x")

        st.markdown("#### Grammatical Errors:")
        if len(analyze_speech.vocab_analysis.grammatical_errors) == 0:
            st.text("None")
        else:
            for i in analyze_speech.vocab_analysis.grammatical_errors:
                st.write(f"- {i['sentence']}\n**Correct:** {i['correct']}\n**Explanation:** {i['explanation']}")

        st.markdown("#### Long Sentences:")
        if len(analyze_speech.vocab_analysis.long_sentences) == 0:
            st.text("None")
        else:
            for i in analyze_speech.vocab_analysis.long_sentences:
                st.write(f"- {i['sentence']}\n**Suggestion:** {i['suggestion']}")

        st.subheader("Optimized Speech")
        st.text(analyze_speech.vocab_analysis.modified_text)

        st.subheader("My favorite")
        st.text(analyze_speech.vocab_analysis.fancy_text)

        st.markdown("#### Word Meanings:")
        if len(analyze_speech.vocab_analysis.meanings) == 0:
            st.text("None")
        else:
            for i in analyze_speech.vocab_analysis.meanings:
                st.write(f"- **{i['word']}:** {i['meaning']}")

        os.unlink(temp_file_path)





