from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService

from backend.agent import root_agent

APP_NAME = "insurance-agent"
DB_URL = "sqlite+aiosqlite:///./insurance_agent.db"


session_service = DatabaseSessionService(db_url=DB_URL)

runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
