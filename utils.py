import os
import json
import openai
import ffmpeg
from tempfile import NamedTemporaryFile
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
You are a helpful and friendly AI assistant for a user going through the process of moving.

Each box has the following details:
- box number
- box size (small, medium, large, extra large)
- whether the box is fragile or not (true or false value)
- where the box's contents are from in the house (master bedroom, bedroom, living room, dinning room, kitchen, bathroom, garage, or attic)
- description of the contents

Your goal is to help users with the following:
- keep track of boxes and their contents
- keep track on the total number of boxes and from which area in the house they are from

Maintain a polite and professional tone in your responses. Always make the user feel valued and heard.

If you box is marked is not fargile, don't mention it in the reponse. If you are mentioning the date a box was packed make sure to spell it out. If you are mentioning the id, refer to it as the number (ex. box number 12).
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


def ask_openai(conversation_history):
    """
    Send OpenAI API a prompt, returns a response back.
    Optionally includes order data to help the assistant provide informed responses.
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=conversation_history,
            temperature=0.7
        )
        agent_reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": agent_reply})
        return agent_reply, conversation_history
    except OpenAIError as e:
        return f"An error occurred: {e}"

def convert_webm_to_wav(webm_bytes):
    with NamedTemporaryFile(suffix=".webm") as temp_in, NamedTemporaryFile(suffix=".wav", delete=False) as temp_out:
        temp_in.write(webm_bytes)
        temp_in.flush()

        ffmpeg.input(temp_in.name).output(temp_out.name).run(overwrite_output=True)
        with open(temp_out.name, "rb") as f:
            return f.read()

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