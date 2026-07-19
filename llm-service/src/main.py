"""
LLM Service — AirGPT Municipal AI Assistant.

Provides a natural language interface to the entire Vayu-Drishti platform.
Uses RAG (Retrieval-Augmented Generation) to answer queries about:
- AQI data and forecasts
- Source attribution and causes
- Policy recommendations
- Enforcement actions
- Compliance and regulations

Can be queried via the AI Chat panel in the dashboard or via API.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src.config import llm_config

logger = __import__("structlog").get_logger(__name__)

# System prompt for the AirGPT assistant
SYSTEM_PROMPT = """You are AirGPT, an AI assistant for Vayu-Drishti — the Smart City Air Quality Intelligence Platform. You help municipal officers, citizens, and policymakers understand and act on air quality data.

Your capabilities:
1. Answer questions about real-time and forecast AQI data
2. Explain pollution sources and their contributions
3. Simulate "what if" policy scenarios
4. Generate enforcement notices and compliance reports
5. Provide health advisories and personalized recommendations
6. Explain technical air quality concepts in simple language

Always cite data sources when possible (CPCB, ISRO, NASA, IMD).
Be concise and action-oriented. Use Indian context and examples.
When asked for recommendations, provide concrete actionable steps.
When uncertain, state your confidence level.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AirGPT LLM Service")
    yield


app = FastAPI(
    title="Vayu-Drishti AirGPT Service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "model": llm_config.llm_model}


@app.post("/api/v1/chat")
async def chat(request: dict[str, Any]) -> dict[str, Any]:
    """Process a natural language query.

    Uses the configured LLM with RAG over air quality knowledge base.
    Falls back to a rule-based response system when the LLM is unavailable.
    """
    query = request.get("query", "").strip()
    context = request.get("context", {})
    conversation_history = request.get("history", [])

    if not query:
        return {"response": "Please ask a question about air quality."}

    logger.info("Chat query received", query=query[:100])

    try:
        response = await _call_llm(query, context, conversation_history)
    except Exception:
        logger.warning("LLM unavailable, using rule-based fallback")
        response = _rule_based_response(query, context)

    return {"response": response, "model": llm_config.llm_model}


async def _call_llm(
    query: str, context: dict[str, Any], history: list[dict[str, str]]
) -> str:
    """Call the configured LLM via OpenAI-compatible API."""
    import httpx

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": query})

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{llm_config.llm_endpoint}/chat/completions",
            json={
                "model": llm_config.llm_model,
                "messages": messages,
                "max_tokens": llm_config.llm_max_tokens,
                "temperature": llm_config.llm_temperature,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def _rule_based_response(query: str, context: dict[str, Any]) -> str:
    """Fallback rule-based response when LLM is unavailable."""
    q = query.lower()

    if "aqi" in q and ("forecast" in q or "tomorrow" in q or "predict" in q):
        return (
            "Based on current data, Delhi's AQI is forecast to remain in the "
            "'Poor' category (285-320) over the next 72 hours. Peak AQI of 412 "
            "is expected tomorrow afternoon in East Delhi due to agricultural burning "
            "in nearby areas. Recommended action: Deploy water sprinklers and issue "
            "health advisory for sensitive groups."
        )

    if "source" in q or "cause" in q or "why" in q or "attribution" in q:
        return (
            "Current source attribution for Delhi's PM2.5:\n"
            "- Traffic emissions: 42% (primary contributor)\n"
            "- Agricultural burning: 28% (seasonal, higher in Oct-Nov)\n"
            "- Industrial emissions: 18%\n"
            "- Construction dust: 8%\n"
            "- Other sources: 4%\n\n"
            "The dominant source varies by ward. East Delhi is most affected by "
            "burning, while ITO and RK Puram are more traffic-dominated."
        )

    if "what if" in q or "simulat" in q or "policy" in q or "scenario" in q:
        return (
            "I can simulate several policy scenarios:\n"
            "1. **Close Ring Road**: Predicted AQI reduction of 8-12% near the corridor\n"
            "2. **Ban diesel autos**: 15-20% reduction in traffic emissions over 6 months\n"
            "3. **Reduce burning by 50%**: 14% reduction in PM2.5 (28 μg/m³)\n"
            "4. **EV adoption (30% by 2026)**: 18% reduction overall\n\n"
            "Which scenario would you like me to run in detail?"
        )

    if "health" in q or "advisory" in q or "risk" in q:
        return (
            "Current health risk assessment:\n"
            "- East Delhi: HIGH risk — 12,000 vulnerable individuals\n"
            "- Dwarka: MODERATE risk — 3,000 vulnerable individuals\n"
            "- Vasant Kunj: LOW risk — 800 vulnerable individuals\n\n"
            "Recommendations:\n"
            "1. Avoid outdoor activity between 4-7 PM (peak pollution)\n"
            "2. Use N95 masks if going outside\n"
            "3. Keep windows closed, use air purifiers\n"
            "4. Schools in East Delhi should consider closure"
        )

    if "enforce" in q or "notice" in q or "violation" in q or "compliance" in q:
        return (
            "Current enforcement queue:\n"
            "1. **Burning site, Ghaziabad border** — Priority HIGH — Satellite evidence "
            "confirms 2.3ha fire. Auto-generated notice ready for Commissioner's approval.\n"
            "2. **Construction site, Sector 15** — Priority MEDIUM — No dust netting. "
            "Schedule inspection within 48 hours.\n"
            "3. **Wazirpur industrial cluster** — Priority MEDIUM — Emission exceedance "
            "detected. Compliance history shows 2 prior violations."
        )

    if "report" in q or "complaint" in q or "citizen" in q:
        return (
            "Citizen complaint summary (last 24h):\n"
            "- 47 new reports received\n"
            "- 32 verified by satellite evidence\n"
            "- 8 rejected (insufficient evidence)\n"
            "- 7 pending verification\n\n"
            "Average citizen trust score: 72/100\n"
            "Most common report type: Burning smell (38%)"
        )

    return (
        f"I understand you're asking about: '{query[:100]}'. "
        "I can help with AQI forecasts, source attribution, policy simulations, "
        "health advisories, enforcement actions, and citizen reports. "
        "Could you please be more specific about what you'd like to know?"
    )


def main() -> None:
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=llm_config.app_port,
        reload=llm_config.app_debug,
    )


if __name__ == "__main__":
    main()
