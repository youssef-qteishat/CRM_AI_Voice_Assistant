import React, { useState, useRef } from 'react';

const Recorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleToggleRecording = async () => {
    if (isRecording) {
      // Stop recording
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      // Start recording
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = event => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.wav');

        const res = await fetch('http://localhost:5000/transcribe', {
          method: 'POST',
          body: formData,
        });

        const data = await res.json();
        setTranscript(data.transcript);
      };

      mediaRecorder.start();
      setIsRecording(true);
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto">
      <button
        onClick={handleToggleRecording}
        className={`w-full py-3 rounded-lg text-white font-bold ${
          isRecording ? 'bg-red-500' : 'bg-blue-500'
        }`}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>

      <textarea
        value={transcript}
        readOnly
        className="w-full mt-4 p-3 border rounded-lg"
        rows="5"
        placeholder="Transcribed text will appear here..."
      />
    </div>
  );
};

export default Recorder;
