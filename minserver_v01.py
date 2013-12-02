from datetime import datetime, timedelta
from functools import update_wrapper
import os

from sqlalchemy import *
from sqlalchemy.orm import *

#engine = create_engine('postgresql://localhost/GIS', echo=True) #mac
engine = create_engine('postgresql://tester:tester@localhost/moduledb', echo=True) # linux_new
####engine = create_engine('postgresql://postgres:1q2w3e4r@localhost/gisdb', echo=True) # linux
###app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1q2w3e4r@localhost/felipecorrea'


Session = sessionmaker(bind=engine)
session = Session()

from sqlalchemy.ext.declarative import declarative_base

from geoalchemy import *
# from geoalchemy.postgis import PGComparator

metadata = MetaData(engine)
Base = declarative_base(metadata=metadata)


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
		# for col in self.__table__.c:
		# pdb.set_trace()
		for col in self.__mapper__.class_manager.local_attrs:
			
		#for col in self.__mapper__.c:
			#if isinstance(col.type.python_type, sqlalchemy.DateTime):
			# ctype = str(col.type)
			value = getattr(self, col)
			ctype = type(value)

			if ctype not in [unicode, int, float, bool, datetime]:
				# pdb.set_trace()
				if hasattr(value, 'desc') and isinstance (value.desc, WKBSpatialElement):
					geojson = session.scalar(value.geojson)
					# col = 'FeatureCollection'
					#pdb.set_trace()
					value = json.loads(geojson)
					
				else:
					continue

			if ctype == datetime:
				value = value.isoformat()
			# else:
				# value = getattr(self, col)
		#out[col.name] = getattr(self, col.name)
			out[col] = value
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
class Device(Base, DomainObject):
	__tablename__ = 'devices'
	uuid = Column('uuid', Unicode, primary_key=True)
	version = Column('version', Unicode)
	cordova = Column('cordova', Unicode)
	platform = Column('platform',Unicode)
	model = Column('model',Unicode)
	# pictures = relationship("Picture", order_by="Picture.id", backref="device")
	pictures = relationship('Picture', backref='device')

class Picture(Base, DomainObject):
	__tablename__ = 'pictures'
	# file
	id = Column('picture_id',Integer, primary_key=True)
	fileName = Column('file_name',Unicode)
	filePath = Column('file_path',Unicode)
	created = Column(DateTime, default=datetime.now())
	# compass
	magneticHeading = Column('compass_magnetic_heading', Float)
	trueHeading = Column('compass_true_heading', Float)
	orientation = Column('compass_orientation', Unicode)
	compassManual = Column('compass_manual', Boolean)
	# gps
	latitude = Column('gps_latitude', Float)
	longitude= Column('gps_longitude', Float)
	accuracy = Column('gps_accuracy', Float)
	altitudeAccuracy = Column('gps_altitude_accuracy', Float)
	heading = Column('gps_heading', Float)
	speed = Column('gps_speed', Float)
	# options GPS
	optionsGPSHighAccuracy = Column('options_gps_highaccuracy', Boolean)
	optionsGPSMaxAge = Column('options_gps_maxage', Unicode)
	optionsGPSTimeout = Column('options_gps_timeout', Unicode)
	# options compass
	optionsCompassFrequency = Column('options_compass_frequency', Float)
	optionsCompassEnabled = Column('options_compass_enabled', Boolean)
	# options picture
	optionsPictureQuality = Column('options_picture_quality', Float)
	#
	# geom = GeometryColumn(Point(2), comparator=PGComparator)
	geom = GeometryColumn(Point(2))
	# device = relationship("Device", backref=backref('pictures', order_by=id))
	unique_device = relationship("Device", backref=backref('picture', order_by=id))
	deviceid = Column('device', Unicode, ForeignKey('devices.uuid'))


import urllib2
import json
import pdb
from werkzeug import secure_filename

from flask import Flask, Response, request, make_response, current_app, render_template
app = Flask(__name__)



#####UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads/')
UPLOAD_FOLDER = os.path.join('/home/felipecorrea/Dropbox/ForestWatchers/web/pyserver/api/static/', 'uploads/') #linux
#UPLOAD_FOLDER = os.path.join('/Volumes/MeioTera/Dropbox/ForestWatchers/web/pyserver/api/static/', 'uploads/') #mac
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# @app.route('/pictures/<code>', methods=['GET'])
@app.route('/api/pictures', methods=['GET'])
@crossdomain(origin='*')
def pictures():
	# pdb.set_trace()
	session = Session()
	
	
	bbox = urllib2.unquote(request.args.get('bbox', ''))
	pics = None

	if bbox is not '':
		bbox_arr = bbox.split(',')
		xmin = bbox_arr[0]
		ymin = bbox_arr[1]
		xmax = bbox_arr[2]
		ymax = bbox_arr[3]

		box = 'Polygon((%s %s, %s %s, %s %s, %s %s, %s %s))' % (xmin, ymin, xmin, ymax, xmax, ymax, xmax, ymin, xmin,ymin)
		# pdb.set_trace()	
		pics = session.query(Picture).filter(Picture.geom.within(box))
	else:
		pics = session.query(Picture).all()

	results = []
	for pic in pics:
		n = {}
		n['picture'] = pic.dictize()
		results.append(n)
	result = {}
	result['result'] = results
	# pdb.set_trace()
	return Response(json.dumps(result), mimetype='application/json')


