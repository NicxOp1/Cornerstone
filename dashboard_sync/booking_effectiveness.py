"""Verify whether Harmony booking actions landed in ServiceTitan."""

import json

try:
    import httpx
except ModuleNotFoundError:
    class _MissingRequestError(Exception):
        pass

    class _MissingAsyncClient:
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("httpx is required to query ServiceTitan")

    class _MissingHttpxModule:
        AsyncClient = _MissingAsyncClient
        RequestError = _MissingRequestError

    httpx = _MissingHttpxModule()

main = None

TRACKED_TOOLS = {
    "create_customer",
    "create_location",
    "create_job",
    "reschedule_appointment",
    "cancel_appointment",
}

CONFIRMED_JOB_STATUSES = {"Scheduled", "InProgress", "Hold", "Completed"}


def _safe_json(raw_value: str | None) -> dict:
    if not raw_value:
        return {}
    try:
        return json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return {}


def _pair_invocations_with_results(transcript: list[dict]) -> list[tuple[dict, dict | None]]:
    invocations = {}
    results = {}
    for item in transcript or []:
        tool_call_id = item.get("tool_call_id")
        if not tool_call_id:
            continue
        if item.get("role") == "tool_call_invocation":
            invocations[tool_call_id] = item
        elif item.get("role") == "tool_call_result":
            results[tool_call_id] = item

    pairs = []
    for tool_call_id, invocation in invocations.items():
        if invocation.get("name") in TRACKED_TOOLS:
            pairs.append((invocation, results.get(tool_call_id)))
    return pairs


async def _st_headers() -> dict:
    main_module = _get_main_module()
    token = await main_module.get_access_token()
    return {
        "Authorization": token,
        "ST-App-Key": main_module.APP_ID,
        "Content-Type": "application/json",
    }


async def _job_has_status(job_id: int, expected_statuses: set[str]) -> bool:
    main_module = _get_main_module()
    url = f"https://api.servicetitan.io/jpm/v2/tenant/{main_module.TENANT_ID}/jobs?ids={job_id}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers=await _st_headers())

    if response.status_code != 200:
        return False

    for job in response.json().get("data", []):
        if job.get("id") == job_id and job.get("jobStatus") in expected_statuses:
            return True
    return False


def _get_main_module():
    global main
    if main is None:
        import main as main_module

        main = main_module
    return main


async def check_call(call: dict) -> str:
    transcript = call.get("transcript_with_tool_calls") or []
    pairs = _pair_invocations_with_results(transcript)
    if not pairs:
        return "not_applicable"

    checks = []
    try:
        for invocation, result in pairs:
            name = invocation.get("name")
            arguments = _safe_json(invocation.get("arguments"))
            result_content = _safe_json(result.get("content") if result else None)

            if name == "create_job":
                job_id = result_content.get("jobId")
                checks.append(
                    job_id is not None and await _job_has_status(job_id, CONFIRMED_JOB_STATUSES)
                )
            elif name == "cancel_appointment":
                job_id = arguments.get("jobId")
                checks.append(job_id is not None and await _job_has_status(job_id, {"Canceled"}))
            elif name == "create_customer":
                checks.append(result_content.get("customerId") is not None)
            elif name == "create_location":
                checks.append(result_content.get("locationId") is not None)
            elif name == "reschedule_appointment":
                checks.append(arguments.get("appointmentId") is not None)
    except httpx.RequestError:
        return "pending"

    if not checks:
        return "not_applicable"
    if all(checks):
        return "confirmed"
    return "mismatch"
