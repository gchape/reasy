import os

import praw
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, session, request
from requests_oauthlib import OAuth2Session

load_dotenv()

CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

reddit = OAuth2Session(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=["identity", "read", "vote"])

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')


def create_reddit_client():
    return praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent='myapp',
                       username=session.get('username'), password=session.get('password'))


@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    authorization_url, state = reddit.authorization_url('https://www.reddit.com/api/v1/authorize')
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route('/reddit_callback')
def reddit_callback():
    state = session.get('oauth_state')

    reddit = OAuth2Session(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, state=state)
    token = reddit.fetch_token('https://www.reddit.com/api/v1/access_token', authorization_response=request.url,
                               client_secret=CLIENT_SECRET)

    session['oauth_token'] = token
    user = reddit.get('https://oauth.reddit.com/api/v1/me').json()
    session['username'] = user['name']
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    return f"Welcome {session['username']}! <br> <a href='/upvote'>Upvote Posts</a>"


@app.route('/upvote', methods=['POST', 'GET'])
def upvote_posts():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        post_urls = request.form.getlist('post_urls')
        reddit_client = create_reddit_client()

        for url in post_urls:
            try:
                post = reddit_client.submission(url=url)
                post.upvote()
            except Exception as e:
                return f"Error upvoting post: {str(e)}"

        return "All posts have been upvoted!"

    return '''
        <form method="post">
            <label for="post_urls">Enter Reddit Post URLs (separate by commas):</label><br>
            <textarea name="post_urls" rows="4" cols="50"></textarea><br>
            <button type="submit">Upvote</button>
        </form>
    '''


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
