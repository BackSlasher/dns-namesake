dns-namesake
============

| A DNS "filter" for testing changes
| This server will answer queries from its own store, and forward any
  unknown quetions to an upstream server.
| The interesting parts in Namesake are:

1. Support for regex in records
2. It will resolve CNAMES fro its own store not according to the "right"
   way - it will respond with ``CNAME``\ s to other record queries
   (authorative behaviour) but will resolve the referred address for the
   client (recursive behaviour)

| These features allow quick scaffolding of DNS changes for testing.
| I don't think it's a good idea to use this server in production.

Examples
--------

Redirect ``bla.aol.com`` to ``cnet.com``:
``bin/dns-namesake --cname=bla.aol.com,cnet.com``

Serve ``yahoo.com`` as ``8.8.8.8``:
``bin/dns-namesake --a=yahoo.com,8.8.8.8``

Redirect all google subdomains to the same subdomain in cnet:
``bin/dns-namesake --cname='/(.+)\.google\.com/,\1.cnet.com'``

Use a file (NOT READY YET):

::

    # /tmp/records

    bla.aol.com CNAME cnet.com
    yahoo.com A 8.8.8.8
    /(.+)\.google\.com/ CNAME \1.cnet.com

``bin/dns-namesake -f /tmp/records``
