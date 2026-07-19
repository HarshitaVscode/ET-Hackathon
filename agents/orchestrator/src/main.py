"""
Agent Orchestrator — Entry Point.

Manages the multi-agent system lifecycle, exposes a REST API
for triggering workflows, and provides health monitoring.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from agents.orchestrator.src.communication_bus import (
    AgentMessage,
    CommunicationBus,
    MessagePriority,
    MessageType,
)
from agents.orchestrator.src.config import orchestrator_config
from agents.orchestrator.src.state_machine import (
    WorkflowDAG,
    build_emergency_workflow,
    build_standard_workflow,
)
from agents.orchestrator.src.utils.logging import get_logger

logger = get_logger(__name__)

bus = CommunicationBus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Agent Orchestrator")
    await bus.start()
    yield
    await bus.stop()
    logger.info("Agent Orchestrator stopped")


app = FastAPI(
    title="Vayu-Drishti Agent Orchestrator",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "agent-orchestrator"}


@app.post("/api/v1/workflow/standard")
async def trigger_standard_workflow() -> dict[str, Any]:
    dag = build_standard_workflow(bus)
    result = await dag.execute()
    return result


@app.post("/api/v1/workflow/emergency")
async def trigger_emergency_workflow() -> dict[str, Any]:
    dag = build_emergency_workflow(bus)
    result = await dag.execute()
    return result


@app.post("/api/v1/workflow/custom")
async def trigger_custom_workflow(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    dag = WorkflowDAG(workflow_id=f"custom-{id(tasks)}", bus=bus)
    for task_data in tasks:
        from agents.orchestrator.src.state_machine import TaskNode
        dag.add_task(TaskNode(**task_data))
    result = await dag.execute()
    return result


@app.post("/api/v1/message")
async def send_message(msg: dict[str, Any]) -> dict[str, Any]:
    message = AgentMessage.from_dict(msg)
    result = await bus.send_message(message)
    return {"sent": True, "message_id": message.message_id, "response": result}


@app.get("/api/v1/agents")
async def list_agents() -> dict[str, Any]:
    return {"agents": list(orchestrator_config.agent_configs.keys())}


def main() -> None:
    import uvicorn
    uvicorn.run(
        "agents.orchestrator.src.main:app",
        host="0.0.0.0",
        port=8300,
        reload=orchestrator_config.app_debug,
    )


if __name__ == "__main__":
    main()
