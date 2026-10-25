import httpx

from app import llm

PREFERRED = ["llama", "qwen", "deepseek", "gemma", "mistral", "gpt-oss", "glm", "kimi", "nemotron"]


def is_free(model):
    pricing = model.get("pricing") or {}
    return model["id"].endswith(":free") or (
        str(pricing.get("prompt", "1")) in ("0", "0.0") and str(pricing.get("completion", "1")) in ("0", "0.0")
    )


def rank(model):
    mid = model["id"].lower()
    family = next((i for i, name in enumerate(PREFERRED) if name in mid), len(PREFERRED))
    return (family, -(model.get("context_length") or 0))


def works(model_id):
    try:
        r = httpx.post(
            llm.BASE_URL,
            headers={"Authorization": f"Bearer {llm._key()}", "X-Title": "Lightcone"},
            json={
                "model": model_id,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": "Return ONLY a JSON object."},
                    {"role": "user", "content": 'Return {"min_qty": 250, "max_qty": 300}'},
                ],
            },
            timeout=40,
        )
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:120]}"
        data = llm._extract_json(r.json()["choices"][0]["message"]["content"] or "")
        return data.get("min_qty") == 250, "ok"
    except Exception as error:
        return False, f"{type(error).__name__}: {str(error)[:120]}"


models = httpx.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]
free = sorted((m for m in models if is_free(m)), key=rank)
print(f"{len(free)} free models listed by OpenRouter right now. Testing the most suitable ones...\n")

good = []
for model in free[:15]:
    ok, info = works(model["id"])
    print(f"{'OK  ' if ok else 'FAIL'} {model['id']}  ({info})")
    if ok:
        good.append(model["id"])
    if len(good) == 3:
        break

print()
if good:
    print("Put this line in backend/.env (replace the LLM_MODELS line):")
    print("LLM_MODELS=" + ",".join(good))
else:
    print("No free model answered correctly right now. Wait a few minutes and run again.")
