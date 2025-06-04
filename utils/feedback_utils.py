from pymongo import MongoClient
from collections import Counter

client = MongoClient('mongodb://localhost:27017/')  # Replace with your actual MongoDB URI
db = client['AIRA_NEW_DB']  # Replace with your actual DB name

def get_feedback_summary():
    """
    Return overall counts of likes and dislikes with some example comments aggregated
    across all users.
    """
    all_feedback_docs = list(db["feedback"].find())
    likes_count = 0
    dislikes_count = 0
    like_comments = []
    dislike_comments = []

    for doc in all_feedback_docs:
        for fb in doc.get('feedback', []):
            if fb.get('feedback_type') == 'like':
                likes_count += 1
                like_comments.extend([c['text'] for c in fb.get('comments', []) if c.get('text')])
            elif fb.get('feedback_type') == 'dislike':
                dislikes_count += 1
                dislike_comments.extend([c['text'] for c in fb.get('comments', []) if c.get('text')])

    # Optionally limit comments displayed for summary (e.g., top 5 each)
    like_comments = like_comments[:5]
    dislike_comments = dislike_comments[:5]

    return {
        "likes_count": likes_count,
        "dislikes_count": dislikes_count,
        "like_comments": like_comments,
        "dislike_comments": dislike_comments,
    }


def get_user_feedback(user_id):
    """
    Return all feedback (likes and dislikes) with comments for a specific user.
    """
    doc = db["feedback"].find_one({"_id": user_id})
    if not doc:
        return {
            "likes": [],
            "dislikes": []
        }

    likes = []
    dislikes = []

    for fb in doc.get('feedback', []):
        fb_type = fb.get('feedback_type')
        comments = [c['text'] for c in fb.get('comments', []) if c.get('text')]
        if fb_type == 'like':
            likes.append({
                "response_id": fb.get('response_id'),
                "comments": comments,
                "timestamp": fb.get('timestamp')
            })
        elif fb_type == 'dislike':
            dislikes.append({
                "response_id": fb.get('response_id'),
                "comments": comments,
                "timestamp": fb.get('timestamp')
            })

    return {
        "likes": likes,
        "dislikes": dislikes,
    }
