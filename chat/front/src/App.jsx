import { useState, useRef, useEffect } from 'react'
import './App.css'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

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

  const cleanMarkdownContent = (content) => {
    if (!content) return content;
    
    let processed = content;

    // processed = processed.replace(/(?<!\*)\* {3}/g, '\n*   ');

    return processed;
  };

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

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        const chunk = decoder.decode(value)
        console.log(chunk)
        // const lines = chunk.split('\n')
        // console.log(lines)

        // for (const line of lines) {
        //   const delta = line
          
        //   if (delta) {
        //     // Acumular contenido
        accumulatedContent += chunk
            
            // const cleanContent = cleanMarkdownContent(accumulatedContent);
            
            // Procesar el contenido para unir palabras rotas
        setMessages(prev => prev.map(msg => 
          msg.id === loadingMessageId 
            ? { ...msg, content: accumulatedContent }
            : msg
        ))
        //   }
        // }
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
            <div className="message-content markdown-body">
              <Markdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </Markdown>
              {/* {isLoading && message.type === 'assistant' && <span className="loading-dots">...</span>} */}
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
