"""Base agent class for Cox Automotive AI Analytics."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings


class BaseAgent(ABC):
    """Base class for all AI agents."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model_name or settings.openrouter_model,
            temperature=0,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url
        )

    @abstractmethod
    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a query and return results."""
        pass

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return ""

    async def generate_response(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        """Generate a response using the LLM."""
        chain = prompt | self.llm
        response = await chain.ainvoke(kwargs)
        return response.content
