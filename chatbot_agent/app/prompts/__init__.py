"""
Prompt Engineering Modules demonstrating Module 3 principles.
"""
from app.prompts.system_prompts import (
    get_system_prompt,
    STRUCTURED_XML_PROMPT,
    FEW_SHOT_PROMPT,
    COT_PROMPT,
    BASELINE_PROMPT,
)
from app.prompts.campus_faqs import CAMPUS_FAQS

__all__ = [
    "get_system_prompt",
    "STRUCTURED_XML_PROMPT",
    "FEW_SHOT_PROMPT",
    "COT_PROMPT",
    "BASELINE_PROMPT",
    "CAMPUS_FAQS",
]
