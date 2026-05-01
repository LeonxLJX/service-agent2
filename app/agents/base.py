from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from app.models.conversation import AgentResponse, Conversation


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def process(self, conversation: Conversation, **kwargs) -> AgentResponse:
        pass

    def _create_response(
        self,
        content: str,
        success: bool = True,
        need_human_intervention: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        return AgentResponse(
            success=success,
            content=content,
            need_human_intervention=need_human_intervention,
            metadata=metadata or {}
        )

    def _should_escalate(self, confidence: float, threshold: float = 0.3) -> bool:
        return confidence < threshold
