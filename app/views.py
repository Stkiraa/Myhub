# -*- coding: utf-8 -*-

from app import app
from flask import g,render_template, url_for, request, session, redirect, abort, flash
import pymysql, datetime

def now():
    return str(datetime.datetime.now())[:-7]

@app.route('/')
def index():
	return render_template('welcome.html', title="Welcome")

@app.route('/home')
def home():
	return render_template('base.html', title='Home')
@app.route('/archive')
def show_entries():
    cur = g.db.cursor()
    cur.execute('select title, text from archives order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    print(entries)
    return render_template('archive.html', entries=entries)

@app.route('/add_entry', methods=['POST'])
def add_entry():
    #logged admin can add entries
    if not session.get('logged_in'):
        flash('You are not logged in!')
        return redirect(url_for('login'))
    elif not session.get('admin'):
        flash('You are not admin!')
    else:
        cur = g.db.cursor()
        cur.execute('insert archives (title, text) values (%s, %s)', (request.form['title'].encode('utf-8'), request.form['text'].encode('utf-8')))
        g.db.commit()
        flash('New entry was successfully posted!')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
#flash('you are logging')
        cur = g.db.cursor()
        cr = cur.execute('select name, passwd from users where name = %s' , (request.form['username'].encode('utf-8'),))
        us = [dict(name=row[0], passwd=row[1]) for row in cur.fetchall()] 
        if cr == 0:
            error = 'Invalid username'
        elif request.form['password'].encode('utf-8').decode('utf-8') != us[0]['passwd']:
            error = 'Invalid password'
        else:
            if request.form['username'].encode('utf-8').decode('utf-8') == app.config['ADMIN'].encode('utf-8').decode('utf-8'):
                session['admin'] = True
            else:
                session['admin'] = False
            session['logged_in'] = True
            session['username'] = request.form['username'].encode('utf-8').decode('utf-8')
            flash('Hello! '+session['username'])
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        cur = g.db.cursor()
        cr = cur.execute('select name from users where name = %s', (request.form['username'].encode('utf-8'),))
        if cr:
            flash('The username is existed')
            return redirect(url_for('signup'))
        else:
            cur.execute('insert users (name, passwd, email) values(%s, %s, %s)', (request.form['username'].encode('utf-8'), request.form['password'].encode('utf-8'), request.form['email'].encode('utf-8')))
            g.db.commit()
            flash('Successfully sign up!')     
            return redirect(url_for('login'))
    return render_template('signup.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('admin', None)
    session.pop('username', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        cur = g.db.cursor()
        _str = '%'+request.form['title'].encode('utf-8').decode('utf-8')+'%'
        cr = cur.execute('select id, title from archives where title like %s', (_str.encode('utf-8'),))
        if cr == 0:
            flash('The article is not existed!')
            return redirect(url_for('search'))
        else:
            arcs = [dict(arc_id=row[0], title=row[1]) for row in cur.fetchall()] 
            return render_template('search.html', arcs=arcs)
    return render_template('search.html', arcs=[])
@app.route('/show_article',methods=['GET', 'POST'])
def show_article():
    if request.method == 'POST':
        cur = g.db.cursor()
        cr = cur.execute('select title, text from archives where id = %s', (request.form['art_id'].encode('utf-8'),))
        if not cr:
            print("wrong")
            flash('The article is not existed!')
            return redirect(url_for('search'))
        else:
            print("right")
            arcs = [dict(artid=request.form['art_id'].encode('utf-8').decode('utf-8'), title=row[0], text=row[1]) for row in cur.fetchall()]
            arc = arcs[0]
            cur.execute('select author, date, text, id from comments where arc_id=%s order by id desc', (request.form['art_id'].encode('utf-8'),))
            comts = [dict(author=row[0], date=row[1], text=row[2], comtid=row[3], rcomts=[]) for row in cur.fetchall()]
            for comt in comts:
                cur.execute('select date, text from recomments where comt_id=%s order by id desc', (comt['comtid'],))
                comt['rcomts']=[dict(date=row[0], text=row[1]) for row in cur.fetchall()]
            return render_template('article.html', artid=arc['artid'], arctitle=arc['title'], arctext=arc['text'],comts=comts)
    return render_template('article.html')

@app.route('/add_comment', methods=['GET', 'POST'])
def add_comment():
    if not session.get('logged_in'):
        flash('You are not logged in!')
        return redirect(url_for('login'))
    if request.method == 'POST':
        cur = g.db.cursor()
        args=(request.form['art_id'].encode('utf-8'), now().encode('utf-8'), request.form['text'].encode('utf-8'), session['username'].encode('utf-8'))
        cur.execute('insert comments(arc_id, date, text, author) values(%s,%s,%s,%s)', args)
        g.db.commit()
        return redirect(url_for('show_article')+'?ID='+request.form['art_id'].encode('utf-8').decode('utf-8'))
    return render_template('comment.html')
@app.route('/reply', methods=['GET', 'POST'])
def reply():
    if not session.get('logged_in'):
        flash('You are not logged in!')
        return redirect(url_for('login'))
    if request.method == 'POST':
        cur = g.db.cursor()
        args=(request.form['comt_id'].encode('utf-8'), now().encode('utf-8'), request.form['text'].encode('utf-8'))
        cur.execute('insert recomments(comt_id, date, text) values(%s,%s,%s)', args)
        g.db.commit()
        return redirect(url_for('show_article')+'?ID='+request.form['art_id'].encode('utf-8').decode('utf-8'))
    return render_template('reply.html')
@app.route('/delete', methods=['POST'])
def delete():    
    cur = g.db.cursor()
    cur.execute('select id from comments where arc_id=%s', (request.form['art_id'].encode('utf-8'),))
    comts = [dict(comtid=row[0]) for row in cur.fetchall()]
    for comt in comts:
        cur.execute('delete from recomments where comt_id = %s', (comt['comtid'],))
        g.db.commit()
    cur.execute('delete from comments where arc_id = %s', (request.form['art_id'].encode('utf-8'),))
    g.db.commit()
    cur.execute('delete from archives where id = %s', (request.form['art_id'].encode('utf-8'),))
    g.db.commit()
    _str = '%'+request.form['title'].encode('utf-8').decode('utf-8')+'%'
    cr = cur.execute('select id, title from archives where title like %s', (_str.encode('utf-8'),))
    if cr == 0:
        flash('The article is not existed!')
        return redirect(url_for('search'))
    else:
        arcs = [dict(arc_id=row[0], title=row[1]) for row in cur.fetchall()] 
        return render_template('search.html', arcs=arcs)
                
@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        cur = g.db.cursor()
        args=(request.form['title'].encode('utf-8'), request.form['text'].encode('utf-8'), request.form['art_id'].encode('utf-8'))
        cur.execute('update archives set title=%s, text=%s where id=%s', args)
        g.db.commit()
        return redirect(url_for('show_article')+'?ID='+request.form['art_id'].encode('utf-8').decode('utf-8'))
    return render_template('update.html')
