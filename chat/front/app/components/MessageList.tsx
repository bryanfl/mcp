"use client"

import React, { memo, useEffect, useRef } from 'react'
import MessageItem from './MessageItem'

type MessageRole = 'user' | 'model' | 'assistant'
type MessageType = 'text' | 'image' | 'action'

export interface Message {
  id?: number
  role: MessageRole
  type: MessageType
  content?: string
  url?: string
  action?: string
}

interface MessageListProps {
  messages: Message[]
}

const MessageList: React.FC<MessageListProps> = memo(({ messages }) => {
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="messages-container flex flex-col gap-3 p-4 overflow-y-auto h-full scrollbar-thin scrollbar-thumb-[#d3052d]/70">
      {messages.map((msg, i) => (
        <MessageItem key={msg.id ?? i} message={msg} />
      ))}
      <div ref={endRef} />
    </div>
  )
})

MessageList.displayName = 'MessageList'

export default MessageList