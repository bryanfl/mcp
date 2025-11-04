import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    // Add user message
    setMessages(prev => [...prev, { type: 'user', content: userMessage }])

    // Add loading message
    const loadingMessageId = Date.now()
    setMessages(prev => [...prev, { type: 'assistant', content: '', id: loadingMessageId }])

    try {
      const apiUrl = import.meta.env.VITE_URL_HOST_AGENT_CHAT || ''
      const response = await fetch(`${apiUrl}/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          // max_iterations: 10
        })
      })

      console.log(response)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        lines.forEach((line, i) => {
          try {
            const delta = line.startsWith('data: ') ? line.slice(6) : line

            setMessages(prev => prev.map(msg => 
              msg.id === loadingMessageId 
                ? { ...msg, content: msg.content + delta.trim() }
                : msg
            ))

          } catch (e) {
            console.error('Error parsing SSE data:', e)
          }
        });
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMessageId 
          ? { ...msg, content: `Error: ${error.message}`, isLoading: false }
          : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>UTP</h1>
      </header>
      
      <div className="messages-container">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.type}`}>
            <div className="message-content">
              {message.content}
              {isLoading && message.type === 'assistant' && <span className="loading-dots">...</span>}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe tu mensaje aquí..."
          className="message-input"
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()} className="send-button">
          {isLoading ? 'Enviando...' : 'Enviar'}
        </button>
      </form>
    </div>
  )
}

export default App
