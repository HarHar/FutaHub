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

if not reload():
	print('Specify the Futaam file by using the --db argument or put your database on ~/.futahub/main.db')
	exit()

if '--test' in argv:
	db = {'users': {'test': {'username': 'test', 'password': '03edf7f5dd7ed2e344a3b1f2ec16c0291902d81fcc60eabc61e35ce61ce53f45f4d6b0e809b36771e75caad552377296b50c359d299d5e79e680848b2aec06ee',
	'db': {"count": 0, "items": [], "name": "el db", "description": "lel fgt"}}}}


mal = utils.MALWrapper()
vndb = utils.VNDB('FutaHub Dev', '0.1')

if mode == 'private':
	@app.route('/')
	def page_index():
		reload()
		return render_template('profile.html', db=db, mode=mode)
else:
	@app.route('/')
	def page_index():
		logged_in = False
		username = ''
		if 'username' in session:
			logged_in = True
			username = escape(session['username'])
		return render_template('home.html', db=db, mode=mode, logged_in=logged_in, username=username)
	@app.route('/test')
	def test():
		session['username'] = 'test'
		return 'Lel logged in as "test" fgt'
	@app.route('/logout')
	def logout():
		session.pop('username', None)
		return redirect(url_for('page_index'))
	@app.route('/login', methods=['GET', 'POST'])
	def login():
		if request.method == 'POST':
			if request.form.get('username') == None or isinstance(request.form.get('password'), basestring) != True: return 'Invalid request'

			user = db['users'].get(request.form.get('username'))
			if user != None:
				if user['password'] == hashlib.sha512(request.form.get('password')).hexdigest():
					session['username'] = request.form['username']
					return redirect(url_for('page_index'))
			return 'Username/password incorrect'
		return render_template('login.html', db=db)

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
    app.run(host='0.0.0.0')
