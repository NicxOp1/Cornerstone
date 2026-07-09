"""Sube grabaciones y transcripciones a Vercel Blob."""

import json

import requests


_BLOB_API_BASE = "https://blob.vercel-storage.com"
_BLOB_API_VERSION = "7"


def _upload(pathname: str, content: bytes, content_type: str, token: str):
    response = requests.put(
        f"{_BLOB_API_BASE}/{pathname}",
        data=content,
        headers={
            "Authorization": f"Bearer {token}",
            "x-content-type": content_type,
            "x-api-version": _BLOB_API_VERSION,
        },
        timeout=30,
    )
    if response.status_code >= 300:
        return None
    return response.json().get("url")


def upload_recording(call_id: str, recording_url: str, token: str):
    if not recording_url:
        return None
    try:
        response = requests.get(recording_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return None

    return _upload(f"recordings/{call_id}.wav", response.content, "audio/wav", token)


def upload_transcript(call_id: str, transcript_with_tool_calls: list, token: str):
    payload = json.dumps(transcript_with_tool_calls).encode("utf-8")
    return _upload(f"transcripts/{call_id}.json", payload, "application/json", token)
