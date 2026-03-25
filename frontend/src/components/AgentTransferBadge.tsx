interface Props {
  to: string
}

export default function AgentTransferBadge({ to }: Props) {
  return (
    <div className="flex items-center gap-2 text-xs text-slate-500 my-1">
      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
        coordinator
      </span>
      <span>→</span>
      <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-mono">
        {to}
      </span>
    </div>
  )
}