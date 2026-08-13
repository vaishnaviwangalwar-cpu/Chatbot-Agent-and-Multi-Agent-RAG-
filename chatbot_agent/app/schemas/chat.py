from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PromptStyleEnum(str, Enum):
    """Supported prompt engineering modes from Module 3."""

    STANDARD = "standard"  # Baseline system prompt
    STRUCTURED_XML = "structured_xml"  # Prompts organized using XML tags
    FEW_SHOT = "few_shot"  # Prompts with input/output examples
    CHAIN_OF_THOUGHT = "cot"  # Step-by-step reasoning instructions


class ChatRequest(BaseModel):
    """
    Incoming chat request payload.
    Validates user input and session identification.
    """

    session_id: str = Field(
        ...,
        description="Unique identifier for the user session.",
        examples=["user_session_101"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's query or message to the assistant.",
        examples=["What are the library opening hours?"],
    )
    prompt_style: Optional[PromptStyleEnum] = Field(
        default=PromptStyleEnum.STRUCTURED_XML,
        description="Prompt engineering style technique to apply.",
    )


class ToolCallInfo(BaseModel):
    """Metadata regarding a function call invoked by the model during a turn."""

    tool_name: str = Field(
        ..., description="Name of the Python tool function called."
    )
    args: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed by the Gemini model to the tool.",
    )
    result: str = Field(
        ..., description="Return value from the executed Python tool."
    )


class ChatResponse(BaseModel):
    """
    Structured API response returned to the client.
    Guarantees consistent JSON contract for front-end consumption.
    """

    session_id: str = Field(
        ..., description="Active session ID for history tracking."
    )
    reply: str = Field(
        ..., description="The assistant's text response to the user."
    )
    tools_used: List[ToolCallInfo] = Field(
        default_factory=list,
        description="List of tools called by the model during generation.",
    )
    turn_count: int = Field(
        ..., description="Number of conversation turns stored in session."
    )
    prompt_style_used: str = Field(
        ..., description="Prompt technique applied to generate the response."
    )


class SessionInfo(BaseModel):
    """Summary of an active session stored in memory."""

    session_id: str
    message_count: int
    max_turns: int
