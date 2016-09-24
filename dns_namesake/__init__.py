from twisted.internet import reactor
from twisted.names import client, dns, server

from store_resolver import StoreResolver
from record_store import RecordStore
from follow_resolver import FollowResolver

def main():

    rs = RecordStore()

    rs.add('bla.google.com', dns.CNAME, 'google.com')
    rs.add('blu.google.com', dns.A, '1.2.3.4')
    rs.add(r'/(.+)\.cnet.com', dns.CNAME, r'\1.google.com')

    factory = server.DNSServerFactory(
        clients=[
            FollowResolver( child_resolvers=[
                StoreResolver(rs),
                client.Resolver(resolv='/etc/resolv.conf'),
            ]),
        ],
    )

    protocol = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(10053, protocol)
    reactor.listenTCP(10053, factory)

    reactor.run()


if __name__ == '__main__':
    raise SystemExit(main())
