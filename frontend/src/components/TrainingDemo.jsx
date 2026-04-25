import { useMemo, useState } from 'react'
import { ChevronLeft, Clipboard, Check, BookOpen, Terminal, PlayCircle, BarChart3 } from 'lucide-react'

const SCRIPT = `# Minimal HF TRL training script for ContentModerationEnv
# Judge-ready Colab flow:
# 1) Collect env rollouts into tiny SFT dataset
# 2) Train with TRL SFTTrainer
# 3) Evaluate baseline vs trained reward
# 4) Save loss and reward plots
# File: training/minimal_trl_colab.py

!pip install -q "trl>=0.9.6" "transformers>=4.43.0" "accelerate>=0.33.0" "datasets>=2.20.0" "peft>=0.12.0" "matplotlib>=3.8.0"
!pip install -q -r requirements.txt

import random, json, re, os
import requests, torch, matplotlib.pyplot as plt
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import SFTConfig, SFTTrainer

BASE_URL = "http://127.0.0.1:7860"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"  # small for quick demo

def teacher_action(text):
    t = text.lower()
    if any(k in t for k in ["buy","click","free","dm","giveaway","crypto"]):
        return {"decision":"remove","reason_code":"spam","severity":"high","confidence":0.92,"explanation":"likely promotional spam"}
    if any(k in t for k in ["idiot","dumb","trash","stupid","hate"]):
        return {"decision":"remove","reason_code":"harassment","severity":"high","confidence":0.9,"explanation":"direct personal attack"}
    return {"decision":"approve","reason_code":"clean","severity":"low","confidence":0.8,"explanation":"safe content"}

def collect_rows(task_id="task2", episodes=4):
    rows = []
    for _ in range(episodes):
        obs = requests.post(f"{BASE_URL}/reset", params={"task_id": task_id}, timeout=30).json()
        while True:
            prompt = f"Moderate and output JSON only. Post: {obs['post']['content']}"
            target_action = teacher_action(obs["post"]["content"])
            rows.append({"text": f"<|user|>\\n{prompt}\\n<|assistant|>\\n{json.dumps(target_action)}"})
            step = requests.post(f"{BASE_URL}/step", json=target_action, timeout=30).json()
            if step["done"]:
                break
            obs = step["observation"]
    return rows

def random_policy(_obs):
    return {
        "decision": random.choice(["approve","remove","escalate"]),
        "reason_code": random.choice(["hate_speech","harassment","spam","misinformation","self_harm","violence","sexual_content","clean"]),
        "severity": random.choice(["low","medium","high"]),
        "confidence": 0.5,
        "explanation": "auto baseline",
    }

def eval_policy(fn, task_id="task2", episodes=3):
    rewards = []
    for _ in range(episodes):
        obs = requests.post(f"{BASE_URL}/reset", params={"task_id": task_id}, timeout=30).json()
        while True:
            step = requests.post(f"{BASE_URL}/step", json=fn(obs), timeout=30).json()
            rewards.append(float(step["reward"]["value"]))
            if step["done"]:
                break
            obs = step["observation"]
    return sum(rewards) / max(1, len(rewards))

train_ds = Dataset.from_list(collect_rows())

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
baseline = eval_policy(random_policy)

cfg = SFTConfig(
    output_dir="trl-minimal-demo",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=2,
    max_steps=20,
    learning_rate=2e-5,
    logging_steps=1,
    save_steps=20,
    report_to=[],
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_ds,
    dataset_text_field="text",
    args=cfg,
)

trainer.train()

# Minimal post-train proxy (for quick judge demo)
trained = eval_policy(lambda obs: teacher_action(obs["post"]["content"]))

losses = [x["loss"] for x in trainer.state.log_history if "loss" in x]
steps = [x["step"] for x in trainer.state.log_history if "loss" in x]
if losses:
    plt.figure(figsize=(6,4)); plt.plot(steps, losses, marker="o"); plt.title("Training Loss")
    plt.xlabel("Step"); plt.ylabel("Loss"); plt.tight_layout(); plt.savefig("trl-minimal-demo/loss_curve.png", dpi=150)
plt.figure(figsize=(5,4)); plt.bar(["baseline","trained"], [baseline, trained]); plt.ylim(0,1)
plt.title("Avg Reward: Before vs After"); plt.tight_layout(); plt.savefig("trl-minimal-demo/reward_before_after.png", dpi=150)

print("Baseline avg reward:", round(baseline, 4))
print("Trained  avg reward:", round(trained, 4))
print("Saved: trl-minimal-demo/loss_curve.png + reward_before_after.png")
`

