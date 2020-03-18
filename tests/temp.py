from dbbase.dbinfo import DB

db = DB(':memory:')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    address = db.relationship("Address", backref="users", lazy='immediate')


class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship("User", back_populates="addresses")

User.addresses = db.relationship(
    "Address", back_populates="user", lazy='immediate')
    #"Address", order_by='Address.id', back_populates="user")

User.metadata.create_all(db.session.bind)

user = User(name='Bob')
db.session.add(user)
db.session.commit()

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

print('user type', type(user))
print('user.addresses', user.addresses)
print('there are ', len(user.addresses), 'addresses')
print('--------------------------')
print('address1.serialize()', address1.serialize())
print('address2.serialize()', address2.serialize())
print('address1.user')
print()
print('user.serialize()', user.serialize())

#self.assertDictEqual(
    #{
        #"userId": 1,
        #"emailAddress": "email1@example.com",
        #"id": 1
    #},
    #address1.to_dict()
#)
#input('ready address1.to_dict()')
#self.assertDictEqual(
    #{
        #"id": 1,
        #"name": "Bob",
        #"addresses": [
            #{
            #"userId": 1,
            #"emailAddress": "email1@example.com",
            #"id": 1
            #},
            #{
            #"userId": 1,
            #"emailAddress": "email2@example.com",
            #"id": 2
            #}
        #]
    #},
    #user.to_dict()
#)
