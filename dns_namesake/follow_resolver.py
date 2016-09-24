from twisted.names import dns, error
from twisted.names.resolve import ResolverChain, FailureHandler
from twisted.internet import reactor, defer
from twisted.python.failure import Failure

class FollowResolver(ResolverChain):
    """
    NITZ: Copied from Resolver in root.py
    Will follow CNAMEs
    L{Resolver} implements recursive lookup starting from a specified list of
    root servers.

    @ivar hints: See C{hints} parameter of L{__init__}
    @ivar _maximumQueries: See C{maximumQueries} parameter of L{__init__}
    @ivar _reactor: See C{reactor} parameter of L{__init__}
    @ivar _resolverFactory: See C{resolverFactory} parameter of L{__init__}
    """
    def __init__(self, child_resolvers, maximumQueries=10,
                 reactor=None, resolverFactory=None):
        """
        @param hints: A L{list} of L{str} giving the dotted quad
            representation of IP addresses of root servers at which to
            begin resolving names.
        @type hints: L{list} of L{str}

        @param maximumQueries: An optional L{int} giving the maximum
             number of queries which will be attempted to resolve a
             single name.
        @type maximumQueries: L{int}

        @param reactor: An optional L{IReactorTime} and L{IReactorUDP}
             provider to use to bind UDP ports and manage timeouts.
        @type reactor: L{IReactorTime} and L{IReactorUDP} provider

        @param resolverFactory: An optional callable which accepts C{reactor}
             and C{servers} arguments and returns an instance that provides a
             C{queryUDP} method. Defaults to L{twisted.names.client.Resolver}.
        @type resolverFactory: callable
        """
        ResolverChain.__init__(self,child_resolvers)
        self._maximumQueries = maximumQueries
        self._reactor = reactor
        if resolverFactory is None:
            from twisted.names.client import Resolver as resolverFactory
        self._resolverFactory = resolverFactory


    def _query(self, query, timeout, filter):
    #def _query(self, name, cls, type, timeout):
        """
        Build a L{dns.Query} for the given parameters and dispatch it
        to each L{IResolver} in C{self.resolvers} until an answer or
        L{error.AuthoritativeDomainError} is returned.

        @type name: C{str}
        @param name: DNS name to resolve.

        @type type: C{int}
        @param type: DNS record type.

        @type cls: C{int}
        @param cls: DNS record class.

        @type timeout: Sequence of C{int}
        @param timeout: Number of seconds after which to reissue the query.
            When the last timeout expires, the query is considered failed.

        @rtype: L{Deferred}
        @return: A L{Deferred} which fires with a three-tuple of lists of
            L{twisted.names.dns.RRHeader} instances.  The first element of the
            tuple gives answers.  The second element of the tuple gives
            authorities.  The third element of the tuple gives additional
            information.  The L{Deferred} may instead fail with one of the
            exceptions defined in L{twisted.names.error} or with
            C{NotImplementedError}.
        """
        if not self.resolvers:
            return defer.fail(error.DomainError())
        q = query
        d = self.resolvers[0].query(q, timeout)
        for r in self.resolvers[1:]:
            d = d.addErrback(
                FailureHandler(r.query, q, timeout)
            )
        return d


    def _lookup(self, name, cls, type, timeout):
        """
        Implement name lookup by recursively discovering the authoritative
        server for the name and then asking it, starting at one of the servers
        in C{self.hints}.
        """
        if timeout is None:
            # A series of timeouts for semi-exponential backoff, summing to an
            # arbitrary total of 60 seconds.
            timeout = (1, 3, 11, 45)
        return self._discoverAuthority(
            dns.Query(name, type, cls), timeout,
            self._maximumQueries)


    # TODO nitz: Remove servers, query resolvers instaed
    def _discoverAuthority(self, query, timeout, queriesLeft):
        """
        Issue a query to a server and follow a delegation if necessary.

        @param query: The query to issue.
        @type query: L{dns.Query}

        @param servers: The servers which might have an answer for this
            query.
        @type servers: L{list} of L{tuple} of L{str} and L{int}

        @param timeout: A C{tuple} of C{int} giving the timeout to use for this
            query.

        @param queriesLeft: A C{int} giving the number of queries which may
            yet be attempted to answer this query before the attempt will be
            abandoned.

        @return: A L{Deferred} which fires with a three-tuple of lists of
            L{twisted.names.dns.RRHeader} giving the response, or with a
            L{Failure} if there is a timeout or response error.
        """
        # Stop now if we've hit the query limit.
        if queriesLeft <= 0:
            return Failure(
                error.ResolverError("Query limit reached without result"))

        d = self._query(query, timeout, False)
        d.addCallback(
            self._discoveredAuthority, query, timeout, queriesLeft - 1)
        return d


    def _discoveredAuthority(self, response, query, timeout, queriesLeft):
        """
        Interpret the response to a query, checking for error codes and
        following delegations if necessary.

        @param response: The L{Message} received in response to issuing C{query}.
        @type response: L{Message}

        @param query: The L{dns.Query} which was issued.
        @type query: L{dns.Query}.

        @param timeout: The timeout to use if another query is indicated by
            this response.
        @type timeout: L{tuple} of L{int}

        @param queriesLeft: A C{int} giving the number of queries which may
            yet be attempted to answer this query before the attempt will be
            abandoned.

        @return: A L{Failure} indicating a response error, a three-tuple of
            lists of L{twisted.names.dns.RRHeader} giving the response to
            C{query} or a L{Deferred} which will fire with one of those.
        """
        answers, authority, additional = response

        if not answers:
            return Failure(error.DomainError())

        # Turn the answers into a structure that's a little easier to work with.
        records = {}
        for answer in answers:
            records.setdefault(answer.name, []).append(answer)

        def findAnswerOrCName(name, type, cls):
            cname = None
            for record in records.get(name, []):
                if record.cls ==  cls:
                    if record.type == type:
                        return record
                    elif record.type == dns.CNAME:
                        cname = record
            # If there were any CNAME records, return the last one.  There's
            # only supposed to be zero or one, though.
            return cname

        seen = set()
        name = query.name
        record = None
        print 'aaaa'
        while True:
            seen.add(name)
            previous = record
            record = findAnswerOrCName(name, query.type, query.cls)
            if record is None:
                if name == query.name:
                    # If there's no answer for the original name, then this may
                    # be a delegation.  Code below handles it.
                    break
                else:
                    # Try to resolve the CNAME with another query.
                    d = self._discoverAuthority(
                        dns.Query(str(name), query.type, query.cls),
                        timeout, queriesLeft)
                    # We also want to include the CNAME in the ultimate result,
                    # otherwise this will be pretty confusing.
                    def cbResolved(results):
                        answers, authority, additional = results
                        answers.insert(0, previous)
                        return (answers, authority, additional)
                    d.addCallback(cbResolved)
                    return d
            elif record.type == query.type:
                return (
                    answers,
                    authority,
                    additional)
            else:
                # It's a CNAME record.  Try to resolve it from the records
                # in this response with another iteration around the loop.
                if record.payload.name in seen:
                    raise error.ResolverError("Cycle in CNAME processing")
                name = record.payload.name
        return Failure(error.DomainError())
