import React, { useState, useRef } from 'react';
import { Mic, StopCircle } from 'lucide-react';

const Recorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [agentResponse, setAgentResponse] = useState('');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleToggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');

          try {
            const res = await fetch('http://localhost:5000/process-audio', {
              method: 'POST',
              body: formData,
            });

            const data = await res.json();
            if (res.ok) {
              setAgentResponse(data.agent_response);
            } else {
              console.error('Backend error:', data.error);
              setAgentResponse(`Error: ${data.error}`);
            }
          } catch (err) {
            console.error('Request failed:', err);
            setAgentResponse('Failed to reach the server.');
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error('Error starting recording:', err);
        alert('Could not access microphone. Make sure permissions are granted.');
      }
    }
  };

  return (
    <div className="flex items-center justify-center mb-100">
      <div
        className="flex flex-col items-center w-full max-w-xl space-y-4 shadow-xl rounded-2xl"
        style={{ backgroundColor: '#c6a380', padding: '10px'}}
      >
        {/* <h1 className="text-2xl font-bold text-center text-gray-800">🎙️ AI Voice Assistant</h1> */}
        <h1 className="text-2xl font-bold text-center text-gray-800" style={{ marginTop: 0 }}>
          AI Voice Assistant
        </h1>
  
        <textarea
          value={agentResponse}
          readOnly
          className="w-full p-4 border border-gray-300 rounded-xl text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
          style={{ backgroundColor: '#feff9c' }}
          rows="6"
          placeholder="Agent response will appear here..."
        />
  
        <button
          onClick={handleToggleRecording}
          className={`w-full flex items-center justify-center gap-3 py-3 text-lg rounded-full font-semibold transition-colors focus:outline-none focus:ring-0 ${
            isRecording
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {isRecording ? <StopCircle className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
          {isRecording ? 'Stop' : 'Start'}
        </button>
      </div>
    </div>
  );
};

export default Recorder;
