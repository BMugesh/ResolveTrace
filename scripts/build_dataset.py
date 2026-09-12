import os
import sys
import argparse
import time
import pandas as pd
import yaml

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.reconstruct import ConversationReconstructor
from src.data.loader import ConversationLoader

def build_dataset():
    parser = argparse.ArgumentParser(description="Build SpotifyCares reconstructed conversation dataset and temporal splits.")
    parser.add_argument("--sample", action="store_true", help="Build on a 500-thread sample for fast testing")
    args = parser.parse_args()

    start_time = time.time()
    print("=" * 70)
    print(f"BUILDING SPOTIFYCARES DATASET (Mode: {'SAMPLE' if args.sample else 'FULL'})")
    print("=" * 70)

    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Use spotify_cares_filtered_threads.csv if present for instant load, or twcs/twcs.csv
    filtered_csv = config['paths']['spotify_filtered_csv']
    if os.path.exists(filtered_csv):
        print(f"Loading filtered brand records from {filtered_csv}...")
        df = pd.read_csv(filtered_csv)
    else:
        raw_csv = config['paths']['raw_twcs_csv']
        print(f"Loading raw TWCS from {raw_csv}...")
        df = pd.read_csv(raw_csv)

    reconstructor = ConversationReconstructor(brand_name="SpotifyCares")
    print("Reconstructing conversation threads...")
    conversations, included_indices = reconstruct_creator = reconstructor.reconstruct_from_dataframe(df)

    if args.sample:
        conversations = conversations[:500]
        print(f"Subsampled to {len(conversations)} threads for fast execution.")

    print(f"Reconstructed {len(conversations):,} total conversation threads.")

    # Save full processed dataset
    output_jsonl = config['paths']['processed_conversations_jsonl']
    ConversationLoader.save_jsonl(conversations, output_jsonl)
    print(f"Saved complete corpus to {output_jsonl}")

    # Perform temporal leakage-safe splitting
    train_convs, val_convs, test_convs = ConversationLoader.temporal_split(
        conversations,
        train_ratio=config['splits']['train_ratio'],
        val_ratio=config['splits']['val_ratio'],
        test_ratio=config['splits']['test_ratio']
    )

    train_path = config['paths']['train_conversations_jsonl']
    val_path = config['paths']['val_conversations_jsonl']
    test_path = config['paths']['test_conversations_jsonl']

    ConversationLoader.save_jsonl(train_convs, train_path)
    ConversationLoader.save_jsonl(val_convs, val_path)
    ConversationLoader.save_jsonl(test_convs, test_path)

    print(f"Saved Train Split ({len(train_convs):,} convs) -> {train_path}")
    print(f"Saved Validation Split ({len(val_convs):,} convs) -> {val_path}")
    print(f"Saved Test Split ({len(test_convs):,} convs) -> {test_path}")

    # Also save a sample CSV for quick inspection
    sample_csv_path = config['paths']['sample_threads_csv']
    os.makedirs(os.path.dirname(sample_csv_path), exist_ok=True)
    sample_tids = [turn['tweet_id'] for c in conversations[:100] for turn in c['turns']]
    df_sample = df[df['tweet_id'].isin(sample_tids)]
    df_sample.to_csv(sample_csv_path, index=False)
    print(f"Saved quick-inspection sample CSV to {sample_csv_path} ({len(df_sample)} rows)")

    print(f"\nDataset build completed in {time.time() - start_time:.2f}s")

if __name__ == '__main__':
    build_dataset()
