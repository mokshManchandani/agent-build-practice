interface Props {
    usd: number
    tokens?:number
}


const CostBadge = ({usd, tokens}: Props) => {
    return (
    <div className="flex items-center gap-2 ml-auto">
      {tokens !== undefined && (
        <span className="text-xs text-slate-400">
          {tokens.toLocaleString()} tokens
        </span>
      )}
      <span className="text-xs text-slate-400 ml-auto">
        ${usd.toFixed(6)}
      </span>
    </div>
  )
}

export default CostBadge;