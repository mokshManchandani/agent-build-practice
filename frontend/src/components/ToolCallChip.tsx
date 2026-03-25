import type { FunctionCallPart } from "../types"

interface Props {
  call: FunctionCallPart
}

export default function ToolCallChip({ call }: Props) {
  const args = Object.entries(call.args)
    .map(([k, v]) => `${k}: ${v}`)
    .join(", ")

  return (
    <div className="flex items-center gap-2 text-xs my-1">
      <span className="text-amber-600">🔧</span>
      <span className="font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
        {call.name}
      </span>
      {args && (
        <span className="text-slate-400 truncate max-w-xs">{args}</span>
      )}
    </div>
  )
}