"""
Client for the real Hunar Voice Agents API (https://api.voice.hunar.ai/docs/external/).

Two-step flow per the docs:
  1. Create an Agent once (persona, prompt, result_schema) -- we create one
     agent per Screening / ReachoutSearch, since the questions differ between
     them and the prompt is static text (not passed per-call).
  2. Create Calls against that agent_id, one per candidate, with a
     callback_config pointing at our webhook so Hunar posts results back.
"""
from typing import Optional
import httpx
from app.config import settings


def build_result_schema(questions: list[str]) -> dict:
    """
    Turns a list of screening/reachout questions into the result_schema the
    agent should fill in. Keys are answer_1, answer_2... (order-based, not
    slugified from the question text) so there's no ambiguity matching them
    back up -- the frontend zips these with the stored question list by index.
    """
    return {f"answer_{i + 1}": "string" for i in range(len(questions))}


def build_result_prompt(questions: list[str]) -> str:
    numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
    return (
        "From the conversation, extract the candidate's answer to each of the "
        f"following questions, in order:\n{numbered}\n\n"
        "Return them as answer_1, answer_2, ... matching the question numbers "
        "above. If a question was not answered, use an empty string for that key."
    )


def build_agent_prompt(job_description: str, questions: list[str], purpose: str) -> str:
    numbered = "\n".join(f"- {q}" for q in questions)
    return (
        f"You are {{persona_name}}, a recruiting voice agent. {purpose}\n\n"
        f"Role details:\n{job_description}\n\n"
        f"Ask the candidate the following questions, one at a time, in a "
        f"natural conversational way -- don't read them like a list:\n{numbered}\n\n"
        f"Keep the call warm, brief, and professional. If the candidate has "
        f"questions of their own, answer briefly using the role details above."
    )


class HunarClient:
    def __init__(self) -> None:
        self.base_url = settings.hunar_base_url.rstrip("/")
        self.headers = {
            "X-API-Key": settings.hunar_api_key,
            "Content-Type": "application/json",
        }

    # ---------- Agents ----------

    async def create_agent(
        self,
        *,
        name: str,
        job_description: str,
        questions: list[str],
        purpose: str,
        objective: str,
    ) -> dict:
        payload = {
            "name": name[:64],
            "language": settings.hunar_language,
            "voice_persona": settings.hunar_voice_persona,
            "agent_prompt": build_agent_prompt(job_description, questions, purpose),
            "objective": objective,
            "introduction": (
                "Hi {callee_name}, this is {persona_name} calling about the "
                f"{name} role. Do you have a couple of minutes to talk?"
            ),
            "result_prompt": build_result_prompt(questions),
            "result_schema": build_result_schema(questions),
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/agents/",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    # ---------- Calls ----------

    async def trigger_call(
        self,
        *,
        agent_id: str,
        phone: str,
        candidate_name: str,
        webhook_url: str,
        request_id: Optional[str] = None,
        custom_data: Optional[dict] = None,
    ) -> dict:
        payload = {
            "agent_id": agent_id,
            "callee_name": candidate_name,
            "mobile_number": phone,
            "custom_data": custom_data or {},
            "callback_config": {
                # call_summary combines status + recording + result in one
                # webhook fired once the call lifecycle completes -- simplest
                # to handle. Add the other 3 callback URLs too if you want
                # earlier, partial updates (e.g. status while still ringing).
                "call_summary_callback_url": webhook_url,
            },
        }
        if request_id:
            payload["request_id"] = request_id[:64]

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/calls/",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_call(self, hunar_call_id: str) -> dict:
        """Optional polling fallback if a webhook is ever missed."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.base_url}/calls/{hunar_call_id}/",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()


hunar_client = HunarClient()
