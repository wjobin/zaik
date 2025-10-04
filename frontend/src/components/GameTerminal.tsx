import { useState, useEffect, useRef } from 'react'
import './GameTerminal.css'

interface GameMessage {
  text: string
  type: 'output' | 'input' | 'error' | 'image'
  imageUrl?: string
}

interface GameState {
  session_id: string
  current_location_id: string
  inventory: string[]
  visited_locations: string[]
  message: string
  image_url?: string
}

const API_BASE = 'http://localhost:8000'

export default function GameTerminal() {
  const [messages, setMessages] = useState<GameMessage[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Start a new game on mount
  useEffect(() => {
    startNewGame()
  }, [])

  const addMessage = (text: string, type: GameMessage['type'] = 'output', imageUrl?: string) => {
    setMessages(prev => [...prev, { text, type, imageUrl }])
  }

  const startNewGame = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/game/new`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ adventure_id: 'halloween_2025' })
      })

      if (!response.ok) {
        throw new Error('Failed to start new game')
      }

      const state: GameState = await response.json()
      setSessionId(state.session_id)

      addMessage('=== Welcome to Zaik ===')
      addMessage('A text adventure powered by AI')
      addMessage('')
      if (state.image_url) {
        addMessage('', 'image', `${API_BASE}${state.image_url}`)
      }
      addMessage(state.message)
    } catch (error) {
      addMessage('Error: Failed to start game. Is the backend running?', 'error')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const sendCommand = async (command: string) => {
    if (!sessionId || !command.trim()) return

    // Display user input
    addMessage(`> ${command}`, 'input')
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE}/api/game/${sessionId}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      })

      if (!response.ok) {
        throw new Error('Failed to send command')
      }

      const result = await response.json()
      addMessage('')
      if (result.state.image_url) {
        addMessage('', 'image', `${API_BASE}${result.state.image_url}`)
      }
      addMessage(result.message)
    } catch (error) {
      addMessage('Error: Failed to send command', 'error')
      console.error(error)
    } finally {
      setIsLoading(false)
      // Re-focus the input field after command is processed
      inputRef.current?.focus()
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!isLoading && input.trim()) {
      sendCommand(input)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // TODO: Add command history navigation with up/down arrows
  }

  return (
    <div className="game-terminal">
      <div className="terminal-output">
        {messages.map((msg, idx) => (
          <div key={idx} className={`terminal-line terminal-${msg.type}`}>
            {msg.type === 'image' && msg.imageUrl ? (
              <img
                src={msg.imageUrl}
                alt="Location"
                className="location-image"
                style={{ maxWidth: '100%', height: 'auto', margin: '10px 0', borderRadius: '4px' }}
              />
            ) : (
              msg.text
            )}
          </div>
        ))}
        {isLoading && (
          <div className="terminal-line terminal-loading">...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="terminal-input-form">
        <span className="terminal-prompt">&gt;</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || !sessionId}
          className="terminal-input"
          placeholder={sessionId ? "Enter command..." : "Starting game..."}
          autoComplete="off"
          spellCheck="false"
        />
      </form>
    </div>
  )
}
