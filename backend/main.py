import json
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from google.genai import types
from google.adk.events import Event
from google.adk.agents.run_config import RunConfig, StreamingMode

from backend.models import ChatRequest, ClarificationRequest
from backend.session import APP_NAME, session_service, runner

api = FastAPI()
api.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Double-text guard — in-memory, single-process only.
# Replace with Redis for multi-worker production use.
active_streams: dict[str, bool] = {}
_run_config = RunConfig(streaming_mode=StreamingMode.SSE)


def serialize_events(event: Event) -> dict | None:
    if not event.content and not event.actions:
        return None

    data = {
        "author": event.author,
        "invocation_id": event.invocation_id,
        "id": event.id,
        "is_final": event.is_final_response(),
        "partial": event.partial or False,
    }

    if event.content and event.content.parts:
        parts = []
        for part in event.content.parts:
            if part.text:
                parts.append({"type": "text", "text": part.text})
            elif part.function_call:
                parts.append(
                    {
                        "type": "function_call",
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args or {}),
                        "id": part.function_call.id,
                    }
                )
            elif part.function_response:
                parts.append(
                    {
                        "type": "function_response",
                        "name": part.function_response.name,
                        "id": part.function_response.id,
                    }
                )
        data["parts"] = parts

    if event.actions:
        if event.actions.state_delta:
            data["state_delta"] = dict(event.actions.state_delta)
        if event.actions.transfer_to_agent:
            data["transfer_to_agent"] = event.actions.transfer_to_agent
    return data


@api.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    if active_streams.get(session_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Inference for the session already running.",
        )

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=req.user_id, session_id=session_id
    )

    if not session:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=req.user_id, session_id=session_id
        )

    async def generate():
        active_streams[session_id] = True
        try:
            message = types.Content(parts=[types.Part(text=req.message)], role="user")
            async for event in runner.run_async(
                user_id=req.user_id,
                session_id=session_id,
                new_message=message,
                run_config=_run_config,
            ):
                data = serialize_events(event)
                if data:
                    yield f"data: {json.dumps(data)}\n\n"
            yield 'data: {"type": "done"}\n\n'

        except Exception as e:
            raise e
        finally:
            active_streams.pop(session_id, None)

    return StreamingResponse(
        content=generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api.post("/chat/clarify")
async def chat_clarify(req: ClarificationRequest):
    if active_streams.get(req.session_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Inference for the session already running.",
        )
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=req.user_id, session_id=req.session_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def generate():
        active_streams[req.session_id] = True
        try:
            message = types.Content(
                role="user",
                parts=[types.Part(text=f"[CLARIFICATION ANSWER]: {req.answer}")],
            )
            async for event in runner.run_async(
                user_id=req.user_id,
                session_id=req.session_id,
                new_message=message,
                run_config=_run_config,
            ):
                data = serialize_events(event)
                if data:
                    yield f"data: {json.dumps(data)}\n\n"
            yield 'data: {"type": "done"}\n\n'
        finally:
            active_streams.pop(req.session_id, None)

    return StreamingResponse(
        content=generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@api.get("/sessions/{user_id}")
async def list_sessions(user_id: str):
    result = await session_service.list_sessions(app_name=APP_NAME, user_id=user_id)
    sessions = result.sessions if result else []
    return {"sessions": [s.id for s in sessions]}


@api.get("/observability/usage/{user_id}/{session_id}")
async def get_usage(user_id: str, session_id: str):
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "total_tokens": session.state.get("total_tokens", 0),
        "estimated_cost_usd": session.state.get("estimated_cost_usd", 0),
        "audit_log": session.state.get("audit_log", []),
    }


@api.get("/health")
async def health():
    return {"status": "ok"}
