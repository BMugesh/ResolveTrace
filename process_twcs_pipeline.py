import pandas as pd
import numpy as np
import re
import time
import os
from collections import defaultdict, deque, Counter

def run_pipeline():
    start_time = time.time()
    print("=" * 70)
    print("STARTING TWCS CONVERSATION EXTRACTION PIPELINE")
    print("=" * 70)
    
    # ---------------------------------------------------------
    # STEP 0: Load and index the TWCS dataset
    # ---------------------------------------------------------
    dataset_path = 'twcs/twcs.csv'
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
        
    print(f"\n[1/5] Loading raw TWCS dataset from {dataset_path}...")
    df = pd.read_csv(
        dataset_path,
        dtype={'tweet_id': np.int64, 'author_id': str, 'inbound': bool, 'text': str, 'response_tweet_id': str},
        keep_default_na=True
    )
    raw_row_count = len(df)
    print(f"Loaded {raw_row_count:,} total rows in {time.time() - start_time:.2f}s")
    
    # Extract numpy arrays for fast indexing
    tweet_ids = df['tweet_id'].values
    author_ids = df['author_id'].values
    inbounds = df['inbound'].values
    texts = df['text'].fillna('').values
    created_ats = df['created_at'].values
    parent_ids = df['in_response_to_tweet_id'].fillna(-1).astype(np.int64).values
    
    print("Building lookup indices...")
    id_to_idx = {tid: i for i, tid in enumerate(tweet_ids)}
    
    # Parent -> children adjacency list
    parent_to_children = defaultdict(list)
    for i in range(raw_row_count):
        p = parent_ids[i]
        if p != -1:
            parent_to_children[p].append(tweet_ids[i])
            
    print(f"Lookup indices created in {time.time() - start_time:.2f}s")
    
    # ---------------------------------------------------------
    # Helper Classification Functions
    # ---------------------------------------------------------
    
    def extract_device_type(text):
        t = text.lower()
        if re.search(r'\b(iphone|ipod)\b', t):
            return 'iPhone'
        elif re.search(r'\b(ipad)\b', t):
            return 'iPad'
        elif re.search(r'\b(macbook|mac|imac|macos|osx|mac mini|mac pro)\b', t):
            return 'Mac'
        elif re.search(r'\b(apple watch|iwatch|watchos)\b', t):
            return 'Apple Watch'
        elif re.search(r'\b(apple tv|appletv|tvos)\b', t):
            return 'Apple TV'
        elif re.search(r'\b(android|samsung|galaxy|pixel|huawei|xiaomi|nexus|oneplus|lg|motorola|xperia|htc)\b', t):
            return 'Android'
        elif re.search(r'\b(windows|win10|win11|win8|pc|laptop|desktop|surface)\b', t):
            return 'Windows/PC'
        elif re.search(r'\b(speaker|bluetooth|echo|alexa|sonos|carplay|android auto|headphone|earbuds|airpod|airpods|headset|soundbar|stereo)\b', t):
            return 'Audio/Accessory'
        elif re.search(r'\b(ps4|ps5|playstation|xbox|roku|smart tv|chromecast)\b', t):
            return 'Smart TV/Console'
        return 'Unspecified'

    def classify_apple_intent(text):
        t = text.lower()
        if re.search(r'\b(battery|drain|dying|drainage|percentage|charge|charging|charger|overheat|overheating|hot)\b', t):
            return 'BATTERY_CHARGING_POWER'
        elif re.search(r'\b(update|updated|updating|ios\s*\d+|11\.\d+|ios11|upgrade|upgraded)\b', t) and re.search(r'\b(slow|lag|freeze|freezing|stuck|bug|glitch|broke|terrible|ruined|sucks|worst|horrible|drains)\b', t):
            return 'OS_UPDATE_DEGRADATION'
        elif re.search(r'\b(crash|crashes|crashing|freeze|freezing|froze|stuck|closes|unresponsive|hang|black screen|white screen|spinning)\b', t):
            return 'APP_CRASH_FREEZE'
        elif re.search(r'\b(apple id|appleid|icloud|itunes account|password|passcode|login|log in|locked out|2fa|verification code|security question|two-factor)\b', t):
            return 'ACCOUNT_APPLEID_ICLOUD'
        elif re.search(r'\b(screen|display|touch|digitizer|touchscreen|cracked|broken screen|lines|face id|touch id|fingerprint|sensor|camera|mic|speaker|headphone jack)\b', t):
            return 'HARDWARE_DISPLAY_SENSOR'
        elif re.search(r'\b(wifi|wi-fi|bluetooth|cellular|lte|3g|4g|5g|signal|service|no service|carrier|airdrop|hotspot|connect|connection|network)\b', t):
            return 'CONNECTIVITY_NETWORK_WIFI'
        elif re.search(r'\b(music|apple music|playlist|songs|tracks|album|artist|itunes store|app store download|downloading)\b', t):
            return 'MEDIA_MUSIC_STORE'
        elif re.search(r'\b(keyboard|typing|key|autocorrect|letter [a-z]|predictive|notification|notifications|badge|lock screen|widget)\b', t):
            return 'KEYBOARD_NOTIFICATIONS_UI'
        elif re.search(r'\b(billing|billed|charge|charged|subscription|refund|receipt|purchase|payment|credit card|apple pay|money|overcharged)\b', t):
            return 'BILLING_PAYMENT_SUBSCRIPTION'
        elif re.search(r'\b(how do i|how to|how can i|is it possible|settings|move to ios|transfer|setup|backup|restore|sync)\b', t):
            return 'HOW_TO_SETTINGS_FEATURE'
        elif len(t.strip()) < 10 or t.strip() in ['@applesupport', 'help', '@applesupport help']:
            return 'AMBIGUOUS_INQUIRY'
        else:
            return 'GENERAL_TECHNICAL_ISSUE'

    def classify_spotify_intent(text):
        t = text.lower()
        if re.search(r'\b(premium|billed|charge|charged|refund|subscription|payment|card|pay|invoice|receipt|cost|price|double charge|unauthorized)\b', t):
            return 'SUBSCRIPTION_BILLING_PREMIUM'
        elif re.search(r'\b(student|hulu|showtime|discount|sheerid|unidays|student discount)\b', t):
            return 'STUDENT_DISCOUNT_HULU'
        elif re.search(r'\b(family|family plan|family account|invited|invite|address|sub-account|member)\b', t):
            return 'FAMILY_PLAN_SETUP'
        elif re.search(r'\b(login|log in|password|reset password|account|email|username|facebook login|locked|hacked|credentials)\b', t):
            return 'ACCOUNT_ACCESS_AUTH'
        elif re.search(r'\b(play|playback|pause|skipping|skip|stop|stops|buffering|greyed|grayed|sound|audio|volume|stream|streaming|quality|distortion|static)\b', t):
            return 'PLAYBACK_STREAMING_AUDIO'
        elif re.search(r'\b(offline|download|downloads|downloaded|sync|songs not downloading)\b', t):
            return 'OFFLINE_SYNC_DOWNLOADS'
        elif re.search(r'\b(crash|crashes|crashing|freeze|freezing|slow|lag|glitch|bug|error code|blank screen|black screen|closes)\b', t):
            return 'APP_CRASH_BUG'
        elif re.search(r'\b(playlist|playlists|library|saved songs|liked|album|artist|queue|shuffle|search|sort|release radar|discover weekly)\b', t):
            return 'PLAYLIST_LIBRARY_CATALOG'
        elif re.search(r'\b(connect|bluetooth|speaker|chromecast|alexa|echo|car|carplay|android auto|smart tv|ps4|xbox|sonos|receiver)\b', t):
            return 'DEVICE_INTEGRATION_CONNECT'
        elif re.search(r'\b(artist profile|distributor|upload|aggregator|put my music|submit music|artist dashboard|spotify for artists)\b', t):
            return 'ARTIST_CONTENT_INQUIRY'
        elif len(t.strip()) < 10 or t.strip() in ['@spotifycares', 'help', '@spotifycares help']:
            return 'AMBIGUOUS_INQUIRY'
        else:
            return 'GENERAL_INQUIRY_FEEDBACK'

    def classify_agent_action(text):
        t = text.lower()
        has_dm = bool(re.search(r'\b(dm|direct message|private message|pm)\b', t)) or ('t.co' in t and ('dm' in t or 'gdrqu22ypt' in t or 'ldfdzrinat' in t or 'join us in a dm' in t))
        has_question = '?' in t or bool(re.search(r'\b(which|what|could you let us know|let us know|tell us|send us|share|confirm|are you on|have you tried|can you check)\b', t))
        has_restart = bool(re.search(r'\b(restart|reboot|turn off and on|power cycle|force restart|turn your device off)\b', t))
        has_update = bool(re.search(r'\b(update|latest version|update to|ios 11|app store|play store|latest update)\b', t)) and not bool(re.search(r'\b(since the update|after the update|with the update)\b', t))
        has_reinstall = bool(re.search(r'\b(clean reinstall|reinstall|uninstall and reinstall|delete and reinstall|delete the app|re-install)\b', t))
        has_instruction = bool(re.search(r'\b(settings\s*>|tap|select|go to|click|check out|steps|guide|article|try this|head over to|here\'s how)\b', t)) or ('http' in t and not has_dm)
        has_catalog = bool(re.search(r'\b(music licensing|content availability|rights|licensing agreements|pass that suggestion|catalog|distributor|aggregator)\b', t))
        has_escalate = bool(re.search(r'\b(escalat|backstage|specialist|pass.*team|engineering team|investigat|look into this backstage|look into this with our team)\b', t))
        has_resolution = bool(re.search(r'\b(glad to hear|great to hear|happy that helped|all sorted|glad.*working|glad.*fixed|awesome news)\b', t))
        has_courtesy = bool(re.search(r'\b(you\'re welcome|no problem|anytime|just give us a shout|we\'re here for you|happy to help|have a great day|have a good one)\b', t))

        if has_resolution:
            return 'CONFIRM_RESOLUTION'
        elif has_reinstall:
            return 'TROUBLESHOOT_REINSTALL'
        elif has_restart:
            return 'TROUBLESHOOT_RESTART'
        elif has_update and ('try' in t or 'ensure' in t or 'make sure' in t or 'update' in t):
            return 'TROUBLESHOOT_UPDATE'
        elif has_catalog:
            return 'EXPLAIN_POLICY_OR_CATALOG'
        elif has_dm and has_question:
            return 'REQUEST_INFO_AND_REDIRECT_DM'
        elif has_dm:
            return 'REDIRECT_DM'
        elif has_escalate:
            return 'ESCALATE_INTERNAL'
        elif has_instruction:
            return 'PROVIDE_INSTRUCTIONS'
        elif has_question:
            return 'REQUEST_INFORMATION'
        elif has_courtesy:
            return 'CLOSING_COURTESY'
        else:
            return 'PROVIDE_GENERAL_ASSISTANCE'

    def extract_state_flags(cumulative_customer_texts, current_turn_idx, previous_agent_texts):
        combined_cust_text = " ".join(cumulative_customer_texts).lower()
        combined_agent_text = " ".join(previous_agent_texts).lower()
        
        has_device = extract_device_type(combined_cust_text) != 'Unspecified'
        has_version = bool(re.search(r'\b(\d+\.\d+(\.\d+)?|ios\s*\d+|android\s*\d+|version\s*\d+)\b', combined_cust_text))
        has_error = bool(re.search(r'\b(error|code|message|screenshot|alert|popup|failed|says)\b', combined_cust_text))
        has_detail = len(combined_cust_text.split()) >= 8
        info_provided = bool(has_device or has_version or has_error or has_detail)
        
        troubleshoot_attempted = bool(re.search(r'\b(tried|already tried|restarted|rebooted|reinstalled|reset|cleared cache|uninstalled|updated|done all)\b', combined_cust_text))
        issue_recurring = bool(re.search(r'\b(still|again|keeps|repeatedly|every time|always|constantly|everyday|for days|since yesterday|won\'t stop)\b', combined_cust_text))
        billing_related = bool(re.search(r'\b(charged|charge|billed|billing|subscription|refund|receipt|invoice|payment|money|cost|price|card)\b', combined_cust_text))
        device_type = extract_device_type(combined_cust_text)
        os_version_provided = has_version
        app_version_provided = bool(re.search(r'\b(version\s*\d+\.\d+|v\d+\.\d+|spotify\s*version|app\s*version)\b', combined_cust_text))
        error_message_provided = has_error
        sentiment_frustrated = bool(re.search(r'\b(frustrat|angry|annoy|pissed|hate|sucks|terrible|horrible|useless|worst|ridiculous|wtf|fucking|broken|ruined|crap|shit|fix this)\b', combined_cust_text)) or ('!' in combined_cust_text and ('why' in combined_cust_text or 'never' in combined_cust_text))
        channel_dm_redirected = bool(re.search(r'\b(dm|direct message|pm)\b', combined_agent_text))
        is_ambiguous = len(combined_cust_text.strip()) < 15 or bool(re.search(r'^[^\x00-\x7F]+$', combined_cust_text))
        
        return {
            'info_provided': info_provided,
            'troubleshoot_attempted': troubleshoot_attempted,
            'issue_recurring': issue_recurring,
            'billing_related': billing_related,
            'device_type': device_type,
            'os_version_provided': os_version_provided,
            'app_version_provided': app_version_provided,
            'error_message_provided': error_message_provided,
            'sentiment_frustrated': sentiment_frustrated,
            'channel_dm_redirected': channel_dm_redirected,
            'turn_index': current_turn_idx,
            'is_ambiguous': is_ambiguous
        }

    def infer_thread_outcome(thread_nodes, brand_name):
        all_cust_texts = [n['text'] for n in thread_nodes if n['inbound']]
        all_agent_texts = [n['text'] for n in thread_nodes if n['author_id'] == brand_name]
        
        if not all_agent_texts:
            return 'UNRESOLVED_OPEN'
            
        last_cust_text = all_cust_texts[-1].lower() if all_cust_texts else ""
        last_agent_text = all_agent_texts[-1].lower() if all_agent_texts else ""
        
        resolved_signals = bool(re.search(r'\b(fixed it|works now|working now|it worked|that worked|sorted now|resolved|all good now|thanks that helped|brilliant thanks|worked thanks|got it working)\b', last_cust_text))
        if resolved_signals:
            return 'RESOLVED'
            
        agent_confirmed_res = bool(re.search(r'\b(glad to hear|great to hear.*fixed|happy to help.*working|glad.*sorted)\b', last_agent_text))
        if agent_confirmed_res:
            return 'RESOLVED'
            
        likely_resolved_signals = bool(re.search(r'\b(thank you|thanks|thx|cheers|awesome thanks|appreciate it|ok thanks|will do|got it thanks|understood)\b', last_cust_text)) and not bool(re.search(r'\b(not working|still|didn\'t work|doesn\'t work|error|fail|why)\b', last_cust_text))
        if likely_resolved_signals and len(thread_nodes) >= 3:
            return 'LIKELY_RESOLVED'
            
        escalated_signals = bool(re.search(r'\b(dm|direct message|private message|backstage|specialist|pass.*team|engineering)\b', last_agent_text))
        if escalated_signals:
            return 'ESCALATED'
            
        return 'UNRESOLVED_OPEN'

    # ---------------------------------------------------------
    # STEP 1 & 2: Process AppleSupport & SpotifyCares
    # ---------------------------------------------------------
    
    def process_brand(brand_name, classify_intent_fn):
        print(f"\n=======================================================")
        print(f"PROCESSING BRAND: {brand_name}")
        print(f"=======================================================")
        
        brand_indices = np.where(author_ids == brand_name)[0]
        brand_tids = tweet_ids[brand_indices]
        print(f"Total outbound tweets for {brand_name}: {len(brand_tids):,}")
        
        # Step 2: Trace to valid customer root tweets
        print("Tracing conversation threads to customer root tweets...")
        valid_roots = set()
        broken_count = 0
        non_inbound_root_count = 0
        
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
                broken_count += 1
                continue
                
            root_idx = id_to_idx[curr]
            if not inbounds[root_idx]:
                non_inbound_root_count += 1
                continue
                
            valid_roots.add(curr)
            
        print(f"Valid root customer tweets identified: {len(valid_roots):,}")
        print(f"Discarded broken fragments: {broken_count:,}")
        print(f"Discarded non-inbound root tweets: {non_inbound_root_count:,}")
        
        # Step 1 & 2: Reconstruct complete thread trees and collect filtered rows
        print("Reconstructing thread trees and collecting filtered rows...")
        brand_filtered_indices = set()
        reconstructed_threads = []
        
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
                        if inbounds[c_idx] or author_ids[c_idx] == brand_name:
                            queue.append(child)
                            
            has_brand = any(author_ids[id_to_idx[t]] == brand_name for t in thread_tids)
            if has_brand:
                thread_records = []
                for t in thread_tids:
                    idx = id_to_idx[t]
                    thread_records.append({
                        'tweet_id': tweet_ids[idx],
                        'author_id': author_ids[idx],
                        'inbound': inbounds[idx],
                        'created_at': created_ats[idx],
                        'text': str(texts[idx]),
                        'response_tweet_id': df.at[idx, 'response_tweet_id'] if pd.notna(df.at[idx, 'response_tweet_id']) else '',
                        'in_response_to_tweet_id': int(parent_ids[idx]) if parent_ids[idx] != -1 else np.nan,
                        'df_index': idx
                    })
                    brand_filtered_indices.add(idx)
                    
                reconstructed_threads.append(thread_records)
                
        print(f"Reconstructed valid complete threads: {len(reconstructed_threads):,}")
        print(f"Total rows in filtered brand dataset (Step 1): {len(brand_filtered_indices):,}")
        
        # Step 3 & 4: Per-Turn Extraction and Thread Outcome Inference
        print("Extracting per-turn structure (Intent, State, Action) and Thread Outcomes...")
        turn_structure_rows = []
        
        for thread in reconstructed_threads:
            root_rec = thread[0]
            root_id = root_rec['tweet_id']
            root_text = root_rec['text']
            
            cust_opening_texts = [n['text'] for n in thread if n['inbound']]
            primary_intent = classify_intent_fn(cust_opening_texts[0] if cust_opening_texts else root_text)
            thread_outcome = infer_thread_outcome(thread, brand_name)
            
            cum_cust_texts = []
            cum_agent_texts = []
            agent_turn_idx = 0
            
            for node in thread:
                if node['inbound']:
                    cum_cust_texts.append(node['text'])
                elif node['author_id'] == brand_name:
                    agent_turn_idx += 1
                    agent_tid = node['tweet_id']
                    agent_text = node['text']
                    
                    state_dict = extract_state_flags(cum_cust_texts, agent_turn_idx, cum_agent_texts)
                    action_label = classify_agent_action(agent_text)
                    is_turn_ambiguous = state_dict['is_ambiguous'] or (primary_intent == 'AMBIGUOUS_INQUIRY') or (action_label == 'PROVIDE_GENERAL_ASSISTANCE')
                    last_cust_msg = cum_cust_texts[-1] if cum_cust_texts else ""
                    
                    turn_structure_rows.append({
                        'thread_root_id': root_id,
                        'agent_tweet_id': agent_tid,
                        'turn_index': agent_turn_idx,
                        'intent': primary_intent,
                        'info_provided': state_dict['info_provided'],
                        'troubleshoot_attempted': state_dict['troubleshoot_attempted'],
                        'issue_recurring': state_dict['issue_recurring'],
                        'billing_related': state_dict['billing_related'],
                        'device_type': state_dict['device_type'],
                        'os_version_provided': state_dict['os_version_provided'],
                        'app_version_provided': state_dict['app_version_provided'],
                        'error_message_provided': state_dict['error_message_provided'],
                        'sentiment_frustrated': state_dict['sentiment_frustrated'],
                        'channel_dm_redirected': state_dict['channel_dm_redirected'],
                        'action': action_label,
                        'outcome': thread_outcome,
                        'is_ambiguous': is_turn_ambiguous,
                        'customer_text': last_cust_msg,
                        'agent_text': agent_text
                    })
                    
                    cum_agent_texts.append(agent_text)
                    
        turn_df = pd.DataFrame(turn_structure_rows)
        print(f"Extracted {len(turn_df):,} support-agent turn records.")
        
        filtered_indices_sorted = sorted(list(brand_filtered_indices))
        filtered_df = df.iloc[filtered_indices_sorted].copy()
        
        return filtered_df, turn_df, reconstructed_threads

    apple_filtered_df, apple_turn_df, apple_threads = process_brand('AppleSupport', classify_apple_intent)
    spotify_filtered_df, spotify_turn_df, spotify_threads = process_brand('SpotifyCares', classify_spotify_intent)
    
    # ---------------------------------------------------------
    # STEP 5: Export CSV Files
    # ---------------------------------------------------------
    print("\n[5/5] Exporting output CSV files...")
    
    apple_filtered_path = 'apple_support_filtered_threads.csv'
    spotify_filtered_path = 'spotify_cares_filtered_threads.csv'
    apple_filtered_df.to_csv(apple_filtered_path, index=False)
    spotify_filtered_df.to_csv(spotify_filtered_path, index=False)
    print(f"Saved: {apple_filtered_path} ({len(apple_filtered_df):,} rows)")
    print(f"Saved: {spotify_filtered_path} ({len(spotify_filtered_df):,} rows)")
    
    apple_turn_path = 'apple_support_turn_structure.csv'
    spotify_turn_path = 'spotify_cares_turn_structure.csv'
    apple_turn_df.to_csv(apple_turn_path, index=False)
    spotify_turn_df.to_csv(spotify_turn_path, index=False)
    print(f"Saved: {apple_turn_path} ({len(apple_turn_df):,} rows)")
    print(f"Saved: {spotify_turn_path} ({len(spotify_turn_df):,} rows)")
    
    # ---------------------------------------------------------
    # Generate Statistical Reporting
    # ---------------------------------------------------------
    def print_brand_report(brand_name, filtered_df, turn_df, threads):
        print(f"\n=======================================================")
        print(f"SUMMARY REPORT: {brand_name}")
        print(f"=======================================================")
        print(f"Total Filtered Dataset Rows (Step 1): {len(filtered_df):,}")
        print(f"Total Reconstructed Conversation Threads (Step 2): {len(threads):,}")
        print(f"Total Support-Agent Turns Extracted (Step 3 & 5): {len(turn_df):,}")
        
        lengths = [len(t) for t in threads]
        print(f"Thread Length (Tweets per thread) - Min: {min(lengths)}, Max: {max(lengths)}, Mean: {np.mean(lengths):.2f}, Median: {np.median(lengths):.0f}")
        
        print(f"\n--- Customer Intent Frequency Distribution ---")
        intent_counts = turn_df['intent'].value_counts()
        for intent, count in intent_counts.items():
            pct = count / len(turn_df) * 100
            print(f"  {intent:35s}: {count:6,} ({pct:5.1f}%)")
            
        print(f"\n--- Agent Action Frequency Distribution ---")
        action_counts = turn_df['action'].value_counts()
        for action, count in action_counts.items():
            pct = count / len(turn_df) * 100
            print(f"  {action:35s}: {count:6,} ({pct:5.1f}%)")
            
        print(f"\n--- Inferred Thread Outcome Frequency Distribution ---")
        print("  (Note: Outcomes are inferred from conversational behavior, not dataset ground truth)")
        outcome_counts = turn_df['outcome'].value_counts()
        for outcome, count in outcome_counts.items():
            pct = count / len(turn_df) * 100
            print(f"  {outcome:35s}: {count:6,} ({pct:5.1f}%)")
            
        print(f"\n--- Conversation State Key Metrics ---")
        print(f"  Info Provided              : {turn_df['info_provided'].sum():6,} ({turn_df['info_provided'].mean()*100:5.1f}%)")
        print(f"  Troubleshoot Already Tried : {turn_df['troubleshoot_attempted'].sum():6,} ({turn_df['troubleshoot_attempted'].mean()*100:5.1f}%)")
        print(f"  Issue Recurring            : {turn_df['issue_recurring'].sum():6,} ({turn_df['issue_recurring'].mean()*100:5.1f}%)")
        print(f"  Billing Related            : {turn_df['billing_related'].sum():6,} ({turn_df['billing_related'].mean()*100:5.1f}%)")
        print(f"  Frustrated Customer Sentiment: {turn_df['sentiment_frustrated'].sum():6,} ({turn_df['sentiment_frustrated'].mean()*100:5.1f}%)")
        print(f"  Ambiguous Turns Flagged    : {turn_df['is_ambiguous'].sum():6,} ({turn_df['is_ambiguous'].mean()*100:5.1f}%)")
        
        print(f"\n--- Top Device Types Identified ---")
        dev_counts = turn_df['device_type'].value_counts()
        for dev, count in dev_counts.items():
            pct = count / len(turn_df) * 100
            print(f"  {dev:25s}: {count:6,} ({pct:5.1f}%)")

    print_brand_report('AppleSupport', apple_filtered_df, apple_turn_df, apple_threads)
    print_brand_report('SpotifyCares', spotify_filtered_df, spotify_turn_df, spotify_threads)
    
    elapsed = time.time() - start_time
    print(f"\n" + "=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print("=" * 70)

if __name__ == '__main__':
    run_pipeline()
