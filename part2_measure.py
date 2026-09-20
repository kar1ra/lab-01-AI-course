import argparse
import json
import os
from pathlib import Path

import tiktoken
from dotenv import load_dotenv

from texts import CORPUS, LANGUAGES

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Keep this below the available API balance.
MAX_TOKENS = 1000

MODEL_MAP = {
    "claude-opus-5": "gpt-5.6-luna",
}

load_dotenv()


def get_tokenizer():
    return tiktoken.get_encoding("o200k_base")


def count_tokens(text):
    tokenizer = get_tokenizer()
    return len(tokenizer.encode(text))


def count_request_tokens(lang):
    tokenizer = get_tokenizer()

    system_tokens = tokenizer.encode(
        CORPUS["system_prompt"][lang]
    )
    complaint_tokens = tokenizer.encode(
        CORPUS["complaint"][lang]
    )

    return len(system_tokens) + len(complaint_tokens)


def openai_request(lang, model_id):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "error": "OPENAI_API_KEY was not found in .env"
        }

    import urllib.request

    url = OPENAI_URL

    payload = {
        "model": model_id,
        "max_completion_tokens": MAX_TOKENS,
        "messages": [
            {
                "role": "system",
                "content": CORPUS["system_prompt"][lang],
            },
            {
                "role": "user",
                "content": CORPUS["complaint"][lang],
            },
        ],
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))

    except Exception as e:
        return {
            "error": str(e)
        }

    answer = result["choices"][0]["message"]["content"]

    usage = result.get("usage", {})

    print(answer)

    return {
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--call", action="store_true")
    parser.add_argument("--model", default="claude-opus-5")

    args = parser.parse_args()

    model_id = MODEL_MAP.get(args.model, args.model)

    print("counting tokens with o200k_base (free, no model run)")

    counts = {}

    for corpus_name in ["sentence", "complaint", "system_prompt"]:
        counts[corpus_name] = {}

        for lang in LANGUAGES:
            n = count_tokens(CORPUS[corpus_name][lang])
            counts[corpus_name][lang] = n

        print(
            f"  {corpus_name:<14}"
            f"en={counts[corpus_name]['en']} "
            f"ru={counts[corpus_name]['ru']} "
            f"kk={counts[corpus_name]['kk']}"
        )

    request_tokens = {}

    for lang in LANGUAGES:
        request_tokens[lang] = count_request_tokens(lang)

    print(
        f"  {'request':<14}"
        f"en={request_tokens['en']} "
        f"ru={request_tokens['ru']} "
        f"kk={request_tokens['kk']} "
        "(system + complaint)"
    )

    billed = None

    if args.call:
        print(
            f"\nanswering the same complaint through OpenAI using {model_id}:"
        )

        billed = {}

        for lang in LANGUAGES:
            print(f"\n[{lang}]")

            result = openai_request(lang, model_id)

            if "error" in result:
                print(result["error"])
            else:
                billed[lang] = result

    output = {
        "model": args.model,
        "model_id": model_id,
        "token_counts": counts,
        "request_tokens": request_tokens,
        "one_request_billed": billed,
    }

    Path("measurements.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nwrote measurements.json")


if __name__ == "__main__":
    main()
