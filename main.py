#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, send_from_directory, escape
from werkzeug import secure_filename
from sys import argv, stderr
import sys, re
import cgi
import utils
from copy import deepcopy
import os
import random, string
import hashlib
import os, json, pickle
import SocketServer
from StringIO import StringIO
import threading
import time

class colours():
    def __init__(self):
        self.enable()
    def enable(self):
    	if os.name == 'nt':
    		self.disable()
    		return
        self.header = '\033[95m'
        self.blue = '\033[94m'
        self.green = '\033[92m'
        self.warning = '\033[93m'
        self.fail = '\033[91m'
        self.bold = '\033[1m'
        self.default = '\033[0m'
    def disable(self):
        self.header = ''
        self.blue = ''
        self.green = ''
        self.warning = ''
        self.fail = ''
        self.default = ''
        self.bold = ''
colors = colours()
##############################################

class rServer(SocketServer.BaseRequestHandler):
	def setup(self):
		try:
			login = self.request.recv(4096).strip('\n').strip('\r')
		except:
			return

		usern = login.split('/')[0]
		passw = login.split('/')[1]
		success = False
		if usern in self.server.db['users']:
			if passw == self.server.db['users'][usern]['password']:
				success = True

		if not success:
			self.request.send('305 NOT AUTHORIZED')
			print('[INFO] ' + repr(self.client_address) + ' has sent an invalid password and is now disconnected')
			self.request.close()
		else:
			print('[INFO] ' + repr(self.client_address) + ' has successfully logged in')
			self.request.send('OK')
			self.logged_in = True
			self.data = ''
			self.usern = usern
			self.passw = passw
			self.curdb = 0
	def handle(self):
		#self.client_address[0] == ip (str)
		#self.request == socket.socket
		data = 'that4chanwolf is gentoo'
		wholething = ''
		while data:
			try:
				data = self.request.recv(4096)
			except:
				return
			if not self.logged_in: continue
			self.data += data.replace('\n', '').replace('\r', '')
			if self.data[-1:] == chr(4):
				cmd = json.load(StringIO(self.data[:-1]))
				self.data = ''

				if cmd['cmd'] == 'pull':
					res = {'cmd': cmd['cmd'], 'response': ''}
					#self.server.db['users'][self.usern]['dbs'][self.curdb].reload()
					if len(self.server.db['users'][self.usern]['dbs']) == 0:
						res['response'] = 'err: No databases available, you should first create one on the website'
					else:
						res['response'] = json.dumps(self.server.db['users'][self.usern]['dbs'][self.curdb])
					self.request.send(json.dumps(res) + chr(4))
				elif cmd['cmd'] == 'push':
					if self.server.db['users'][self.usern].get('readonly') == True:
						self.request.send(json.dumps({'cmd': cmd['cmd'], 'response': 'Read-only database'}) + chr(4))
						continue
					self.server.db['users'][self.usern]['dbs'][self.curdb] = json.load(StringIO(cmd['args']))

					res = {'cmd': cmd['cmd'], 'response': 'OK'}
					self.request.send(json.dumps(res) + chr(4))
				elif cmd['cmd'] == 'save':
					#doesn't do anything
					res = {'cmd': cmd['cmd'], 'response': 'OK'}
					self.request.send(json.dumps(res) + chr(4))
				elif cmd['cmd'] == 'sdb':
					try:
						self.curdb += 1
						repr(self.server.db['users'][self.usern]['dbs'][self.curdb])
					except IndexError:
						self.curdb = 0

					res = {'cmd': cmd['cmd'], 'response': 'OK'}
					self.request.send(json.dumps(res) + chr(4))
				continue

	def finish(self):
		pass
###########################################################

class streamWrapper(object):
	def __init__(self, out):
		self.out = out
		self.regexes = {'request': r'(.*) - - \[(.*)\] "(.*) (.*) HTTP(.*)" (.*) -',
		'start': r' \* Running on (.*)', 'reload': ' \* Detected change in (.*), reloading(.*)',
		'reloading2': r' \* Restarting with reloader'}
		self.status_colors = {'200': colors.green, '304': colors.green, '404': colors.fail, '301': colors.fail, '500': colors.fail}
	def write(self, obj):
		matched = False
		for regex in self.regexes:
			m = re.match(self.regexes[regex], obj) 
			if m != None:
				matched = True
				groups = m.groups()
				del m

				if regex == 'request':
					#0 = ip; 1 = timestamp; 2 = mode, 3 = page, 4 = protocol ver, 5 = status
					c = self.status_colors[groups[5]] if (groups[5] in self.status_colors) else colors.warning
					self.out.write(groups[2] + ' ' + c + groups[3] + colors.default + ' [' + groups[5] + colors.default + ' - ' + groups[1] + ']\n')
					del c
				elif regex == 'start':
					self.out.write(colors.header + '**' + colors.default + ' Application ready on ' + colors.blue + groups[0] + colors.default + '\n')
				elif regex == 'reload':
					self.out.write(colors.header + '**' + colors.default + ' Changes detected on ' + colors.blue + groups[0] + colors.default + ', reloading\n')
		if not matched: self.out.write(colors.fail + obj + colors.default)

