from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
import forms
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user, login_user, login_required, logout_user
import os

import secrets
from PIL import Image

db=SQLAlchemy()

def create_app():
    app = Flask(__name__)
    SECRET_KEY = os.urandom(32)
    app.config['SECRET_KEY'] = SECRET_KEY
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'notesDB.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

app = create_app()

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "index"
login_manager.login_message_category = "info"

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), unique=True, nullable=False)
    category = db.relationship("Category", back_populates="user")
    note = db.relationship("Note", foreign_keys="Note.user_id")
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("name", db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    note = db.relationship("Note", back_populates="category")
    
class Note(db.Model):
    __tablename__ = "note"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("Name", db.String)
    text = db.Column("Note Text", db.Text)
    photo = db.Column(db.String(20), nullable=True, default='default.png')
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False) 
    user = db.relationship("User", back_populates="note")  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'] )
def register():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('categories'))
    form = forms.RegisterForm()
    if form.validate_on_submit():
        password_code = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, email=form.email.data, password=password_code)
        db.session.add(user)
        db.session.commit()
        flash('Registration successfull! You can log in now.')
        return redirect(url_for('register'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('categories'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('categories'))
        else:
            flash('Login unsuccessfull. Check your email and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form = forms.CategoryForm()
    if form.validate_on_submit():
        new_category = Category(name=form.name.data, user_id=current_user.id)
        db.session.add(new_category)
        db.session.commit()
        return redirect(url_for('categories'))
    return render_template('categories.html', form=form, categories=categories)

@app.route('/addnote', methods=['GET', 'POST'])
@login_required
def addnote():
    form = forms.NoteWithCategoryForm()
    if form.validate_on_submit():
        new_note = Note(name = form.name.data, text = form.text.data, category_id = form.category.data.id, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
        flash('Note added successfully')
        return redirect(url_for('categories'))
    return render_template('addNote.html', form=form)

@app.route('/category/<int:category_id>/notes', methods=["GET", "POST"])
@login_required
def notes(category_id):
    category = Category.query.get_or_404(category_id)
    notes = Note.query.filter_by(category_id=category_id).all()
    form = forms.NoteForm()
    if category is None:
        return "Category not found", 404
    if form.validate_on_submit():
        add_note = Note(name=form.name.data,text=form.text.data, category_id=category_id, user_id=current_user.id)
        db.session.add(add_note)
        db.session.commit()
        return redirect(request.url)
    return render_template('notes.html',category=category, notes=notes, form=form)


@app.route('/category/<int:category_id>/update_category', methods=['GET', 'POST'])
@login_required
def update_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = forms.CategoryUpdateForm()
    if form.validate_on_submit():
        category.name = form.name.data
        db.session.commit()
        flash('Category name successfully updated', 'success')
        return redirect(url_for('categories'))
    elif request.method == 'GET':
        form.name.data = category.name
    return render_template('update_category.html',category=category, form=form)

@app.route('/delete/<int:id>', methods=['GET', 'POST','DELETE'])
@login_required
def category_delete(id):
    categoryDelete = Category.query.get_or_404(id)
    db.session.delete(categoryDelete)
    db.session.commit()
    flash('Category deleted successfully')
    return redirect(url_for('categories'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/notesPhotos', picture_fn)
    output_size = (250, 250)
    image = Image.open(form_picture)
    image.thumbnail(output_size)
    image.save(picture_path)
    return picture_fn

@app.route('/addnotephoto/<int:id>', methods=['GET', 'POST'])
@login_required
def addNotePhoto(id):
    noteid = Note.query.get_or_404(id)
    form = forms.AddNotePhotoForm()
    if form.validate_on_submit():
        if form.photo.data:
            photo = save_picture(form.photo.data)
            noteid.photo = photo
        db.session.commit()
        flash('Photo successfully added', 'success')
        return redirect(url_for('categories'))
    photo = url_for('static', filename='notesPhotos/' + noteid.photo)
    return render_template('addNotePhoto.html',noteid=noteid, form=form)
        
@app.route('/update_note/<int:note_id>', methods=['GET', 'POST'])
@login_required
def update_note(note_id):
    noteid = Note.query.get_or_404(note_id)
    form = forms.NoteUpdateForm()
    if form.validate_on_submit():
        if form.photo.data:
            photo = save_picture(form.photo.data)
            noteid.photo = photo
        noteid.name = form.name.data
        noteid.text = form.text.data
        db.session.commit()
        flash('Note successfully updated', 'success')
        return redirect(url_for('categories'))
    elif request.method == 'GET':
        form.name.data = noteid.name
        form.text.data = noteid.text
    return render_template('update_note.html',noteid=noteid, form=form)

@app.route('/<int:note_id>', methods=['GET', 'POST'])
@login_required
def photo(note_id):
    noteid = Note.query.get_or_404(note_id)
    photo1 = url_for('static', filename='notesPhotos/' + noteid.photo)
    return render_template('photo.html',noteid=noteid, photo=photo1)

@app.route('/delete/<int:id>/note', methods=['GET', 'POST','DELETE'])
@login_required
def note_delete(id):
    noteDelete = Note.query.get_or_404(id)
    db.session.delete(noteDelete)
    db.session.commit()
    flash('Note deleted successfully')
    return redirect(url_for('categories'))

@app.route('/search', methods=['POST'])
@login_required
def search():
    form = forms.SearchForm()
    notes = Note.query
    if form.validate_on_submit():
        searched = form.searched.data
        notes = notes.filter(Note.name.like('%' + searched + '%'))
        notes = notes.order_by(Note.name).all()
        return render_template("search.html", form=form, searched=searched, notes=notes)
    return render_template('index.html')
        
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))
        
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=True)