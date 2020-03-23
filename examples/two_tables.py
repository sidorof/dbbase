# two_tables.py
"""
This example mirrors the user guide example for serialization with
two tables.
"""

from dbbase import DB

db = DB(config=':memory:')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name =  db.Column(db.String(50), nullable=False)
    addresses = db.relationship(
        "Address", backref="user", lazy='immediate')

    def full_name(self):
        return '{first} {last}'.format(
            first=self.first_name, last=self.last_name)

class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

db.create_all()

user = User(id=3, first_name='Bob', last_name='Smith')
user.save()

address1 = Address(
    email_address='email1@example.com',
    user_id=user.id
)
address2 = Address(
    email_address='email2@example.com',
    user_id=user.id
)

db.session.add(address1)
db.session.add(address2)
db.session.commit()

# ------------------------------------------------
print('default serialization for user')
print(user.serialize(indent=2))
input('ready')

# ------------------------------------------------
print('modified serialization: stop list for first/last names')
User.SERIAL_STOPLIST = ['first_name', 'last_name']
print(user.serialize(indent=2))
input('ready')

# ------------------------------------------------
print('now only the email_address portion of address shows')
Address.SERIAL_LIST = ['email_address']
print(user.serialize(indent=2))
input('ready')

# ------------------------------------------------
User.SERIAL_LIST = None
User.SERIAL_STOPLIST = []
User.SERIAL_STOPLIST = None

Address.SERIAL_LIST = None
Address.SERIAL_STOPLIST = []
Address.SERIAL_STOPLIST = None

print('full again')
print(user.serialize(indent=2, sort=True))
input('ready')
print()
print('serialization of just an address')
print(address1.serialize(indent=2, sort=True))
input('ready')

# ------------------------------------------------
User.SERIAL_LIST = ['id', 'first_name', 'last_name', 'addresses']
print(user.serialize(indent=2))
