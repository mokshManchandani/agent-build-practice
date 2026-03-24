import type {ChatMessage as ChatMessageType } from '../types'
import AgentTransferBadge from './AgentTransferBadge'
import ToolCallChip from './ToolCallChip'
import CostBadge from './CostBadge'


interface Props{
    message: ChatMessageType
}

const ChatMessage = ({message}: Props) => {
    const isUser = message.role === 'user'

    if(isUser) {
        return (
        <div className="flex justify-end mb-3">
            <div className="bg-blue-600 text-white text-sm px-4 py-2.5 rounded-2xl rounded-br-sm max-w-md">
            {message.text}
            </div>
        </div>
        )
    }

    return (
        <div className="flex flex-col mb-3 max-w-2xl">
            {/* Agent transfer badge */}
            {message.transfer && (
                <AgentTransferBadge to={message.transfer} />
            )}

            {/* Tool call chips */}
            {message.toolCalls && message.toolCalls.length > 0 && (
                <div className="mb-1">
                {message.toolCalls.map((call) => (
                    <ToolCallChip key={call.id} call={call} />
                ))}
                </div>
            )}

            {/* Message bubble */}
            <div className="bg-white border border-slate-200 text-slate-800 text-sm px-4 py-2.5 rounded-2xl rounded-bl-sm shadow-sm">
                {/* Author label */}
                {message.author && (
                <p className="text-xs font-semibold text-slate-400 mb-1">
                    {message.author}
                </p>
                )}

                {/* Text content */}
                <p className="whitespace-pre-wrap leading-relaxed">
                {message.text}
                {message.isStreaming && (
                    <span className="inline-block w-1.5 h-3.5 bg-slate-400 ml-0.5 animate-pulse rounded-sm" />
                )}
                </p>

                {/* Footer — cost badge */}
                {message.costUsd !== undefined && !message.isStreaming && (
                <div className="flex mt-2 pt-2 border-t border-slate-100">
                    <CostBadge usd={message.costUsd} tokens={message.totalTokens}/>
                </div>
                )}
            </div>
        </div>
    )
}

export default ChatMessage;