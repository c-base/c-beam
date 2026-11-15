import ldap

class LdapRfidCheck:                                                                                                                                                                           
    def __init__(self, ldapuri, baseDn, userDn, userPassword, rfidAttr, searchFilter):                                                                                                         
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        self.__connection = ldap.initialize(ldapuri)
        # self.__connection.set_option(ldap.OPT_X_TLS_CACERTFILE,CACERTFILE)
        # self.__connection.start_tls_s()
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

        if self.__rfidAttr not in attr:
            return None

        return attr[self.__rfidAttr][0]

    def getUserForRfid(self, rfid):
        # print("lookup: " + rfid + " - " + self.__searchFilter + " - " + self.__rfidAttr) 
        result = self.__connection.search_s(self.__baseDn, ldap.SCOPE_SUBTREE, '%s' % (self.__searchFilter), [self.__rfidAttr])
        # print(result)
        for dn, attrs in result:
            # an entry can carry several rfid values, each possibly comma separated
            for value in attrs.get(self.__rfidAttr, []):
                if isinstance(value, bytes):
                    value = value.decode()
                if rfid in value.split(','):
                    return dn
        return None
