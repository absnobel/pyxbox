from datetime import datetime
from flask_login import AnonymousUserMixin


class User(AnonymousUserMixin):
  
    def __repr__(self):
        return '<User{}>'
