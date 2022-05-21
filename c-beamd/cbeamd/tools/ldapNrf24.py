import ldap
import sys
import logging

logger = logging.getLogger('nrf24Ldap.py')
filelogging = logging.FileHandler('/tmp/nrf24LdapScript.log')
filelogging.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(filelogging)
logger.setLevel(logging.DEBUG)


# search in a ldapResult for specified dn and return the key for given attr. if your attr for dn is found, key will returned. if not found None returned
# todo return exception...
def getAttrForLdapDn(dn, attr, result):
    for entry, attrs in result:
        if entry == dn:
            if attr in attrs.keys():
                return attrs[attr]
    return None

# search in a ldapResult for specified attr == key  and return the dn. if not found None returned
# todo return exception...


def getDnForLdapAttr(attr, key, result):
    for dn, attrs in result:
        if attr in attrs.keys():
            # a ldapentry can have multiple attribute with the same key
            for nrf24s in attrs[attr]:
                for k in nrf24s.split(','):
                    if k == key:
                        return dn
    return None


class LdapNrf24Check:
    def __init__(self, ldapuri, baseDn, userDn, userPassword, nrf24Attr, searchFilter):
        self.__connection = ldap.initialize(ldapuri)
        self.__connection.bind_s(userDn, userPassword)
        self.__baseDn = baseDn
        self.__nrf24Attr = nrf24Attr
        self.__searchFilter = searchFilter

    def cleanup(self):
        self.__connection.unbind()

    def getNrf24ForUser(self, user):
        result = self.__connection.search_s(self.__baseDn, ldap.SCOPE_SUBTREE, "(&%s(uid=%s)" % (self.__searchFilter, user), [self.__nrf24Attr])
        if len(result) != 1:
            return None

        entry, attr = result[0]
        if len(attr[self.__nrf24Attr]) != 1:
            return None

        if self.__nrf24Attr not in attr.keys():
            return None

        return attr[self.__nrf24Attr][0]

    def getUserForNrf24(self, nrf24):
        result = self.__connection.search_s(self.__baseDn, ldap.SCOPE_SUBTREE, '%s' % (self.__searchFilter), [self.__nrf24Attr])
        return getDnForLdapAttr(self.__nrf24Attr, nrf24, result)


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print("Usage %s <nrf24_UUID>\n" % sys.argv[0])
        print("Search ldap for nrf24-tag\n")
        sys.exit(1)

    nrf24UUid = sys.argv[1]

    logger.warning("[%s] appeared" % nrf24UUid)
    # anonymous bind against lea
    f = LdapNrf24Check("ldap://10.0.1.7:389/", 'ou=crew,dc=c-base,dc=org', '', '', 'nrf24', '(memberOf=cn=crew,ou=groups,dc=c-base,dc=org)')
    userDn = f.getUserForNrf24(nrf24UUid)
    logger.warning("[%s] known as" % userDn)

    print(userDn)
