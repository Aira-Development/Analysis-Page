from flask import Flask
from routes.dashboard import dashboard_bp
from routes.analysis import analysis_bp
from routes.users import user_bp
from routes.feedback import feedback_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(user_bp)
app.register_blueprint(feedback_bp)

# Home route redirecting to dashboard
@app.route('/')
def home():
    return '<h2>Welcome to AIRA Analytics Dashboard</h2><p><a href="/dashboard">Go to Dashboard</a></p>'

if __name__ == '__main__':
    app.run(debug=True)
