from twisted.web import xmlrpc, server, resource
from twisted.python import log
from twisted.python import logfile
from twisted.enterprise import adbapi
import xmlrpclib
import sys

class MyServer(xmlrpc.XMLRPC):

    """
    An example object to be published.
    """

    def xmlrpc_echo(self, x):
        """
        Return all passed args.
        """
        return x
#    xmlrpc_echo.help = "echo everything back"
    xmlrpc_echo.signature = [
        ['string', 'string'],
        ['int', 'int'],
    ]

    def xmlrpc_add(self, a, b):
        """
        Return sum of arguments.
        """
        return a + b
#    xmlrpc_add.help = "sum a and b"
    xmlrpc_add.signature = [
        ['int', 'int', 'int'],
        ['float', 'float', 'float'],
    ]

    def xmlrpc_fault(self):
        """
        Raise a Fault indicating that the procedure should not be used.
        """
        raise xmlrpc.Fault(123, "The fault procedure is faulty.")
#    xmlrpc_fault.help = "just falty"
    xmlrpc_fault.signature = [
        ['faulty'],
    ]

    def xmlrpc_binary(self):
        """
        return a file with binary
        """
        with open(__file__, "rb") as handle:
            return xmlrpclib.Binary(handle.read())
        raise xmlrpc.Fault(123, "can not find bindary file")
#    xmlrpc_binary.help = "use binary to echo things back safely"
    xmlrpc_binary.signature = [
        ['binary'],
    ]

    def xmlrpc_db(self):
        """
        return user list in database
        """
        return dbpool.runQuery("select * from users")
#    xmlrpc_db.help = "use binary to echo things back safely"
    xmlrpc_db.signature = [
        ['list'],
    ]

    def checkin(self, transaction, username, place, now):
        user = transaction.execute(
            "select * from users where username=%s", (username, ))
        result = transaction.fetchall()
        print result
        updated = False
        if len(result):
            transaction.execute(
                "update users set place=%s,last_checkin=%s where username=%s",
                (place,
                 now,
                 username))
            updated = True
        else:
            transaction.execute(
                "insert into users (username, place, last_checkin)values(%s, %s, %s)",
                (username,
                 place,
                 now))
        transaction.execute(
            "select * from users where username=%s", (username, ))
        return updated and 'updated' or 'created', transaction.fetchall()[0]

    def xmlrpc_checkin(self, username, place, now):
        """
        return user list in database
        """
        return dbpool.runInteraction(self.checkin, username, place, now)

#    xmlrpc_db.help = "use binary to echo things back safely"
    xmlrpc_db.signature = [
        ['list'],
    ]

    @xmlrpc.withRequest
    def xmlrpc_headerValue(self, request, headerName):
        log.msg("headerValue method called")
        return request.requestHeaders.getRawHeaders(headerName)
    xmlrpc_binary.signature = [
        ['string', 'string'],
    ]


def randPassedTime():
    the_time = datetime.datetime.utcnow() - datetime.timedelta(
        days=random.randint(1, 100))
    return the_time.isoformat()


def initTables(transaction):
    table_exists_query = "SHOW TABLES LIKE 'users'"
    create_table_query = '''CREATE TABLE `users` (
                                `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
                                `username` VARCHAR(255) NULL,
                                `place` VARCHAR(255) NULL,
                                `last_checkin` VARCHAR(255) NULL,
                                UNIQUE INDEX `username` (`username`),
                                PRIMARY KEY (`id`)
                            );
                            '''
    transaction.execute(table_exists_query)
    result = transaction.fetchall()
    if not len(result):
        transaction.execute(create_table_query)
        default_users = [
            ("tom", "LA", randPassedTime()),
            ("jerry", "NY", randPassedTime()),
            ("lucy", "NV", randPassedTime()),
        ]
        for username, place, last_checkin in default_users:
            transaction.execute(
                "INSERT INTO `users` (username, place,last_checkin) VALUES(%s, %s, %s)",
                (username,
                 place,
                 last_checkin))
if __name__ == '__main__':
    import datetime
    import random
    import ConfigParser
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.read('config.ini')

    if not config.get('log', 'filename'):
        log.startLogging(sys.stdout)
    else:
        log.startLogging(logfile.DailyLogFile(
            config.get('log', 'filename'), config.get('log', 'path')))
    log.msg("try to connect mysql")
    import MySQLdb
    mysql_config = dict(cp_reconnect=True)
    for k in ['host', 'user', 'passwd', 'db']:
        mysql_config[k] = config.get('mysql', k)
    dbpool = adbapi.ConnectionPool("MySQLdb", **mysql_config)
    dbpool.runInteraction(initTables)
    log.msg("try to init service")
    from twisted.internet import reactor
    root = resource.Resource()
    rpc = MyServer()
    xmlrpc.addIntrospection(rpc)
    root.putChild(config.get('service', 'mount_point'), rpc)
    reactor.listenTCP(config.getint('service', 'port'), server.Site(root))
    log.msg(
        "service listened on port http://0.0.0.0:%s/%s" %
        (config.getint('service', 'port'), config.get('service', 'mount_point')))
    reactor.run()
