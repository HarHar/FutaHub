#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, send_from_directory
from werkzeug import secure_filename
from sys import argv
import cgi
import utils
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

@app.route('/')
def page_index():
    return render_template('profile.html', db=db)

@app.route('/ajax/entry/<id>')
def ajax_entry(id):
	entry = db['items'][int(id)].copy()
	for item in entry:
		entry[item] = cgi.escape(unicode(entry[item]))

	if entry['type'] in ['anime', 'manga']:
		deep = mal.details(entry['aid'], entry['type'])
	elif entry['type'] == 'vn':
		deep = vndb.get('vn', 'basic,details', '(id='+ str(entry['aid']) + ')', '')['items'][0]

	if entry['type'] == 'anime':
		out = '<img src="{0}" style="float: left; padding-right: 10px;" />'.format(deep['image_url'])
		out += '<h1>' + entry['name'] + '</h1>'
		out += '<b>Status: </b>{0}'.format(utils.translated_status[entry['type']][entry['status']]) + '<br />'
		out += '<b>Last episode watched: </b>{0}'.format(entry['lastwatched']) + '<br />'
		out += '<b>Total episodes: </b>{0}'.format(deep['episodes']) + '<br />'
		out += '<b>Genre: </b>{0}'.format(entry['genre']) + '<br />'
		if deep['end_date'] != None:
			out += '<b>Year: </b>{0} - {1}'.format(deep['start_date'], deep['end_date']) + '<br />'
		else:
			out += '<b>Year: </b>{0} - {1}'.format(deep['start_date'], 'ongoing') + '<br />'
		out += '<b>Type: </b>{0}'.format(deep['type']) + '<br />'
		out += '<b>Classification: </b>{0}'.format(deep['classification']) + '<br />'
		out += '<b>Synopsis: </b>{0}'.format(utils.remove_html_tags(deep['synopsis'])) + '<br />'
		out += '<br /><b>Observations: </b>{0}'.format(entry['obs']) if entry['obs'] != '' else '<br /><b>No observations</b>'
	elif entry['type'] == 'manga':
		out = '<img src="{0}" style="float: left; padding-right: 10px;" />'.format(deep['image_url'])
		out += '<h1>' + entry['name'] + '</h1>'
		out += '<b>Status: </b>{0}'.format(utils.translated_status[entry['type']][entry['status']]) + '<br />'
		out += '<b>Last chapter/volume read: </b>{0}'.format(entry['lastwatched']) + '<br />'
		out += '<b>Chapters/volumes: </b>{0}/{1}'.format(deep['chapters'], deep['volumes']) + '<br />'
		out += '<b>Type: </b>{0}'.format(deep['type']) + '<br />'
		out += '<b>Synopsis: </b>{0}'.format(utils.remove_html_tags(deep['synopsis'])) + '<br />'
		out += '<br /><b>Observations: </b>{0}'.format(entry['obs']) if entry['obs'] != '' else '<br /><b>No observations</b>'
	elif entry['type'] == 'vn':
		"""				toprint = {'Name': entry['name'], 'Genre': entry['genre'],
				 'Observations': entry['obs'], 'Status': utils.translated_status[entry['type']][entry['status'].lower()]}
		"""
		out = '<img src="{0}" style="float: left; padding-right: 10px;" />'.format(deep['image'])
		if len(deep['aliases']) == 0:
			out += '<h1>' + deep['title'] + '</h1>'
		else:
			out += '<h1>' + deep['title'] + '</h1><h3> [' + deep['aliases'].replace('\n', '/') + ']</h1>' 
		out += '<b>Status: </b>{0}'.format(utils.translated_status[entry['type']][entry['status']]) + '<br />'
		platforms = []
		for platform in deep['platforms']:
			names = {'lin': 'Linux', 'mac': 'Mac', 'win': 'Windows', 'and': 'Android', 'oth': 'Other', 'xb3': 'Xbox 360'}
			if platform in names:
				platform = names[platform]
			else:
				platform = platform[0].upper() + platform[1:]
			platforms.append(platform)
		out += '<b>Platforms: </b>{0}'.format('/'.join(platforms)) + '<br />'
		out += '<b>Released: </b>{0}'.format(deep['released']) + '<br />'
		out += '<b>Languages: </b>{0}'.format('/'.join(deep['languages'])) + '<br />'
		out += '<b>Synopsis: </b>{0}'.format(deep['description']) + '<br />'
		out += '<br /><b>Observations: </b>{0}'.format(entry['obs']) if entry['obs'] != '' else '<br /><b>No observations</b>'
	return out


if __name__ == '__main__':
    app.debug = True if '--debug' in argv else False
    app.run(host='0.0.0.0')
