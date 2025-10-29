"""
Task Igniter Agent for the "Task Ignition Ritual".
Decomposes large, vague tasks into actionable subtasks.

MVP Version: Uses simple LangChain prompting instead of complex LangGraph.
"""
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.core.llm_factory import get_chat_model


class SubtaskItem(BaseModel):
    """Schema for a subtask."""
    title: str = Field(description="Clear, actionable title for the subtask")
    description: str = Field(description="Detailed description of what needs to be done")
    priority: int = Field(description="Priority level (1=highest, 5=lowest)", ge=1, le=5)
    is_minimum_viable: bool = Field(
        description="Whether this is the minimum viable starting task",
        default=False
    )


class TaskDecomposition(BaseModel):
    """Schema for task decomposition result."""
    main_task_title: str = Field(description="Refined title for the main task")
    main_task_description: str = Field(description="Clear description of the overall goal")
    subtasks: List[SubtaskItem] = Field(
        description="List of 3-5 actionable subtasks",
        min_items=3,
        max_items=5
    )
    reasoning: str = Field(description="Brief explanation of the decomposition strategy")


class TaskIgniterAgent:
    """
    Agent for task ignition ritual.
    Helps users overcome procrastination by breaking down large tasks.
    """

    def __init__(self):
        """Initialize the agent with LLM and parser."""
        self.llm = get_chat_model(temperature=0.7)
        self.output_parser = PydanticOutputParser(pydantic_object=TaskDecomposition)

        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a productivity coach helping users overcome procrastination.

Your mission: Transform vague, overwhelming tasks into clear, actionable subtasks.

Guidelines:
1. Break down the task into 3-5 concrete subtasks
2. Each subtask should be specific and actionable
3. Identify the "minimum viable starting task" - the smallest, easiest step to build momentum
4. Order subtasks logically (the first should usually be the easiest)
5. Use encouraging, clear language

{format_instructions}"""),
            ("user", "I need help with this task: {task_description}")
        ])

    def decompose_task(self, task_description: str) -> TaskDecomposition:
        """
        Decompose a large task into actionable subtasks.

        Args:
            task_description: User's original task description

        Returns:
            TaskDecomposition with main task and subtasks
        """
        # Format the prompt
        formatted_prompt = self.prompt.format_messages(
            task_description=task_description,
            format_instructions=self.output_parser.get_format_instructions()
        )

        # Get LLM response
        response = self.llm.invoke(formatted_prompt)

        # Parse the response
        result = self.output_parser.parse(response.content)

        # Ensure at least one task is marked as minimum viable
        if not any(task.is_minimum_viable for task in result.subtasks):
            # Mark the first task as minimum viable
            result.subtasks[0].is_minimum_viable = True

        return result


def get_task_igniter() -> TaskIgniterAgent:
    """Get task igniter agent instance."""
    return TaskIgniterAgent()
