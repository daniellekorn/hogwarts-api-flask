import json


class Student:

    def __init__(self, first, last, house, magic_skills, desired_skills, course_interest):
        self.first = first
        self.last = last
        self.name = f"{first} {last}"
        self.house = house
        self.magic_skills = magic_skills
        self.desired_skills = desired_skills
        self.course_interest = course_interest

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def as_obj(self):
        return self.__dict__

    # whenever updating need to do last-update: datetime.datetime.utcnow()
