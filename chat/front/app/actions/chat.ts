'use server'

interface ChatMessage {
  id?: number
  role: 'user' | 'model'
  content: string
  type: MessageType
  action?: string
}

type MessageType = 'text' | 'action'

export async function sendMessageAction(
  userMessage: string,
  prevMessages: ChatMessage[]
) {
  const apiUrl = process.env.NEXT_PUBLIC_URL_HOST_AGENT_CHAT || ''

  try {
    const response = await fetch(`${apiUrl}/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMessage,
        history: prevMessages
      }),
      cache: 'no-store'
    })

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`)
    }

    return response
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : 'Error desconocido en el servidor'
    console.error('Error en sendMessageAction:', message)
    throw new Error(message)
  }
}