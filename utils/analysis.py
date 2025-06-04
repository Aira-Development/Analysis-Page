from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import Counter
from bson.objectid import ObjectId

client = MongoClient('mongodb://localhost:27017/')  # Replace with your actual MongoDB URI
db = client['AIRA_NEW_DB']  # Replace with your actual DB name


from datetime import datetime, timedelta
from collections import Counter

def get_dashboard_summary():
    today = datetime.utcnow().date()
    seven_days_ago = today - timedelta(days=7)

    users = list(db["users"].find())
    journals = list(db["journal"].find())
    sentiments = list(db["sentiment"].find())
    feedbacks = list(db["feedback"].find())

    # --- total users ---
    total_users = len(users)

    # --- new registrations today ---
    new_registrations_today = sum(
        1 for user in users 
        if 'created_at' in user and 
           (user['created_at'].date() if isinstance(user['created_at'], datetime) else datetime.fromisoformat(user['created_at']).date()) == today
    )

    # --- active users today (from journals) ---
    active_users_today = sum(
        any(journal['date'] == today.isoformat() for journal in user_doc.get('journals', []))
        for user_doc in journals
    )

    # --- dropout count (users inactive for last 7 days) ---
    # Assume users have a 'last_active' datetime field or infer from journals or sentiments.
    # If no last_active, fallback to last journal date or last sentiment date

    def get_last_active(user):
        # Try last_active field first
        if 'last_active' in user:
            return user['last_active'] if isinstance(user['last_active'], datetime) else datetime.fromisoformat(user['last_active'])
        
        # fallback: latest journal date
        user_journals = [j for j in journals if j.get('user_id') == user['_id']]
        journal_dates = [datetime.fromisoformat(j['date']) for j in user_journals if 'date' in j]
        if journal_dates:
            return max(journal_dates)
        
        # fallback: latest sentiment date
        user_sentiments = [doc for doc in sentiments if doc.get('user_id') == user['_id']]
        sentiment_dates = []
        for doc in user_sentiments:
            for s in doc.get('sentiments', []):
                if 'date' in s:
                    sentiment_dates.append(datetime.fromisoformat(s['date']))
        if sentiment_dates:
            return max(sentiment_dates)
        
        return None

    dropout_count = 0
    for user in users:
        last_active_dt = get_last_active(user)
        if last_active_dt is None or last_active_dt.date() < seven_days_ago:
            dropout_count += 1

    # --- most common mood today ---

    moods = [s['emotional_state'] for s in sum([doc['sentiments'] for doc in sentiments], [])]
    most_common_mood = Counter(moods).most_common(1)[0][0] if moods else "Neutral"
    
    # --- average mental score today ---
    scores = [s['mental_score'] for s in sum([doc['sentiments'] for doc in sentiments], [])]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    # --- overall usage ---
    total_messages_sent = 0
    user_hours_map = {}  # user_id -> total seconds spent

    for user_doc in journals:  # Assuming you're iterating through user documents
        user_id = user_doc.get('user_id')
        journals = user_doc.get('journals', [])
        
        for journal_entry in journals:
            # Count messages - now properly checking the messages array
            messages = journal_entry.get('messages', [])
            if isinstance(messages, list):
                total_messages_sent += len(messages)
            else:
                # fallback: count 1 message per journal entry if messages is not a list
                total_messages_sent += 1

            # Calculate duration in seconds from created_at timestamps if available
            if messages and len(messages) >= 2:
                try:
                    # First message timestamp
                    first_msg = messages[0]
                    # Last message timestamp
                    last_msg = messages[-1]
                    
                    start_dt = datetime.fromisoformat(first_msg['created_at'].replace("Z", "+00:00"))
                    print(f"Start datetime: {start_dt}")
                    end_dt = datetime.fromisoformat(last_msg['created_at'].replace("Z", "+00:00"))
                    duration = (end_dt - start_dt).total_seconds()
                    print(f"End datetime: {end_dt}, Duration: {duration} seconds")
                    if duration < 0:
                        duration = 0
                except Exception:
                    duration = 0
            else:
                # fallback: estimate 30 mins (1800 seconds) per journal if no timestamps
                duration = 1800

            if user_id:
                user_hours_map[user_id] = user_hours_map.get(user_id, 0) + duration

    total_seconds_app_used = sum(user_hours_map.values())
    total_hours_app_used = round(total_seconds_app_used / 3600, 2)
    avg_hours_app_used = round(total_hours_app_used / total_users, 2) if total_users > 0 else 0

    def calculate_feedback_stats(users):
        total_likes = 0
        total_dislikes = 0
        user_count = len(users)
        
        for user in users:
            # Count likes/dislikes from feedback array
            uid = ObjectId(user['_id'])
            print(f"Processing user ID: {uid}")
            feedback_doc = next((s for s in feedbacks if s['_id'] == uid), None)

            if not feedback_doc or not feedback_doc.get('feedback'):
                continue

            for feedback in feedback_doc["feedback"]:
                if feedback.get('feedback_type') == 'like':
                    total_likes += 1
                elif feedback.get('feedback_type') == 'dislike':
                    total_dislikes += 1
            
            # Count ratings from daily_feedbacks (assuming 4-5 stars = like, 1-3 = dislike)
            for daily_feedback in feedback_doc["daily_feedbacks"]:
                rating = daily_feedback.get('rating', 0)
                if rating >= 4:
                    total_likes += 1
                elif rating >= 1:  # Explicit check to avoid counting 0 ratings
                    total_dislikes += 1
        
        # Calculate averages
        avg_likes = round(total_likes / user_count, 2) if user_count > 0 else 0
        avg_dislikes = round(total_dislikes / user_count, 2) if user_count > 0 else 0
        
        return {
            "total_likes": total_likes,
            "total_dislikes": total_dislikes,
            "avg_likes_per_user": avg_likes,
            "avg_dislikes_per_user": avg_dislikes,
            "total_feedback": total_likes + total_dislikes
        }

    feedback_stats = calculate_feedback_stats(users)

    return {
        'total_users': total_users,
        'new_registrations_today': new_registrations_today,
        'active_users_today': active_users_today,
        'dropout_count': dropout_count,
        'most_common_mood': most_common_mood,
        'avg_mental_score': avg_score,
        'overall_usage': {
            'total_messages_sent': total_messages_sent,
            'total_hours_app_used': total_hours_app_used,
            'avg_hours_app_used': avg_hours_app_used,
        },
        'feedback_stats': feedback_stats
    }

