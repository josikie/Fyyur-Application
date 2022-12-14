from operator import or_
from queue import Empty
from models import TheShows, db, Artist, Venue
import dateutil.parser
from flask_moment import Moment
import babel
from flask import Flask
from flask_migrate import Migrate
from flask import (render_template, request, flash, redirect, url_for)
import logging
from logging import Formatter, FileHandler
from forms import *
from sqlalchemy import exc, or_
from datetime import datetime
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)

# TODO: connect to a local postgresql database
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
# models/tables in models.py, I separate it. flask db init to make initial migrates folder, 
# then flask db migrate and flask db upgrade to make the tabel in database created


def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

# table class in models.py, I separate it. flask db init to make initial migrates folder, 
# then flask db migrate and upgrade to make the tabel in database created

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
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue. (done)
  data = []
  # query rows from city and state column then eliminate duplicate rows
  cities = Venue.query.with_entities(Venue.city, Venue.state).distinct()
  for city in cities:
    ccity = city.city
    sstate = city.state
    # query data from Venue with particular city and state
    theVenues = Venue.query.filter_by(city=ccity, state=sstate).all()
    vvenue = []
    for venue in theVenues:
      vvenue.append({
        'id' : venue.id,
        'name' : venue.name,
        'num_upcoming_shows' : TheShows.query.filter_by(venue_id = venue.id).count()
      })
    obj = {
      'city' : ccity,
      'state' : sstate,
      'venues' : vvenue
    }
    data.append(obj)

  if len(data) == 0:
    return render_template('pages/empty.html', link="/venue")
  return render_template('pages/venues.html', areas=data);
# done
@app.route('/venues', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee" (done)
  
  # get the word that user type in search bar
  search_term = request.form.get('search_term')
  if search_term == '' :
    return redirect(url_for('venues'))
  # get Venue data based on what user type in search bar (case-insensitive)
  data = Venue.query.filter(Venue.name.ilike('%' + search_term +'%')).all()
  # structured the data into object as a response
  response = {
    'count' : len(data),
    'data' : data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))
