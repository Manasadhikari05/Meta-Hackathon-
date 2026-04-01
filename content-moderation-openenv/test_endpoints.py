"""Manual endpoint connectivity test - run after starting the uvicorn server."""
import json
import requests

BASE = "http://127.0.0.1:8000"
SEP = "=" * 55

def pp(label, r):
    print(f"\n{label}")
    print(f"  HTTP {r.status_code}")
    try:
        body = r.json()
        print(f"  {json.dumps(body, indent=2)[:400]}")
    except Exception:
        print(f"  RAW: {r.text[:200]}")


print(SEP)
print("  CONTENT MODERATION OPENENV — ENDPOINT TESTS")
print(SEP)

# 1. Health check
pp("1. GET /health", requests.get(f"{BASE}/health"))

# 2. State before any reset
pp("2. GET /state (fresh server)", requests.get(f"{BASE}/state"))

# 3. Reset task1
r = requests.post(f"{BASE}/reset", params={"task_id": "task1"})
pp("3. POST /reset?task_id=task1", r)
obs = r.json()
print(f"\n  [Observation summary]")
print(f"    post_id : {obs.get('post', {}).get('post_id')}")
print(f"    platform: {obs.get('post', {}).get('platform')}")
print(f"    content : {obs.get('post', {}).get('content', '')[:100]}...")
print(f"    author  : {obs.get('author')}")
print(f"    topic   : {obs.get('thread_context', {}).get('topic')}")
print(f"    step    : {obs.get('step')}")

# 4. Step - valid action
action = {
    "decision": "remove",
    "reason_code": "hate_speech",
    "severity": "high",
    "confidence": 0.92,
    "explanation": "Post contains explicit hate speech targeting a group.",
}
r = requests.post(f"{BASE}/step", json=action)
pp("4. POST /step (remove/hate_speech/high/0.92)", r)
res = r.json()
print(f"\n  [Result summary]")
print(f"    reward.value: {res.get('reward', {}).get('value')}")
print(f"    done        : {res.get('done')}")
print(f"    info        : {res.get('info')}")

# 5. State after episode
pp("5. GET /state (after task1 done)", requests.get(f"{BASE}/state"))

# 6. Reset task2 (batch)
r = requests.post(f"{BASE}/reset", params={"task_id": "task2"})
pp("6. POST /reset?task_id=task2 (batch)", r)
obs2 = r.json()
print(f"\n  task_id={obs2.get('task_id')}  step={obs2.get('step')}  post_id={obs2.get('post',{}).get('post_id')}")

# 7. Reset task3 (edge-case)
r = requests.post(f"{BASE}/reset", params={"task_id": "task3"})
pp("7. POST /reset?task_id=task3 (hard/edge)", r)
obs3 = r.json()
print(f"\n  task_id={obs3.get('task_id')}  step={obs3.get('step')}  post_id={obs3.get('post',{}).get('post_id')}")

# 8. Invalid task_id
pp("8. POST /reset?task_id=garbage (error handling)", requests.post(f"{BASE}/reset", params={"task_id": "garbage"}))

# 9. Invalid action schema (422 expected from FastAPI)
bad_action = {"decision": "WRONG_VAL", "reason_code": "clean", "severity": "low", "confidence": 0.5}
pp("9. POST /step with bad decision value (expect 422)", requests.post(f"{BASE}/step", json=bad_action))

# 10. Double step after done (episode guard)
requests.post(f"{BASE}/reset", params={"task_id": "task1"})
requests.post(f"{BASE}/step", json={"decision": "approve", "reason_code": "clean", "severity": "low", "confidence": 0.9})
pp("10. POST /step again after done (episode guard)", requests.post(f"{BASE}/step", json={"decision": "approve", "reason_code": "clean", "severity": "low", "confidence": 0.9}))

print(f"\n{SEP}")
print("  ALL CHECKS COMPLETE")
print(SEP)
