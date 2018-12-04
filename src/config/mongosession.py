#!/usr/bin/env python
# -*- coding: utf-8 -*-

from web.session import Store
import time

class MongoStore(Store):
    def __init__(self, db, collection_name):
        self.collection = db[collection_name]

    def __contains__(self, key):
        data = self.collection.find_one({'session_id':key})
        return bool(data)

    def __getitem__(self, key):
        now = time.time()
        s = self.collection.find_one({'session_id':key})
        if not s:
            raise KeyError
        else:
            s.update({'attime':now})
            return s

    def __setitem__(self, key, value):
        now = time.time()

        value['attime'] = now

        s = self.collection.find_one({'session_id':key})
        if s:
            value = dict(map(lambda x: (str(x[0]), x[1]), [(k,v) for (k,v) in value.iteritems() if k not in ['_id']]))
            s.update(**value)
            #self.collection.save(s)
            self.collection.replace_one({'_id':s['_id']}, s, upsert=True)
        else:
            self.collection.insert_one(value)

    def __delitem__(self, key):
        self.collection.delete_one({'session_id':key})

    def cleanup(self, timeout):
        timeout = timeout/(24.0*60*60) #timedelta takes numdays as arg
        last_allowed_time = time.time() - timeout
        self.collection.delete_many({'attime' : { '$lt' : last_allowed_time}})