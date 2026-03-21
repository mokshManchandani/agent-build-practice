from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.models.llm_response import LlmResponse
from google.adk.agents.callback_context import CallbackContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.tools import get_claim_status, get_policy_details


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
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
    cost = (
        state["total_prompt_tokens"] * INPUT_COST
        + state["total_response_tokens"] * OUTPUT_COST
    )
    state["estimated_cost_usd"] = round(cost, 6)
    print(f"[TOKENS] total={state['total_tokens']} cost=${state['estimated_cost_usd']}")
    return None


def after_agent_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    call_times: dict = {}
    call_args: dict = {}
    audit_log: list = []

    for event in callback_context.session.events:
        for call in event.get_function_calls():
            call_times[call.id] = event.timestamp
            call_args[call.id] = dict(call.args or {})

        for response in event.get_function_responses():
            start = call_times.get(response.id)
            latency = round((event.timestamp - start) * 1000) if start else None
            audit_log.append(
                {
                    "tool": response.name,
                    "args": call_args.get(response.id, {}),
                    "latency_ms": latency,
                    "status": "ok"
                    if "error" not in str(response.response)
                    else "error",
                }
            )

    if audit_log:
        callback_context.state["audit_log"] = audit_log
        print(f"[AUDIT] {len(audit_log)} tool call(s) logged")

    return None


root_agent = LlmAgent(
    name="observed_agent",
    model="gemini-2.0-flash",
    instruction="You are an insurance assistant. Answer policy and claims questions using your tools.",
    tools=[get_claim_status, get_policy_details],
    after_model_callback=after_model_callback,
    after_agent_callback=after_agent_callback,
)

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent, app_name="exercise-07", session_service=session_service
)
