import utils
import subprocess
import json
from deepgram import FileSource


###################
# DEMO: used for debugging before integrating python script with UI
###################

with open("order_data.json") as f:
    order_data = json.load(f)

AUDIO_FILE = "/Users/youssefqteishat/Documents/CRM_AI_Voice_Assistant/sample.mp3"

def main():
    try:
        # STEP 1: Ingest the audio file
        with open(AUDIO_FILE, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # STEP 2: Get the transcript of the voice file
        customer_inquiry = utils.get_transcript(payload)

        # STEP 3: Send this information to OpenAI to respond.
        # Extract the transcribed text from the Deepgram response
        transcribed_text = customer_inquiry["results"]["channels"][0]["alternatives"][0]["transcript"]
        agent_answer = utils.ask_openai(transcribed_text, order_data=order_data)

        # STEP 4: Print responses that can be used for integration with an app or stored in a customer database for analytics
        print('Topics:', utils.get_topics(customer_inquiry))
        print('Summary:', utils.get_summary(customer_inquiry))

        # STEP 5: Take the OpenAI response and write this out as an audio file
        print("Agent Answer:", agent_answer)
        utils.save_speech_summary(agent_answer)

        #play output
        subprocess.run(["afplay", "output.wav"])

    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    main()