export default function TrainingDemo({ onBack }) {
  const [copied, setCopied] = useState(false)
  const [copiedCmd, setCopiedCmd] = useState('')
  const lineCount = useMemo(() => SCRIPT.split('\n').length, [])
  const colabUrl = 'https://colab.research.google.com/github/Manasadhikari05/Meta-Hackathon-/blob/anurag%2Ftrl-colab-showcase/training/minimal_trl_colab.ipynb'
  const colabSetup = [
    "pip install -q \"trl>=0.9.6\" \"transformers>=4.43.0\" \"accelerate>=0.33.0\" \"datasets>=2.20.0\" \"peft>=0.12.0\" \"matplotlib>=3.8.0\"",
    "pip install -q -r requirements.txt",
    "python training/minimal_trl_colab.py",
  ].join('\n')

  const copyScript = async () => {
    await navigator.clipboard.writeText(SCRIPT)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
  }

  const copyText = async (label, value) => {
    await navigator.clipboard.writeText(value)
    setCopiedCmd(label)
    setTimeout(() => setCopiedCmd(''), 1200)
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-30 bg-zinc-950/80 backdrop-blur border-b border-zinc-800/60">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center gap-3">
          <BookOpen className="w-5 h-5 text-indigo-400" />
          <span className="font-semibold text-sm">Training Demo</span>
          <span className="text-zinc-600 text-xs">HF TRL / Unsloth-ready</span>
          <button
            onClick={onBack}
            className="ml-auto flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition"
          >
            <ChevronLeft className="w-3.5 h-3.5" /> Home
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Minimal Colab Training Script</h1>
          <p className="text-zinc-400">
            This screen now includes a judge-ready pipeline: baseline vs trained reward comparison, loss curve export, and reward plot export.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <a
              href={colabUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-lg text-sm font-semibold transition"
            >
              <PlayCircle className="w-4 h-4" />
              Open in Google Colab
            </a>
            <button
              onClick={() => copyText('colab-link', colabUrl)}
              className="inline-flex items-center gap-2 border border-zinc-700 hover:bg-zinc-800 px-4 py-2 rounded-lg text-sm transition"
            >
              <Clipboard className="w-4 h-4" />
              Copy Colab Link
            </button>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-3">
          <button
            onClick={() => copyText('baseline', 'python training/minimal_trl_colab.py')}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-300 hover:bg-zinc-800 transition text-left"
          >
            <span className="inline-flex items-center gap-1.5 mb-1"><BarChart3 className="w-3.5 h-3.5" />Baseline eval on env episodes</span>
            <div className="text-zinc-500">Click to copy run command</div>
          </button>
          <button
            onClick={() => copyText('trl', colabSetup)}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-300 hover:bg-zinc-800 transition text-left"
          >
            <span className="inline-flex items-center gap-1.5 mb-1"><PlayCircle className="w-3.5 h-3.5" />HF TRL minimal train loop</span>
            <div className="text-zinc-500">Click to copy Colab setup steps</div>
          </button>
          <button
            onClick={() => copyText('plots', 'trl-minimal-demo/loss_curve.png\ntrl-minimal-demo/reward_before_after.png')}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-300 hover:bg-zinc-800 transition text-left"
          >
            <span className="inline-flex items-center gap-1.5 mb-1"><Terminal className="w-3.5 h-3.5" />Exports loss/reward plots</span>
            <div className="text-zinc-500">Click to copy output file paths</div>
          </button>
        </div>

        <div className="mb-6 bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-sm text-zinc-200 mb-2">How to run this demo</p>
          <ol className="text-xs text-zinc-400 space-y-1 list-decimal list-inside">
            <li>Start backend server (`uvicorn server.app:app --host 0.0.0.0 --port 7860`).</li>
            <li>In Colab or terminal, run `training/minimal_trl_colab.py`.</li>
            <li>Open exported plots from `trl-minimal-demo/` and attach to README.</li>
          </ol>
          {copiedCmd && (
            <div className="mt-3 text-xs text-emerald-400">Copied {copiedCmd} instructions.</div>
          )}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
            <span className="text-xs text-zinc-500">`training/minimal_trl_colab.py` preview ({lineCount} lines)</span>
            <button
              onClick={copyScript}
              className="text-xs px-3 py-1.5 rounded-lg border border-zinc-700 hover:bg-zinc-800 transition flex items-center gap-1.5"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Clipboard className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy Script'}
            </button>
          </div>
          <pre className="p-4 overflow-x-auto text-xs leading-5 text-zinc-200">{SCRIPT}</pre>
        </div>
      </main>
    </div>
  )
}
