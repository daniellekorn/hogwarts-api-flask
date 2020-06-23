from flask import Flask, json, request
from data.dataLayer import DataLayer
from data.skills import Skills
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from models.user import User
from data.mconfig import myCode

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = MYCODE

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

datalayer = DataLayer(app)


@app.route("/students", methods=["GET", "POST"])
def get_all_students():
    if request.method == "POST":
        content = request.json
        new_student = datalayer.create_student_from_dict(content)
        datalayer.add_student(new_student.as_obj())
        return app.response_class(response=json.dumps({'new student': new_student}, default=str), status=200,
                                  mimetype='application/json')
    else:
        students = [student.as_obj() for student in datalayer.get_all_students()]
        return app.response_class(response=json.dumps({'students': students}), status=200, mimetype='application/json')


@app.route("/students/<student_name>",  methods=["GET", "PUT", "DELETE"])
def student_profile(student_name):
    if request.method == "PUT":
        content = request.json
        datalayer.update_student(content)
        return app.response_class(response={'updated': student_name}, status=200, mimetype='application/json')
    elif request.method == "DELETE":
        student = datalayer.get_id_by_name(student_name)
        datalayer.delete_student(student)
        return app.response_class(response={'deleted': student_name}, status=200, mimetype='application/json')
    else:
        student = datalayer.get_student(student_name)
        return app.response_class(response=student.to_json(), status=200, mimetype='application/json')


@app.route('/authorize/<password>', methods=['GET'])
def authorize_delete(password):
    answer = datalayer.check_password(password)
    return app.response_class(response=json.dumps(answer, default=str), status=200, mimetype='application/json')


@app.route('/dashboard/perday', methods=["GET"])
def students_per_day():
    answer = list(datalayer.students_added_per_day())
    return app.response_class(response=json.dumps(answer), status=200, mimetype='application/json')


@app.route('/dashboard/desired', methods=["GET"])
def desired_skills():
    answer = list(datalayer.students_with_desired_magic())
    return app.response_class(response=json.dumps(answer), status=200, mimetype='application/json')


@app.route('/dashboard/skills', methods=["GET"])
def all_skills():
    answer = list(datalayer.students_with_each_skill())
    return app.response_class(response=json.dumps(answer), status=200, mimetype='application/json')


@app.route('/dashboard/courses', methods=["GET"])
def course_interest():
    answer = datalayer.most_desired_course()
    return app.response_class(response=json.dumps(answer), status=200, mimetype='application/json')


@app.route('/users/signup', methods=["POST"])
def signup():
    content = request.json
    if content.get('password') != content.get('confirm'):
        return app.response_class(response={'Error: Passwords do not match'}, status=400, mimetype='application/json')
    elif (content.get('first') and content.get('last') and content.get('email') and content.get('username') and
          content.get('password')):
        # will not allow to make new profile based on pre-existing username or email
        if datalayer.find_user_by_email(content.get('email')):
            return app.response_class(response={'User with given email already exists'}, status=400,
                                      mimetype='application/json')
        if datalayer.find_user_by_username(content.get('username')):
            return app.response_class(response={'Username already in use'}, status=400, mimetype='application/json')
        try:
            new_user = User(content.get('first'), content.get('last'), content.get('email'), content.get('username'),
                       bcrypt.generate_password_hash(content.get('password')).decode('utf-8'))
        except ValueError as e:
            return app.response_class(response={f'{e}'}, status=400, mimetype='application/json')
        except Exception as e:
            print(e)
            return app.response_class(response={f'{e}'}, status=400, mimetype='application/json')
        user_id = datalayer.add_user(new_user)
        created_user = datalayer.get_user_by_id(user_id)
        return app.response_class(response=json.dumps(created_user), status=200, mimetype='application/json')
    else:
        return app.response_class(response={'All fields are required'}, status=400, mimetype='application/json')


@app.route('/users/login', methods=['POST'])
def login():
    content = request.json
    username = content.get('username')
    password = content.get('password')

    response = datalayer.find_user_by_username(username)

    if response:
        if bcrypt.check_password_hash(response.get('password'), password):
            access_token = create_access_token(identity={
                'first': response.get('first'),
                'last': response.get('last'),
                'username': response.get('username'),
            })
            result = {'token': access_token}
        else:
            result = {"error": "Invalid password"}
    else:
        result = {"result": "No such user found"}
    return result


if __name__ == "__main__":
    app.run()