# done
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id (done)

  # get all venue with id = venue_id
  venue = Venue.query.get_or_404(venue_id)
  # get show that had been played there in the past
  # we can use this code too : db.session.query(TheShows).join(Artist).all() 
  # but it opens session, so I think this code better:
  # past_shows = TheShows.query.join(Artist).add_columns(TheShows.show_date, Artist.id, Artist.name, Artist.image_link).filter(TheShows.venue_id==venue_id, TheShows.show_date <= time_now).all()
  pshows = []
  upshows = []
  # append all shows that had been played to an array
  for show in venue.the_shows:
    # structure it to the right form in object
    s = {'artist_id' : show.venue_id,
    'artist_name' : show.venue.name,
    'artist_image_link' : show.venue.image_link,
    'start_time' : show.show_date.strftime("%Y%m%d, %H:%M")
    }
    if show.show_date <= datetime.now():
      pshows.append(s)
    else:
      upshows.append(s)

  data = vars(venue)
 
  # structure the data object with the right form
  data = {
    'id' : venue.id,
    'name' : venue.name,
    'genres' : venue.genres,
    'address' : venue.address,
    'city' : venue.city,
    'state' : venue.state,
    'phone' : venue.phone,
    'website' : venue.website_link,
    'facebook_link' : venue.facebook_link,
    'seeking_talent' : venue.seeking_talent,
    'seeking_description' : venue.seeking_description,
    'image_link' : venue.image_link,
    'past_shows' : pshows,
    'upcoming_shows' : upshows,
    'past_shows_count' : len(pshows),
    'upcoming_shows_count' : len(upshows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------
# 
@app.route('/venue', methods=['GET'])
def create_venue_form():
  # inisiate form
  try:
    form = VenueForm()
  except:
    return redirect(url_for('artists'))
  # send the form to the new venue page, so we can use the VenueForm there
  return render_template('forms/new_venue.html', form=form)
# done
@app.route('/venue', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion (done)
  data = ''
  # get the form with its data from user
  form = VenueForm(request.form, meta={'csrf': False})
  error = False
  # 1. Take the data from the form, 
  # 2. make new venue,
  # 3. if the data is validate, then add new venue object to the database,
  # 4. if there is something wrong, rollback database so we cancel to add new venue 
  if form.validate() :
    try:
      name = form.name.data
      data = name
      city = form.city.data
      state = form.state.data
      genres = form.genres.data
      address = form.address.data
      phone = form.phone.data
      image_link = form.image_link.data
      facebook_link = form.facebook_link.data
      seeking_talent = form.seeking_talent.data
      seeking_description = form.seeking_description.data
      venue = Venue(name=name,city=city, state=state, address=address, genres=genres, 
      phone=phone, image_link=image_link, facebook_link=facebook_link, 
      seeking_talent=seeking_talent, seeking_description=seeking_description)
      db.session.add(venue)
      db.session.commit()
      data = venue.name
    except ValueError as e:
      app.logger.error(e)
      db.session.rollback()
      error = True
    finally:
      db.session.close()
  else:
    error = True

  if error:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('An error occurred. ' + data + ' could not be listed. \n' + str(message), 'danger')
    return redirect(url_for('index'))
  else:
    flash('Venue ' + data + ' was successfully listed!', 'info')
    return redirect(url_for('index'))

#done
@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  name = ''
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get_or_404(venue_id)
    name = venue.name
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + name + ' has been removed.', 'info')
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage (done)
    return redirect(url_for('venues'))
  except exc.SQLAlchemyError as e :
    app.logger.error(e)
    db.session.rollback()
    flash('Venue ' + name + ' failed to remove.', 'danger')
    return redirect(url_for('venues'))
  finally:
    db.session.close()

#  Artists
#  ----------------------------------------------------------------
# done
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  cities = Artist.query.with_entities(Artist.city, Artist.state).distinct()
  for city in cities:
    ccity = city.city
    sstate = city.state
    theArtists = Artist.query.filter_by(city = ccity, state = sstate).all()
    artistArr = []
    for artist in theArtists:
      artistObj = {
        'id' : artist.id,
        'name' : artist.name
      }
      artistArr.append(artistObj)
    data.append({
      'city' : ccity,
      'state' : sstate,
      'artists' : artistArr
    })

  if len(data) == 0:
    return render_template('pages/empty.html', link='/artist')
  return render_template('pages/artists.html', theData=data)

# done
@app.route('/artists', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term')
  if search_term == '' :
    return redirect(url_for('artists'))
  count = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).count()
  artistsData = Artist.query.filter(Artist.name.ilike('%'+ search_term +'%')).all()
  data = []
  for artist in artistsData:
    data.append({
      'id' : artist.id,
      'name' : artist.name,
      'num_upcoming_shows' : TheShows.query.filter_by(artist_id=artist.id).count()
    })
  response={
    "count": count,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

# done
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get_or_404(artist_id)
  past_shows = []
  upcoming_shows = []
  for show in artist.the_shows:
    s ={
      'venue_id' : show.venue_id,
      'venue_name' : show.artist.name,
      'venue_image_link' : show.artist.image_link,
      'start_time' : show.show_date.strftime('%Y%m%d, %H%M')
    }
    if show.show_date <= datetime.now():
      past_shows.append(s)
    else:
      upcoming_shows.append(s)
 
  data = {
    'id' : artist.id,
    'name' : artist.name,
    'genres' : artist.genres,
    'city' : artist.city,
    'state' : artist.state,
    'phone' : artist.phone,
    'website' : artist.website_link,
    'facebook_link' : artist.facebook_link,
    'seeking_venue' : artist.seeking_venue,
    'seeking_description' : artist.seeking_description,
    'image_link' : artist.image_link,
    'past_shows' : past_shows,
    'upcoming_shows' : upcoming_shows,
    'past_shows_count' : len(past_shows),
    'upcoming_shows_count' : len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(obj=artist)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist = Artist.query.get_or_404(artist_id)
    form = ArtistForm(formdata=request.form, obj=artist)
    form.populate_obj(artist)
    db.session.commit()
    flash(artist.name + ' has been updated', 'info')
  except:
    db.session.rollback()
    flash(artist.name + ' failed to update', 'danger')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try: 
    venue = Venue.query.get(venue_id)
    form = VenueForm(formdata=request.form, obj=venue)
    form.populate_obj(venue)
    db.session.commit()
    flash(venue.name + ' has been updated', 'info')
  except:
    db.session.rollback()
    flash(venue.name + ' failed to update', 'danger')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artist', methods=['GET'])
def create_artist_form():
  try:
    form = ArtistForm()
  except:
    return redirect(url_for('artists'))
  return render_template('forms/new_artist.html', form=form)

# done
@app.route('/artist', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form, meta={'csrf':False})
  data = ''
  error = False
  if form.validate() :
    try:
      name = form.name.data
      data = name
      city = form.city.data
      state = form.state.data
      phone = form.phone.data
      genres = form.genres.data
      facebook_link = form.facebook_link.data
      image_link = form.image_link.data
      website_link = form.website_link.data
      seeking_venue = form.seeking_venue.data
      seeking_description = form.seeking_description.data
      artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres,
                      facebook_link=facebook_link, image_link=image_link, website_link=website_link, 
                      seeking_venue=seeking_venue, seeking_description=seeking_description)
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + data + ' was successfully listed!', 'info')
      return redirect(url_for('index'))
    except ValueError as e:
      app.logger.error(e)
      db.session.rollback()
      error = True
    finally:
      db.session.close()
  else:
    error = True
  
  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('An error occurred. ' + data + ' could not be listed. \n' + str(message), 'danger')
    return redirect(url_for('index'))
  else:
    # on successful db insert, flash success
    flash('Artist ' + data + ' was successfully listed!', 'info')
    return redirect(url_for('index'))
#done
@app.route('/artists/<artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):
  # delete artist with corresponding id with its shows
  try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash(artist.name + ' has succesfully deleted.', 'info')
    return redirect(url_for('index'))
  except:
    db.session.rollback()
    flash(artist.name + ' has not succesfully deleted.', 'danger')
  finally:
    db.session.close()

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
# done
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  the_shows = TheShows.query.all()
  showsArr = []
  for show in the_shows:
    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)
    showsArr.append({
      'venue_id' : show.venue_id,
      'venue_name' :venue.name,
      'artist_id' : show.artist_id,
      'artist_name' : artist.name,
      'artist_image_link' : artist.image_link,
      'start_time' : str(show.show_date)
    })
  if len(showsArr) == 0:
    return render_template('pages/empty.html', link='/show')
  return render_template('pages/shows.html', shows=showsArr)

@app.route('/show')
def create_shows():
  # renders form. do not touch.
  try:
    form = ShowForm()
  except:
    return redirect(url_for('shows'))

  return render_template('forms/new_show.html', form=form)
# done
@app.route('/show', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form, meta={'csrf': False})
  error = False
  if form.validate() :
    try:
      artist_id = form.artist_id.data
      venue_id = form.venue_id.data
      show_date = form.start_time.data
      show = TheShows(artist_id=artist_id, venue_id=venue_id, show_date=show_date)
      db.session.add(show)
      db.session.commit()
    except ValueError as e:
      app.logger.error(e)
      db.session.rollback()
      error = True
    finally:
      db.session.close()
  else:
    error = True

  if error:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('An error occurred. Show could not be listed. \n' + str(message), 'danger')
    return redirect(url_for('index'))
  else:
    flash('Show successfully listed!', 'info')
    return redirect(url_for('index'))
# done
@app.route('/shows', methods=['POST'])
def search_shows():
  # TODO: impelement search on shows with partial date search. 
  search_term = request.form.get('search_term', '')
  
  if search_term == '' :
    return redirect(url_for('shows'))
  
  venues = Venue.query.join(TheShows).add_columns(Venue.id, Venue.name, TheShows.artist_id ,TheShows.show_date).filter(Venue.name.ilike('%' + search_term + '%')).all()
  count = Venue.query.join(TheShows).add_columns(Venue.id, Venue.name, TheShows.artist_id, TheShows.show_date).filter(Venue.name.ilike('%' + search_term + '%')).count()
  data = []
  response = {}
  for venue in venues:
    artist = Artist.query.get(venue.artist_id)
    data.append({
      'venue_id' : venue.id,
      'venue_name' : venue.name,
      'artist_id' : venue.artist_id,
      'artist_name' : artist.name,
      'artist_image_link' : artist.image_link,
      'start_time' : str(venue.show_date)
    })
  
  response = {
      'count' : count,
      'data' : data
  }

  return render_template('/pages/show.html', response=response, search_term=request.form.get('search_term', ''))

#  Search by City, State
#  -----------------------------------------------------------------
@app.route('/state', methods=['POST'])
def search_by_city_state():
  # TODO: implement search by city, state
  search_term = request.form.get('search_term', '')
  if search_term == '':
    return redirect(url_for('index'))
  theResponse = {}
  the_venues = Venue.query.filter(or_(Venue.city.ilike('%'+ search_term +'%'), Venue.state.ilike('%'+ search_term +'%'))).all()
  the_artists = Artist.query.filter(or_(Artist.city.ilike('%'+ search_term +'%'), Artist.state.ilike('%'+ search_term +'%'))).all()
  
  venuesObj = []
  for venue in the_venues:
    venuesObj.append({
      'id' : venue.id,
      'name' : venue.name
    })
  
  artistsObj = []
  for artist in the_artists:
    artistsObj.append({
      'id': artist.id,
      'name' : artist.name
    })

  countVenues = Venue.query.filter(or_(Venue.city.ilike('%'+ search_term +'%'), Venue.state.ilike('%'+ search_term +'%'))).count()
  countArtists = Artist.query.filter(or_(Artist.city.ilike('%'+ search_term +'%'),  Artist.state.ilike('%'+ search_term +'%'))).count()
  count = countVenues + countArtists

  theResponse = {
    'count' : count,
    'venues' : venuesObj,
    'artists' : artistsObj
  }

  return render_template('/pages/state.html', response=theResponse, search_term=request.form.get('search_term', ''))

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
    app.debug=True
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
