import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail, cloudinary
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm
from flaskblog.models import User, Post, Like, Comment
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message




# with app.app_context():
#     db.create_all()





# Route for our home page
@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=4)
    return render_template("home.html", posts=posts, )



# Route for our about page
@app.route("/about")
def about():
    return render_template("about.html", title='About')



# Route for our register page
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
# Showing a flashed message if the registration is successful
    if form.validate_on_submit():
# Hashing a password before saving it to the database
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # Creating a new instance of a user
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('You account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


# Route for our login page
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
# Showing a flashed message if the login is validated correctly
        user = User.query.filter_by(email=form.email.data).first()
    # Checking if username and password is valid before user can be logged in
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
    # Making sure the user logs in first before accessing the "account" page
            next_page = request.args.get('next')
            flash(f"{user.username} You have been successfully logged in", 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)




# Route for logging out
@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('home'))



# Creating a save profile picture function
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile pics', picture_fn)
    
    # Resizing the image file of our profile picture 
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    

    return picture_fn
    
    
    
# Route for the account page
@app.route('/account',  methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
# Auto-filling the account details in ourr account page
    if form.validate_on_submit():
        if form.picture.data:
    # Calling the save profile picture function
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
# Setting a profile picture
    image_file = url_for('static', filename='profile pics/' + current_user.image_file)
    return render_template('account.html',
                            title='Account', image_file=image_file, form=form)
    
    
# Creating a new post
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    image_url = None

    if form.validate_on_submit():
        try:
            # Attempt to upload the image to Cloudinary
            if 'image' in request.files and request.files['image']:
                image = request.files['image']
                upload_result = cloudinary.uploader.upload(image)
                image_url = upload_result.get('secure_url')

            # Create a new post with the provided data
            post = Post(
                title=form.title.data,
                content=form.content.data,
                author=current_user,
                image_url=image_url
            )

            db.session.add(post)
            db.session.commit()

            flash('Your post has been created', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            flash(f"Error creating post: {str(e)}", 'error')

    return render_template('create_post.html', title='New Post', form=form, legend='New Post', image_url=image_url)


# Getting all posts or error if no post is found
@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


# Updating a post
@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='UpdatePost')



# Deleting a post 
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))




# Getting the current user total post when clicked upon
@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=4)
    return render_template("user_posts.html", posts=posts, user=user)



def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f''' To reset your password, visit the the following link: {url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
    '''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('A reset password email has been sent to you', 'success')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)



@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
# Hashing a password before saving it to the database
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        flash('You password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)



@app.route('/like-post/<post_id>', methods=['GET'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id)
    like = Like.query.filter_by(author=current_user.id, post_id=post_id).first()
    if not post:
        flash('Post does not exist', 'error')
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
    return redirect(url_for('home', post_id=post_id))
    
    
@app.route("/create-comment/<int:post_id>", methods=['POST'])
@login_required 
def create_comment(post_id):
    text = request.form.get('text')
    
    if not text:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('home'))
    else:
        post = Post.query.filter_by(id = post_id)
    
        if post:
            comment = Comment(text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
            flash('Comment added successfully!', 'success')
            return redirect(url_for('home'))
        else: 
            flash('Post does not exist.', 'error')
            
        return redirect(url_for('home'))
    
    # comment = Comment(text=text, author=current_user.id, post_id=post_id)
    
    




@app.route('/delete-comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Check if current user is the comment author or the post creator
    # if current_user.id == comment.the_user or current_user.id == comment.post.author:

    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'success')
    # else:
    #     flash('You do not have the permission to delete this comment.', 'danger')
    
    return redirect(url_for('home')) # Redirect to the appropriate view.
