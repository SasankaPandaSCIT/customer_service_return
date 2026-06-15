import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './index.css';

function App() {
  const [messages, setMessages] = useState([
    { role: 'agent', content: 'Hello! I am the Loopp AI Support Agent. How can I assist you with your refund today?' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [agentStream, setAgentStream] = useState('');
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);
  const ws = useRef(null);
  const recognitionRef = useRef(null);
  const agentStreamRef = useRef("");

  const playTTS = (text) => {
    try {
      const audioUrl = `http://localhost:8000/api/tts?text=${encodeURIComponent(text)}`;
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (err) {
      console.error("Failed to play TTS audio:", err);
    }
  };

  useEffect(() => {
    // Connect to WebSocket using the environment variable
    const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
    ws.current = new WebSocket(`${wsUrl}/ws/chat`);

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'stream') {
        setIsTyping(false);
        agentStreamRef.current += data.content;
        setAgentStream(agentStreamRef.current);
      } else if (data.type === 'clear_stream') {
        agentStreamRef.current = "";
        setAgentStream("");
      } else if (data.type === 'log') {
        console.log("Agent Log:", data.content);
      } else if (data.type === 'end') {
        console.log("END EVENT RECEIVED. agentStreamRef.current =", agentStreamRef.current);
        setIsTyping(false);
        if (agentStreamRef.current) {
            const finalContent = agentStreamRef.current;
            setMessages(prev => {
                const newMessages = [...prev, { role: 'agent', content: finalContent }];
                return newMessages;
            });
            agentStreamRef.current = "";
            setAgentStream("");
            
            // Trigger Voice Output
            playTTS(finalContent);
        }
      }
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket Error:", error);
    };

    ws.current.onclose = () => {
      console.log("WebSocket Connection Closed");
      setIsTyping(false);
      if (agentStreamRef.current) {
        const finalContent = agentStreamRef.current;
        setMessages(prev => [...prev, { role: 'agent', content: finalContent }]);
        agentStreamRef.current = "";
        setAgentStream("");
        playTTS(finalContent);
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const toggleListen = (e) => {
    e.preventDefault();
    
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input is not supported in your browser.");
      return;
    }

    // Always create a fresh instance to avoid stale state bugs in Chrome
    const recognition = new SpeechRecognition();
    recognition.continuous = false; // continuous=true is notoriously buggy in some Windows Chrome versions
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    const initialInput = input;

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';
      
      for (let i = 0; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      
      const fullTranscript = (finalTranscript + interimTranscript).trim();
      if (fullTranscript) {
        setInput(initialInput ? `${initialInput} ${fullTranscript}` : fullTranscript);
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    
    try {
      recognition.start();
      setIsListening(true);
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
      setIsListening(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, agentStream]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim() || !ws.current) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);
    
    ws.current.send(JSON.stringify({ text: input }));
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="brand">Loopp</div>
        <div>
          <span className="badge">AI Support Studio</span>
        </div>
      </div>
      
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-bubble">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
            </div>
            <div className="message-time">Just now</div>
          </div>
        ))}
        
        {/* Render the current stream */}
        {agentStream && (
          <div className="message agent">
            <div className="message-bubble">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{agentStream}</ReactMarkdown>
            </div>
            <div className="message-time">Typing...</div>
          </div>
        )}

        {isTyping && !agentStream && (
          <div className="message agent">
            <div className="message-bubble">
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-container" onSubmit={handleSend}>
        <button 
          type="button" 
          className={`chat-mic-btn ${isListening ? 'recording' : ''}`}
          onClick={toggleListen}
          title={isListening ? "Stop listening" : "Start voice input"}
        >
          🎤
        </button>
        <input 
          type="text" 
          className="chat-input"
          placeholder="Type your message here..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="chat-send-btn" disabled={!input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;