sys.stderr = streamWrapper(sys.stderr)
sys.__stderr__ = streamWrapper(sys.__stderr__)

mode = 'private'
dbpath = ''
for i, arg in enumerate(argv):
	if arg.replace('-', '').lower() == 'mode':
		if len(argv) > i:
			if not (argv[i+1].lower() in ['private', 'public']):
				stderr.write('Mode should be "private" or "public"\n')
				exit(1)
			else: mode = argv[i+1].lower()
	elif arg.replace('-', '').lower() in ['db', 'database']:
		if len(argv) > i:
			if os.path.exists(argv[i+1]) == False:
				print colors.fail + 'Path does not exist' + colors.default
				exit()
			else: dbpath = argv[i+1]
	elif arg.replace('-', '').lower() in ['createdb', 'create']:
		if len(argv) > i:
			if not (argv[i+1].lower() in ['private', 'public']):
				stderr.write('Use: --createdb private or --createdb public\n')
				exit(1)
			else:
				if argv[i+1].lower() == 'private':
					print colors.fail + 'Symlink your Futaam database file to ~/.futahub/main.db or use the --db argument' + colors.default
				else:
					if os.path.exists(os.path.join(os.path.join(os.environ['HOME'], '.futahub/'), 'public.db')):
						print colors.warning + 'File exists' + colors.default
						exit(2)
					if os.path.exists(os.path.join(os.environ['HOME'], '.futahub/')) == False:
						os.mkdir(os.path.join(os.environ['HOME'], '.futahub/'))
					open(os.path.join(os.path.join(os.environ['HOME'], '.futahub/'), 'public.db'), 'w').write(json.dumps({'users': {}}))
					print colors.green + 'Empty database created on ~/.futahub/public.db' + colors.default
					exit()

app = Flask(__name__)

storage_dir = os.path.join(os.environ['HOME'], '.futahub/')

db = {}
if dbpath == '':
	dbpath = os.path.join(storage_dir, 'main.db' if mode == 'private' else 'public.db')
mtime = 0
lastchange = 0
lastwrite = 0

def reload():
	global db, dbpath, mtime
	if os.path.exists(dbpath):
		if os.stat(dbpath).st_mtime != mtime:
			mtime = os.stat(dbpath).st_mtime
			f = open(dbpath, 'r')
			f_contents = f.read().split('\n')
			if len(f_contents) == 2:
				if f_contents[0] == '[json]':
					db = json.loads(f_contents[1])
				elif f_contents[0] == '[pickle]':
					db = pickle.loads(f_contents[1])
				else:
					return False
			else:
				db = json.loads(f_contents[0])
			return True
	return False

def save():
	global db, dbpath
	f = open(dbpath, 'w')
	f.write(json.dumps(db))
	f.close()

def saveWorker():
	global db
	interval = 60
	while True:
		global lastwrite, lastchange
		time.sleep(interval)
		if lastchange > lastwrite:
			save()
			lastwrite = time.time()
swThread = threading.Thread(target=saveWorker)
swThread.setDaemon(True)
swThread.start()

if not reload():
	print('Specify the Futaam file by using the --db argument or put your database on ~/.futahub/main.db')
	exit()

if '--test' in argv:
	db = {'users': {'test': {'username': 'test', 'password': 'aa0be1cfae626f5d8b03825011df6261e282ae8f3725725e886d190eef148841',
	'dbs': [{"count": 0, "items": [], "name": "el db", "description": "lel fgt"}]}}}

mal = utils.MALWrapper()
vndb = utils.VNDB('FutaHub Dev', '0.1')

if mode == 'private':
	@app.route('/')
	def page_index():
		reload()
		return render_template('profile.html', db=db, mode=mode)
