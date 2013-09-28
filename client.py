import xmlrpclib, httplib
import datetime

class ProxiedTransport(xmlrpclib.Transport):
    user_agent='My xmlRPC Client'
    def set_proxy(self, proxy):
        self.proxy = proxy
    def make_connection(self, host):
        self.realhost = host
        h = httplib.HTTPConnection(self.proxy)
        return h
    def send_request(self, connection, handler, request_body):
        connection.putrequest("POST", 'http://%s%s' % (self.realhost, handler))
    def send_host(self, connection, host):
        connection.putheader('Host', self.realhost)


if __name__ == '__main__':
    import datetime
    import random
    import ConfigParser
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.read('config.ini')
client_args={}
if config.getint('client', 'proxy_port'):
    p = ProxiedTransport()
    p.set_proxy('%s:%s' % (config.get('client', 'proxy_host'), config.get('client', 'proxy_port')))
    client_args['transport'] = p
server = xmlrpclib.Server('http://localhost:%s/%s' % (config.getint('service', 'port'), config.get('service', 'mount_point')), **client_args)
if config.getboolean('client', 'list_methods'):
    for method in server.system.listMethods():
        print "%s %s: %s" %(method, server.system.methodSignature(method), server.system.methodHelp(method))

try:
    username='walter'
    place="UT"
    now=datetime.datetime.utcnow().isoformat()
    response = server.checkin(username, place, now)
    if hasattr(response, 'data'):
        print response.data
    else:
        print response
except xmlrpclib.ProtocolError as err:
    print "A protocol error occurred"
    print "URL: %s" % err.url
    print "HTTP/HTTPS headers: %s" % err.headers
    print "Error code: %d" % err.errcode
    print "Error message: %s" % err.errmsg
except xmlrpclib.Fault as err:
    print "A fault occurred"
    print "Fault code: %d" % err.faultCode
    print "Fault string: %s" % err.faultString