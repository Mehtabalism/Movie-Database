from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired
import requests

API_KEY = "6001a0e43f7c263249bfb05b7fcdde30"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String, unique=False, nullable=False)
    rating = db.Column(db.Float, unique=False, nullable=False)
    ranking = db.Column(db.Integer, unique=False, nullable=False)
    review = db.Column(db.String, unique=False, nullable=True)
    img_url = db.Column(db.String, unique=False, nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'

db.create_all()

class EditForm(FlaskForm):
    new_rating = FloatField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    new_review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    new_movie_title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for movie in all_movies:
        movie.ranking = len(all_movies) - all_movies.index(movie)
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route('/edit/<movie_id>', methods=["GET", "POST"])
def edit(movie_id):
    edit_form = EditForm()
    movie_to_update = Movie.query.get(movie_id)
    if edit_form.validate_on_submit():
        movie_to_update.rating = edit_form.new_rating.data
        movie_to_update.review = edit_form.new_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=edit_form, movie=movie_to_update)


@app.route('/delete', methods=["GET", "POST"])
def delete():
    movie_id = request.args.get('movie_id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        # api_parameters = {'api_key': API_KEY}
        # response = requests.get(url='https://api.themoviedb.org/3/authentication/guest_session/new', params=api_parameters)
        # response.raise_for_status()

        movie_parameters = {'api_key': API_KEY,
                            'query': add_form.new_movie_title.data,
                            'include_adult': 'false',
                            'language': 'en-US'}
        response = requests.get(url='https://api.themoviedb.org/3/search/movie', params=movie_parameters)
        response.raise_for_status()
        data = response.json()
        return render_template('select.html', found_movies=data['results'])
    return render_template('add.html', form=add_form)


@app.route('/fetch', methods=["GET", "POST"])
def fetch():
    movie_id = request.args.get('id')
    parameters = {'api_key': API_KEY,
                  'language': 'en-US'}
    response = requests.get(url=f'https://api.themoviedb.org/3/movie/{movie_id}', params=parameters)
    response.raise_for_status()
    data = response.json()

    new_movie = Movie(
        title=data['title'],
        year=int(data['release_date'].split('-')[0]),
        description=data['overview'],
        rating=100,
        ranking=100,
        review="None",
        img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', movie_id=Movie.query.filter_by(title=data['title']).first().id))


if __name__ == '__main__':
    app.run(debug=True)
