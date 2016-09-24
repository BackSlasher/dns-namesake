# Holds records

from twisted.names import dns
import re

IS_REGEX=re.compile('^/(.+)/$')

def validate_type(type):
    assert type in (dns.CNAME, dns.A, dns.AAAA), 'record type {} illegal'.format(type)


class Result(object):
    def __init__(self, type, payload):
        validate_type(type)
        self.type = type
        assert isinstance(payload, str), 'payload must be string'
        self.payload = payload
    def to_record(self):
        if self.type == dns.A:
            return dns.Record_A(self.payload)
        elif self.type == dns.AAAA:
            return dns.Record_AAAA(self.payload)
        elif self.type == dns.CNAME:
            return dns.Record_CNAME(self.payload)
        else:
            raise Exception('Bad type')

class Record(object):
    def __init__(self, name, type, payload):
        regex_res = re.search(IS_REGEX, name)
        if regex_res:
            self.is_regex = True
            self.regex = re.compile('^{}$'.format(regex_res.groups()[0]))
        else:
            self.is_regex = False
            self.name = name

        validate_type(type)
        self.type = type

        self.payload = payload 

    def match(self, name, type):
        # Reject if record type is wrong and not CNAME
        if self.type != type and self.type != dns.CNAME:
            return None
        # We got that far, check if name matches
        if self.is_regex:
            regex_res = re.match(self.regex, name)
            if regex_res:
                return Result(
                    self.type,
                    re.sub(self.regex, self.payload, name),
                )
            else:
                return None
        else:
            if name == self.name:
                return Result(
                    self.type,
                    self.payload,
                    )
            else:
                return None

    def __repr__(self):
        if self.is_regex:
            rep = '/{}/'.format(self.regex)
        else:
            rep = self.name
        return '{}({} {} {})'.format(type(self).__name__, rep, self.type, self.payload)

class RecordStore(object):
    def __init__(self):
        self.records = []

    def add(self, name, type, payload):
        r = Record(name, type, payload)
        self.records.append(r)

    def match(self, name, type):
        for record in self.records:
            res = record.match(name, type)
            if res:
                return res
        return None
