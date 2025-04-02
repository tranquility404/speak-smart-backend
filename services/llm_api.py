import os

from groq import Groq
from dataclasses import dataclass

from utils.utils import extract_json_from_llm

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

@dataclass
class VocabAnalysis:
    repeated_words: str
    meanings: str
    grammatical_errors: str
    long_sentences: str
    modified_text: str
    fancy_text: str

    def __init__(self, data):
        self.repeated_words: str = data["repeated_words"]
        self.meanings: str = data["meanings"]
        self.grammatical_errors: str = data["grammatical_errors"]
        self.long_sentences: str = data["long_sentences"]

        self.modified_text: str = data["modified_text"]
        self.fancy_text: str = data["fancy_text"]

def transcribe(file_path):
    with open(file_path, "rb") as file:
        result = client.audio.transcriptions.create(
            file=(file_path, file.read()),
            model="whisper-large-v3",
            response_format="verbose_json",
        )
    print("whisper result", result)
    return result

def get_llm_analysis(transcription):
    completion = client.chat.completions.create(
        model="qwen-2.5-32b",
        messages=[
            {
                "role": "system",
                "content": """
                            Generate No Preamble. Assume you are an excellent public speaker coach. 
                            Note:
                            - don't change language of the sentence.
                            - don't change the perspective or meaning of the sentence.
                            - each of the list will be a set (no duplicates).
                            Create a list of:
                            - "repeated_words": list of top 10 repeated words with repetition count (only include meaningful words, no helping or stop words).
                            - "grammatical_errors": list of top 5 grammatical errors with correct sentence & very short explanation (only include grammatical errors) (keep explanation very short and easy to understand).
                            - "long_sentences": list of top 5 long sentences with suggestion (suggestion will be moderately optimized length sentence with concise & appropriate words).
                            Generate text:
                            - "modified_text": by optimizing all long sentences, correct grammatical errors, remove repeated words.
                            - "fancy_text": by using fancy & sophisticated words while maintaining conciseness.
                            - "meanings": list of top 5 fancy words used in the "fancy_text" & their meanings in very short and easy to understand language.
                            Output format:
                            {
                                "repeated_words": [ { "word": "", "count": number } ],
                                "grammatical_errors": [ { "sentence": "", "correct": "",  "explanation": "" } ]
                                "long_sentences": [ { "sentence": "", "suggestion": "" } ],
                                "modified_text": "",
                                "fancy_text": "",
                                "meanings": [ { "word" : "", "meaning": "" } ]
                            }
                            For following text:
                            """
            },
            {
                "role": "user",
                "content": transcription
            },
        ],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        stream=False,
        stop=None,
    )

    # for chunk in completion:
    #     print(chunk.choices[0].delta.content or "", end="")

    output = completion.choices[0].message.content
    print("llm output: ", output)
    return output

def generate_rephrasals(speech_text):
    completion = client.chat.completions.create(
        model="qwen-2.5-32b",
        messages=[
            {
                "role": "system",
                "content": """
                            You are tasked with generating 5 different rephrasals of the provided speech text in the following styles:  
                            1) Fancy and Sophisticated Words.  
                            2) Technical Terms and Jargon.  
                            3) Humorous with Funny Metaphors.  
                            4) Concise and Appropriate Wording.  
                            5) Philosophical and Deep Thinker.  
                            No preamble, only return the JSON output.
                            Output format:
                            {
                                "fancy_and_sophisticated_words": "string",
                                "technical_terms_and_jargon": "string",
                                "humorous_with_funny_metaphors": "string",
                                "concise_and_appropriate_wording": "string",
                                "philosophical_and_deep_thinker": "string"
                            }
                            For following speech text:
                            """
            },
            {
                "role": "user",
                "content": speech_text
            },
        ],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        stream=False,
        stop=None,
    )

    # for chunk in completion:
    #     print(chunk.choices[0].delta.content or "", end="")

    output = completion.choices[0].message.content
    print("llm output: ", output)
    return output

def generate_random_topics():
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": """
                    Generate 5 random topics for a public speech. Make sure the topics cover a wide range of categories, from technology to entertainment, history to personal development, and throw in some unique and creative ideas that I wouldn't normally think of. Avoid repeating similar topics or ideas.
                    Each topic should be 4-5 words long. 
                    No preamble, only return the JSON output.
                    Output format:
                    {
                        'topics': ['Topic 1', 'Topic 2', 'Topic 3', 'Topic 4', 'Topic 5']
                    }
                    """
            },
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    output = completion.choices[0].message.content
    # print("drill output: ", output)
    return output

def generate_speech(topic):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""
                    Generate a speech of approximately 2 minutes in length on the topic: {topic}.
                    Do not include any preamble, introductions, or conclusions. 
                    Respond strictly in this JSON format:
                    {{ "speech": "Your generated speech here." }}
                    """
            },
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    output = completion.choices[0].message.content
    # print("drill output: ", output)
    return output

def generate_slow_fast_drill():
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": """
                    Generate a JSON-formatted list of 5 drill exercise texts. Each object should include:
                    - "text": A clear and structured sentence with at least 200 and at max 300 characters for effective speech practice.
                    - "type": "fast" or "slow", based on the expected speech rate.
                    - "expected_speech_rate": A range in words per minute (WPM), categorized as follows:
                     - "slow": 100-129 WPM
                     - "fast": 176-220 WPM
                    Ensure an even mix of all types and text associated with type should be of kind which is supposed to be spoken that way(slow or fast). No preamble, only return the JSON output.
                    Output format:
                    {
                        "drill_exercises": [
                            {
                                "text": "",
                                "type": "",
                                "expected_speech_rate": [min, max]
                            },
                            ...
                        ]
                    }
                    """
            },
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    output = completion.choices[0].message.content
    # print("drill output: ", output)
    return output

def generate_mock_interview():
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant that generates mock interview questions in JSON format. The questions should be broad, open-ended, and suitable for general job interviews. Ensure the questions cover various categories such as Personal & Behavioral, Communication, Problem-Solving, Time Management, and Company-Specific. Avoid technical or job-specific questions. Keep the tone professional yet approachable. Your response must be a valid JSON object with no additional text, explanations, or preamble."
            },
            {
                "role": "user",
                "content": "Generate a JSON-formatted mock interview with 5 questions. Each question should include:\n- A \"category\" (e.g., Personal & Behavioral, Communication & Teamwork, etc.)\n- A \"question\" that is broad and open-ended.\n- \"advice\" that provides guidance on how to approach answering the question effectively.\n\nThe JSON format should be:\n\n{\n  \"mock_interview\": [\n    {\n      \"category\": \"Category Name\",\n      \"question\": \"Interview question text\",\n      \"advice\": \"Advice on how to answer the question effectively.\"\n    },\n    ...\n  ]\n}\n\nOnly return the JSON output. Do not include any preamble, explanations, or additional text."
            },
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    output = completion.choices[0].message
    return output

if __name__ == "__main__":
    output = extract_json_from_llm(generate_slow_fast_drill())

    print(output["drill_exercises"])
