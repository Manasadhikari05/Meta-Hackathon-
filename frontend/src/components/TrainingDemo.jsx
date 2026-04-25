import { useMemo, useState } from 'react'
import { ChevronLeft, Clipboard, Check, BookOpen } from 'lucide-react'

const SCRIPT = `# Minimal HF TRL training script for ContentModerationEnv
# Run in Colab after cloning this repository.

!pip install -q "trl>=0.9.6" "transformers>=4.43.0" "accelerate>=0.33.0" "datasets>=2.20.0" "peft>=0.12.0"
!pip install -q -r requirements.txt

import os
import requests
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import SFTConfig, SFTTrainer

BASE_URL = "http://127.0.0.1:7860"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"  # small for quick demo

def collect_rows(task_id="task2", max_steps=8):
    rows = []
    obs = requests.post(f"{BASE_URL}/reset", params={"task_id": task_id}, timeout=30).json()
    for _ in range(max_steps):
        prompt = (
            "You are a moderation model. Return JSON with decision, reason_code, severity, confidence, explanation.\\n\\n"
            f"Post: {obs['post']['content']}\\n"
            f"Author violations: {obs['author']['prior_violations']}\\n"
            f"Topic: {obs['thread_context']['topic']}"
        )
        target = '{"decision":"escalate","reason_code":"harassment","severity":"medium","confidence":0.6,"explanation":"borderline risk"}'
        rows.append({"text": f"<|user|>\\n{prompt}\\n<|assistant|>\\n{target}"})

        step = requests.post(
            f"{BASE_URL}/step",
            json={
                "decision": "escalate",
                "reason_code": "harassment",
                "severity": "medium",
                "confidence": 0.6,
                "explanation": "borderline risk",
            },
            timeout=30,
        ).json()
        if step["done"]:
            break
        obs = step["observation"]
    return rows

train_ds = Dataset.from_list(collect_rows(task_id="task2", max_steps=8))
print("Training rows:", len(train_ds))

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

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
print("Done: minimal TRL demo completed.")
`

export default function TrainingDemo({ onBack }) {
  const [copied, setCopied] = useState(false)
  const lineCount = useMemo(() => SCRIPT.split('\n').length, [])

  const copyScript = async () => {
    await navigator.clipboard.writeText(SCRIPT)
    setCopied(true)
    setTimeout(() => setCopied(false), 1200)
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
            This is a separate feature screen for judges to quickly verify that your OpenEnv environment can be trained with Hugging Face TRL.
          </p>
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
