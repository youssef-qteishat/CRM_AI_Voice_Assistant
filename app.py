from flask import Flask, request, jsonify
from flask_cors import CORS
import utils
import json
import subprocess
from deepgram import FileSource


app = Flask(__name__)
CORS(app)

with open("box_data.json") as f:
    box_data = json.load(f)

conversation_history = [
    {"role": "system", "content": utils.system_prompt}
]

@app.route("/agent-audio", methods=["GET"])
def get_agent_audio():
    return send_file("output.wav", mimetype="audio/wav")

@app.route("/process-audio", methods=["POST"])
def process_audio():
    print("processing recorded audio")
    try:
        file = request.files["audio"]
        webm_data = file.read()

        # Convert webm to wav
        wav_data = utils.convert_webm_to_wav(webm_data)

        # Build Deepgram payload with correct format
        payload: FileSource = {
            "buffer": wav_data,
            "mimetype": "audio/wav"
        }

        customer_inquiry = utils.get_transcript(payload)
        transcribed_text = customer_inquiry["results"]["channels"][0]["alternatives"][0]["transcript"]

        user_msg = f"The following is moving box data:\n{json.dumps(box_data, indent=2)}\n\nThe user asks: {transcribed_text}"
        conversation_history.append({"role": "user", "content": user_msg})

        agent_answer, updated_history = utils.ask_openai(conversation_history)
        conversation_history[:] = updated_history
        utils.save_speech_summary(agent_answer)

        subprocess.run(["afplay", "output.wav"])

        return jsonify({
            "transcription": transcribed_text,
            "agent_response": agent_answer,
            "summary": utils.get_summary(customer_inquiry),
            "topics": list(utils.get_topics(customer_inquiry))
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
