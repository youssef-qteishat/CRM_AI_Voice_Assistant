import os
import json
import openai
from openai import OpenAIError
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions, SpeakOptions

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DEEPGRAM_API_KEY or not OPENAI_API_KEY:
    raise ValueError("Please set the DG_API_KEY and/or OPENAI_API_KEY environment variable.")

# Initialize the clients
deepgram = DeepgramClient(DEEPGRAM_API_KEY)
openai_client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Define the system prompt for OpenAI
system_prompt = """
You are a helpful and friendly customer service assistant for an electronics warehouse.
Your goal is to help customers with issues like:
- Billing questions
- Getting updates on orders
- Explaining contents of each order (number of the items and type of items delivered)

Maintain a polite and professional tone in your responses. Always make the customer feel valued and heard.

Always spell out dates and abbriviations for states and street names. And convert UTC time to Pacific Standard Time.

Always express the cost of a given order as a dollar amount.
"""

# Set Deepgram options for TTS and STT
text_options = PrerecordedOptions(
    model="nova-2", # Use Deepgram's 'nova-2' model for speech-to-text
    language="en", # Set the language to English
    summarize="v2", # Generate a short summary of the conversation
    topics=True, # Identify the main topics discussed
    intents=True, # Detect the user's intent
    smart_format=True, # Enable smart formatting for punctuation and capitalization
    sentiment=True, # Analyze the sentiment of the speaker
)

speak_options = SpeakOptions(
    model="aura-asteria-en", # Use Deepgram's 'aura-asteria-en' model for text-to-speech
    encoding="linear16", # Set the audio encoding
    container="wav" # Set the audio container format to WAV
)


def ask_openai(prompt, order_data=None):
    """
    Send OpenAI API a prompt, returns a response back.
    Optionally includes order data to help the assistant provide informed responses.
    """
    try:
        user_prompt = prompt

        if order_data:
            formatted_data = json.dumps(order_data, indent=2)
            user_prompt = f"The following is customer order data:\n{formatted_data}\n\nCustomer says: {prompt}"

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        return f"An error occurred: {e}"


def get_transcript(payload, options=text_options):
    """
    Returns a JSON of Deepgram's transcription given an audio file.
    """
    response = deepgram.listen.rest.v("1").transcribe_file(payload, options).to_json()
    return json.loads(response)

def get_topics(transcript):
    """
    Returns back a list of all unique topics in a transcript.
    """
    topics = set()  # Initialize an empty set to store unique topics

    # Traverse through the JSON structure to access topics
    for segment in transcript['results']['topics']['segments']:
        # Iterate over each topic in the current segment
        for topic in segment['topics']:
            # Add the topic to the set
            topics.add(topic['topic'])
    return topics
def get_summary(transcript):
    """
    Returns the summary of the transcript as a string.
    """
    return transcript['results']['summary']['short']

def save_speech_summary(transcript, options=speak_options):
    """
    Writes an audio summary of the transcript to disk.
    """
    s = {"text": transcript}
    filename = "output.wav"
    response = deepgram.speak.rest.v("1").save(filename, s, options)