from pymongo import MongoClient
from bson.objectid import ObjectId
from models.student import Student
from data.mconfig import MPASS
from datetime import datetime
from flask_caching import Cache
from models.user import User


class DataLayer:

    def __init__(self, app):
        self.__cluster = MongoClient\
            (f"mongodb+srv://dtonkorn:{MPASS}@cluster0-o7bkz.mongodb.net/test?retryWrites=true&w=majority")
        self.__db = self.__cluster["hogwarts"]
        self.__collection = self.__db["students"]
        self.__user_collection = self.__db["users"]
        cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_THRESHOLD': 1000})
        cache.init_app(app)
        self.__cache = cache

    # STUDENT DB FUNCTIONALITY
    def get_all_students(self):
        students = [doc for doc in self.__collection.find()]
        student_dicts = [self.create_student_from_dict(student) for student in students]
        for student in student_dicts:
            self.__cache.set(student.first, student, timeout=30)
        return student_dicts

    def get_student(self, name):
        student = self.__cache.get(name.split()[0])
        if not student:
            student = self.__db.students.find_one({"first": name.split()[0], "last": name.split()[1]})
        return student

    def get_id_by_name(self, student_name):
        split_name = student_name.split()
        student = self.__db.students.find_one({"first": split_name[0], "last": split_name[1]})
        student_id = student['_id']
        return student_id

    def add_student(self, student):
        try:
            self.__collection.insert(student)
        except Exception as e:
            return {f'Error: {e}'}

    def update_student(self, data):
        try:
            self.__collection.update({"last": data.get('last')},
                                     {"$set": {'magic_skills': data.get('magic_skills'), 'desired_skills':
                                      data.get('desired_skills'), 'course_interest': data.get('course_interest'),
                                      'last_updated': datetime.now()}})
            self.__cache.delete("students")
            print("cache deleted")
        except Exception as e:
            return {f'Error: {e}'}

    def delete_student(self, student_id):
        try:
            self.__cache.delete(student_id)
            self.__collection.delete_one({'_id': ObjectId(student_id)})
        except Exception as e:
            return {f'Error: {e}'}

    def check_password(self, password):
        return self.__db["deleteAuth"].find_one({'password': password})

    def students_added_per_day(self):
        return self.__collection.aggregate([{
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%m-%d",
                        "date": {"$toDate": "$_id"},
                    }
                },
                "count": {"$sum": 1}
            }
        }])

    def students_with_desired_magic(self):
        desired = self.__collection.aggregate([{"$unwind": "$desired_skills"}, {"$group": {'_id': "$desired_skills",
                                              'count': {"$sum": 1}}}])
        return desired

    def students_with_each_skill(self):
        skills_data = self.__collection.aggregate([{"$project": {'skills_arr': {"$objectToArray": '$magic_skills'}}},
                        {"$unwind": "$skills_arr"},
                        {"$group": {'_id': "$skills_arr.k", 'count': {"$sum": 1}}}])
        return skills_data

    def most_desired_course(self):
        desired = self.__collection.aggregate([{"$unwind": "$course_interest"}, {"$group": {'_id': "$course_interest",
                                              'count': {"$sum": 1}}}])
        biggest = 0
        for item in list(desired):
            if item['count'] > biggest:
                biggest = item['count']
                desired = item
        return desired

    @staticmethod
    def create_student_from_dict(student_dict):
        return Student(student_dict.get('first'), student_dict.get('last'), student_dict.get('house'),
                       student_dict.get('magic_skills'), student_dict.get('desired_skills'),
                       student_dict.get('course_interest'))

    # USER DB FUNCTIONALITY
    def add_user(self, user):
        try:
            user = self.__user_collection.insert(user)
            return user
        except Exception as e:
            return {f'Error: {e}'}

    def find_user_by_email(self, email):
        user = self.__user_collection.find_one({"email": email})
        user_obj = self.create_user_from_dict(user)
        return user_obj

    def get_user_by_id(self, user_id):
        user = self.__user_collection.find_one({"_id": ObjectId(user_id)})
        user_obj = self.create_user_from_dict(user)
        return user_obj

    def find_user_by_username(self, username):
        user = self.__user_collection.find_one({"username": username})
        user_obj = self.create_user_from_dict(user)
        return user_obj

    @staticmethod
    def create_user_from_dict(user):
        return User(user.get('first'), user.get('last'), user.get('email'), user.get('username'), user.get('password'))


