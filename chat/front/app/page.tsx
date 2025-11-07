"use client"

import React from 'react'
import ChatHeader from './components/ChatHeader'
import ChatInput from './components/ChatInput'
import MessageList from './components/MessageList'
import { useChat } from './hooks/useChat'

const App: React.FC = () => {
  const { messages, handleSubmit, input, setInput, isLoading } = useChat()

  return (
    <div className="chat-container flex flex-col h-screen bg-[#fff] text-white">
      {/* Header */}
      <ChatHeader title="Asistente UTP" />

      {/* Mensajes */}
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
      </div>

      {/* Input */}
      <ChatInput
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onSubmit={handleSubmit}
        isLoading={isLoading}
      />
    </div>
  )
}

export default App