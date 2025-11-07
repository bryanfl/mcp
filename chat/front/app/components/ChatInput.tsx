import React, { ChangeEvent, FormEvent } from 'react'

interface ChatInputProps {
  value: string
  onChange: (e: ChangeEvent<HTMLInputElement>) => void
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
  isLoading?: boolean
}

const ChatInput: React.FC<ChatInputProps> = ({ value, onChange, onSubmit, isLoading = false }) => (
  <form
    onSubmit={onSubmit}
    className="input-form flex items-center gap-2 p-4 border-t border-white/10 bg-[#fff]"
  >
    <input
      type="text"
      value={value}
      onChange={onChange}
      placeholder="Escribe tu mensaje aquí..."
      className="message-input border-2 border-gray-100 flex-1 bg-[#fff] text-black rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#d3052d] disabled:opacity-50"
      disabled={isLoading}
    />
    <button
      type="submit"
      disabled={isLoading || !value.trim()}
      className={`send-button bg-[#d3052d] hover:bg-[#b20424] text-white px-4 py-2 rounded-lg font-medium transition ${
        isLoading ? 'opacity-60 cursor-not-allowed' : ''
      }`}
    >
      {isLoading ? 'Enviando...' : 'Enviar'}
    </button>
  </form>
)

export default ChatInput