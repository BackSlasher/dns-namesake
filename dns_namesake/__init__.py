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
    parser.add_argument('-p', '--port', type=int, help='Port to listen on', default=10053)
    parser.add_argument('--tcp', action='store_true', help='listen in TCP as well as UDP')
    parser.add_argument('--resolv', help='Resolv conf path for unknown queries. Set to empty to avoid using it', default='/etc/resolv.conf')
    parser.add_argument('-f', '--forward', type=str, action='append', help='Forward unknown queries to this server')
    args = parser.parse_args()

    # Extract server config from args
    port = args.port
    listen_tcp = args.tcp
    resolv = args.resolv
    if not resolv: resolv=None
    forward_servers=args.forward

    # Extract records from args
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
                client.Resolver(resolv=resolv, servers=forward_servers),
            ]),
        ],
    )

    protocol = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(port, protocol)
    if listen_tcp:
        reactor.listenTCP(port, factory)

    reactor.run()


if __name__ == '__main__':
    raise SystemExit(main())
