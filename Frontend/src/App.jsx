import { useState, useRef, useEffect } from 'react';
import './App.css';

const API_URL = '/orchestrator/ask';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: '¡Hola! Soy tu asistente GraphRAG. ¿Qué deseas consultar hoy?'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input.trim();
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: userQuery
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: userQuery,
          limit: 5 // Límite predeterminado
        })
      });

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const data = await response.json();
      
      // Mapea la propiedad según lo que retorne tu pydantic QuestionResponse (ej: data.answer o data.response)
      const botText = typeof data === 'string' 
        ? data 
        : (data.answer || data.response || data.result || JSON.stringify(data, null, 2));

      const botMessage = {
        id: Date.now() + 1,
        sender: 'bot',
        text: botText
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: ` Error de conexión: ${err.message || 'No se pudo obtener respuesta del servidor.'}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Encabezado */}
      <header className="chat-header">
        <div className="logo-container">
          <div className="logo-icon">🔮</div>
          <div>
            <h1>GraphRAG System</h1>
            <span className="status-badge">Recuperación Híbrida</span>
          </div>
        </div>
      </header>

      {/* Historial de Mensajes */}
      <main className="messages-container">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message-wrapper ${msg.sender === 'user' ? 'user-wrapper' : 'bot-wrapper'}`}
          >
            <div className={`message-bubble ${msg.sender}`}>
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message-wrapper bot-wrapper">
            <div className="message-bubble bot loading-bubble">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </main>

      {/* Formulario de Entrada */}
      <footer className="input-container">
        <form onSubmit={handleSend} className="input-form">
          <input
            type="text"
            placeholder="Escribe tu consulta aquí..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={!input.trim() || loading}>
            <span>Preguntar</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </form>
      </footer>
    </div>
  );
}

export default App;