from record_store import RecordStore
from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server
from twisted.names.common import ResolverBase


class StoreResolver(ResolverBase):
    def __init__(self, store):
        ResolverBase.__init__(self)
        assert isinstance(store, RecordStore), 'This is not a record store'
        self.store = store

    def _lookup(self, name, cls, type, timeout):
        if cls != dns.IN:
            return defer.fail(error.DomainError())

        # Try to answer dynamically
        res = self.store.match(name, type)
        
        if res:
            # Return positive response
            # Be prepared to chase CNAMEs
            if res.payload:
            #    if query.type == res.type:
                answer = dns.RRHeader(
                    name=name,
                    type=res.type,
                    payload=res.to_record(),
                )
                answers = [answer]
                authority = []
                additional = []
                return defer.succeed((answers, authority, additional))
            # Return negative response
            else:
                return defer.fail(error.AuthoritativeDomainError())
        # Don't know
        else:
            return defer.fail(error.DomainError())
