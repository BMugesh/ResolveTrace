import re
from typing import Dict, Any

class RuleBasedIntentClassifier:
    """
    Deterministic rule-based intent classifier grounded in SpotifyCares empirical support patterns.
    """
    @staticmethod
    def classify(text: str) -> str:
        t = text.lower()
        
        # 1. Billing / Premium Payment / Refunds
        if re.search(r'\b(premium|billed|charge|charged|refund|subscription|payment|card|pay|invoice|receipt|cost|price|double charge|unauthorized|auto-renew|renewed)\b', t):
            if re.search(r'\b(student|hulu|showtime|sheerid|unidays)\b', t):
                return 'STUDENT_DISCOUNT_HULU'
            if re.search(r'\b(family|family plan|invited|address|relative|members)\b', t):
                return 'FAMILY_PLAN_SETUP'
            return 'SUBSCRIPTION_BILLING_PREMIUM'
            
        # 2. Student Discount / Hulu Bundle
        if re.search(r'\b(student|hulu|showtime|discount|sheerid|unidays|student discount|re-verify|reverify)\b', t):
            return 'STUDENT_DISCOUNT_HULU'
            
        # 3. Family Plan Management
        if re.search(r'\b(family plan|family account|invited to family|invite link|error code 3|address verification|home address)\b', t):
            return 'FAMILY_PLAN_SETUP'
            
        # 4. Account Access / Password / Hacked
        if re.search(r'\b(login|log in|password|reset password|account|email|username|facebook login|locked|hacked|credentials|verification email)\b', t):
            return 'ACCOUNT_ACCESS_AUTH'
            
        # 5. Offline Sync & Downloads
        if re.search(r'\b(offline|download|downloads|downloaded|sync|songs not downloading|local files|greyed out offline)\b', t):
            return 'OFFLINE_SYNC_DOWNLOADS'
            
        # 6. Playback / Audio Streaming
        if re.search(r'\b(play|playback|pause|skipping|skip|stop|stops|buffering|greyed|grayed|sound|audio|volume|stream|streaming|quality|distortion|static|stops playing)\b', t):
            return 'PLAYBACK_STREAMING_AUDIO'
            
        # 7. App Instability / Bug / Crash
        if re.search(r'\b(crash|crashes|crashing|freeze|freezing|slow|lag|glitch|bug|error code|blank screen|black screen|closes|unresponsive)\b', t):
            return 'APP_CRASH_BUG'
            
        # 8. Playlist / Library / Catalog Search
        if re.search(r'\b(playlist|playlists|library|saved songs|liked|album|artist|queue|shuffle|search|sort|release radar|discover weekly|catalog|discography)\b', t):
            return 'PLAYLIST_LIBRARY_CATALOG'
            
        # 9. Device Integration / Bluetooth / Connect
        if re.search(r'\b(connect|bluetooth|speaker|chromecast|alexa|echo|car|carplay|android auto|smart tv|ps4|xbox|sonos|receiver|soundbar)\b', t):
            return 'DEVICE_INTEGRATION_CONNECT'
            
        # 10. Artist / Song Submission
        if re.search(r'\b(artist profile|distributor|upload|aggregator|put my music|submit music|artist dashboard|spotify for artists|independent artist)\b', t):
            return 'ARTIST_CONTENT_INQUIRY'
            
        # 11. Ambiguous / Short
        if len(t.strip()) < 10 or t.strip() in ['@spotifycares', 'help', '@spotifycares help', 'spotify', 'hello']:
            return 'AMBIGUOUS_INQUIRY'
            
        # 12. General Inquiry / Feedback
        return 'GENERAL_INQUIRY_FEEDBACK'
