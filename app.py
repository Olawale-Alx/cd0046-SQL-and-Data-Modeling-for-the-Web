#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm, Form
from sqlalchemy import func
from forms import *
from flask_migrate import Migrate
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    # This is the model object for the venue table
    __tablename__ = 'venue'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    genres = db.Column(db.PickleType, nullable=False)
    address = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String(500), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    venue_shows = db.relationship('Show', backref='venue', lazy=True, cascade='all, delete')

    def __repr__(self):
      return f'<Venue {self.id} {self.name} {self.city}>'


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(200))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(300))
    image_link = db.Column(db.String(500))
    artist_shows = db.relationship('Show', backref='artist', lazy=True, cascade='all, delete')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
  __tablename__ = 'show'

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', ondelete='CASCADE'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', ondelete='CASCADE'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  # show_venues = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  show_venues = db.session.query(Venue.city, Venue.state).distinct()

  venues_arr = []

  for venue in show_venues:
    venue = dict(zip(('city', 'state'), venue))
    venue['venues'] = []
    venue_req = db.session.query(Venue).filter_by(city=venue['city'], state=venue['state']).all()
    for venue_information in venue_req:
      venue_shows = Show.query.filter_by(venue_id=venue_information.id).all()
      venue_information = {'id': venue_information.id, 'name': venue_information.name, 'num_upcoming_shows': len(upcoming_venue_shows(venue_shows))}
      venue['venues'].append(venue_information)
    venues_arr.append(venue)

  return render_template('pages/venues.html', show_venues=venues_arr);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    'search_venue': []}

  venues_search = db.session.query(Venue.name, Venue.id).all()

  for venue in venues_search:
    name = venue[0]
    id = venue[1]
    if name.find(request.form.get('search_term', '')) != -1:
      venue_shows = db.session.query(Show).filter_by(venue_id=id).all()
      venue = dict(zip(('name', 'id'), venue))
      venue['num_upcoming_shows'] = len(upcoming_venue_shows(venue_shows))
      response['search_venue'].append(venue)

  response['count'] = len(response['venue_shows'])

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = db.session.query(Venue).filter_by(id=venue_id).first()
  venue_shows = db.session.query(Show).filter_by(venue_id=venue_id).all()
  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres,
    'address': venue.address,
    'city': venue.city,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link,
    'past_shows': past_venue_shows(venue_shows),
    'upcoming_shows': upcoming_venue_shows(venue_shows),
    'past_shows_count': len(past_venue_shows(venue_shows)),
    'upcoming_shows_count': len(upcoming_venue_shows(venue_shows))
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm(request.form)
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  
  try:
    venue = Venue(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      address = form.address.data,
      phone = form.phone.data,
      genres = form.genres.data,
      facebook_link = form.facebook_link.data,
      image_link = form.image_link.data,
      website = form.website_link.data,
      seeking_talent = form.seeking_talent.data,
      seeking_description = form.seeking_description.data
    )

    db.session.add(venue)
    db.session.commit()

    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except ValueError as error:
    print(error)
    flash('An error ocurred. Venue ' + form.name.data + ' could not be listed.')
    db.session.rollback()

  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False

  try:
    show_venue = db.session.query(Venue).get(venue_id)
    db.session.delete(show_venue)
    db.session.commit()
    flash('The venue was successfully deleted. Redirecting back to venues page')
    return render_template('pages/venues.html')
  
  except ValueError as err:
    print(err)
    db.session.rollback()
    flash('The venue delete was unsuccessful. Try again.')

  finally:
    db.session.close()

  if (error):
    abort(500)
  else:
    return jsonify({'success': True})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artist_data = []
  artists = db.session.query(Artist.id, Artist.name).all()
  for artist in artists:
    artist = dict(zip(('id', 'name'), artist))
    artist_data.append(artist)

  return render_template('pages/artists.html', artists=artist_data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response = {
    'artist_search': []
  }

  artists = db.session.query(Artist.id, Artist.name).all()

  for artist in artists:
    id = artist[0]
    name = artist[1]
    if name.find(request.form.get('search_term', '')) != -1:
      show_artist = db.session.query(Artist).filter_by(artist_id=id).all()
      artist = dict(zip(('id', 'name'), artist))
      artist['num_upcoming_shows'] = len(upcoming_venue_shows(show_artist))
      response['artist_search'].append(artist)
  response['count'] = len(response['artist_search'])
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = db.session.query(Artist).filter_by(id=artist_id).first()
  show_artist = db.session.query(Show).filter_by(artist_id=artist_id).all()
  data1 = {
    "id": artist.id,
    "name": artist.name,
    "genres": ''.join(list(filter(lambda x : x != '{' and x != '}', artist.genres ))).split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_venue_shows(show_artist),
    "upcoming_shows": upcoming_venue_shows(show_artist),
    "past_shows_count": len(upcoming_venue_shows(show_artist)),
    "upcoming_shows_count": len(past_venue_shows(show_artist)),
  }
  return render_template('pages/show_artist.html', artist=data1)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm(request.form)
  # TODO: populate form with fields from artist with ID <artist_id>
  song_artist = db.session.query(Artist).get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=song_artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    form = ArtistForm(request.form)
    song_artist = db.session.query(Artist).get(artist_id)
    song_artist.name = form.name.data
    song_artist.city = form.city.data
    song_artist.state = form.state.data
    song_artist.phone = form.phone.data
    song_artist.genres = form.genres.data
    song_artist.facebook_link = form.facebook_link.data
    song_artist.website = form.website_link.data
    song_artist.image_link = form.image_link.data
    song_artist.seeking_venue = form.seeking_venue.data
    song_artist.seeking_description = form.seeking_description.data
    db.session.commit()

  except Exception as error:
    print(f'Error: {error}')
    flash('An error ocurred. Venue ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()

  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm(request.form)  
  # TODO: populate form with values from venue with ID <venue_id>
  event_venue = db.session.query(Venue).filter_by(id=venue_id).first()
  return render_template('forms/edit_venue.html', form=form, venue=event_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    form = VenueForm(request.form)
    event_venue = db.session.query(Venue).get(venue_id)
    event_venue.name = form.name.data
    event_venue.city = form.city.data
    event_venue.state = form.state.data
    event_venue.address = form.address.data
    event_venue.phone = form.phone.data
    event_venue.genres = form.genres.data
    event_venue.facebook_link = form.facebook_link.data
    event_venue.website = form.website_link.data
    event_venue.image_link = form.image_link.data
    event_venue.seeking_talent = form.seeking_talent.data
    event_venue.seeking_description = form.seeking_description.data
    db.session.commit()

  except Exception as error:
    print(f'Error: {error}')
    flash('An error ocurred. Venue ' + request.form['name'] + ' could not be listed.')

  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm(request.form)
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  forms = ArtistForm(request.form)

  try:
    show_artist = Artist(name=forms.name.data, city=forms.city.data, state=forms.state.data, phone=forms.phone.data, genres=forms.genres.data, facebook_link=forms.facebook_link.data, image_link=forms.image_link.data, website=forms.website_link.data, seeking_venue=forms.seeking_venue.data, seeking_description=forms.seeking_description.data)
    db.session.add(show_artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except ValueError as error:
    print(f'Error: {error}')
    flash('Error! Artist ' + request.form['name'] + ' was not listed!')
    db.session.rollback()

  finally:
    db.session.close()

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  music_shows = db.session.query(Show).all()
  show_data = []

  for show in music_shows:
    show = {'venue_id': show.venue_id,
    'venue_name': db.session.query(Venue.name).filter_by(id=show.venue_id).first()[0],
    'artist_id': show.artist_id,
    'artist_image_link': db.session.query(Artist.image_link).filter_by(id=show.artist_id).first()[0],
    'start_time': str(show.start_time)}
  
    show_data.append(show)
  return render_template('pages/shows.html', shows=show_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm()

  try:
    events = Show(
      venue_id = form.venue_id.data,
      artist_id = form.artist_id.data,
      start_time = form.start_time.data,
      )
    
    db.session.add(events)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  
  except Exception as error:
    print(f'Error: {error}')
    flash('An error ocurred. Show could not be listed!')
    db.session.rollback()
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')

  finally:
    db.session.close()
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

def upcoming_venue_shows(venue_shows):
  upcoming_venue_shows = []

  for venue_show in venue_shows:
    if venue_show.start_time > datetime.now():
      upcoming_venue_shows.append({
        'artist_id': venue_show.artist_id,
        'artist_name': db.session.query(Artist).filter_by(id=venue_show.artist_id).first().name,
        'artist_image_link': db.session.query(Artist).filter_by(id=venue_show.artist_id).first().image_link,
        'start_time': format_datetime(str(venue_show.start_time))
      })
  
  return upcoming_venue_shows

def past_venue_shows(venue_shows):
  past_venues = []

  for venue_show in venue_shows:
    if venue_show.start_time < datetime.now():
      past_venues.append({
        'artist_id': venue_show.artist_id,
        'artist_name': db.session.query(Artist).filter_by(id=venue_show.artist_id).first().name,
        'artist_image_link': db.session.query(Artist).filter_by(id=venue_show.artist_id).first().image_link,
        'start_time': format_datetime(str(venue_show.start_time))
      })

  return past_venues


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
