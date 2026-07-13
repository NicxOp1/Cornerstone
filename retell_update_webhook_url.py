# Publica el draft actual (v9: modelo claude-5-sonnet + voz retell-Grace, hecho
# por el superior de Joaquin) pero:
#   1. Fuerza model_high_priority = true (v9 lo tenia en false; hoy la latencia
#      en vivo es sana con true y no hay margen probado sin eso).
#   2. Repunta webhook_url directo a nuestro backend (dashboard_sync/webhook.py)
#      en vez del hook de Make.com, para sacar a Make del loop de post-call sync.
# No toca el general_prompt/general_tools del LLM ni el tool-level webhook de
# missed_transferred_call (ese sigue en Make, sin cambios).
#
# Uso:
#   python retell_update_webhook_url.py            # dry-run, solo imprime el diff
#   python retell_update_webhook_url.py --apply    # aplica y publica de verdad

import argparse
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.retellai.com"
AGENT_ID = "agent_51ec7087047e7fecc75e91fc38"
LLM_ID = "llm_6953456ea6ffaff400dec7894259"

BACKEND_BASE_URL = "https://cornerstone-d1ln.onrender.com"


def auth_headers():
    key = os.getenv("RETELL_API_KEY")
    if not key:
        sys.exit("RETELL_API_KEY no esta seteado en .env")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def new_webhook_url():
    token = os.getenv("DASHBOARD_SYNC_TOKEN")
    if not token:
        sys.exit("DASHBOARD_SYNC_TOKEN no esta seteado en .env")
    return f"{BACKEND_BASE_URL}/webhooks/callSynced?token={token}"


def get_agent(headers, version=None):
    params = {"version": version} if version is not None else {}
    r = requests.get(f"{API_BASE}/get-agent/{AGENT_ID}", headers=headers, params=params)
    r.raise_for_status()
    return r.json()


def get_llm(headers, version=None):
    params = {"version": version} if version is not None else {}
    r = requests.get(f"{API_BASE}/get-retell-llm/{LLM_ID}", headers=headers, params=params)
    r.raise_for_status()
    return r.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Ejecuta el cambio de verdad (si no, dry-run)")
    args = parser.parse_args()

    headers = auth_headers()
    target_url = new_webhook_url()

    print("Obteniendo draft actual (latest) de Retell...")
    agent = get_agent(headers)
    llm = get_llm(headers)
    print(f"Agent version actual: {agent.get('version')} (is_published={agent.get('is_published')})")
    print(f"LLM version actual  : {llm.get('version')} (is_published={llm.get('is_published')})")

    print("\n--- Plan ---")
    print(f"model               : {llm.get('model')} (sin cambios)")
    print(f"voice_id            : {agent.get('voice_id')} (sin cambios)")
    print(f"model_high_priority : {llm.get('model_high_priority')} -> True")
    print(f"webhook_url         : {agent.get('webhook_url')} -> {target_url}")

    if not args.apply:
        print("\n[DRY RUN] No se aplico ningun cambio. Correr con --apply para ejecutar.")
        return

    print("\nAplicando cambios...")

    r = requests.patch(
        f"{API_BASE}/update-retell-llm/{LLM_ID}",
        headers=headers,
        json={"model_high_priority": True},
    )
    r.raise_for_status()
    new_llm = r.json()
    new_llm_version = new_llm.get("version")
    print(f"LLM actualizado -> nueva version {new_llm_version} (model_high_priority={new_llm.get('model_high_priority')})")

    r = requests.patch(
        f"{API_BASE}/update-agent/{AGENT_ID}",
        headers=headers,
        json={
            "webhook_url": target_url,
            "response_engine": {"type": "retell-llm", "llm_id": LLM_ID, "version": new_llm_version},
        },
    )
    r.raise_for_status()
    new_agent = r.json()
    new_agent_version = new_agent.get("version")
    print(f"Agent actualizado -> nueva version draft {new_agent_version}")

    check = get_agent(headers, version=new_agent_version)
    check_llm = get_llm(headers, version=new_llm_version)
    assert check.get("webhook_url") == target_url
    assert check["response_engine"]["version"] == new_llm_version
    assert check_llm.get("model_high_priority") is True
    assert check_llm.get("model") == llm.get("model")
    assert check.get("voice_id") == agent.get("voice_id")
    print("Verificacion pre-publish OK.")

    r = requests.post(
        f"{API_BASE}/publish-agent-version/{AGENT_ID}",
        headers=headers,
        json={"version": new_agent_version},
    )
    r.raise_for_status()
    print(f"Version {new_agent_version} publicada.")

    final = get_agent(headers)
    print(
        f"Chequeo final: version={final.get('version')} is_published={final.get('is_published')} "
        f"webhook_url={final.get('webhook_url')} voice_id={final.get('voice_id')}"
    )


if __name__ == "__main__":
    main()
