import os
from dotenv import load_dotenv

from google.adk.agents import LlmAgent, SequentialAgent

from .tools import get_policy_details, get_claim_status, calculate_payout_estimate
from .tools.clarification import request_clarification
from .observability import after_agent_callback, after_model_callback

load_dotenv()

# ── Agent definition ───────────────────────────────────────────────────────

# ── Policy agent ───────────────────────────────────────────────────────────
policy_agent = LlmAgent(
    name="policy_agent",
    model="gemini-2.0-flash",
    description=(
        "Handles policy lookups. Use this when the user asks about "
        "their policy details, coverage limits, or premium amount."
    ),
    instruction="""
You are a policy lookup specialist.
Use get_policy_details to retrieve policy information.
Always ask for the policy number if the user hasn't provided one.
Keep answers factual and concise.
""",
    tools=[get_policy_details],
    output_key="policy_result",
    after_model_callback=after_model_callback,
    after_agent_callback=after_agent_callback,
)

# ── Claims agent ───────────────────────────────────────────────────────────
claims_agent = LlmAgent(
    name="claims_agent",
    model="gemini-2.0-flash",
    description=(
        "Handles claim status checks, payout estimates, and payout approvals. "
        "Use this when the user asks about an existing claim, wants to estimate "
        "a payout, or wants to approve and process a payout."
    ),
    instruction="""
You are a claims processing specialist.
Use get_claim_status to check existing claims.
Use calculate_payout_estimate when the user wants to know their payout.

PAYOUT APPROVAL RULE — follow exactly:
Step 1: Call get_claim_status to verify the claim details.
Step 2: Call request_clarification with a single clear question confirming
        the claim_id, amount and reason. Do this via the tool — never ask
        in text.
Step 3: When the user confirms, process the approval and respond with a clear 
        confirmation message stating the claim_id and amount that was approved.
        Always send a text response — never end the turn silently.

Never ask for confirmation in text. Always use the request_clarification tool.
Always ask for claim ID or damage details if not provided.
If a claim is rejected, acknowledge it and refer to appeals@insurance.com.
""",
    tools=[get_claim_status, calculate_payout_estimate, request_clarification],
    output_key="claims_result",
    after_agent_callback=after_agent_callback,
    after_model_callback=after_model_callback,
)


# ── Claims pipeline ─────────────────────────────────────────────────────────
# SequentialAgent: intake_agent → risk_agent → decision_agent
# Data flows via output_key into session.state, read by next agent via {var}

intake_agent = LlmAgent(
    name="intake_agent",
    model="gemini-2.0-flash",
    description="Extracts and validates claim details from the user's message.",
    instruction="""
You are a claims intake specialist.
Use get_claim_status to fetch the current claim data once you have the claim_id.
Ask for the claim_id if the user hasn't provided one.

Summarise what you find in this format:
Claim ID: <value>
Policy: <value>
Type: <value>
Status: <value>
Payout estimate: <value>
Adjuster notes: <value>
""",
    tools=[get_claim_status],
    output_key="intake_result",
    after_model_callback=after_model_callback,
    after_agent_callback=after_agent_callback,
)

risk_agent = LlmAgent(
    name="risk_agent",
    model="gemini-2.0-flash",
    description="Assesses claim risk based on intake results.",
    instruction="""
You are a risk assessment specialist.
You have received the following intake report:

{intake_result}

Based on this, assess the risk level of the claim:
- LOW: status is approved or paid, payout is under $5,000
- MEDIUM: status is under_review, payout is $5,000–$15,000
- HIGH: status is under_review or submitted, payout is over $15,000 or claim type is theft/fraud

Respond in this format:
Risk Level: <LOW | MEDIUM | HIGH>
Reason: <one sentence>
""",
    tools=[],
    output_key="risk_result",
    after_model_callback=after_model_callback,
    after_agent_callback=after_agent_callback,
)

decision_agent = LlmAgent(
    name="decision_agent",
    model="gemini-2.0-flash",
    description="Makes final claim processing decision based on risk assessment.",
    instruction="""
You are a claims decision specialist.
You have the following information:

Intake: {intake_result}
Risk: {risk_result}

Make a final recommendation:
- LOW risk → Recommend: AUTO-APPROVE
- MEDIUM risk → Recommend: MANUAL REVIEW
- HIGH risk → Recommend: ESCALATE TO SENIOR ADJUSTER

Respond in this format:
Decision: <AUTO-APPROVE | MANUAL REVIEW | ESCALATE>
Summary: <two sentences explaining the decision>
""",
    tools=[],
    output_key="decision_result",
    after_model_callback=after_model_callback,
    after_agent_callback=after_agent_callback,
)

claims_pipeline = SequentialAgent(
    name="claims_pipeline",
    description="Runs a structured multi-step claims analysis only. Use this when the user explicitly asks for a full claims assessment, risk analysis, or claims report. Do NOT use for simple claim lookups or payout approvals.",
    sub_agents=[intake_agent, risk_agent, decision_agent],
)
# ── Coordinator ────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    name="coordinator",
    model="gemini-2.0-flash",
    description="Routes insurance queries to the right specialist agent.",
    instruction="""
You are an insurance assistant coordinator.
Route every request to the correct specialist:
- Policy questions → policy_agent
- Claim status checks, payout estimates, or payout approvals → claims_agent
- Explicit requests for full claims analysis or risk assessment report → claims_pipeline

Important: payout approvals always go to claims_agent, never claims_pipeline.

Do not answer questions directly. Always delegate to a specialist.
If a question is outside insurance entirely, respond directly yourself — do not transfer to any specialist. Say: "That is outside the scope of insurance inquiries."
""",
    sub_agents=[policy_agent, claims_agent, claims_pipeline],
    after_model_callback=after_model_callback,
    after_agent_callback=after_agent_callback,
)
