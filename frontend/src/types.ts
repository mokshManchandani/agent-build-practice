export interface TextPart {
  type: "text";
  text: string;
}

export interface FunctionCallPart {
  type: "function_call";
  name: string;
  args: Record<string, unknown>;
  id: string;
}

export interface FunctionResponsePart {
  type: "function_response";
  name: string;
  id: string;
}

export type Part = TextPart | FunctionCallPart | FunctionResponsePart;

export interface AuditEntry {
  id?: string;
  tool: string;
  args: Record<string, unknown>;
  latency_ms: number | null;
  status: "ok" | "error";
}

export interface StateDelta {
  clarification_question?: string;
  awaiting_clarification?: boolean;
  audit_log?: AuditEntry[];
  total_tokens?: number;
  estimated_cost_usd?: number;
  claims_result?: string;
  [key: string]: unknown;
}

export interface AgentEvent {
  author: string;
  invocation_id: string;
  id: string;
  is_final: boolean;
  partial: boolean;
  parts?: Part[];
  state_delta?: StateDelta;
  transfer_to_agent?: string;
  type?: "done";
}

export type MessageRole = "user" | "agent";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  author?: string;
  text: string;
  isStreaming?: boolean;
  toolCalls?: FunctionCallPart[];
  transfer?: string;
  clarificationContext?: string;
  awaitingClarification?: boolean;
  costUsd?: number;
  totalTokens?: number;
  auditLog?: AuditEntry[];
}
