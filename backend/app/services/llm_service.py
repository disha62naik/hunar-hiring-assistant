"""
Small helper for the two LLM-assisted steps in this project:
1. Turning a job description into screening questions / reachout questions.
2. Extracting structured search criteria (titles, skills, location) from a JD.

Uses Anthropic's API if ANTHROPIC_API_KEY is set; otherwise falls back to a
simple heuristic so the app still works end-to-end without an extra key.
"""
import json
import re
from app.config import settings

try:
    import anthropic
except ImportError:
    anthropic = None


async def generate_questions(job_description: str, n: int = 5) -> list[str]:
    if settings.anthropic_api_key and anthropic:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": (
                    f"Based on this job description, write {n} short screening "
                    f"questions a voice AI agent should ask a candidate over a "
                    f"phone call. Return ONLY a JSON array of strings.\n\n"
                    f"Job description:\n{job_description}"
                ),
            }],
        )
        text = msg.content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))

    # Fallback: generic questions that work for most roles
    return [
        "Can you briefly walk me through your relevant experience for this role?",
        "What is your current notice period?",
        "What are your salary expectations for this position?",
        "Are you open to the work location/mode described in the job posting?",
        "Do you have any questions about the role before we proceed?",
    ][:n]


async def extract_search_criteria(job_description: str) -> dict:
    if settings.anthropic_api_key and anthropic:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "Extract search criteria from this job description as JSON "
                    'with keys "titles" (list of job title strings), "skills" '
                    '(list of strings), "location" (string or null). Return ONLY '
                    f"the JSON object.\n\nJob description:\n{job_description}"
                ),
            }],
        )
        text = msg.content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))

    # Fallback: crude keyword extraction so the pipeline still runs
    first_line = job_description.strip().split("\n")[0][:60]
    return {"titles": [first_line], "skills": [], "location": None}
