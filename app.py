from flask import Flask, session
from flask.ext import restful
from flask.ext.restful import reqparse, abort, Api, Resource
from flask.ext.httpauth import HTTPBasicAuth
from models import *

application = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@127.0.0.1/contas'
application.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

auth = HTTPBasicAuth()

db.init_app(application)
api = restful.Api(application)


@auth.verify_password
def verify_password(token, password):
    if 'token' in session:
        user = User.query.filter_by(token=session['token']).first()

        if user:
            return True
    else:
        return None

    return None


#TODO: SEPARATE THEM INTO BLUEPRINTS
class UsersList(Resource):

    @auth.login_required
    def get(self, user_id):
        user = User.query.get(user_id)
        return user.serialize


class Users(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', type=str)
        self.parser.add_argument('email', type=str)
        self.parser.add_argument('password', type=str)

    def post(self):
        try:
            args = self.parser.parse_args()
            user = User(args['username'], args['email'], args['password'])

            if not User.verify_user_exists(user.username, user.email):
                db.session.add(user)
                db.session.commit()

                user.generate_token(user.id)
                session['token'] = user.token
                session['user_id'] = user.id

                return {'token': user.token, 'user_id': user.id}, 200
            else:
                return False, 400
        except Exception as e:
            print(e)


class UserLogin(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', type=str)
        self.parser.add_argument('password', type=str)

    def post(self):
        args = self.parser.parse_args()

        user = User.query.filter_by(username=args['username']).first()
        correct_password = user.check_password(args['password'])

        if correct_password:

            user.generate_token(user.id)
            session['token'] = user.token

            return {'token': user.token}, 200
        else:
            return False, 400

#---------------------------------------------------------------------------------

class Transactions(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('user_id', type=int)
        self.parser.add_argument('category', type=int)
        self.parser.add_argument('type', type=int)
        self.parser.add_argument('amount', type=float)
        self.parser.add_argument('description', type=str)

    @auth.login_required
    def post(self):
        args = self.parser.parse_args()
        transaction = Transaction(args['user_id'], args['category'], args['type'],
                                  args['amount'], args['description']
                                 )

        db.session.add(transaction)
        db.session.commit()

        return 'added', 200

class TransactionsList(Resource):

    @auth.login_required
    def get(self, user_id):
        return Transaction.get_all_by_user_id(user_id)

#---------------------------------------------------------------------------------------
api.add_resource(UsersList, '/users/<user_id>')
api.add_resource(Users, '/user/')

api.add_resource(Transactions, '/transaction/')
api.add_resource(TransactionsList, '/transactions/<user_id>')


if __name__ == '__main__':

    application.run(debug=True, port=2323)
