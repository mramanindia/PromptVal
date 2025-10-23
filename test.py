#!/usr/bin/env python3
import json
from promptval import analyze_prompt, PromptValConfig

TEXT = """I want a car, it should be under 100K, look between range of 100K to 200K"""

CFG = PromptValConfig(
    provider="openai",       # or "anthropic", "gemini", "xai", "openai_compatible"
    model="gpt-4o-mini",
    temperature=0.0,
    timeout=30.0,
    base_url=None,           # set if using openai_compatible
)

def main():
    result = analyze_prompt(TEXT, config=CFG)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()