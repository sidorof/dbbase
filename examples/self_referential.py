# examples/self_referential.py
"""
This example shows an example where serialization works with
self-referential models.
"""
from dbbase import DB

db = DB(config=":memory:")


class Node(db.Model):
    """self-referential table"""

    __tablename__ = "nodes"
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("nodes.id"))
    data = db.Column(db.String(50))
    children = db.relationship(
        "Node", lazy="joined", order_by="Node.id", join_depth=10
    )

    SERIAL_FIELDS = ["id", "parent_id", "data", "children"]


db.create_all()

node1 = Node(id=1, data="this is node1")
node2 = Node(id=2, data="this is node2")
node3 = Node(id=3, data="this is node3")
node4 = Node(id=4, data="this is node4")
node5 = Node(id=5, data="this is node5")
node6 = Node(id=6, data="this is node6")

db.session.add(node1)
db.session.commit()
node1.children.append(node2)
db.session.commit()
node2.children.append(node3)
db.session.commit()
node2.children.append(node4)
db.session.commit()
node1.children.append(node5)
db.session.commit()
node5.children.append(node6)
db.session.commit()

print("Example of self-referential serialization")
print(node1.serialize(indent=2))
input("ready")

print("Example in compact form")
print(node1.serialize())
