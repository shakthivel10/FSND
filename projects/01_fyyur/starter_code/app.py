#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import aliased
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from werkzeug.datastructures import MultiDict

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

#  connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://shakthivel@localhost:5432/fyyurapp'
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
  __tablename__ = 'Show'
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
  start_time = db.Column(db.DateTime(), primary_key=True)
  venue = db.relationship("Venue", back_populates="venue_shows")
  artist = db.relationship("Artist", back_populates="artist_show")

class Venue(db.Model):
  __tablename__ = 'Venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  # new fields added
  website = db.Column(db.String(200))
  seeking_talent = db.Column(db.Boolean)
  seeking_description = db.Column(db.String(3000))
  genres = db.Column(db.ARRAY(db.String(20)))
  venue_shows = db.relationship('Show', back_populates='venue')   

class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  # new fields added
  genres = db.Column(db.ARRAY(db.String(20)))
  website = db.Column(db.String(200))
  seeking_venue = db.Column(db.Boolean)
  seeking_description = db.Column(db.String(3000))
  artist_show = db.relationship('Show', back_populates='artist')   
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

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
def venues(): # DONE

  cities = db.session.query(Venue.city, Venue.state).distinct().all()
  
  data = []
  for c in cities:
    city_data = {}
    city_data["city"] = c.city
    city_data["state"] = c.state
    city_data["venues"] = []
    city_venues = Venue.query.filter(Venue.city==c.city, Venue.state==c.state).all()
    for city_venue in city_venues:
      venue_data = {}
      venue_data["id"] = city_venue.id
      venue_data["name"] = city_venue.name
      venue_data["num_upcoming_shows"] = Show.query.filter(Show.venue_id== city_venue.id, Show.start_time > datetime.now()).count()
      city_data["venues"].append(venue_data)

    data.append(city_data)
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues(): # DONE

  search_term = request.form.get('search_term',"")
  print(type(search_term))
  res = Venue.query.filter(func.lower(Venue.name).contains(search_term.lower(),autoescape = True)).all()
  print(len(res))
  
  response = {"count":len(res),"data":res}

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id): # DONE

  res = Venue.query.filter(Venue.id == venue_id).first()

  past_shows = []
  upcoming_shows = []

  for s in res.venue_shows:
    d = {}
    d["start_time"] = s.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    d["artist_id"] = s.artist.id
    d["artist_name"] = s.artist.name
    d["artist_image_link"] = s.artist.image_link

    if s.start_time <= datetime.now():
      past_shows.append(d)
    else:
      upcoming_shows.append(d)
  
  res.past_shows = past_shows
  res.upcoming_shows = upcoming_shows
  
  res.past_shows_count = len(past_shows)
  res.upcoming_shows_count = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=res)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission(): # DONE

  id = db.session.execute("SELECT MAX(id) FROM \"Venue\" ").scalar() + 1

  try:
    venue = Venue( 
    id = id,
    name = request.form.get("name",""),
    city = request.form.get('city',""),
    state = request.form.get('state',""),
    address = request.form.get('address',""),
    phone = request.form.get('phone',""),
    facebook_link = request.form.get('facebook_link',""),
    genres = request.form.getlist('genres'),
    image_link = "",
    website = "",
    seeking_talent = False,
    seeking_description = ""
    )

    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form.get("name","") + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id): # DONE

  try:
    venue = Venue.query.filter(Venue.id == venue_id).first()
    db.session.delete(venue)
    db.session.commit()
    flash('Venue was successfully deleted!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')  # DONE
def artists():
  res = db.session.query(Artist.id, Artist.name)

  return render_template('pages/artists.html', artists=res)

@app.route('/artists/search', methods=['POST'])
def search_artists():  # DONE

  search_term = request.form.get('search_term',"")
  print(type(search_term))
  res = Artist.query.filter(func.lower(Artist.name).contains(search_term.lower(),autoescape = True)).all()
  print(len(res))
  
  response = {"count":len(res),"data":res}

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):  # DONE

  res = Artist.query.filter(Artist.id == artist_id).first()

  past_shows = []
  upcoming_shows = []

  for s in res.artist_show:
    d = {}
    d["start_time"] = s.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    d["venue_id"] = s.venue.id
    d["venue_name"] = s.venue.name
    d["venue_image_link"] = s.venue.image_link
    if s.start_time <= datetime.now():
      past_shows.append(d)
    else:
      upcoming_shows.append(d)
  
  res.past_shows = past_shows
  res.upcoming_shows = upcoming_shows
  
  res.past_shows_count = len(past_shows)
  res.upcoming_shows_count = len(upcoming_shows)
  
  return render_template('pages/show_artist.html', artist=res)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id): # DONE
  
  artist=Artist.query.filter(Artist.id == artist_id).first()
  
  artist_data = {}
  artist_data["name"] = artist.name
  artist_data["city"] = artist.city
  artist_data["state"] = artist.state
  artist_data["phone"] = artist.phone
  artist_data["facebook_link"] = artist.facebook_link
  artist_data["genres"] = artist.genres

  form = ArtistForm(formdata=MultiDict(artist_data))
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist=Artist.query.filter(Artist.id == artist_id).first()

    artist.name = request.form.get("name",""),
    artist.city = request.form.get('city',""),
    artist.state = request.form.get('state',""),
    artist.phone = request.form.get('phone',""),
    artist.facebook_link = request.form.get('facebook_link',""),
    artist.genres = request.form.getlist('genres')
    
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form.get("name","") + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id): # DONE
  
  venue=Venue.query.filter(Venue.id == venue_id).first()
  
  venue_data = {}
  venue_data["name"] = venue.name
  venue_data["city"] = venue.city
  venue_data["state"] = venue.state
  venue_data["address"] = venue.address
  venue_data["phone"] = venue.phone
  venue_data["facebook_link"] = venue.facebook_link
  venue_data["genres"] = venue.genres

  form = VenueForm(formdata=MultiDict(venue_data))
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  try:
    venue=Venue.query.filter(Venue.id == venue_id).first()

    venue.name = request.form.get("name",""),
    venue.city = request.form.get('city',""),
    venue.state = request.form.get('state',""),
    venue.address = request.form.get('address',""),
    venue.phone = request.form.get('phone',""),
    venue.facebook_link = request.form.get('facebook_link',""),
    venue.genres = request.form.getlist('genres'),
    
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form.get("name","") + ' could not be updated.')
  finally:
    db.session.close()
  
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission(): # DONE

  id = db.session.execute("SELECT MAX(id) FROM \"Artist\" ").scalar() + 1

  try:
    artist = Artist( 
    id = id,
    name = request.form.get("name",""),
    city = request.form.get('city',""),
    state = request.form.get('state',""),
    phone = request.form.get('phone',""),
    facebook_link = request.form.get('facebook_link',""),
    genres = request.form.getlist('genres'),
    image_link = "",
    website = "",
    seeking_venue = False,
    seeking_description = ""
    )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form.get("name","") + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows(): # DONE

  res = Show.query.all()
  data = []

  for r in res:
    d = {}
    d["venue_id"] = r.venue.id 
    d["venue_name"] = r.venue.name
    d["artist_id"] = r.artist.id 
    d["artist_name"] = r.artist.name
    d["artist_image_link"] = r.artist.image_link
    d["start_time"] = r.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    data.append(d)
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission(): # DONE

  print(request.form)
  try:
    show = Show( 
    venue_id = request.form.get("venue_id",""),
    artist_id = request.form.get("artist_id",""),
    start_time = request.form.get("start_time","")
    )

    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


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
