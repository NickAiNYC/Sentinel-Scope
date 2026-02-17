"""
Base Agent class for SiteSentinel-AI Agentic OS.
All agents inherit from this base to ensure consistent interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """
    Abstract base class for all SiteSentinel agents.
    Enforces the async run() interface for LangGraph compatibility.
    """
    
    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's logic.
        
        Args:
            state: Current workflow state from LangGraph
        
        Returns:
            Updated state dict to merge into workflow
        """
        pass