def get_mental_health_data():
    sentiments = list(db["sentiment"].find())
    users = list(db["users"].find())
    user_data = []

    # print(f"Total users: {len(users)}, Total sentiment docs: {len(sentiments)}")

    for user in users:
        uid = str(user['_id'])
        name = user.get('username', 'Unknown')
        streak = user.get('streak', 0)

        # Get sentiment entry for user
        sentiment_doc = next((s for s in sentiments if s['user_id'] == uid), None)
        if not sentiment_doc or not sentiment_doc.get('sentiments'):
            continue

        user_sentiments = sentiment_doc['sentiments']
        sorted_sentiments = sorted(user_sentiments, key=lambda x: x['date'])

        latest_score = sorted_sentiments[-1]['mental_score']
        if len(sorted_sentiments) >= 2:
            score_diff = latest_score - sorted_sentiments[-2]['mental_score']
        else:
            score_diff = 0

        common_mood = Counter([s['emotional_state'] for s in user_sentiments]).most_common(1)[0][0]

        user_data.append({
            'username': name,
            'user_id': uid,
            'current_score': round(latest_score, 2),
            'score_diff': round(score_diff, 2),
            'streak': streak,
            'common_mood': common_mood
        })

    # Sort by users with most decline in mental health
    user_data = sorted(user_data, key=lambda x: x['score_diff'])
    return user_data

def get_usage_data():
    journals = list(db["journal"].find())
    users = list(db["users"].find())
    usage_stats = []

    for user in users:
        uid = str(user['_id'])
        name = user['username']

        # Find total messages sent by user
        user_journal = next((doc for doc in journals if doc['user_id'] == uid), None)
        if not user_journal:
            continue

        total_messages = sum(
            1 for journal in user_journal.get('journals', [])
            for msg in journal.get('messages', []) if msg['role'] == 'User'
        )

        last_active = max(
            (msg['created_at'] for journal in user_journal.get('journals', []) for msg in journal.get('messages', []) if msg['role'] == 'User'),
            default="N/A"
        )

        usage_stats.append({
            'username': name,
            'user_id': uid,
            'total_messages': total_messages,
            'last_active': last_active
        })

    usage_stats = sorted(usage_stats, key=lambda x: x['total_messages'], reverse=True)
    return usage_stats