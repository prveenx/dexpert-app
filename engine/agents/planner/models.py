# FILE: /Planner/models.py
from typing import Optional, Literal, List
from pydantic import BaseModel, Field


class SubTask(BaseModel):
    """A single sub-task in a complex workflow decomposition."""
    step: int = Field(..., description="Step number in the sequence")
    agent: Literal["browser", "os"] = Field(..., description="Which agent handles this step")
    instruction: str = Field(..., description="Concrete instruction for the agent")
    depends_on: Optional[int] = Field(None, description="Step number this depends on")


class PlannerDecision(BaseModel):
    """
    The strict schema for the Planner's decision making.

    Supports three modes:
      - CHAT: Direct response to user
      - TASK: Simple task delegation (1-2 pages, single agent)
      - COMPLEX_TASK: Multi-step workflow requiring scratchpad coordination
    """
    decision_type: Literal["CHAT", "TASK", "COMPLEX_TASK", "ESCALATE"] = Field(..., alias="type")
    target_agent: Optional[Literal["browser", "os"]] = None
    content: str = Field(..., description="Chat reply OR task instruction for the agent")
    thought_process: str = Field(..., description="Reasoning behind the decision")

    # Complex task fields (only used when decision_type == "COMPLEX_TASK")
    task_complexity: Optional[Literal["simple", "complex"]] = Field(
        None, description="'simple' for on-page tasks, 'complex' for multi-page queue-driven tasks"
    )
    target_count: Optional[int] = Field(
        None, description="Number of items to collect (e.g., 10 shops)"
    )
    sub_tasks: Optional[List[SubTask]] = Field(
        None, description="Ordered list of sub-tasks for complex workflow"
    )

    class Config:
        populate_by_name = True