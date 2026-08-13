import json
import logging
from typing import Generator, List

from google.genai import types

from app.config import settings
from app.genai_client import get_genai_client
from app.prompts import get_system_prompt
from app.schemas.chat import ChatRequest, ChatResponse, PromptStyleEnum, ToolCallInfo
from app.services.memory_service import memory_service
from app.tools.campus_tools import CAMPUS_TOOLS

logger = logging.getLogger(__name__)


def _build_config(style: PromptStyleEnum) -> types.GenerateContentConfig:
    """Builds the shared GenerateContentConfig for all Gemini API calls."""
    return types.GenerateContentConfig(
        system_instruction=get_system_prompt(style),
        tools=CAMPUS_TOOLS,
        thinking_config=types.ThinkingConfig(thinking_level=settings.thinking_level),
        temperature=settings.temperature,
        max_output_tokens=settings.max_output_tokens,
        top_p=settings.top_p,
        top_k=settings.top_k,
    )


def _extract_tool_calls(afc_history) -> List[ToolCallInfo]:
    """Extracts ToolCallInfo objects from Gemini's automatic_function_calling_history."""
    tools_used = []
    if not afc_history:
        return tools_used
    for turn in afc_history:
        for part in turn.parts:
            if part.function_call:
                call = part.function_call
                tools_used.append(ToolCallInfo(
                    tool_name=call.name,
                    args=dict(call.args or {}),
                    result="Tool executed automatically by SDK",
                ))
    return tools_used


class AgentService:
    """
    Orchestrates the ChatBot Agent pipeline (SOLID Single Responsibility Principle).
    Handles Gemini API interaction, prompt selection, session memory, and tool execution.
    """

    def process_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Processes an incoming user message through the full AI Agent pipeline:
        1. Resolves system prompt based on prompt engineering style.
        2. Retrieves conversation context from Session Memory.
        3. Invokes Gemini with automatic function calling (Tool Calling).
        4. Updates session memory with the new turn.
        5. Returns structured ChatResponse.
        """
        session_id = request.session_id
        style = request.prompt_style

        contents = memory_service.get_gemini_contents(session_id, request.message)
        config = _build_config(style)

        logger.info(f"Processing chat for session={session_id} style={style}")

        response = get_genai_client().models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=config,
        )

        reply = response.text or "I apologize, but I could not generate a response."
        tools_used = _extract_tool_calls(response.automatic_function_calling_history)

        # Fallback: capture model-requested but not yet executed tool calls
        if not tools_used and response.function_calls:
            for call in response.function_calls:
                tools_used.append(ToolCallInfo(
                    tool_name=call.name,
                    args=dict(call.args or {}),
                    result="Tool requested by model",
                ))

        turn_count = memory_service.append_turn(session_id, request.message, reply)

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            tools_used=tools_used,
            turn_count=turn_count,
            prompt_style_used=style.value if style else PromptStyleEnum.STRUCTURED_XML.value,
        )

    def process_chat_stream(self, request: ChatRequest) -> Generator[str, None, None]:
        """
        Streams response tokens and tool execution events in real time via SSE.
        Yields Server-Sent Event strings.
        """
        session_id = request.session_id
        style = request.prompt_style

        contents = memory_service.get_gemini_contents(session_id, request.message)
        config = _build_config(style)

        client = get_genai_client()
        full_reply = ""
        seen_tool_calls = []

        try:
            for chunk in client.models.generate_content_stream(
                model=settings.gemini_model,
                contents=contents,
                config=config,
            ):
                # Emit tool call events (deduplicated)
                for tool_info in _extract_tool_calls(chunk.automatic_function_calling_history):
                    call_data = {"tool_name": tool_info.tool_name, "args": tool_info.args}
                    if call_data not in seen_tool_calls:
                        seen_tool_calls.append(call_data)
                        yield f"event: tool_call\ndata: {json.dumps(call_data)}\n\n"

                # Stream text tokens
                if chunk.text:
                    full_reply += chunk.text
                    yield f"event: token\ndata: {json.dumps({'text': chunk.text})}\n\n"

            # Fallback: if streaming yielded tool calls but no text, do one sync call for the final reply
            if not full_reply:
                sync_response = client.models.generate_content(
                    model=settings.gemini_model,
                    contents=contents,
                    config=config,
                )
                full_reply = sync_response.text or "I completed your request."
                for tool_info in _extract_tool_calls(sync_response.automatic_function_calling_history):
                    call_data = {"tool_name": tool_info.tool_name, "args": tool_info.args}
                    if call_data not in seen_tool_calls:
                        seen_tool_calls.append(call_data)
                        yield f"event: tool_call\ndata: {json.dumps(call_data)}\n\n"
                yield f"event: token\ndata: {json.dumps({'text': full_reply})}\n\n"

        except Exception as err:
            logger.error(f"Gemini stream error: {err}")
            full_reply = "The AI service is experiencing high demand. Please wait a moment and try again."
            yield f"event: token\ndata: {json.dumps({'text': full_reply})}\n\n"

        turn_count = memory_service.append_turn(session_id, request.message, full_reply)
        yield f"event: done\ndata: {json.dumps({'session_id': session_id, 'turn_count': turn_count, 'tools_used': seen_tool_calls})}\n\n"


# Singleton instance
agent_service = AgentService()
