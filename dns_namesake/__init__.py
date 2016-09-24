import argparse

from twisted.internet import reactor
from twisted.names import client, dns, server

from store_resolver import StoreResolver
from record_store import RecordStore
from follow_resolver import FollowResolver

SEPARATOR=','

# Arg helpers
def generic_record(inp):
    name, payload = inp.split(SEPARATOR)
    return (name, payload)

def main():

    # Args
    parser = argparse.ArgumentParser(description='DNS filter')
    parser.add_argument('--a', action='append', type=generic_record, help='A records', default=[])
    parser.add_argument('--aaaa', action='append', type=generic_record, help='AAAA records', default=[])
    parser.add_argument('--cname', action='append', type=generic_record, help='CNAME records', default=[])
    args = parser.parse_args()

    # Add to record store
    rs = RecordStore()
    for r in args.a:
        rs.add(r[0], dns.A, r[1])
    for r in args.aaaa:
        rs.add(r[0], dns.AAAA, r[1])
    for r in args.cname:
        rs.add(r[0], dns.CNAME, r[1])

    factory = server.DNSServerFactory(
        clients=[
            FollowResolver( child_resolvers=[
                StoreResolver(rs),
                # TODO handle other cases where we need different upstreams
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
