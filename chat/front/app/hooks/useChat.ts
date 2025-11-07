"use client"
import { useState, useRef, useEffect, useCallback, FormEvent } from 'react'

type MessageType = 'text' | 'action'

interface ChatMessage {
  id?: number
  role: 'user' | 'model'
  content: string
  type: MessageType
  action?: string
}

interface MetaData {
  accion?: string
  imagen?: string
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    const loadingMessageId = Date.now()
    // Tomar solo los últimos 10 mensajes tipo texto
    const prevMessages = [...messages.filter(m => ['user', 'model'].includes(m.role))].slice(-10)

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMessage, type: 'text' },
      { role: 'model', content: '', id: loadingMessageId, type: 'text' }
    ])

    try {
      const apiUrl = process.env.NEXT_PUBLIC_URL_HOST_AGENT_CHAT || ''
      const response = await fetch(`${apiUrl}/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, history: prevMessages })
      })

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`)

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No readable stream found')

      const decoder = new TextDecoder()
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const valueDecoder = decoder.decode(value)

        const match = valueDecoder.match(/({.*})/)
        if (match) {
          const meta: MetaData = JSON.parse(match[1])
          console.log(meta)

          if (meta.accion === 'solicitar_contacto') {
            setMessages(prev => [
              ...prev,
              { role: 'model', content: '', type: 'action', action: 'contactar_asesor' }
            ])
          }

          if (meta.imagen) {
            // mostrar imagen en el chat (por implementar)
          }
        } else {
          accumulated += valueDecoder
          setMessages(prev =>
            prev.map(msg =>
              msg.id === loadingMessageId ? { ...msg, content: accumulated } : msg
            )
          )
        }
      }
    } catch (error: unknown) {
      const errMsg = error instanceof Error ? error.message : 'Error desconocido'
      setMessages(prev =>
        prev.map(msg =>
          msg.id === loadingMessageId
            ? { ...msg, content: `Error: ${errMsg}` }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  return { messages, input, setInput, handleSubmit, isLoading, messagesEndRef }
}