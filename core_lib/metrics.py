from abc import ABC, abstractmethod

from typing import Any, Dict

"""
Defines the contract for creating objective, non-AI evaluation metrics.
"""

class BaseMetric(ABC):
    """
    Abstract Base Class for a "dumb" metric.

    Each metric must have a name and a method to calculate its value
    from an agent's final state.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique, machine-readable name of the metric (e.g., 'total_latency_ms')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A human-readable description of what the metric measures."""
        pass

    @abstractmethod
    def calculate(self, final_state: Dict[str, Any]) -> Any:
        """
        Calculates the metric's value based on the agent's final state.

        Args:
            final_state: The dictionary representing the agent's complete state
                         at the end of a run.

        Returns:
            The calculated value of the metric.
        """
        pass