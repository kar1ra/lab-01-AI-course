"""Part 3 -- calculate the cost of one support request."""

import argparse
import json
import sys
from pathlib import Path

from texts import LANGUAGES


DEFAULT_MEASUREMENTS = Path(__file__).with_name("measurements.json")

# GPT-5.6 Luna prices per 1 million tokens
INPUT_PRICE = 0.20
OUTPUT_PRICE = 1.20


def load_measurements(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(
            f"{path.name} not found. Run part2_measure.py first."
        )
    except json.JSONDecodeError as exc:
        sys.exit(f"{path.name} is not valid JSON: {exc}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--measurements",
        type=Path,
        default=DEFAULT_MEASUREMENTS,
    )
    parser.add_argument(
        "--requests-per-day",
        type=int,
        default=2000,
    )

    args = parser.parse_args()

    data = load_measurements(args.measurements)
    billed = data.get("one_request_billed")

    if not billed:
        sys.exit(
            "No real API measurements found. "
            "Run part2_measure.py --call first."
        )

    print("prices from OpenAI API")
    print("model:", data["model_id"])
    print("input price: $0.20 per 1M tokens")
    print("output price: $1.20 per 1M tokens")

    print("\nONE SUPPORT REQUEST -- tokens and cost")
    print("-" * 72)

    print(
        f"{'':<14}"
        + "".join(f"{lang.upper():>12}" for lang in LANGUAGES)
    )

    inputs = {
        lang: billed[lang]["input_tokens"]
        for lang in LANGUAGES
    }

    outputs = {
        lang: billed[lang]["output_tokens"]
        for lang in LANGUAGES
    }

    costs = {}

    for lang in LANGUAGES:
        input_cost = inputs[lang] / 1_000_000 * INPUT_PRICE
        output_cost = outputs[lang] / 1_000_000 * OUTPUT_PRICE
        costs[lang] = input_cost + output_cost

    print(
        f"{'input tokens':<14}"
        + "".join(f"{inputs[l]:>12}" for l in LANGUAGES)
    )

    print(
        f"{'output tokens':<14}"
        + "".join(f"{outputs[l]:>12}" for l in LANGUAGES)
    )

    print(
        f"{'cost, USD':<14}"
        + "".join(f"{costs[l]:>12.6f}" for l in LANGUAGES)
    )

    print(
        f"{'cost, cents':<14}"
        + "".join(f"{costs[l] * 100:>12.4f}" for l in LANGUAGES)
    )

    # Annual projection
    per_year = args.requests_per_day * 365

    print(
        f"\nAT {args.requests_per_day:,} REQUESTS/DAY "
        "-- US dollars per year"
    )
    print("-" * 72)

    print(
        f"{'':<14}"
        + "".join(f"{lang.upper():>12}" for lang in LANGUAGES)
    )

    yearly = {
        lang: costs[lang] * per_year
        for lang in LANGUAGES
    }

    print(
        f"{'yearly cost':<14}"
        + "".join(f"{yearly[l]:>12.2f}" for l in LANGUAGES)
    )

    # Ratios
    print("\nTWO RATIOS THAT ARE NOT THE SAME NUMBER")
    print("-" * 72)

    input_ratio = {
        lang: inputs[lang] / inputs["en"]
        for lang in LANGUAGES
    }

    total_ratio = {
        lang: costs[lang] / costs["en"]
        for lang in LANGUAGES
    }

    print(
        f"{'input only':<14}"
        + "".join(
            f"{input_ratio[l]:>11.2f}x"
            for l in LANGUAGES
        )
    )

    print(
        f"{'total bill':<14}"
        + "".join(
            f"{total_ratio[l]:>11.2f}x"
            for l in LANGUAGES
        )
    )

    print("\nTHE DIFFERENCE FROM ENGLISH")
    print("-" * 72)

    for lang in ("ru", "kk"):
        difference = yearly[lang] - yearly["en"]

        print(
            f"{lang.upper()} instead of EN: "
            f"${difference:,.2f}/year more "
            f"({total_ratio[lang]:.2f}x)"
        )


if __name__ == "__main__":
    main()
