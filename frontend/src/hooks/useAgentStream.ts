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
  const prevTotalTokensRef = useRef<number>(0);

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

      upsertMessage({
        id: agentMsgId,
        role: "agent",
        text: "",
        isStreaming: true,
      });

      // All accumulators declared ABOVE try so finally can access them
      let streamingText = "";
      let author = "";
      let toolCalls: FunctionCallPart[] = [];
      let transfer: string | undefined;
      let latestCost: number | undefined;
      let latestAuditLog: AuditEntry[] | undefined;
      let latestTokens: number | undefined;
      let clarificationSet = false;
      let awaitingClarification = false;

      try {
        const res = await fetch(`${API}${endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let doneSignal = false;

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

            if (event.type === "done") {
              doneSignal = true;
              break;
            }

            // Track author
            if (event.author) author = event.author;

            // Capture transfer once — first transfer_to_agent event only
            if (event.transfer_to_agent && !transfer) {
              transfer = event.transfer_to_agent;
            }

            // Collect tool calls from ALL events — deduplicate by id
            if (event.parts && !event.partial) {
              for (const part of event.parts) {
                if (part.type === "function_call") {
                  const alreadyExists = toolCalls.some((t) => t.id === part.id);
                  if (!alreadyExists) {
                    toolCalls = [...toolCalls, part];
                  }
                }
              }
            }

            // State delta
            if (event.state_delta) {
              if (event.state_delta.estimated_cost_usd !== undefined) {
                latestCost = event.state_delta.estimated_cost_usd;
              }
              if (event.state_delta.audit_log) {
                latestAuditLog = event.state_delta.audit_log;
              }
              // Set clarification only once per stream turn
              if (
                event.state_delta.clarification_question &&
                !clarificationSet
              ) {
                setPendingClarification(
                  event.state_delta.clarification_question,
                );
                clarificationSet = true;
              }
              // Track awaiting_clarification to hide text bubble
              if (event.state_delta.awaiting_clarification === true) {
                awaitingClarification = true;
              }
              // Per-turn tokens — subtract baseline
              if (event.state_delta.total_tokens !== undefined) {
                latestTokens =
                  event.state_delta.total_tokens - prevTotalTokensRef.current;
              }
            }

            // Partial text — typewriter effect
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

            // Final event — settle bubble with complete data
            if (event.is_final && !event.partial && event.parts) {
              for (const part of event.parts) {
                if (part.type === "text") {
                  streamingText = part.text;
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
                    awaitingClarification,
                  });
                }
              }
            }
          }
          if (doneSignal === true) {
            break;
          }
        }
      } finally {
        setIsStreaming(false);
        streamingIdRef.current = null;

        // Update token baseline for next turn
        if (latestTokens !== undefined) {
          prevTotalTokensRef.current += latestTokens;
        }

        setMessages((prev) =>
          prev.map((m) => {
            if (m.id !== agentMsgId) return m;
            const finalText = m.text || streamingText;
            // Remove completely empty bubbles
            if (!finalText && !m.toolCalls?.length && !m.transfer) return m;
            return {
              ...m,
              isStreaming: false,
              text: finalText,
              awaitingClarification,
            };
          }),
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

      const newSessionId = sessionId ?? `session-${Date.now()}`;
      if (!sessionId) setSessionId(newSessionId);

      await processStream(
        "/chat/stream",
        { message: text, user_id: userId, session_id: newSessionId },
        userMsgId,
      );
    },
    [sessionId, processStream, upsertMessage],
  );

  const sendClarification = useCallback(
    async (answer: string, userId = "user-1") => {
      if (!sessionId) return;
      const userMsgId = `user-clarify-${Date.now()}`;

      // Capture BEFORE clearing — will be null after setPendingClarification(null)
      const context = pendingClarification ?? undefined;

      upsertMessage({
        id: userMsgId,
        role: "user",
        text: answer,
        clarificationContext: context,
      });

      setPendingClarification(null); // clear AFTER upsert

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
    [sessionId, pendingClarification, processStream, upsertMessage],
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
