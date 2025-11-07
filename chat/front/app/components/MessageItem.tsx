import React from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

type MessageRole = 'user' | 'model' | 'assistant'
type MessageType = 'text' | 'image' | 'action'

interface Message {
  id?: number
  role: MessageRole
  type: MessageType
  content?: string
  url?: string
  action?: string
}

interface Props {
  message: Message
}

const MessageItem: React.FC<Props> = ({ message }) => {
  // 🖼️ Imagen
  if (message.type === 'image' && message.url) {
    return (
      <div className="message assistant">
        <img
          src={message.url}
          alt="imagen relacionada"
          className="chat-image max-w-xs rounded-lg shadow-md"
        />
      </div>
    )
  }

  // ⚙️ Acción (botón de contacto)
  if (message.type === 'action' && message.action === 'contactar_asesor') {
    return (
      <div className="message assistant">
        <button
          className="contact-button bg-[#d3052d] text-white px-4 py-2 rounded-lg hover:bg-[#b20424] transition"
          onClick={() => alert('Contacto con un asesor')}
        >
          Contacta con un asesor
        </button>
      </div>
    )
  }

  // 💬 Mensaje normal (texto con Markdown)
  return (
    <div
      className={`message ${message.role === 'user' ? 'justify-end' : 'justify-start'} flex`}
    >
      <div
        className={`message-content markdown-body px-4 py-2 rounded-2xl text-sm leading-relaxed max-w-[75%] ${
          message.role === 'user'
            ? 'bg-[#d3052d] text-white rounded-br-none'
            : 'bg-[#eeeeee] text-black rounded-bl-none'
        }`}
      >
        <Markdown remarkPlugins={[remarkGfm]}>
          {message.content || ''}
        </Markdown>
      </div>
    </div>
  )
}

export default MessageItem