@app.route('/mobile/upload/', methods=['POST'])
@crossdomain(origin='*')
def mobile_upload():
	# test = parse_encoded_json( request.form['entry'])
	js = json.JSONDecoder()
	json_entry = urllib2.unquote( urllib2.unquote( request.form['entry'] ) )
	json_device = urllib2.unquote( urllib2.unquote( request.form['device'] ) )
	entry = js.decode(json_entry)
	device = js.decode(json_device)
	# pdb.set_trace()

	###
	# save file
	###
	
	file = request.files['file']
	filename = secure_filename(file.filename)
	filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
	file.save(filepath)
    #pdb.set_trace()
	GeometryDDL(Device.__table__)
	GeometryDDL(Picture.__table__)
	

	###
	### 
	dbdevice = Device(
		uuid=device['uuid'],
		version=device['version'], 
		cordova=device['cordova'], 
		platform = device['platform'], 
		model=device['model'])

	####gpoint = "POINT(%f %f)" % (entry['gps']['latitude'],entry['gps']['longitude'])
	#gpoint = "POINT(%r %r)" % (entry['gps']['latitude'],entry['gps']['longitude'])
	gpoint = "POINT(%r %r)" % (entry['gps']['longitude'], entry['gps']['latitude'])

	#pdb.set_trace()

	dbpicture = Picture(
		fileName=filename,
		filePath=filepath,

		magneticHeading = entry['compass']['magneticHeading'],
		trueHeading = entry['compass']['trueHeading'],
		orientation = entry['compass']['orientation'],
		compassManual = entry['compass']['useManual'] == 'enable',
		# gps
		latitude = entry['gps']['latitude'],
		longitude= entry['gps']['longitude'],
		accuracy = entry['gps']['accuracy'],
		altitudeAccuracy = entry['gps']['altitudeAccuracy'],
		heading = entry['gps']['heading'],
		speed = entry['gps']['speed'],
		# options GPS
		optionsGPSHighAccuracy = entry['options']['GPSOptions']['enableHighAccuracy'],
		optionsGPSMaxAge = entry['options']['GPSOptions']['maximumAge'],
		optionsGPSTimeout = entry['options']['GPSOptions']['timeout'],
		# options compass
		optionsCompassFrequency = entry['options']['CompassOptions']['frequency'],
		optionsCompassEnabled = (entry['options']['CompassOptions']['enabled'] == 'enable'),
		# options picture
		optionsPictureQuality = entry['options']['PictureOptions']['quality'],
		geom = WKTSpatialElement(gpoint)		
		# device = dbdevice
		)
	
	session = Session()

	dev = session.query(Device).filter_by(uuid=device['uuid']).first()

	results = []
	value = {}
	if dev != None:
		# pdb.set_trace()
		pic = session.query(Picture).filter_by(fileName = filename).first()
		if pic == None:
			dev.pictures.append(dbpicture)
		else:
			value['status'] = 'duplicated'
			results.append(value)
			return Response(json.dumps(results), mimetype='application/json')
	else:
		dbdevice.pictures.append(dbpicture)
		# session.add(dbpicture)
		session.add(dbdevice)

	# pdb.set_trace()
	# if dev != None:
	# 	dev.pictures.append(dbpicture)
	# dbpicture.geom = WKTSpatialElement(gpoint)
	# # pdb.set_trace()
	# session.add(dbpicture)
	# # session.add(dbdevice)
	# pdb.set_trace()
	session.commit()
	
	value['status'] = 'inserted'
	results.append(value)
	return Response(json.dumps(results), mimetype='application/json')

@app.route("/<page>")
def index(page=None):
	if page == None:
		return render_template('index.html')
	else:
		# pdb.set_trace()
		if  str(page).endswith('html'):
			return render_template(page)
		else:
			return render_template(('%s.html') % page)


if __name__ == '__main__':
	app.debug = True

	#app.config['SECRET_KEY'] = 'abc1234'
	#toolbar = DebugToolbarExtension(app)
	#app.run(threaded=True)
   # Alternately
    # app.run(processes=3)
    # app.run(threaded=True)
	app.run(host='0.0.0.0', port=4000,  processes=3)

# @app.route("/registers", methods=["POST", "GET", "PUT", "DELETE"])
# def registers():
#     file = request.files['file']
#     print file.filename
#     filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#     print filepath
#     file.save(filepath)
#     info = parse_encoded_json( request.form['info'] )
#     device = parse_encoded_json( request.form['device'] )
#     print info
#     print device
#     return filepath

