#!/usr/bin/env python3
"""
ResolveTrace — Golden Set Blind Manual Annotation Review Tool

This interactive CLI tool supports double-blind manual review of the 207-case
golden benchmark set to evaluate AgentActionExtractor against human judgment
without confirmation bias.

Usage:
  # Primary reviewer (all 207 cases in randomized order, incremental save):
  python scripts/review_golden_set.py

  # Second reviewer (random subset of 35 cases, saved to separate file):
  python scripts/review_golden_set.py --reviewer2

  # Inter-rater agreement analysis between Reviewer 1 and Reviewer 2:
  python scripts/review_golden_set.py --compare
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime, timezone
import pandas as pd
from sklearn.metrics import cohen_kappa_score

ACTION_CATEGORIES = [
    "REQUEST_INFO_AND_REDIRECT_DM",
    "REQUEST_INFORMATION",
    "PROVIDE_INSTRUCTIONS",
    "REDIRECT_DM",
    "PROVIDE_GENERAL_ASSISTANCE",
    "ESCALATE_INTERNAL",
    "CONFIRM_RESOLUTION",
    "CLOSING_COURTESY",
    "TROUBLESHOOT_REINSTALL",
    "TROUBLESHOOT_UPDATE",
    "TROUBLESHOOT_RESTART",
    "EXPLAIN_POLICY_OR_CATALOG"
]

GOLDEN_CSV_PATH = "data/golden/golden_set.csv"
TEST_CONVS_PATH = "data/processed/test_conversations.jsonl"
OUTPUT_R1_PATH = "artifacts/manual_review.csv"
OUTPUT_R2_PATH = "artifacts/manual_review_r2.csv"
ORDER_R1_PATH = "artifacts/.review_order_r1.json"
ORDER_R2_PATH = "artifacts/.review_order_r2.json"

def load_data():
    if not os.path.exists(GOLDEN_CSV_PATH):
        print(f"Error: Golden set not found at {GOLDEN_CSV_PATH}")
        sys.exit(1)

    df_golden = pd.read_csv(GOLDEN_CSV_PATH)

    # Load authentic historical agent replies
    agent_texts = {}
    if os.path.exists(TEST_CONVS_PATH):
        with open(TEST_CONVS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                cid = str(c.get("conversation_id"))
                ag_turns = [
                    t["text"] for t in c.get("turns", [])
                    if not t.get("inbound") and (t.get("author_id") == "SpotifyCares" or t.get("author_type") == "support")
                ]
                if ag_turns:
                    agent_texts[cid] = ag_turns[0]

    # Map agent text to golden rows
    records = []
    for _, row in df_golden.iterrows():
        cid = str(row["conversation_id"])
        if cid in agent_texts:
            raw_agent = agent_texts[cid]
        elif cid.startswith("EDGE_"):
            raw_agent = "[Synthetic Challenge Case — No historical Twitter agent reply. Expected action reflects canonical policy for this query]"
        else:
            raw_agent = "[Agent response text unavailable in test split]"

        records.append({
            "case_id": row["id"],
            "conversation_id": cid,
            "customer_message": row["customer_message"],
            "agent_message": raw_agent,
            "extractor_label": row["expected_action"],
            "intent": row["intent"]
        })

    return records

def print_menu():
    print("\n--- Standardized Support Actions ---")
    for i, act in enumerate(ACTION_CATEGORIES, 1):
        print(f"  [{i:2d}] {act}")
    print("  [ q] Save and Quit")
    print("-----------------------------------")

def prompt_human_label():
    while True:
        choice = input("\nEnter your action label (1-12, full name, or 'q' to quit): ").strip()
        if choice.lower() in ("q", "quit", "exit"):
            return "QUIT"

        # Check numeric selection
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(ACTION_CATEGORIES):
                return ACTION_CATEGORIES[idx - 1]
            print(f"Invalid number. Please enter 1 to {len(ACTION_CATEGORIES)}.")
            continue

        # Check exact or case-insensitive match
        upper_choice = choice.upper()
        if upper_choice in ACTION_CATEGORIES:
            return upper_choice

        # Partial search match
        matches = [a for a in ACTION_CATEGORIES if upper_choice in a]
        if len(matches) == 1:
            confirm = input(f"Did you mean '{matches[0]}'? [Y/n]: ").strip().lower()
            if confirm in ("", "y", "yes"):
                return matches[0]

        print("Action not recognized. Enter a number (1-12) or consult artifacts/annotation_guide.md.")

def compute_and_print_summary(csv_path: str):
    if not os.path.exists(csv_path):
        print("No completed reviews found.")
        return

    df = pd.read_csv(csv_path)
    if len(df) == 0:
        print("Review file is empty.")
        return

    n_total = len(df)
    n_agreed = int((df["agreement"] == "AGREE").sum())
    n_overridden = int((df["agreement"] == "OVERRIDE").sum())
    agree_pct = (n_agreed / n_total) * 100

    print("\n" + "=" * 70)
    print(f"MANUAL REVIEW SUMMARY ({csv_path})")
    print("=" * 70)
    print(f"Total Cases Reviewed:  {n_total}")
    print(f"Human-Extractor Match: {n_agreed} ({agree_pct:.1f}%)")
    print(f"Human Overrides:       {n_overridden} ({(n_overridden / n_total) * 100:.1f}%)")

    # Cohen's Kappa
    try:
        kappa = cohen_kappa_score(df["human_label"], df["extractor_label"])
        print(f"Cohen's Kappa (κ):     {kappa:.4f}")
        if kappa >= 0.81:
            k_desc = "Almost Perfect Agreement"
        elif kappa >= 0.61:
            k_desc = "Substantial Agreement"
        elif kappa >= 0.41:
            k_desc = "Moderate Agreement"
        elif kappa >= 0.21:
            k_desc = "Fair Agreement"
        else:
            k_desc = "Slight / Poor Agreement"
        print(f"Agreement Level:       {k_desc}")
    except Exception as e:
        print(f"Cohen's Kappa calculation error: {e}")

    # Breakdown of overrides
    overrides_df = df[df["agreement"] == "OVERRIDE"]
    if len(overrides_df) > 0:
        print("\n--- Top Disagreements (Extractor vs Human) ---")
        pairs = overrides_df.groupby(["extractor_label", "human_label"]).size().reset_index(name="count")
        pairs = pairs.sort_values(by="count", ascending=False)
        for _, r in pairs.head(10).iterrows():
            print(f"  {r['count']:2d} cases: Extractor = {r['extractor_label']}  -->  Human = {r['human_label']}")

        print("\n--- Sample Override Rationales ---")
        sample_reasons = overrides_df[overrides_df["override_reason"].notna() & (overrides_df["override_reason"].str.strip() != "")].head(5)
        for _, r in sample_reasons.iterrows():
            print(f"  [{r['case_id']}] Extractor: {r['extractor_label']} | Human: {r['human_label']}")
            print(f"       Reason: {r['override_reason']}")

    print("=" * 70 + "\n")

def run_compare():
    if not os.path.exists(OUTPUT_R1_PATH) or not os.path.exists(OUTPUT_R2_PATH):
        print(f"Both {OUTPUT_R1_PATH} and {OUTPUT_R2_PATH} must exist to run inter-rater comparison.")
        print("Please ensure Reviewer 1 and Reviewer 2 have labeled cases.")
        return

    df1 = pd.read_csv(OUTPUT_R1_PATH)
    df2 = pd.read_csv(OUTPUT_R2_PATH)

    merged = pd.merge(df1, df2, on="case_id", suffixes=("_r1", "_r2"))
    n_overlap = len(merged)
    if n_overlap == 0:
        print("No overlapping reviewed cases found between Reviewer 1 and Reviewer 2.")
        return

    n_agreed = int((merged["human_label_r1"] == merged["human_label_r2"]).sum())
    agree_pct = (n_agreed / n_overlap) * 100
    kappa = cohen_kappa_score(merged["human_label_r1"], merged["human_label_r2"])

    print("\n" + "=" * 70)
    print("INTER-RATER RELIABILITY ANALYSIS (Reviewer 1 vs Reviewer 2)")
    print("=" * 70)
    print(f"Overlapping Cases Evaluated: {n_overlap}")
    print(f"Inter-Rater Agreement:       {n_agreed} / {n_overlap} ({agree_pct:.1f}%)")
    print(f"Inter-Rater Cohen's Kappa:   {kappa:.4f}")

    disagreements = merged[merged["human_label_r1"] != merged["human_label_r2"]]
    if len(disagreements) > 0:
        print("\n--- Inter-Rater Disagreements ---")
        for _, r in disagreements.iterrows():
            print(f"  Case: {r['case_id']}")
            print(f"    Customer: \"{r['customer_message_r1'][:70]}...\"")
            print(f"    Reviewer 1: {r['human_label_r1']}")
            print(f"    Reviewer 2: {r['human_label_r2']}")
            print(f"    Extractor:  {r['extractor_label_r1']}")
    print("=" * 70 + "\n")

def main():
    parser = argparse.ArgumentParser(description="ResolveTrace Golden Set Blind Review Tool")
    parser.add_argument("--reviewer2", action="store_true", help="Review a 35-case random subset as second reviewer")
    parser.add_argument("--compare", action="store_true", help="Compare Reviewer 1 and Reviewer 2 inter-rater reliability")
    parser.add_argument("--summary", action="store_true", help="Print summary of existing review file and exit")
    args = parser.parse_args()

    if args.compare:
        run_compare()
        return

    output_csv = OUTPUT_R2_PATH if args.reviewer2 else OUTPUT_R1_PATH
    order_file = ORDER_R2_PATH if args.reviewer2 else ORDER_R1_PATH
    reviewer_title = "REVIEWER 2 (SUBSET MODE)" if args.reviewer2 else "PRIMARY REVIEWER (FULL 207 SET)"

    if args.summary:
        compute_and_print_summary(output_csv)
        return

    all_records = load_data()

    # Determine subset or full set
    if args.reviewer2:
        # Deterministic 35-case sample with fixed seed
        rng = random.Random(42)
        target_records = rng.sample(all_records, 35)
    else:
        target_records = all_records

    # Maintain consistent random permutation across sessions
    if os.path.exists(order_file):
        with open(order_file, "r", encoding="utf-8") as f:
            saved_order = json.load(f)
        id_to_rec = {r["case_id"]: r for r in target_records}
        ordered_records = [id_to_rec[cid] for cid in saved_order if cid in id_to_rec]
        # Append any newly added cases
        ordered_records += [r for r in target_records if r["case_id"] not in saved_order]
    else:
        ordered_records = list(target_records)
        rng = random.Random(1337 if not args.reviewer2 else 42)
        rng.shuffle(ordered_records)
        os.makedirs(os.path.dirname(order_file), exist_ok=True)
        with open(order_file, "w", encoding="utf-8") as f:
            json.dump([r["case_id"] for r in ordered_records], f)

    # Load existing progress
    reviewed_ids = set()
    if os.path.exists(output_csv):
        df_existing = pd.read_csv(output_csv)
        reviewed_ids = set(df_existing["case_id"].astype(str))

    remaining = [r for r in ordered_records if r["case_id"] not in reviewed_ids]

    print("=" * 75)
    print(f"RESOLVETRACE BLIND ANNOTATION REVIEW TOOL — {reviewer_title}")
    print("=" * 75)
    print(f"Target Output:      {output_csv}")
    print(f"Total in Scope:     {len(ordered_records)}")
    print(f"Already Completed:  {len(reviewed_ids)}")
    print(f"Remaining to Label: {len(remaining)}")
    print("\n[Protocol Rules]")
    print("  1. Label independently based on artifacts/annotation_guide.md.")
    print("  2. Extractor label is hidden until AFTER you input your label.")
    print("  3. Progress is saved immediately after each case. Resume anytime.")
    print("=" * 75)

    if not remaining:
        print("\nAll cases in this set have been reviewed!")
        compute_and_print_summary(output_csv)
        return

    input("\nPress Enter to begin review session...")
    print_menu()

    total_done = len(reviewed_ids)

    try:
        for idx, case in enumerate(remaining, 1):
            total_done += 1
            progress_str = f"[{total_done} / {len(ordered_records)}]"

            print("\n" + "#" * 75)
            print(f"CASE {case['case_id']}  {progress_str}  (Thread ID: {case['conversation_id']})")
            print("#" * 75)
            print("\n[CUSTOMER TWEET]")
            print(f"  \"{case['customer_message']}\"")
            print("\n[HISTORICAL AGENT REPLY]")
            print(f"  \"{case['agent_message']}\"")
            print("-" * 75)

            # Step 1: Blind Human Label
            human_label = prompt_human_label()
            if human_label == "QUIT":
                print("\nReview session paused. Progress has been saved.")
                break

            # Step 2: Unblind Extractor Label
            extractor_label = case["extractor_label"]
            match_str = "MATCH" if human_label == extractor_label else "DISCREPANCY"
            print(f"\n---> Extractor Label: [{extractor_label}] ({match_str})")
            print(f"---> Your Label:      [{human_label}]")

            # Step 3: Confirm Agree vs Override
            if human_label == extractor_label:
                default_choice = "A"
                prompt_text = "Confirm agreement? [A]gree / [O]verride: "
            else:
                default_choice = "O"
                prompt_text = "Different from extractor. Confirm? [O]verride / [A]gree with extractor: "

            decision_input = input(prompt_text).strip().upper()
            if decision_input == "":
                decision_input = default_choice

            if decision_input.startswith("A"):
                agreement = "AGREE"
                reason = ""
            else:
                agreement = "OVERRIDE"
                reason = input("Enter one-line rationale for override: ").strip()

            # Step 4: Incremental Persistence
            new_row = {
                "case_id": case["case_id"],
                "conversation_id": case["conversation_id"],
                "customer_message": case["customer_message"],
                "agent_message": case["agent_message"],
                "human_label": human_label,
                "extractor_label": extractor_label,
                "agreement": agreement,
                "override_reason": reason,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }

            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            df_row = pd.DataFrame([new_row])
            header = not os.path.exists(output_csv)
            df_row.to_csv(output_csv, mode="a", header=header, index=False)
            print(f"Saved {case['case_id']} -> {agreement}")

    except KeyboardInterrupt:
        print("\n\nReview interrupted by user. Progress saved.")

    compute_and_print_summary(output_csv)

if __name__ == "__main__":
    main()
