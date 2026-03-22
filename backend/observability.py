# backend/observability.py
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai import types


def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    usage = getattr(llm_response, "usage_metadata", None)
    if not usage:
        return None

    state = callback_context.state
    state["total_prompt_tokens"] = state.get("total_prompt_tokens", 0) + (
        getattr(usage, "prompt_token_count", 0) or 0
    )
    state["total_response_tokens"] = state.get("total_response_tokens", 0) + (
        getattr(usage, "candidates_token_count", 0) or 0
    )
    state["total_tokens"] = state.get("total_tokens", 0) + (
        getattr(usage, "total_token_count", 0) or 0
    )

    INPUT_COST = 0.10 / 1_000_000
    OUTPUT_COST = 0.40 / 1_000_000
    state["estimated_cost_usd"] = round(
        state["total_prompt_tokens"] * INPUT_COST
        + state["total_response_tokens"] * OUTPUT_COST,
        6,
    )
    return None


def after_agent_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    call_times: dict = {}
    call_args: dict = {}
    this_turn_log: list = []

    current_invocation = callback_context.invocation_id

    for event in callback_context.session.events:
        if event.invocation_id != current_invocation:
            continue
        for call in event.get_function_calls():
            call_times[call.id] = event.timestamp
            call_args[call.id] = dict(call.args or {})
        for response in event.get_function_responses():
            start = call_times.get(response.id)
            latency = round((event.timestamp - start) * 1000) if start else None
            this_turn_log.append(
                {
                    "id": response.id,
                    "tool": response.name,
                    "args": call_args.get(response.id, {}),
                    "latency_ms": latency,
                    "status": "ok"
                    if "error" not in str(response.response)
                    else "error",
                }
            )

    if not this_turn_log:
        return None

    existing: list = callback_context.state.get("audit_log", [])
    seen_ids: set = {e["id"] for e in existing if "id" in e}
    new_entries = [e for e in this_turn_log if e["id"] not in seen_ids]

    if new_entries:
        callback_context.state["audit_log"] = existing + new_entries

    return None
