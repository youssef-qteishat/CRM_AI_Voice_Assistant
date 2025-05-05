from flask import Flask, request, jsonify
from flask_cors import CORS
import utils
import json
from deepgram import FileSource


app = Flask(__name__)
CORS(app)

with open("order_data.json") as f:
    order_data = json.load(f)

@app.route("/process-audio", methods=["POST"])
def process_audio():
    try:
        file = request.files["audio"]
        buffer_data = file.read()

        payload: FileSource = {"buffer": buffer_data}
        customer_inquiry = utils.get_transcript(payload)
        transcribed_text = customer_inquiry["results"]["channels"][0]["alternatives"][0]["transcript"]
        agent_answer = utils.ask_openai(transcribed_text, order_data=order_data)

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
