// src/hooks/useAgentStream.ts
import { useState, useRef, useCallback } from "react";
import type {
  AgentEvent,
  ChatMessage,
  AuditEntry,
  FunctionCallPart,
} from "../types";

const API = "http://localhost:8000";

export function useAgentStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pendingClarification, setPendingClarification] = useState<
    string | null
  >(null);
  const streamingIdRef = useRef<string | null>(null);

  const upsertMessage = useCallback((message: ChatMessage) => {
    setMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === message.id);
      if (idx === -1) return [...prev, message];
      const updated = [...prev];
      updated[idx] = message;
      return updated;
    });
  }, []);

  const processStream = useCallback(
    async (endpoint: string, body: object, _userMessageId: string) => {
      setIsStreaming(true);
      const agentMsgId = `agent-${Date.now()}`;
      streamingIdRef.current = agentMsgId;

      // Placeholder bubble while streaming
      upsertMessage({
        id: agentMsgId,
        role: "agent",
        text: "",
        isStreaming: true,
      });

      try {
        const res = await fetch(`${API}${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let streamingText = "";
        let author = "";
        let toolCalls: FunctionCallPart[] = [];
        let transfer: string | undefined;
        let latestCost: number | undefined;
        let latestAuditLog: AuditEntry[] | undefined;
        let latestTokens: number | undefined;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;

            let event: AgentEvent;
            try {
              event = JSON.parse(raw);
            } catch {
              continue;
            }

            if (event.type === "done") break;

            // Track which agent is responding
            if (event.author) author = event.author;

            // Agent transfer badge
            if (event.transfer_to_agent) {
              transfer = event.transfer_to_agent;
            }

            // Tool calls — only on non-partial events to avoid duplicates
            if (event.parts) {
              for (const part of event.parts) {
                if (part.type === "function_call" && !event.partial) {
                  toolCalls = [...toolCalls, part];
                }
              }
            }

            // State delta — cost, audit log, clarification
            if (event.state_delta) {
              if (event.state_delta.estimated_cost_usd !== undefined) {
                latestCost = event.state_delta.estimated_cost_usd;
              }
              if (event.state_delta.audit_log) {
                latestAuditLog = event.state_delta.audit_log;
              }
              if (event.state_delta.clarification_question) {
                setPendingClarification(
                  event.state_delta.clarification_question,
                );
              }
              if (event.state_delta.total_tokens !== undefined) {
                latestTokens = event.state_delta.total_tokens;
              }
            }

            // Partial text — update streaming bubble word by word
            if (event.parts && event.partial) {
              for (const part of event.parts) {
                if (part.type === "text") {
                  streamingText += part.text;
                  upsertMessage({
                    id: agentMsgId,
                    role: "agent",
                    author,
                    text: streamingText,
                    isStreaming: true,
                    toolCalls,
                    transfer,
                    costUsd: latestCost,
                    totalTokens: latestTokens,
                  });
                }
              }
            }

            // Final event — settle the bubble with complete data
            if (event.is_final && !event.partial && event.parts) {
              for (const part of event.parts) {
                if (part.type === "text") {
                  upsertMessage({
                    id: agentMsgId,
                    role: "agent",
                    author,
                    text: part.text,
                    isStreaming: false,
                    toolCalls,
                    transfer,
                    costUsd: latestCost,
                    totalTokens: latestTokens,
                    auditLog: latestAuditLog,
                  });
                }
              }
            }
          }
        }
      } finally {
        setIsStreaming(false);
        streamingIdRef.current = null;
        // Ensure bubble is settled even if stream ended without is_final
        setMessages((prev) =>
          prev.map((m) =>
            m.id === agentMsgId ? { ...m, isStreaming: false } : m,
          ),
        );
      }
    },
    [upsertMessage],
  );

  const sendMessage = useCallback(
    async (text: string, userId = "user-1") => {
      const userMsgId = `user-${Date.now()}`;
      upsertMessage({ id: userMsgId, role: "user", text });
      setPendingClarification(null);

      // Generate session ID on first message and keep it for the whole session
      const newSessionId = sessionId ?? `session-${Date.now()}`;
      if (!sessionId) setSessionId(newSessionId);

      await processStream(
        "/chat/stream",
        {
          message: text,
          user_id: userId,
          session_id: newSessionId,
        },
        userMsgId,
      );
    },
    [sessionId, processStream, upsertMessage],
  );

  const sendClarification = useCallback(
    async (answer: string, userId = "user-1") => {
      if (!sessionId) return;
      const userMsgId = `user-clarify-${Date.now()}`;
      upsertMessage({ id: userMsgId, role: "user", text: answer });
      setPendingClarification(null);

      await processStream(
        "/chat/clarify",
        {
          session_id: sessionId,
          user_id: userId,
          invocation_id: "",
          answer,
        },
        userMsgId,
      );
    },
    [sessionId, processStream, upsertMessage],
  );

  return {
    messages,
    isStreaming,
    sessionId,
    pendingClarification,
    sendMessage,
    sendClarification,
  };
}
