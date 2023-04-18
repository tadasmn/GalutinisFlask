from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
from wtforms_sqlalchemy.fields import QuerySelectField
import app
from app import current_user

from flask_wtf.file import FileField,FileAllowed

def category_query():
    return app.User.query.get(current_user.id).category

def get_pk(obj):
    return str(obj)

class RegisterForm(FlaskForm):
    name = StringField('Name', [DataRequired()])
    email = StringField('Email', [DataRequired(), Email()])
    password = PasswordField('Password', [DataRequired()])
    confirmed_password = PasswordField("Repeat password", [EqualTo('password', 'Passwords do not match')])
    submit = SubmitField("Register")

    def validate_name(self, name):
        user = app.User.query.filter_by(name=name.data).first()
        if user:
            raise ValidationError('User already in use')
        
    def validate_email(self, email):
        user = app.User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already in use')
        
class LoginForm(FlaskForm):
    email = StringField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    submit = SubmitField('Login')
    
class CategoryForm(FlaskForm):
    name = StringField('Name of category', [DataRequired()])
    submit = SubmitField('Add new category')
    
class NoteForm(FlaskForm):
    name = StringField('Name of Note', [DataRequired()])
    text = TextAreaField('Note text', [DataRequired()])
    submit = SubmitField('Add new note')
    
class NoteWithCategoryForm(FlaskForm):
    name = StringField('Name of note', [DataRequired()])
    text = TextAreaField('Note text', [DataRequired()])
    category = QuerySelectField(query_factory=category_query, allow_blank=False, get_label="name", get_pk=get_pk)
    submit = SubmitField('Add Note')
    
class CategoryUpdateForm(FlaskForm):
    name = StringField('New Category Name', [DataRequired()])
    submit = SubmitField('Update')
            
class AddNotePhotoForm(FlaskForm):
    photo = FileField('', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Add Photo')
    
class NoteUpdateForm(FlaskForm):
    name = StringField('Name', [DataRequired()])
    text = TextAreaField('Note text', [DataRequired()])
    photo = FileField('Update photo', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')
            
class SearchForm(FlaskForm):
    searched = StringField('Searched', [DataRequired()])
    submit = SubmitField('Submit')