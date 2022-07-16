from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import re


app = Flask(__name__)
cors = CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'shop.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'

app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'random_username'
app.config['MAIL_PASSWORD'] = 'random_password'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create(): # Creates database
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop(): # Deletes database
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    shop = Category(category_name = 'Shop',
                    item_range=24,)

    db.session.add(shop)
    db.session.commit()


categories = [{
    'id': 1,
    'name':'Todd', 
},
{
    'id':2, 
    'name':'Walter'
}]

category_global_index = len(categories)


# category_relationship = {
#     parent_id:1,
#     child_id:1,
# }

@app.route('/')
def welcome():
    return "Welcome to the Jungle!"


@app.route('/confirm_age', methods=['GET'])
def confirm_age():
    over_18 = False

    if over_18:
        return jsonify(message='Welcome!'), 401 # UNAUTHORISED
    else:
        return jsonify(message='You must be over 18 years old to enter this page.'), 200 # OK
        

@app.route('/categories', methods=['GET'])
def get():
    return jsonify({'categories':categories})


@app.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    return jsonify({'category':categories[id -1]})


@app.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    category_index = None

    for index, category in enumerate(categories):
        if category['id'] == id:
            category_index = index
            break
    
    if category_index != None:
        categories.pop(category_index)

    return jsonify()


@app.route('/categories', methods=['POST'])
def add_category():
    print('request')
    json = request.get_json()
    
    global category_global_index

    print(json)
    category_global_index = category_global_index + 1

    category = {
        'id': ((category_global_index)),
        'name': json['name'],
    }
    return jsonify({'category':category})


@app.route('/categories/<int:id>', methods=['UPDATE'])
def update_category(id: int):
    category_id = int(request.form['id'])
    category = category.query.filter_by(category_id=category_id).first()
    if category:
        category.category_name = request.form['name']
        category.category_type = request.form['category_type']
        return jsonify(message='Category updated!')   


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()


    if re.search('^\w+@(\w+\.)?\w+\.(com|org|net|edu|gov|info|io|pl)$', email, re.IGNORECASE):
        if test:
            return jsonify(message="That email already exists in our database."), 409 # CONFLICT
        else:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            password = request.form['password']
            user = User(fisrt_name=first_name, last_name=last_name,email=email, password=password)

            db.session.add(user)
            db.session.commit()
            return jsonify(message='User created successfully.'), 201 # CREATED

    else:
        return jsonify(message='email is invalid')

@app.route('/login', methods=['POST'])
def login():

    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    
    test = User.query.filter_by(email=email, password=password).first()

    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded!', access_token=access_token)
    else:
        return jsonify(message='Wrong email or password'), 401 # PERMISSION DENIES 


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    
    if user:
        msg = Message(
            'Your password is ' + user.password,
            sender = 'shop@mail.com',
            recipients=[email] 
        )
        mail.send(msg)

        return jsonify(message='Password sent to ' + email)
    else:
        return jsonify(message='No such email in our database.'), 401 # UNAUTHORISED


@app.route('/remove_user/<int:id>', methods=['DELETE'])
def remove_user(id: int):
    user = User.query.filter_by(id=id).first()

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(message='User successfully removed!')
    else:
        return jsonify(message='User does not exist.')


# database models:
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Category(db.Model):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String)
    item_range = Column(Integer)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class CategorySchema(ma.Schema):
    class Meta:
        fields = ('category_id', 'category_name', 'item_range')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
        

if __name__ == '__main__':
    app.run(debug=True)

# before using flask commands in CLI, type: 
    # export FLASK_APP=app_name.py