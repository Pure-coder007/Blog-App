from datetime import datetime
# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flaskblog import db, login_manager, app
from flask_login import UserMixin
from sqlalchemy.sql import func


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True, passive_deletes=True)
    likes = db.relationship('Like', backref='user', lazy=True, passive_deletes=True)
    
# Sending the token for the reset of password which lasts 30 minutes
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    
# Verifying the reset token for when the user sends the token back to the app

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
    
    
    
    
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


# Creating a post class to hold our posts
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer,  db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    comments = db.relationship('Comment', backref='post', lazy=True, passive_deletes=True)
    likes = db.relationship('Like', backref='post', lazy=True, passive_deletes=True)
    user = db.relationship('User', backref='user_post', lazy=True, passive_deletes=True)
    
    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
    

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # Corrected ForeignKey
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete= 'CASCADE'), nullable=False)
    the_user = db.relationship('User', backref='user_comment', lazy=True, passive_deletes=True)

    
    
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # Corrected ForeignKey
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete= 'CASCADE'), nullable=False)


