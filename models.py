#!/usr/bin/python

import pdb
import urllib2

from flask import Flask, Response, request
from flask.ext.sqlalchemy import SQLAlchemy

from datetime import datetime

import random
import json
import simplejson as JSON2


app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1q2w3e4r@localhost/felipecorrea'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/felipecorrea'

db = SQLAlchemy(app)

def time_now():
	return datetime.utcnow().isoformat()

def drop():
	print 'dropping db'
	db.drop_all()
	print 'done'

def create():
	print 'creating db'
	db.create_all()
	print 'done'

def custom_populate(hasCompass=False, hasGPS=False, hasDevice=False, hasPicture=False, hasOptions=False):
	n = random.randint(1, 5)
	for x in range(n):
		entry = Entry(time_now(), random.uniform(-90,90), random.uniform(-180,180))
		db.session.add(entry)
		
		if hasCompass:

			compass = Compass(random.uniform(0,360), random.uniform(0,360), random.randint(0,20), entry)
			db.session.add(compass)

		if hasGPS:
			gps = GPS(random.randint(0,1000), random.randint(0,400), random.randint(0,400), 0, random.uniform(0,100), entry)
			db.session.add(gps)

	db.session.commit()


# =========================================
# functions

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
# =========================================
# decorator


class DomainObject(object):

	def dictize(self):
		out = {}
		for col in self.__table__.c:
			#if isinstance(col.type.python_type, sqlalchemy.DateTime):
			ctype = str(col.type)
			if ctype == 'DATETIME' or ctype == 'DATE' or ctype == 'TIME':
				value = getattr(self, col.name).isoformat()
			else:
				value = getattr(self, col.name)
		#out[col.name] = getattr(self, col.name)
			out[col.name] = value
		return out

	@classmethod
	def undictize(cls, dict_):
		raise NotImplementedError()

	def __str__(self):
		return self.__unicode__().encode('utf8')

	def __unicode__(self):
		repr = u'<%s' % self.__class__.__name__
		table = class_mapper(self.__class__).mapped_table
		for col in table.c:
			try:
				repr += u' %s=%s' % (col.name, getattr(self, col.name))
			except Exception, inst:
				repr += u' %s=%s' % (col.name, inst)
				repr += '>'
		return repr
# =========================================
# Domain Objects


class Entry(db.Model, DomainObject):
	id=db.Column(db.Integer, primary_key=True)
	created = db.Column(db.DateTime)
	submitted = db.Column(db.DateTime)
	latitude = db.Column(db.Float)
	longitude = db.Column(db.Float)
	Compass = db.relationship('Compass', uselist=False, backref='entry')
	GPS = db.relationship('GPS', uselist=False, backref='entry')
	Picture = db.relationship('Picture', uselist=False, backref='entry')
	Device = db.relationship('Device', uselist=False, backref='entry')
	Options = db.relationship('Options', uselist=False, backref='entry')

	def __init__(self, created, latitude, longitude):
		self.created = created
		self.submitted = time_now()
		self.latitude = latitude
		self.longitude = longitude
	
	def __repr__(self):
		return '<Entry lat=%r, long=%r>' % (self.latitude, self.longitude)
	

class Compass(db.Model, DomainObject):
	id=db.Column(db.Integer, primary_key=True)
	magnetic_heading = db.Column(db.Float)
	true_heading = db.Column(db.Float)
	heading_accuracy = db.Column(db.Float)
	
	entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
	Entry = db.relationship('Entry', uselist=False, backref='compass')

	def __init__(self, magnetic_heading, true_heading, heading_accuracy, entry=None):
		self.magnetic_heading = magnetic_heading
		self.true_heading = true_heading
		self.heading_accuracy = heading_accuracy
		self.Entry = entry

	def __repr__(self):
		return '<Compass magnetic_heading=%r>' % self.magnetic_heading

class GPS(db.Model, DomainObject):
	id=db.Column(db.Integer, primary_key=True)
	altitude = db.Column(db.Float)
	accuracy = db.Column(db.Float)
	altitude_accuracy = db.Column(db.Float)
	heading = db.Column(db.Float)
	speed = db.Column(db.Float)

	entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
	Entry = db.relationship('Entry', uselist=False, backref='gps')

	def __init__(self, altitude, accuracy, altitude_accuracy, heading, speed, entry=None):
		self.altitude = altitude
		self.accuracy = accuracy
		self.altitude_accuracy = altitude_accuracy
		self.heading = heading
		self.speed = speed
		self.Entry = entry

	def __repr__(self):
		return '<GPS accuracy=%r>' % (self.accuracy)

class Device(db.Model, DomainObject):
	id=db.Column(db.Integer, primary_key=True)
	version = db.Column(db.String(50))
	cordova = db.Column(db.String(50))
	platform = db.Column(db.String(50))
	uuid = db.Column(db.String(50))
	model = db.Column(db.String(50))

	entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
	Entry = db.relationship('Entry', uselist=False, backref='device')

	def __init__(self, version, cordova, platform, uuid, model, entry=None):
		self.version = version
		self.cordova = cordova
		self.platform = platform
		self.uuid = uuid
		self.model = model
		self.Entry = entry

	def __repr__(self):
		return '<Device uuid=%r>' % (self.uuid)

