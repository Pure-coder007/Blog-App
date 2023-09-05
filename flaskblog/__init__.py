import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv

# from flaskblog import app

load_dotenv()

app = Flask(__name__)
# Creating a secret key
app.config['SECRET_KEY'] = '1e04deb868b1640f313bbb8c680f3d49'
# Setting our location of our database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app) 
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
# Setting a message for a user wanting to access the account page without logging in first
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "easytransact.send@gmail.com"
app.config['MAIL_PASSWORD'] = 'hhdvxgezdtgoobgd'
mail = Mail(app)


from flaskblog import routes

# os.environ.get("EMAIL_USER"), os.environ.get("EMAIL_PASS")


print(type(os.getenv('EMAIL_USER')))
print(os.getenv('EMAIL_PASS'))

# Creating an instance of our database 
# with app.app_context():
#     db.create_all()

# app.app_context().push()
#         # db.create_all()
#     # app.run(debug=True)  
