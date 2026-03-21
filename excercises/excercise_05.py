from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from backend.tools import get_claim_status, get_policy_details


collision_checker = LlmAgent(
    name="collision_checker",
    model="gemini-2.0-flash",
    instruction="""
    You are checking collision coverage.
    The user will provide the claim number in their prompt
    Use their claim number and you are supposed to call the tool to get a response
    USE get_claim_status tool to fetch the details of the claim
    Respond: ELIGIBLE or NOT ELIGIBLE with one sentence reason.
    """,
    tools=[get_claim_status],
    output_key="collision_eligibility",
)

rental_checker = LlmAgent(
    name="rental_checker",
    model="gemini-2.0-flash",
    instruction="""
You are checking rental reimbursement coverage.
The user will provide a claim and policy number in their request.
You MUST immediately call get_policy_details with the provided policy number.
After calling the tool, respond in exactly this format:
COVERED - $X/day up to $Y
or
NOT COVERED
""",
    tools=[get_policy_details],
    output_key="rental_eligibility",
)

medical_checker = LlmAgent(
    name="medical_checker",
    model="gemini-2.0-flash",
    instruction="""
You are checking medical payments coverage.
The user will provide a claim and policy number in their request.
You MUST immediately call get_policy_details with the provided policy number.
After calling the tool, respond in exactly this format:
COVERED up to $X per person
or
NOT COVERED
""",
    tools=[get_policy_details],
    output_key="medical_eligibility",
)
coverage_fanout = ParallelAgent(
    name="coverage_checker",
    sub_agents=[collision_checker, rental_checker, medical_checker],
)

synthesis_agent = LlmAgent(
    name="synthesis_agent",
    model="gemini-2.0-flash",
    instruction="""
    Summarise the coverage eligibility results:

    Collision: {collision_eligibility}
    Rental: {rental_eligibility}
    Medical: {medical_eligibility}

    Provide a clear summary of what the policyholder is entitled to claim.
    """,
    output_key="coverage_summary",
)

root_agent = SequentialAgent(
    name="coverage_pipeline", sub_agents=[coverage_fanout, synthesis_agent]
)

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent, app_name="exercise-05", session_service=session_service
)
