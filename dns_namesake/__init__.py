from twisted.internet import reactor
from twisted.names import client, dns, server

from store_resolver import StoreResolver
from record_store import RecordStore

def main():

    rs = RecordStore()

    factory = server.DNSServerFactory(
        clients=[
            StoreResolver(rs),
            #client.Resolver(resolv='/etc/resolv.conf'),
        ],
    )

    protocol = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(10053, protocol)
    reactor.listenTCP(10053, factory)

    reactor.run()


if __name__ == '__main__':
    raise SystemExit(main())
