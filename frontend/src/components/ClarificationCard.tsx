import { useState } from "react"

interface Props {
  question: string
  onSubmit: (answer: string) => void
  disabled: boolean
}

export default function ClarificationCard({ question, onSubmit, disabled }: Props) {
  const [answer, setAnswer] = useState("")

  const handleSubmit = () => {
    if (!answer.trim() || disabled) return
    onSubmit(answer.trim())
    setAnswer("")
  }

  return (
    <div className="border border-blue-200 bg-blue-50 rounded-xl p-4 my-2">
      <p className="text-sm font-medium text-blue-800 mb-3">
        🤔 {question}
      </p>
      <div className="flex gap-2">
        <input
          type="text"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Your answer..."
          disabled={disabled}
          className="flex-1 text-sm border border-blue-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !answer.trim()}
          className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  )
}