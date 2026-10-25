import json

import httpx

from app import llm

print("Key loaded:", bool(llm._key()), "| starts with:", llm._key()[:10] + "..." if llm._key() else "-")
print("Models:", llm.MODELS)
print("Offline mode:", not llm.enabled())

if llm._key():
    r = httpx.get(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {llm._key()}"},
        timeout=20,
    )
    print("\nKey check:", r.status_code, r.text[:300])

    for model in llm.MODELS:
        r = httpx.post(
            llm.BASE_URL,
            headers={"Authorization": f"Bearer {llm._key()}", "X-Title": "Lightcone"},
            json={"model": model, "messages": [{"role": "user", "content": 'Reply with {"ok": true}'}]},
            timeout=llm.TIMEOUT_S,
        )
        print(f"\nModel {model}: HTTP {r.status_code}")
        try:
            body = r.json()
            if r.status_code == 200:
                print("  answer:", body["choices"][0]["message"]["content"][:200])
            else:
                print("  error:", json.dumps(body)[:400])
        except Exception:
            print("  raw:", r.text[:400])
