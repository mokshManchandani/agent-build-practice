from google.adk.tools.tool_context import ToolContext


def request_clarification(question: str, tool_context: ToolContext) -> dict:
    """Pause execution to ask the user a clarifying question or request approval.
    Use when you need more information before proceeding, or when you need explicit user confirmation
    before taking an irreversible action

    Args:
        question (str): The specific question to ask the user.

    Returns:
        dict: a dictionary with status 'awaiting' and the question.
    """

    tool_context.state["clarification_question"] = question
    tool_context.state["awaiting_clarification"] = True
    return {"status": "awaiting", "question": question}