else:
	def info():
		global db, session, mode
		logged_in = False
		username = ''
		user = None
		if 'username' in session:
			logged_in = True
			username = escape(session['username'])
			user = db['users'][session['username']]
		return {'logged_in': logged_in, 'username': username, 'user': user, 'mode': mode, 'db': db}

	@app.route('/')
	def page_index():
		logged_in = False
		username = ''
		if 'username' in session:
			logged_in = True
			username = escape(session['username'])
		return render_template('home.html', info=info())
	@app.route('/logout')
	def logout():
		session.pop('username', None)
		return redirect(url_for('page_index'))
	@app.route('/login', methods=['GET', 'POST'])
	def login():
		if request.method == 'POST':
			if request.form.get('username') == None or isinstance(request.form.get('password'), basestring) != True: return render_template('message.html', info=info(), message='Invalid request')

			user = db['users'].get(request.form.get('username'))
			if user != None:
				if user['password'] == hashlib.sha256(request.form.get('password')).hexdigest():
					session['username'] = request.form['username']
					return redirect(url_for('page_index'))
			return render_template('message.html', info=info(), message='Username/password incorrect')
		return render_template('login.html', info=info())
	@app.route('/newdb')
	def newdb():
		if 'username' in session:
			return render_template('newdb.html', info=info())
		else:
			return redirect(url_for('page_index'))
	@app.route('/newdb_empty', methods=['POST'])
	def newdb_empty():
		if 'username' in session:
			assert(isinstance(request.form.get('dbname'), basestring))
			assert(isinstance(request.form.get('dbdesc'), basestring))
			for d in db['users'][session['username']]['dbs']:
				if d['name'] == request.form['dbname']:
					return render_template('message.html', info=info(), message='A database with that name already exists')
			db['users'][session['username']]['dbs'].append({'name': request.form['dbname'], 'description': request.form['dbdesc'], 'count': 0, 'items': []})

			global lastchange
			lastchange = time.time()

			return render_template('message.html', info=info(), message='Database created, connect to this server using Futaam to start editing it')
		else:
			return redirect(url_for('page_index'))
	@app.route('/newdb_existing', methods=['POST'])
	def newdb_existing():
		if 'username' in session:
			assert(request.files.get('dbfile') != None)
			#for d in db['users'][session['username']]['dbs']:
			#	if d['name'] == request.form['dbname']:
			#		return render_template('message.html', info=info(), message='A database with that name already exists')
			#db['users'][session['username']]['dbs'].append({'name': request.form['dbname'], 'description': request.form['dbdesc'], 'count': 0, 'items': []})
			f = request.files['dbfile'].read().split('\n')
			if f[0] != '[json]':
				return render_template('message.html', info=info(), message='Error: not a Futaam file')
			jsondb = json.loads(f[1])
			sanitized = {'items': []}
			sanitized['name'] = jsondb['name'][:128]
			sanitized['description'] = jsondb['description'][:256]
			for i, entry in enumerate(jsondb['items']):
				e = jsondb['items'][i]
				sanitized['items'].append({'status': e['status'][0], 'hash': e['hash'][:128], 'name': e['name'][:128], 'obs': e['obs'][:128], 'lastwatched': e['lastwatched'][:64], 'genre': e['genre'][:256], 'aid': e['aid'], 'type': e['type'][:12], 'id': e['id']})

			db['users'][session['username']]['dbs'].append(sanitized)

			global lastchange
			lastchange = time.time()
			return render_template('message.html', info=info(), message='Database created, connect to this server using Futaam to start editing it')
		else:
			return redirect(url_for('page_index'))
	@app.route('/register', methods=['GET', 'POST'])
	def register():
		if 'username' in session:
			return render_template('message.html', info=info(), message='Already logged in')
		if request.method == 'POST':
			for field, ftype in (('username', basestring), ('password', basestring), ('password2', basestring)):
				if isinstance(request.form.get(field), ftype) == False: return 'Invalid request'

			if request.form['password'] != request.form['password2']:
				return render_template('message.html', info=info(), message='Passwords did not match.')

			if request.form['username'] in db['users']:
				return render_template('message.html', info=info(), message='User already exists.')

			db['users'][request.form['username']] = {'username': request.form['username'], 'password': hashlib.sha256(request.form['password']).hexdigest(),
			'dbs': []}

			global lastchange
			lastchange = time.time()

			session['username'] = request.form['username']
			return render_template('message.html', info=info(), message=u'✔ Registered')
		return render_template('register.html', info=info())

	def serverThread():
		rserver = SocketServer.ThreadingTCPServer(('0.0.0.0', 8500), rServer)
		rserver.db = db
		rserver.allow_reuse_address = True
		rserver.serve_forever()
	thread = threading.Thread(target=serverThread)
	thread.setDaemon(True)
	thread.start()

@app.route('/ajax/entry/<id>')
def ajax_entry(id):
	if not str(id).isdigit():
		return '<h1>Entry not found</h1>', 404
	elif int(id) >= len(db['items']):
		return '<h1>Entry not found</h1>', 404

	entry = deepcopy(db['items'][int(id)])
	for item in entry:
		entry[item] = cgi.escape(unicode(entry[item]))

	if entry['type'] in ['anime', 'manga']:
		return render_template('entry_details.html', entry=entry, deep=mal.details(entry['aid'],
			entry['type']), trstatus=utils.translated_status[entry['type']][entry['status']])
	elif entry['type'] == 'vn':
		deep = vndb.get('vn', 'basic,details', '(id='+ str(entry['aid']) + ')', '')['items'][0]
		platforms = []
		for platform in deep['platforms']:
			names = {'lin': 'Linux', 'mac': 'Mac', 'win': 'Windows', 'and': 'Android', 'oth': 'Other', 'xb3': 'Xbox 360'}
			if platform in names:
				platform = names[platform]
			else:
				platform = platform[0].upper() + platform[1:]
			platforms.append(platform)
		deep['aliases'] = deep['aliases'].replace('\n', '')
		deep['languages'] = '/'.join(deep['languages'])
		return render_template('entry_details.html', entry=entry, deep=deep,
			trstatus=utils.translated_status[entry['type']][entry['status']], platforms='/'.join(platforms),
			aliases_len=len(deep['aliases']))

if __name__ == '__main__':
    app.debug = True if '--debug' in argv else False
    app.secret_key = ''.join([random.choice(string.letters) for x in xrange(0, 30)])
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    try:
    	app.run(host='0.0.0.0')
    except:
    	save()
    	os.kill(os.getpid(), 9)