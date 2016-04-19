from flask import Flask, render_template, session, redirect, url_for, flash
from flask import request
from datetime import datetime

from flask.ext.script import Manager

from flask.ext.bootstrap import Bootstrap

from flask.ext.moment import Moment

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required

from flask.ext.sqlalchemy import SQLAlchemy

import os

from flask.ext.mail import Mail, Message
import traceback
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)




app = Flask(__name__)
manager = Manager(app)
Bootstrap(app)
moment = Moment(app)

basedir = os.path.abspath(os.path.dirname(__file__))



app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] =
app.config['FLASKY_ADMIN'] =

app.config['MAIL_SERVER'] = 'smtp.163.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] =
app.config['MAIL_PASSWORD'] =


class NameForm(Form):
    name = StringField('What is your name', validators=[Required()])
    # 可选参数 validators 指定一个由验证函数组成的列表,在接受用户提交的数据之前验证数据。验证函数 Required() 确保提交的字段不为空。
    submit = SubmitField('Submit')


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)
mail = Mail(app)

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     form = NameForm()
#     if form.validate_on_submit():
#         old_name = session.get('name')
#         if old_name is not None and old_name != form.name.data:
#             flash('Looks like you have changed your name!')
#         session['name'] = form.name.data
#         return redirect(url_for('index'))
#     return render_template('index.html', current_time=datetime.utcnow(), form=form, name=session.get('name'))

def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + subject, sender=app.config['FLASKY_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            if app.config['FLASKY_ADMIN']:
                try:
                    send_email(app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user)
                except Exception as e:
                    exstr = traceback.format_exc()
                    print(exstr)
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html', current_time=datetime.utcnow(), form=form, name=session.get('name'),
                           known=session.get('known', False))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<Role %r>' % self.name

    users = db.relationship('User', backref='role')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)

    def __repr__(self):
        return '<User % r>' % self.username

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))


app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config['SECRET_KEY'] = 'hard to guess'

from flask.ext.script import Shell


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


manager.add_command('shell', Shell(make_context=make_shell_context))

from flask.ext.migrate import Migrate, MigrateCommand

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    db.create_all()
    manager.run()
