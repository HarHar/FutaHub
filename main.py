#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, send_from_directory
from werkzeug import secure_filename
from sys import argv, stderr
import cgi
import utils
from copy import deepcopy

mode = 'private'
for i, arg in enumerate(argv):
	if arg.replace('-', '').lower() == 'mode':
		if len(argv) > i:
			if not (argv[i+1].lower() in ['private', 'public']):
				stderr.write('Mode should be "private" or "public"\n')
				exit(1)

app = Flask(__name__)

import os, json
storage_dir = os.path.join(os.environ['HOME'], '.futahub/')

db = {}
if os.path.exists(os.path.join(storage_dir, 'main.db')):
	db = json.loads(open(os.path.join(storage_dir, 'main.db')).read().split('\n')[1])
else:
	print('Put your database on ~/.futahub/main.db')
	print('This behavior will be changed on the future')
	exit()

mal = utils.MALWrapper()
vndb = utils.VNDB('FutaHub Dev', '0.1')

if mode == 'private':
	@app.route('/')
	def page_index():
	    return render_template('profile.html', db=db)
else:
	@app.route('/')
	def page_index():
		return 'Not implemented yet', 418 #Error 418 I'm a teapot

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
    app.run(host='0.0.0.0')
