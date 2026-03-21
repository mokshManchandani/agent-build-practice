from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from backend.tools import get_claim_status, get_policy_details


policy_specialist = LlmAgent(
    name="policy_specialist",
    model="gemini-2.0-flash",
    instruction="""
You are a policy checker. Your only job is this:
The user will provide a policy number in their message.
Call get_policy_details with that policy number immediately.
Summarise the coverage limits from the result.
Stop after responding. Do not call any tool more than once.
""",
    tools=[get_policy_details],
    output_key="policy_summary",
)

fraud_specialist = LlmAgent(
    name="fraud_specialist",
    model="gemini-2.0-flash",
    instruction="""
You are a fraud checker. Your only job is this:
Call get_claim_status with the claim number from the user's message.
If the estimated_payout in the result is above 20000, respond: FRAUD_SUSPECTED - reason.
Otherwise respond: CLEAR - reason.
Stop after responding. Do not call any tool more than once.
""",
    tools=[get_claim_status],
    output_key="fraud_assessment",
)

risk_specialist = LlmAgent(
    name="risk_specialist",
    model="gemini-2.0-flash",
    instruction="""
You are a risk assessor. Your only job is this:
Call get_claim_status with the claim number from the user's message.
Based on the estimated_payout and status in the result, respond with exactly:
LOW / MEDIUM / HIGH - one sentence reason.
Stop after responding. Do not call any tool more than once.
""",
    tools=[get_claim_status],
    output_key="risk_assessment",
)

synthesis_specialist = LlmAgent(
    name="synthesis_specialist",
    model="gemini-2.0-flash",
    instruction="""
Synthesise the insurance assessment:

Policy: {policy_summary}
Fraud check: {fraud_assessment}
Risk: {risk_assessment}

Provide a final recommendation: AUTO-APPROVE, MANUAL REVIEW, or ESCALATE.
Include a two-sentence justification.
""",
    output_key="final_recommendation",
)

# Add these two agents alongside the existing specialists
senior_review_agent = LlmAgent(
    name="senior_review_agent",
    model="gemini-2.0-flash",
    instruction="""
You are a senior adjuster reviewing a high-risk claim.
Policy: {policy_summary}
Fraud: {fraud_assessment}
Risk: {risk_assessment}
Recommend: ESCALATE TO SENIOR ADJUSTER with detailed justification.
""",
    output_key="final_recommendation",
)

auto_approve_agent = LlmAgent(
    name="auto_approve_agent",
    model="gemini-2.0-flash",
    instruction="""
This is a low-risk claim cleared for auto-approval.
Policy: {policy_summary}
Risk: {risk_assessment}
Recommend: AUTO-APPROVE with one sentence confirmation.
""",
    output_key="final_recommendation",
)
parallel_fanout = ParallelAgent(
    name="parallel_fanout",
    sub_agents=[policy_specialist, fraud_specialist, risk_specialist],
)


class InsuranceSwarmAgent(BaseAgent):
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:

        async for event in self.sub_agents[0].run_async(ctx):
            yield event

        fraud_result = ctx.session.state.get("fraud_assessment", "")
        risk = ctx.session.state.get("risk_assessment", "LOW")

        if "FRAUD_SUSPECTED" in fraud_result:
            ctx.session.state["final_recommendation"] = (
                "ESCALATE - Fraud suspected. Referred to special investigations unit."
            )
            return
        elif "HIGH" in risk:
            async for event in self.sub_agents[2].run_async(ctx):
                yield event
        else:
            if "LOW" in risk:
                async for event in self.sub_agents[3].run_async(ctx):
                    yield event
            else:
                async for event in self.sub_agents[1].run_async(ctx):
                    yield event


root_agent = InsuranceSwarmAgent(
    name="insurance_swarm",
    sub_agents=[
        parallel_fanout,
        synthesis_specialist,
        senior_review_agent,
        auto_approve_agent,
    ],
)
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent, app_name="exercise-06", session_service=session_service
)
