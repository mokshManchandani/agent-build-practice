import { useState, useRef, useEffect } from "react"
import { useAgentStream } from "./hooks/useAgentStream"
import ChatMessage from "./components/ChatMessage"
import ClarificationCard from "./components/ClarificationCard"

const App = () => {
  const { messages, isStreaming, pendingClarification, sendMessage, sendClarification } = useAgentStream();
  const [input, setInput] = useState<string>();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(()=>{
    bottomRef.current?.scrollIntoView({ behavior: "smooth"})
  }, [messages])

  const handleSend = () => {
    if(!input?.trim() || isStreaming) return
    sendMessage(input.trim())
    setInput("")
  }

  return (
    <div className="flex h-screen bg-white font-sans">

      {/* ── Sidebar ── */}
      <aside className="w-64 flex-shrink-0 bg-[#1c1c1c] flex flex-col py-4 px-3">
        {/* New chat button */}
        <button className="flex items-center gap-3 text-sm text-white/80 hover:text-white hover:bg-white/10 rounded-lg px-3 py-2 mb-6 transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New chat
        </button>

        {/* Nav items */}
        <nav className="flex flex-col gap-1">
          {["Search", "Chats", "Projects", "Artifacts"].map((item) => (
            <button
              key={item}
              className="flex items-center gap-3 text-sm text-white/60 hover:text-white hover:bg-white/10 rounded-lg px-3 py-2 transition-colors text-left"
            >
              {item}
            </button>
          ))}
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* User info */}
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-7 h-7 rounded-full bg-orange-500 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
            M
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-sm text-white/80 truncate">Insurance Agent</span>
            <span className="text-xs text-white/40">Pro plan</span>
          </div>
        </div>
      </aside>

      {/* ── Main chat area ── */}
      <main className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-slate-100">
          <span className="text-sm font-medium text-slate-700">
            Insurance Claims Assistant
          </span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
              gemini-2.0-flash
            </span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-3xl mb-4">🏥</div>
              <h2 className="text-xl font-semibold text-slate-700 mb-2">
                Insurance Claims Assistant
              </h2>
              <p className="text-sm text-slate-400 max-w-sm">
                Ask about policy details, claim status, or request a full claims assessment.
              </p>
              <div className="flex flex-wrap gap-2 mt-6 justify-center">
                {[
                  "What is the status of claim CLM-98765?",
                  "Look up policy POL-12345",
                  "Run a full claims assessment",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => { sendMessage(suggestion) }}
                    className="text-xs text-slate-600 border border-slate-200 rounded-full px-3 py-1.5 hover:bg-slate-50 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Clarification card */}
          {pendingClarification && (
            <ClarificationCard
              question={pendingClarification}
              onSubmit={sendClarification}
              disabled={isStreaming}
            />
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="px-6 py-4 border-t border-slate-100">
          <div className="flex items-end gap-3 bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3">
            <button className="text-slate-400 hover:text-slate-600 flex-shrink-0 mb-0.5">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder="Message Insurance Agent..."
              disabled={isStreaming}
              rows={1}
              className="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 resize-none focus:outline-none disabled:opacity-50 max-h-32"
              style={{ lineHeight: "1.5" }}
            />
            <button
              onClick={handleSend}
              disabled={isStreaming || !input?.trim()}
              className="flex-shrink-0 w-8 h-8 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-200 text-white rounded-lg flex items-center justify-center transition-colors mb-0.5"
            >
              {isStreaming ? (
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              )}
            </button>
          </div>
          <p className="text-xs text-slate-400 text-center mt-2">
            Insurance Agent can make mistakes. Verify important information.
          </p>
        </div>
      </main>
    </div>
  )
}

export default App;