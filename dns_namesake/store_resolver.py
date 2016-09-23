from record_store import RecordStore
from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server


class StoreResolver(object):
    def __init__(self, store):
        assert isinstance(store, RecordStore), 'This is not a record store'
        self.store = store

    def query(self, query, timeout=None):
        name = query.name.name
        # Try to answer dynamically
        res = self.store.match(name, query.type)
        
        if res:
            # Return positive response
            # Be prepared to chase CNAMEs
            if res.payload:
            #    if query.type == res.type:
                answer = dns.RRHeader(
                    name=name,
                    payload=res.to_record(),
                )
                answers = [answer]
                authority = []
                additional = []
                return defer.succeed((answers, authority, additional))
            # Return negative response
            else:
                print 'shallnotpass'
                return defer.fail(error.AuthoritativeDomainError())
        # Don't know
        else:
            print 'dunno'
            return defer.fail(error.DomainError())
