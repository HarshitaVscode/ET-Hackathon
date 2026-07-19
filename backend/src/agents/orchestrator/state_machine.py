from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from src.agents.orchestrator.communication_bus import (
    AgentMessage,
    CommunicationBus,
    MessagePriority,
    MessageType,
)
from src.agents.orchestrator.utils.logging import get_logger

logger = get_logger(__name__)


class AgentState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    task_id: str
    agent_name: str
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    state: AgentState = AgentState.PENDING
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    priority: MessagePriority = MessagePriority.NORMAL
    started_at: float = 0.0
    completed_at: float = 0.0
    error: str | None = None


class WorkflowDAG:
    def __init__(self, workflow_id: str, bus: CommunicationBus) -> None:
        self.workflow_id = workflow_id
        self.bus = bus
        self.tasks: dict[str, TaskNode] = {}
        self._context: dict[str, Any] = {
            "workflow_id": workflow_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    def add_task(self, task: TaskNode) -> WorkflowDAG:
        self.tasks[task.task_id] = task
        return self

    def get_execution_order(self) -> list[str]:
        visited: set[str] = set()
        temp_visited: set[str] = set()
        order: list[str] = []

        def dfs(task_id: str) -> None:
            if task_id in temp_visited:
                raise ValueError(f"Cycle detected at {task_id}")
            if task_id in visited:
                return
            temp_visited.add(task_id)
            task = self.tasks[task_id]
            for dep in task.depends_on:
                if dep in self.tasks:
                    dfs(dep)
            temp_visited.remove(task_id)
            visited.add(task_id)
            order.append(task_id)

        for task_id in self.tasks:
            if task_id not in visited:
                dfs(task_id)
        return order

    async def execute(self) -> dict[str, Any]:
        order = self.get_execution_order()
        logger.info("Executing workflow", workflow_id=self.workflow_id, tasks=order)

        completed: dict[str, Any] = {}
        failed: list[str] = []

        for task_id in order:
            task = self.tasks[task_id]
            if task.state == AgentState.SKIPPED:
                continue

            deps_met = all(
                self.tasks[dep].state == AgentState.COMPLETED
                for dep in task.depends_on
                if dep in self.tasks
            )
            if not deps_met:
                task.state = AgentState.SKIPPED
                logger.warning("Task skipped - dependencies not met", task=task_id)
                continue

            task.state = AgentState.RUNNING
            task.started_at = time.time()

            try:
                result = await self._execute_task(task)
                task.output_data = result or {}
                task.state = AgentState.COMPLETED
                task.completed_at = time.time()
                completed[task_id] = task.output_data
                self._context[task_id] = result
                logger.info("Task completed", task=task_id, agent=task.agent_name)
            except Exception as exc:
                task.state = AgentState.FAILED
                task.error = str(exc)
                failed.append(task_id)
                logger.error("Task failed", task=task_id, error=str(exc))
                fallback = self._get_fallback(task)
                if fallback:
                    task.output_data = fallback
                    completed[task_id] = fallback

        return {
            "workflow_id": self.workflow_id,
            "status": "completed" if not failed else "degraded",
            "completed_tasks": len(completed),
            "failed_tasks": failed,
            "results": completed,
            "context": self._context,
        }

    async def _execute_task(self, task: TaskNode) -> dict[str, Any] | None:
        context = {}
        for dep in task.depends_on:
            if dep in self.tasks and self.tasks[dep].output_data:
                context[dep] = self.tasks[dep].output_data

        message = AgentMessage(
            sender_id="orchestrator",
            target_agent=task.agent_name,
            message_type=MessageType.REQUEST,
            payload={
                "task_id": task.task_id,
                "input": task.input_data,
                "context": context,
                "workflow_id": self.workflow_id,
            },
            priority=task.priority,
            context_id=self.workflow_id,
        )

        result = await asyncio.wait_for(
            self.bus.send_message(message),
            timeout=task.timeout_seconds,
        )
        return result

    def _get_fallback(self, task: TaskNode) -> dict[str, Any] | None:
        return {"error": task.error, "is_fallback": True, "task_id": task.task_id}


def build_standard_workflow(bus: CommunicationBus) -> WorkflowDAG:
    dag = WorkflowDAG(workflow_id=f"wf-{uuid4().hex[:8]}", bus=bus)
    dag.add_task(TaskNode(
        task_id="burn_detection",
        agent_name="burn_detection",
        priority=MessagePriority.HIGH,
    ))
    dag.add_task(TaskNode(
        task_id="traffic_analysis",
        agent_name="traffic_monitor",
    ))
    dag.add_task(TaskNode(
        task_id="source_attribution",
        agent_name="source_attribution",
        depends_on=["burn_detection", "traffic_analysis"],
    ))
    dag.add_task(TaskNode(
        task_id="aqi_forecast",
        agent_name="aqi_forecast",
        depends_on=["source_attribution", "traffic_analysis"],
    ))
    return dag


def build_emergency_workflow(bus: CommunicationBus) -> WorkflowDAG:
    dag = WorkflowDAG(workflow_id=f"emergency-{uuid4().hex[:8]}", bus=bus)
    dag.add_task(TaskNode(
        task_id="burn_detection",
        agent_name="burn_detection",
        priority=MessagePriority.EMERGENCY,
    ))
    dag.add_task(TaskNode(
        task_id="aqi_forecast",
        agent_name="aqi_forecast",
        depends_on=["burn_detection"],
        priority=MessagePriority.EMERGENCY,
    ))
    dag.add_task(TaskNode(
        task_id="emergency_response",
        agent_name="emergency_response",
        depends_on=["burn_detection", "aqi_forecast"],
        priority=MessagePriority.EMERGENCY,
    ))
    return dag
