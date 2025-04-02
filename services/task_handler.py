from dto.analysis_report import AnalysisReport
from services.analyze_speech import AnalyzeSpeech

def load_audio(file_path: str, analyze_speech: AnalyzeSpeech):
    analyze_speech.load_audio(file_path=file_path)

def get_transcription(file_path: str, analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    analyze_report.transcription.data = analyze_speech.get_transcription(file_path=file_path)
    analyze_report.transcription.status = "Loaded✅"

def get_speech_rate(analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    analyze_report.speech_rate.data = analyze_speech.get_speech_rate().get_dto()
    analyze_report.speech_rate.status = "Loaded✅"

def get_intonation(analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    data = analyze_speech.get_intonation()
    if data != 0:
        analyze_report.intonation.data = data.get_dto()
        analyze_report.intonation.status = "Loaded✅"
    else:
        analyze_report.intonation.data = "Not Enough Data"
        analyze_report.intonation.status = "Not Enough Data"

def get_energy(analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    analyze_report.energy.data = analyze_speech.get_energy().get_dto()
    analyze_report.energy.status = "Loaded✅"

def get_confidence(analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    analyze_report.confidence.data = analyze_speech.get_pauses().get_dto()
    analyze_report.confidence.status = "Loaded✅"

def get_conversation_score(analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    analyze_report.conversation_score.data = analyze_speech.get_conversation_score()
    analyze_report.conversation_score.status = "Loaded✅"

def get_vocal_analysis(analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    analyze_report.vocab_analysis.data = analyze_speech.get_vocab_analysis()
    analyze_report.vocab_analysis.status = "Loaded✅"

def get_speech_rate_fig(analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    analyze_report.speech_rate_fig.data = analyze_speech.speech_rate.get_graph()
    analyze_report.speech_rate_fig.status = "Loaded✅"

def get_intonation_fig(analyze_speech: AnalyzeSpeech, analyze_report: AnalysisReport):
    if analyze_speech.intonation:
        analyze_report.intonation_fig.data = analyze_speech.intonation.get_graph()
        analyze_report.intonation_fig.status = "Loaded✅"
    else:
        analyze_report.intonation_fig.data = "Not Enough Data"
        analyze_report.intonation_fig.status = "Not Enough Data"

