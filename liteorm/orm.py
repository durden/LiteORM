"""
Tiny little ORM (Object Relational Mapper) for SQLite 3.
"""


import inspect
import sqlite3

# FIXME: Lots of little 'id' hacks, can probably use inspect.getmembers()
# FIXME: Doesn't support empty/optional fields


class UnsupportedTypeError(Exception):
    """Data type is not supported"""
    pass


class LiteORM(object):
    """
    Provides a way to write/read to SQLite 3 database with Python objects

    The following assumptions must be satisfied to use this ORM with your
    Python class:
        - It must have an integer member called 'id'.

    This ORM has the following limitations:
        - Only integers and string types allowed
        - No None or NULL values allowed
        - Not very secure for possible SQL injection issues
    """

    def __init__(self, name):
        """Create database object with given filename"""

        self._name = name
        self._connection = sqlite3.connect(name)
        self._cursor = self._connection.cursor()

    @property
    def name(self):
        """Return name of database file"""

        return self._name

    @property
    def connection(self):
        """Return connection for database object"""

        return self._connection

    @property
    def cursor(self):
        """Return cursor of database object"""

        return self._cursor

    def _sqlize_value(self, value):
        """Prepare value so that it can be inserted into sql statement"""

        if isinstance(value, int):
            return '%s' % (value)
        else:
            # Strings are quoted in sql
            return "'%s'" % (value)

    def create_table(self, model):
        """
        Create table for given model class definition

        Any attributes that are None are assumed to be string type for now.
        """

        table_name = model.__class__.__name__

        # Create mapping of attribute name and type
        attrs = {}
        for name, value in model.__dict__.iteritems():
            if isinstance(value, int):
                if name == 'id':
                    attrs[name] = 'integer primary key autoincrement'
                elif name.endswith('_id'):
                    attrs[name] = 'integer'
                    key = 'foreign key(%s)' % (name)
                    attrs[key] = 'references %s(id)' % (name.strip('_id'))
                else:
                    attrs[name] = 'integer'
            elif isinstance(value, str) or value is None:
                attrs[name] = 'text'
            else:
                raise UnsupportedTypeError('%s not supported' % (type(value)))

        # List of space separated pairs of field name and field type
        fields = ['%s %s' % (name, dtype) for name, dtype in attrs.iteritems()]

        # Single string of field info separated by commas
        field_str = ','.join(fields)

        create_cmd = 'create table %s (%s)' % (table_name, field_str)
        self._cursor.execute(create_cmd)
        self._connection.commit()

    def delete_table(self, table_name):
        """Delete given table from database"""

        self._cursor.execute('drop table %s' % (table_name))
        self._connection.commit()

    def insert(self, model):
        """
        Insert given model instance into database

        Model instance will have .id attribute filled out after successful
        insertion.
        """

        table_name = model.__class__.__name__

        attrs = {}
        for name, value in model.__dict__.iteritems():
            if name == 'id':
                continue

            attrs[name] = self._sqlize_value(value)

        # FIXME: Handle errors
        #values_strs = [('%s' % value) for value in attrs.values()]
        insert_cmd = 'insert into %s (%s) values (%s)' % (table_name,
                                                    ','.join(attrs.keys()),
                                                    ','.join(attrs.values()))

        self._cursor.execute(insert_cmd)
        self._connection.commit()

        model.id = self._cursor.lastrowid

        return model

    def update(self, model):
        """Update given model instance in database"""

        table_name = model.__class__.__name__

        fields = []
        for name, value in model.__dict__.iteritems():
            if name == 'id':
                continue

            fields.append('='.join([name, self._sqlize_value(value)]))

        field_str = ','.join(fields)

        # FIXME: Optimize and only update changed values?
        # FIXME: Handle errors
        update_cmd = 'update %s set %s where id=%d' % (table_name, field_str,
                                                       model.id)
        self._cursor.execute(update_cmd)
        self._connection.commit()

    def delete(self, model):
        """Delete given model instance from database"""

        self._cursor.execute('delete from %s where id=%d' % (
                                                    model.__class__.__name__,
                                                    model.id))

    def select(self, model_class, where=None, order=None):
        """Select objects from model_class with where and order clauses"""

        if where is None:
            where = ''
        else:
            where = ''.join(['where ', where])

        if order is None:
            order = ''
        else:
            order = ''.join(['order by ', order])

        attrs = inspect.getargspec(model_class.__init__.__func__).args
        attrs.remove('self')

        field_str = ','.join(attrs)

        # FIXME: This is obviously insecure, but is it worth the effort?
        select_cmd = 'select id, %s from %s %s %s' % (field_str,
                                                      model_class.__name__,
                                                      where,
                                                      order)

        res = self._cursor.execute(select_cmd)

        # Build a list of objects and fill out each with it's id
        res_list = []
        for row in res:
            id_attr = row[0]
            row = list(row)
            row = row[1:]

            model = model_class(*row)
            model.id = id_attr

            res_list.append(model)

        return res_list


if __name__ == "__main__":

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
