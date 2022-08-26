#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import traceback
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import *
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

# app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@ app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

    areas = Venue.query.distinct(Venue.city, Venue.state).all()

    result = []
    for area in areas:
        data = {
            "city": area.city,
            "state": area.state,
        }

        venues = Venue.query.filter_by(city=area.city, state=area.state).all()
        set_venue = [{
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows))),
        } for venue in venues]

        data["venues"] = set_venue
        result.append(data)

    return render_template('pages/venues.html', areas=result)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_form = request.form.get('search_term')
    venues = Venue.query.filter(Venue.name.ilike('%'+search_form+'%')).all()
    response = {
        "count": Venue.query.filter(Venue.name.ilike('%'+search_form+'%')).count(),
        "data": [{
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows))),
        } for venue in venues]
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venues = Venue.query.filter_by(id=venue_id).all()
    artists_past_shows = Artist.query.join(Show, Artist.id == Show.artist_id).filter(Show.venue_id == venue_id).filter(
        Show.start_time < datetime.now()).order_by(Show.start_time).all()

    artists_upcoming_shows = Artist.query.join(Show, Artist.id == Show.artist_id).filter(
        Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).order_by(Show.start_time).all()

    for venue in venues:
        data = {
            "id": venue_id,
            "name": venue.name,
            "genres": [venue.genres],
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website_link,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.looking_for_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": [{
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time)
            } for artist in artists_past_shows for show in artist.shows if show.start_time < datetime.now() and show.venue_id == venue.id],
            "upcoming_shows": [{
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(show.start_time)
            } for artist in artists_upcoming_shows for show in artist.shows if show.start_time > datetime.now() and show.venue_id == venue.id],
            "past_shows_count": len(list(filter(lambda x: x.start_time < datetime.now(), venue.shows))),
            "upcoming_shows_count": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
        }

    # data = list(filter(lambda d: d['id'] ==
    #                    venue_id, [data]))[0]
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@ app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    form = VenueForm(request.form)

    try:
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            website_link=form.website_link.data,
            looking_for_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )

        db.session.add(venue)
        db.session.commit()
    # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    except:
        db.session.rollback()
        flash('An error occured. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    # return render_template('pages/home.html')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html', form=form)


@ app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
        traceback.print_exc()
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artists = db.session.query(Artist).all()
    data = [{
        "id": artist.id,
        "name": artist.name,
    } for artist in artists]

    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    search_form = request.form.get('search_term')
    artists = Artist.query.filter(Artist.name.ilike('%'+search_form+'%')).all()
    response = {
        "count": Artist.query.filter(Artist.name.ilike('%'+search_form+'%')).count(),
        "data": [{
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), artist.shows))),
        } for artist in artists]
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id

    artists = Artist.query.filter_by(id=artist_id).all()
    venues_past_shows = Venue.query.join(Show, Venue.id == Show.venue_id).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).order_by(Show.start_time).all()

    venues_upcoming_shows = Venue.query.join(Show, Venue.id == Show.venue_id).filter(
        Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).order_by(Show.start_time).all()

    for artist in artists:
        data = {
            "id": artist_id,
            "name": artist.name,
            "genres": [artist.genres],
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website_link,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.looking_for_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": [{
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(show.start_time)
            } for venue in venues_past_shows for show in venue.shows if show.start_time < datetime.now() and show.artist_id == artist.id],
            "upcoming_shows": [{
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(show.start_time)
            } for venue in venues_upcoming_shows for show in venue.shows if show.start_time > datetime.now() and show.artist_id == artist.id],
            "past_shows_count": len(list(filter(lambda x: x.start_time < datetime.now(), artist.shows))),
            "upcoming_shows_count": len(list(filter(lambda x: x.start_time > datetime.now(), artist.shows)))
        }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    form = ArtistForm()

    artists = Artist.query.filter_by(id=artist_id).all()

    for artist in artists:
        artist = {
            "id": artist.id,
            "name": artist.name,
            "genres": [artist.genres],
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website_link,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.looking_for_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link
        }
    # TODO: populate form with fields from artist with ID <artist_id>

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    form = ArtistForm(request.form)
    try:
        artist = Artist.query.filter_by(id=artist_id).first()
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website_link = form.website_link.data
        artist.looking_for_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('An error occured. Could not be updated.')

    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venues = Venue.query.filter_by(id=venue_id).all()

    for venue in venues:
        venue = {
            "id": venue.id,
            "name": venue.name,
            "genres": [venue.genres],
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website_link,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.looking_for_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link
        }

    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes

    form = VenueForm(request.form)

    try:
        venue = Venue.query.filter_by(id=venue_id).first()

        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        venue.website_link = form.website_link.data
        venue.looking_for_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.commit()

    except Exception:
        db.session.rollback()
        flash('An error occured. Could not be updated.')

    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    form = ArtistForm(request.form)

    try:
        if form.validate():
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website_link=form.website_link.data,
                looking_for_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(artist)
            db.session.commit()

    # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    except:
        db.session.rollback()
        flash('An error occured. Artist ' +
              request.form['name'] + ' could not be listed.')
        traceback.print_exc()
    finally:
        db.session.close()

    return render_template('pages/home.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@ app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.

    shows = Show.query.order_by(Show.start_time).all()

    artists = Artist.query.join(Show, Artist.id == Show.artist_id).filter(
        Artist.id == Show.artist_id).all()

    venues = Venue.query.join(Show).filter(Venue.id == Show.venue_id).all()

    data = [{
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(show.start_time)
    }for show in shows for artist in artists if show.artist_id == artist.id for venue in venues if show.venue_id == venue.id]

    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)

    try:
        show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data
        )

        db.session.add(show)
        db.session.commit()
    # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        db.session.rollback()

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
        flash('An error occured. Show could not be listed.')
        traceback.print_exc()
    finally:
        db.session.close()

    return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
