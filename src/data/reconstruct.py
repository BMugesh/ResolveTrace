import pandas as pd
import numpy as np
from collections import defaultdict, deque
from typing import List, Dict, Any, Tuple, Set

class ConversationReconstructor:
    """
    Reconstructs complete conversation threads for a specific support brand
    by following response_tweet_id / in_response_to_tweet_id chains.
    Enforces strict conversation tree validity:
      1. Root message must exist and be inbound (customer opening message).
      2. No broken intermediate parent links.
      3. Turns are ordered chronologically.
    """
    def __init__(self, brand_name: str = "SpotifyCares"):
        self.brand_name = brand_name

    def reconstruct_from_dataframe(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Set[int]]:
        tweet_ids = df['tweet_id'].values
        author_ids = df['author_id'].values
        inbounds = df['inbound'].values
        texts = df['text'].fillna('').values
        created_ats = df['created_at'].values
        parent_ids = df['in_response_to_tweet_id'].fillna(-1).astype(np.int64).values
        
        id_to_idx = {tid: i for i, tid in enumerate(tweet_ids)}
        parent_to_children = defaultdict(list)
        for i in range(len(tweet_ids)):
            p = parent_ids[i]
            if p != -1:
                parent_to_children[p].append(tweet_ids[i])

        brand_indices = np.where(author_ids == self.brand_name)[0]
        brand_tids = tweet_ids[brand_indices]

        # Find valid roots
        valid_roots = set()
        for tid in brand_tids:
            curr = tid
            broken = False
            visited = set()
            while True:
                if curr not in id_to_idx:
                    broken = True
                    break
                idx = id_to_idx[curr]
                p = parent_ids[idx]
                if p == -1:
                    break
                if p in visited:
                    broken = True
                    break
                visited.add(p)
                curr = p

            if broken:
                continue

            root_idx = id_to_idx[curr]
            if not inbounds[root_idx]:
                continue

            valid_roots.add(curr)

        # Build thread objects
        conversations = []
        all_included_indices = set()

        for root_id in valid_roots:
            queue = deque([root_id])
            thread_tids = []
            visited = set()

            while queue:
                curr = queue.popleft()
                if curr in visited:
                    continue
                visited.add(curr)
                if curr not in id_to_idx:
                    continue
                thread_tids.append(curr)

                for child in parent_to_children.get(curr, []):
                    if child in id_to_idx:
                        c_idx = id_to_idx[child]
                        if inbounds[c_idx] or author_ids[c_idx] == self.brand_name:
                            queue.append(child)

            has_brand = any(author_ids[id_to_idx[t]] == self.brand_name for t in thread_tids)
            if not has_brand:
                continue

            # Assemble turns chronologically
            turns = []
            for tid in thread_tids:
                idx = id_to_idx[tid]
                all_included_indices.add(idx)
                turns.append({
                    "tweet_id": int(tweet_ids[idx]),
                    "author_id": str(author_ids[idx]),
                    "author_type": "customer" if inbounds[idx] else "support",
                    "inbound": bool(inbounds[idx]),
                    "timestamp": str(created_ats[idx]),
                    "text": str(texts[idx]),
                    "in_response_to_tweet_id": int(parent_ids[idx]) if parent_ids[idx] != -1 else None
                })

            conversations.append({
                "conversation_id": str(root_id),
                "brand": self.brand_name,
                "root_tweet_id": int(root_id),
                "num_turns": len(turns),
                "opening_timestamp": turns[0]["timestamp"],
                "turns": turns
            })

        return conversations, all_included_indices
