'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Loader2, Bot, User, Lightbulb } from 'lucide-react'

interface AIAssistantProps {
  compact?: boolean
}

const suggestions = [
  'Which wards need sprinklers?',
  'What if we close Ring Road?',
  'Explain AQI spike at 4PM',
  'Generate compliance report',
  'Show me top polluting industries',
]

const quickActions = [
  { label: 'Summary', query: 'Give me a quick summary of today\'s air quality' },
  { label: 'Forecast', query: 'What\'s the AQI forecast for the next 3 days?' },
  { label: 'Sources', query: 'What are the main pollution sources today?' },
  { label: 'Health', query: 'Health advisory for current AQI levels' },
  { label: 'Policy', query: 'Which GRAP stage is active and what are the measures?' },
]

export function AIAssistant({ compact }: AIAssistantProps) {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    {
      role: 'assistant',
      content: 'Welcome to **AirGPT**. I can help you analyze air quality data, simulate policies, and generate compliance reports. Try asking me about current conditions, forecasts, or sources.',
    },
  ])
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    const userMsg = { role: 'user' as const, content: query }
    setMessages((prev) => [...prev, userMsg])
    setQuery('')
    setLoading(true)

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, history: messages.slice(-5) }),
      })
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response || 'I apologize, I could not process that request.' }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'I apologize, I am currently unable to reach the AI service. Using fallback knowledge base.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleQuickAction = (q: string) => {
    setQuery(q)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      {!compact && (
        <div className="flex-1 overflow-auto space-y-3 mb-3 pr-1 custom-scrollbar">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}>
              <div className={`flex gap-2 max-w-[90%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'user'
                    ? 'bg-vayu-600/20'
                    : 'bg-gradient-to-br from-vayu-500 to-purple-500'
                }`}>
                  {msg.role === 'user' ? <User size={12} className="text-vayu-400" /> : <Bot size={12} className="text-white" />}
                </div>
                <div className={`p-2.5 rounded-xl text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-vayu-600/20 text-vayu-200 border border-vayu-600/30 rounded-tr-sm'
                    : 'bg-gray-800/60 text-gray-200 border border-gray-700/50 rounded-tl-sm'
                }`}>
                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-1 mb-1.5 pb-1.5 border-b border-gray-700/40">
                      <Sparkles size={10} className="text-vayu-400" />
                      <span className="text-[9px] text-vayu-400 font-semibold">AirGPT</span>
                    </div>
                  )}
                  <div className="leading-relaxed">{msg.content}</div>
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start animate-slide-up">
              <div className="flex gap-2">
                <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-vayu-500 to-purple-500 flex items-center justify-center">
                  <Bot size={12} className="text-white" />
                </div>
                <div className="bg-gray-800/60 border border-gray-700/50 p-2.5 rounded-xl rounded-tl-sm">
                  <div className="flex items-center gap-2">
                    <Loader2 size={12} className="animate-spin text-vayu-400" />
                    <span className="text-[10px] text-gray-400">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
      )}

      {/* Quick actions (compact mode) */}
      {compact && messages.length <= 1 && (
        <div className="space-y-1.5 mb-3">
          <div className="flex items-center gap-1 mb-1.5">
            <Lightbulb size={10} className="text-amber-400" />
            <span className="text-[9px] text-gray-500 font-medium">Suggestions</span>
          </div>
          {quickActions.slice(0, 3).map((a) => (
            <button
              key={a.label}
              onClick={() => handleQuickAction(a.query)}
              className="block w-full text-left text-[10px] text-gray-400 hover:text-gray-200 px-2 py-1.5 rounded-lg bg-gray-800/30 hover:bg-gray-800/60 transition-all border border-transparent hover:border-gray-700/50"
            >
              {a.label}
            </button>
          ))}
        </div>
      )}

      {/* Suggestions (expanded mode) */}
      {!compact && messages.length <= 1 && (
        <div className="mb-3">
          <div className="flex items-center gap-1 mb-2">
            <Lightbulb size={10} className="text-amber-400" />
            <span className="text-[9px] text-gray-500 font-medium">Try asking</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {quickActions.map((a) => (
              <button
                key={a.label}
                onClick={() => handleQuickAction(a.query)}
                className="text-[9px] text-gray-400 hover:text-gray-200 px-2 py-1 rounded-full bg-gray-800/50 hover:bg-gray-800 border border-gray-700/30 hover:border-gray-600/50 transition-all"
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask AirGPT anything..."
          className="flex-1 bg-gray-800/80 border border-gray-700/60 rounded-xl px-3.5 py-2.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-vayu-500/40 focus:ring-1 focus:ring-vayu-500/10 transition-all"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="p-2.5 bg-gradient-to-br from-vayu-500 to-vayu-700 hover:from-vayu-400 hover:to-vayu-600 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl transition-all shadow-lg shadow-vayu-600/20 hover:shadow-vayu-500/30"
        >
          <Send size={14} className="text-white" />
        </button>
      </form>
    </div>
  )
}
