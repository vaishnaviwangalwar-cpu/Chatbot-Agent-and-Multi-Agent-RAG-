from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse, SessionInfo, PromptStyleEnum
from app.services.agent_service import agent_service
from app.services.memory_service import memory_service
from app.prompts import get_system_prompt

router = APIRouter(prefix="/api", tags=["ChatBot Agent"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to Campus Assistant AI Agent",
    description="Processes user message with session memory, prompt engineering, and automatic tool calling.",
)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    try:
        response = agent_service.process_chat(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response from AI Agent: {str(e)}",
        )


@router.post(
    "/chat/stream",
    summary="Stream message tokens & events from Campus Assistant AI Agent",
    description="Streams real-time text tokens, tool execution events, and session completion via Server-Sent Events (SSE).",
)
def chat_stream_endpoint(request: ChatRequest):
    try:
        return StreamingResponse(
            agent_service.process_chat_stream(request),
            media_type="text/event-stream",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming response from AI Agent: {str(e)}",
        )


@router.get(
    "/sessions",
    response_model=List[SessionInfo],
    summary="List active conversation sessions",
)
def list_sessions() -> List[SessionInfo]:
    return memory_service.list_sessions()


@router.get(
    "/chat/{session_id}",
    summary="Get conversation history for a specific session",
)
def get_session_history(session_id: str):
    history = memory_service.get_history_turns(session_id)
    return {
        "session_id": session_id,
        "turns": history,
        "turn_count": len(history),
    }


@router.delete(
    "/chat/{session_id}",
    summary="Clear conversation session history",
)
def clear_session(session_id: str):
    memory_service.clear_session(session_id)
    return {"message": f"Session '{session_id}' memory cleared successfully."}


@router.get(
    "/prompts",
    summary="Get available Prompt Engineering styles",
)
def get_prompt_styles():
    return {
        "styles": [e.value for e in PromptStyleEnum],
        "details": {
            style.value: get_system_prompt(style) for style in PromptStyleEnum
        },
    }
