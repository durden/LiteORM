#LiteORM
Tiny ORM (Object Relational Mapper) for Python and SQLite3

##Why
There are several great ORMs for Python (
[SQLAlchemy](http://www.sqlalchemy.org/), ([SQLObject](http://www.sqlobject.org)))
but they can be somewhat big and have several other dependencies.  This isn't
usually a problem, but I figured this was an opportunity to learn more about
how ORMs work and do a little Python metaprogramming and inspection.

###Usage

Test it from command line

    python liteorm/orm.py

From Python

    class User(object):
        def __init__(self, name, age, email):
            self.id = 0
            self.name = name
            self.age = age
            self.email = email

        def __str__(self):
            return 'id: %d, name: %s, age: %d, email: %s' % (self.id,
                                                             self.name,
                                                             self.age,
                                                             self.email)
    user = User('luke', 100, 'mymail')
    db = LiteORM('test.db')
    db.create_table(user)
    db.insert(user)
    user.name = 'charles'
    db.update(user)

    res = db.select(User, 'name = "charles"')
    for user in res:
        print user
