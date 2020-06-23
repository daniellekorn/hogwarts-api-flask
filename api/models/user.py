class User(dict):

    def __init__(self, first, last, email, username, password):
        dict.__init__(self, first=first, last=last, email=email, username=username, password=password)
