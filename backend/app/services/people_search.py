# """
# People-search provider abstraction. Two providers implemented: Apollo.io
# and People Data Labs (PDL). Selected via PEOPLE_SEARCH_PROVIDER in .env.

# Both return a normalized list of dicts:
# { "name", "phone", "email", "title", "company", "raw_profile" }
# """
# from typing import Optional
# import httpx
# from app.config import settings


# async def search_apollo(criteria: dict, max_results: int = 20) -> list[dict]:
#     """
#     Apollo.io People Search. Docs: https://docs.apollo.io/reference/people-search
#     Apollo's free/trial tiers gate phone numbers behind a separate "reveal"
#     call (people/match) -- included below.
#     """
#     headers = {
#         "Content-Type": "application/json",
#         "X-Api-Key": settings.apollo_api_key,
#     }
#     search_payload = {
#         "person_titles": criteria.get("titles", []),
#         "person_locations": [criteria["location"]] if criteria.get("location") else [],
#         "q_keywords": " ".join(criteria.get("skills", [])),
#         "per_page": max_results,
#     }

#     async with httpx.AsyncClient(timeout=30) as client:
#         resp = await client.post(
#             "https://api.apollo.io/v1/mixed_people/search",
#             headers=headers,
#             json=search_payload,
#         )
#         resp.raise_for_status()
#         people = resp.json().get("people", [])

#         results = []
#         for person in people:
#             # Reveal phone/email for each match (costs Apollo credits -- consider
#             # only doing this for candidates the recruiter explicitly selects,
#             # rather than for every search result).
#             match_resp = await client.post(
#                 "https://api.apollo.io/v1/people/match",
#                 headers=headers,
#                 json={"id": person.get("id"), "reveal_phone_number": True},
#             )
#             match = match_resp.json().get("person", {}) if match_resp.status_code == 200 else {}
#             results.append({
#                 "name": person.get("name"),
#                 "phone": (match.get("phone_numbers") or [{}])[0].get("raw_number", ""),
#                 "email": match.get("email") or person.get("email"),
#                 "title": person.get("title"),
#                 "company": (person.get("organization") or {}).get("name"),
#                 "raw_profile": person,
#             })
#         return results


# async def search_pdl(criteria: dict, max_results: int = 20) -> list[dict]:
#     """
#     People Data Labs Person Search API.
#     Docs: https://docs.peopledatalabs.com/docs/person-search-api
#     """
#     headers = {"X-Api-Key": settings.pdl_api_key}
#     # PDL uses Elasticsearch-style queries
#     must = []
#     if criteria.get("titles"):
#         must.append({"terms": {"job_title": criteria["titles"]}})
#     if criteria.get("location"):
#         must.append({"term": {"location_locality": criteria["location"].lower()}})
#     if criteria.get("skills"):
#         must.append({"terms": {"skills": [s.lower() for s in criteria["skills"]]}})

#     query = {"query": {"bool": {"must": must}}} if must else {"query": {"match_all": {}}}

#     async with httpx.AsyncClient(timeout=30) as client:
#         resp = await client.get(
#             "https://api.peopledatalabs.com/v5/person/search",
#             headers=headers,
#             params={"sql": None} if False else None,
#             json={**query, "size": max_results},
#         )
#         resp.raise_for_status()
#         data = resp.json().get("data", [])

#         results = []
#         for person in data:
#             phones = person.get("phone_numbers") or []
#             results.append({
#                 "name": person.get("full_name"),
#                 "phone": phones[0] if phones else "",
#                 "email": (person.get("emails") or [{}])[0].get("address", ""),
#                 "title": person.get("job_title"),
#                 "company": person.get("job_company_name"),
#                 "raw_profile": person,
#             })
#         return results


# async def search_people(criteria: dict, max_results: int = 20) -> list[dict]:
#     provider = settings.people_search_provider.lower()
#     if provider == "apollo":
#         return await search_apollo(criteria, max_results)
#     if provider == "pdl":
#         return await search_pdl(criteria, max_results)
#     raise ValueError(f"Unknown PEOPLE_SEARCH_PROVIDER: {provider}")

"""
People-search provider abstraction. Two providers implemented: Apollo.io
and People Data Labs (PDL). Selected via PEOPLE_SEARCH_PROVIDER in .env.

Both return a normalized list of dicts:
{ "name", "phone", "email", "title", "company", "raw_profile" }
"""
from typing import Optional
import httpx
from app.config import settings


