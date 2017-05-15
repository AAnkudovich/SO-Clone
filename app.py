from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
import datetime
from slugify import slugify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
import QuestionMatcher as matcher

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/ezylia'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

db=SQLAlchemy(app)
Bootstrap(app)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(),Length(min=4, max=80)])
    password = PasswordField('Password', validators=[InputRequired,Length(min=8, max=80)])
    remember = BooleanField('Remember me')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('Username', validators=[InputRequired(), Length(min=4)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, unique=False)
    subject = db.Column(db.String(160), unique=False)
    slug = db.Column(db.String(160), unique=True)
    body = db.Column(db.String(2000), unique=False)
    answerNo = db.Column(db.Integer, unique=False)
    views = db.Column(db.Integer, unique=False)

    def __init__(self, subject, body,slug, answerNo ):
        self.timestamp = datetime.datetime.now()
        self.subject = subject
        self.slug = slug
        self.body = body
        self.views = 0
        self.answerNo = 0

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, unique=False)
    question_id = db.Column(db.Integer, unique=False)
    body = db.Column(db.String(2000), unique=False)
    upvote_count = db.Column(db.Integer, unique=False)

    def __init__(self, question_id, body):
        self.timestamp = datetime.datetime.now()
        self.question_id = question_id
        self.body = body
        self.upvote_count = 0


@app.route('/')
def index():
	questions = Question.query.all()
	return render_template('home.html', questions=questions)

@app.route('/ask-ezylia', methods=['GET', 'POST'])
def askEzylia():
	if request.method == 'POST':
            subject = request.form['question_subject']
            body = request.form['question_body']
            date = datetime.datetime.now()
            slug = slugify(request.form['question_subject'])
            pre_entries = Question.query.filter(Question.slug.contains(slug))

            if pre_entries.count():
                slug += '-%s' % (pre_entries.count() + 1,)
            # slugify(request.form['question_subject'] )
            question = Question(subject, body, slug, 0)
            db.session.add(question)
            db.session.commit()
            return redirect('/')
  	else:
    		return render_template('ask-ezylia.html')


@app.route('/ask-ezylia/<string:question_slug>', methods=['GET'])
def question(question_slug):
    question = Question.query.filter_by(slug=question_slug).first()
    question.views += 1
    db.session.commit()
    answers = Answer.query.filter_by(question_id=question.id).all()
    return render_template('question.html', question=question, answers=answers)

@app.route('/answer/<int:question_id>', methods=['POST'])
def answer(question_id):
    question = Question.query.get(question_id)
    question.answerNo += 1
    body = request.form['answer_body']
    answer = Answer(question.id, body)
    db.session.add(answer)
    db.session.commit()
    return redirect('/ask-ezylia/' + question.slug)


@app.route('/api/question/<int:question_id>', methods=['GET'])
def api_question(question_id):
    question = Question.query.get(question_id)
    return jsonify({"question_id":question.id, "subject":question.subject})


@app.route('/api/upvote/<int:answer_id>', methods=['GET', 'POST'])
def upvote(answer_id):
    answer = Answer.query.get(answer_id)
    if answer is None:
        return make_json_error(500)

    if request.method == 'POST':
        answer.upvote_count += 1
        db.session.commit()
        return jsonify({'success': True, 'new_total': answer.upvote_count}), 200, {'ContentType': 'application/json'}
    else:
        return jsonify(upvote_count=answer.upvote_count)


@app.route('/api/matchscore', methods=['GET'])
def get_match_score():
    subject = request.args.get('subject')
    match_score = matcher.get_match_scores(subject)
    return jsonify({"matchscore":match_score})

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    # if request.method == 'POST':
    if form.validate_on_submit():
        return '<h1>' + str(form.data) + '</h1>'


    return render_template('login.html', form=form)

@app.route('/sign-up', methods=['GET', 'POST'])
def signup():
    form= RegisterForm()

    return render_template('signup.html', form=form)


if __name__ == '__main__':
	app.run(debug=True)