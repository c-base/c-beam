import ldap
import sys
import logging

logger = logging.getLogger('rfidLdap.py')
filelogging = logging.FileHandler('/tmp/rfidLdapScript.log')
filelogging.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(filelogging)
logger.setLevel(logging.DEBUG)


# search in a ldapResult for specified dn and return the key for given attr. if your attr for dn is found, key will returned. if not found None returned
# todo return exception...
def getAttrForLdapDn(dn, attr, result):
    for entry, attrs in result:
        if entry == dn:
            if attrs.has_key(attr):
                return attrs[attr]
    return None

# search in a ldapResult for specified attr == key  and return the dn. if not found None returned
# todo return exception...
def getDnForLdapAttr(attr, key, result):
    for dn, attrs in result:
        if attrs.has_key(attr):
            # a ldapentry can have multiple attribute with the same key
            for rfids in attrs[attr]:
                for k in rfids.split(','):
                    if k == key:
                        return dn
    return None


class LdapRfidCheck:
    def __init__(self, ldapuri, baseDn, userDn, userPassword, rfidAttr, searchFilter):
        self.__connection = ldap.initialize(ldapuri)
        self.__connection.bind_s(userDn, userPassword)
        self.__baseDn = baseDn
        self.__rfidAttr = rfidAttr
        self.__searchFilter = searchFilter

    def cleanup(self):
        self.__connection.unbind()

    def getRfidForUser(self, user):
        result = self.__connection.search_s(self.__baseDn, ldap.SCOPE_SUBTREE, "(&%s(uid=%s)" % (self.__searchFilter, user), [self.__rfidAttr])
        if len(result) != 1:
            return None

        entry, attr = result[0]
        if len(attr[self.__rfidAttr]) != 1:
            return None

        if not attr.has_key(self.__rfidAttr):
            return None

        return attr[self.__rfidAttr][0]

    def getUserForRfid(self, rfid):
        result = self.__connection.search_s(self.__baseDn, ldap.SCOPE_SUBTREE, '%s' % (self.__searchFilter), [self.__rfidAttr])
        return getDnForLdapAttr(self.__rfidAttr, rfid, result)
        

if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print("Usage %s <RFID_UUID>\n" % sys.argv[0])
        print("Search ldap for rfid-tag\n")
        sys.exit(1)

    rfidUUid = sys.argv[1]

    logger.warning("[%s] appeared" % rfidUUid)
    # anonymous bind against lea
    f = LdapRfidCheck("ldap://10.0.1.7:389/", 'ou=crew,dc=c-base,dc=org', '', '', 'rfid', '(memberOf=cn=crew,ou=groups,dc=c-base,dc=org)')
    userDn = f.getUserForRfid(rfidUUid)
    logger.warning("[%s] known as" % userDn)

    print(userDn)