class Picture(db.Model, DomainObject):
	id=db.Column(db.Integer, primary_key=True)
	directory_path = db.Column(db.String(255))
	filename = db.Column(db.String(255))

	entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
	Entry = db.relationship('Entry', uselist=False, backref='picture')

	def __init__(self, directory_path, filename, entry=None):
		self.directory_path = directory_path
		self.filename = filename
		self.Entry = entry

	def __repr__(self):
		return '<Picture filename=%r>' % self.picture

class Options(db.Model, DomainObject):
	id=db.Column(db.Integer, primary_key=True)
	gps_high_accuracy_enabled = db.Column(db.Boolean)
	gps_maximum_age = db.Column(db.Integer)
	gps_timeout = db.Column(db.Float)
	compass_enabled = db.Column(db.Boolean)
	compass_frequency = db.Column(db.Float)
	picture_quality = db.Column(db.Float)

	entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
	Entry = db.relationship('Entry', uselist=False, backref='options')

	def __init__(self, gps_high_accuracy_enabled, gps_maximum_age, gps_timeout, compass_enabled, compass_frequency, picture_quality, entry=None):
		self.gps_high_accuracy_enabled = gps_high_accuracy_enabled
		self.gps_maximum_age = gps_maximum_age
		self.gps_timeout = gps_timeout
		self.compass_enabled = compass_enabled
		self.compass_frequency = compass_frequency
		self.picture_quality = picture_quality
		self.Entry = entry

	def __repr__(self):
		return '<Options compass_enabled=%r>' % (self.compass_enabled)
		
# =========================================
# Models

@app.route('/time/', methods=['GET'])
@app.route('/time/<t>', methods=['GET'])
@app.route('/time/<t>/', methods=['GET'])
def time_test(t='2'):
	#pdb.set_trace()
	import time
	ti = float(t)
	time.sleep(ti)
	return 'waited for %r s' % (ti)

# @app.before_request
# def before_request():
# 	pdb.set_trace()

@app.route('/some/', methods=['POST'])
def some():
	return 'got'

@app.route('/mobile/upload/', methods=['POST'])
def mobile_upload():
	# test = parse_encoded_json( request.form['entry'])
	js = json.JSONDecoder()
	json_entry = urllib2.unquote( urllib2.unquote( request.form['entry'] ) )
	json_device = urllib2.unquote( urllib2.unquote( request.form['device'] ) )
	entry = js.decode(json_entry)
	device = js.decode(json_device)
	pdb.set_trace()
	return 'posted'

@app.route('/entries', methods=['GET','POST'])
@app.route('/entries/', methods=['GET','POST'])
@app.route('/entries/<int:entry_id>', methods=['GET', 'POST'])
@app.route('/entries/<int:entry_id>/', methods=['GET', 'POST'])
def entries(entry_id=-1):
	if request.method == 'GET':		
		limit = request.args.get('limit', 20)
		offset = request.args.get('offset', 0)
		result = {}
		options = {}
		results = []
		app.logger.debug('limit is %r' % limit)
		# if request.args.get('limit'):
		# 	limit = int(request.args.get('limit'))

		if entry_id == -1:
			all_entries = Entry.query.order_by(Entry.created.desc()).offset(offset).limit(limit)
			options['rows_in_db'] = Entry.query.count()
			options['rows_returned'] = all_entries.count()
			options['limit'] = limit
			options['offset'] = offset
			result['query_params'] = options
		else:
			all_entries = Entry.query.filter_by(id=entry_id)
		
		for x in all_entries:
			n = {}
			n['entry'] = x.dictize()
			if x.compass != []:
				n['compass'] = x.compass[0].dictize()
			if x.gps != []:
				n['gps'] = x.gps[0].dictize()
			if x.device != []:
				n['device'] = x.device[0].dictize()
			if x.picture != []:
				n['picture'] = x.picture[0].dictize()
			if x.options != []:
				n['options'] = x.options[0].dictize()
			results.append(n)
		
		result['result'] = results
		
		return Response(json.dumps(result), mimetype="application/json")
	
	elif request.method == 'POST':
		
		test = parse_encoded_json( request.form['test'])
		pdb.set_trace()
		return 'posted'
	
	return 'dunno'

# =========================================
# routes

def parse_encoded_json(encoded_string):
	return JSON2.loads( urllib2.unquote( encoded_string ) )

if __name__ == '__main__':
	app.debug = True

	#app.config['SECRET_KEY'] = 'abc1234'
	#toolbar = DebugToolbarExtension(app)
	#app.run(threaded=True)
   # Alternately
    # app.run(processes=3)
    # app.run(threaded=True)
	app.run(host='0.0.0.0', port=4000,  processes=3)



# pdb.set_trace()
# #db.drop_all()
# #db.session.commit()
# db.create_all()
# entry = Entry(time_now(), -20.3041, -45.1234)
# compass = Compass(359.9, 349.9, 10, entry)
# db.session.add(entry)
# db.session.add(compass)
# db.session.commit()
# # # db.create_all()
# # entry = Entry(datetime.utcnow(), -20.3041, -45.1234)
# # db.session.add(entry)
# # db.session.commit()
# # entries = Entry.query.all()
# # print entries