async def search_apollo(criteria: dict, max_results: int = 20) -> list[dict]:
    """
    Apollo.io People Search. Docs: https://docs.apollo.io/reference/people-search
    Apollo's free/trial tiers gate phone numbers behind a separate "reveal"
    call (people/match) -- included below.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": settings.apollo_api_key,
    }
    search_payload = {
        "person_titles": criteria.get("titles", []),
        "person_locations": [criteria["location"]] if criteria.get("location") else [],
        "q_keywords": " ".join(criteria.get("skills", [])),
        "per_page": max_results,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.apollo.io/v1/mixed_people/search",
            headers=headers,
            json=search_payload,
        )
        resp.raise_for_status()
        people = resp.json().get("people", [])

        results = []
        for person in people:
            # Reveal phone/email for each match (costs Apollo credits -- consider
            # only doing this for candidates the recruiter explicitly selects,
            # rather than for every search result).
            match_resp = await client.post(
                "https://api.apollo.io/v1/people/match",
                headers=headers,
                json={"id": person.get("id"), "reveal_phone_number": True},
            )
            match = match_resp.json().get("person", {}) if match_resp.status_code == 200 else {}
            results.append({
                "name": person.get("name"),
                "phone": (match.get("phone_numbers") or [{}])[0].get("raw_number", ""),
                "email": match.get("email") or person.get("email"),
                "title": person.get("title"),
                "company": (person.get("organization") or {}).get("name"),
                "raw_profile": person,
            })
        return results


async def search_pdl(criteria: dict, max_results: int = 20) -> list[dict]:
    """
    People Data Labs Person Search API.
    Docs: https://docs.peopledatalabs.com/docs/person-search-api
    POST with an Elasticsearch-style query body.
    """
    headers = {"X-Api-Key": settings.pdl_api_key, "Content-Type": "application/json"}
    must = []
    if criteria.get("titles"):
        must.append({"terms": {"job_title": criteria["titles"]}})
    if criteria.get("location"):
        must.append({"term": {"location_locality": criteria["location"].lower()}})
    if criteria.get("skills"):
        must.append({"terms": {"skills": [s.lower() for s in criteria["skills"]]}})

    query = {"query": {"bool": {"must": must}}} if must else {"query": {"match_all": {}}}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.peopledatalabs.com/v5/person/search",
            headers=headers,
            json={**query, "size": max_results},
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])

        results = []
        for person in data:
            phones = person.get("phone_numbers") or []
            results.append({
                "name": person.get("full_name"),
                "phone": phones[0] if phones else "",
                "email": (person.get("emails") or [{}])[0].get("address", ""),
                "title": person.get("job_title"),
                "company": person.get("job_company_name"),
                "raw_profile": person,
            })
        return results


MOCK_NAMES = [
    ("Priya Sharma", "Senior Backend Engineer", "Zeta Systems"),
    ("Arjun Mehta", "Backend Engineer II", "Novaloop Tech"),
    ("Kavya Reddy", "Software Engineer, Backend", "Finstack Labs"),
    ("Rohan Kapoor", "Staff Backend Engineer", "Orbitly"),
    ("Ananya Iyer", "Backend Developer", "Cloudmint"),
]


async def search_mock(criteria: dict, max_results: int = 20) -> list[dict]:
    """
    Stand-in for a real people-search provider, for when Apollo/PDL/Coresignal
    signup is blocked (work-email gates, pending approval, etc) and there's
    no time left to wait on vendor access. Generates realistic-looking
    candidates so the rest of the pipeline (search -> dashboard -> voice
    reachout) is fully buildable and demoable end to end.

    Every generated candidate uses MOCK_TEST_PHONE_NUMBER from .env -- your
    own real number -- so "reach out to all" actually places real, working
    Hunar calls you can answer yourself, rather than dialing invalid numbers.
    Set that env var before using this provider. Swap PEOPLE_SEARCH_PROVIDER
    back to "apollo"/"pdl"/"coresignal" the moment you have a real account;
    this exists to unblock development and demoing, not to replace the real
    integration in the final submission.
    """
    title = (criteria.get("titles") or ["Software Engineer"])[0]
    location = criteria.get("location") or "Bangalore, India"
    test_phone = settings.mock_test_phone_number

    results = []
    for name, _, company in MOCK_NAMES[: min(max_results, len(MOCK_NAMES))]:
        results.append({
            "name": name,
            "phone": test_phone,  # intentionally the same real number for every row
            "email": f"{name.lower().replace(' ', '.')}@example.com",
            "title": title,
            "company": company,
            "raw_profile": {"mock": True, "location": location},
        })
    return results


async def search_people(criteria: dict, max_results: int = 20) -> list[dict]:
    provider = settings.people_search_provider.lower()
    if provider == "apollo":
        return await search_apollo(criteria, max_results)
    if provider == "pdl":
        return await search_pdl(criteria, max_results)
    if provider == "mock":
        return await search_mock(criteria, max_results)
    raise ValueError(f"Unknown PEOPLE_SEARCH_PROVIDER: {provider}")