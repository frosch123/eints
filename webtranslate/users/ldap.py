"""
User and group management handled by Ldap.

The owner and translators of the rights are mapped to posixGroups in ldap through
the C{<ldap/>} section in the config file.

Note that the groups resp. group membership is not project specific.
"""

from webtranslate import rights, userauth

import traceback

# Also initialized in the config loader.
ldap_host = None
ldap_basedn_users = None
ldap_basedn_groups = None

owner_group = None
translator_groups = {} # Mapping of iso language name to role name.

server = None

class LdapUserAuthentication(userauth.UserAuthentication):
    """
    Implementation of UserAuthentication for Ldap authentication system.

    @ivar is_auth: Whether the user authenticated successfully. False for annonymous access.
    @type is_auth: C{bool}

    @ivar name: Username, "unknown" for annoymous access.
    @type name: C{str}

    @ivar groups: 
    """
    def __init__(self, is_auth, name, groups):
        super(LdapUserAuthentication, self).__init__(is_auth, name)
        self.groups = groups

    def may_access(self, pname, prjname, lngname):
        # Get page access rights for all types of users.
        accesses = rights.get_accesses(pname, self.name)
        if accesses[self.name] == True or accesses['SOMEONE'] == True:
            return True

        # User must get access through a OWNER or TRANSLATOR role.
        if prjname is None or self.name == "unknown": return False

        if self.groups is None: return False

        if lngname is not None and accesses['TRANSLATOR'] == True:
            group = translator_groups.get(lngname)
            if group is not None and group != "" and group in self.groups: return True

        if accesses['OWNER'] == True:  # 'prjname is not None' has been already established.
            if owner_group is not None and owner_group != "" and owner_group in self.groups: return True

        return False


def init():
    """
    Initialize the user admin system.
    """
    global server, ldap_host
    import ldap3

    rights.init_page_access()

    server = ldap3.Server(ldap_host)


def get_authentication(user, pwd, ip):
    """
    Authenticate a user and return an authentication object.

    @param user: Name of the user, if provided (external data).
    @type  user: C{str} or C{None}

    @param pwd: Password of the user, if provided (external data).
    @type  pwd: C{str} or C{None}

    @return: UserAuthentication object to test accesses with.
    @rtype: C{UserAuthentication}
    """

    if ip == "127.0.0.1" and user == "translators":
        return LdapUserAuthentication(True, user, set([owner_group]))

    # Verify user.
    # Note that failure to authenticate is not fatal, it falls back to an 'unknown' user.
    groups = set()
    if user is not None and user != "" and pwd is not None and pwd != "":
        global server, ldap_basedn_users, ldap_basedn_groups
        import ldap3

        try:
            escaped_user = ldap3.utils.conv.escape_bytes(user)
            with ldap3.Connection(server, auto_bind=True, client_strategy=ldap3.STRATEGY_SYNC, user="uid="+escaped_user+","+ldap_basedn_users, password=pwd) as c:
                if c.search(ldap_basedn_users, '(uid='+escaped_user+')', attributes=['cn', 'memberOf']):
                    user = c.response[0]['attributes']['cn'][0]
                    groups.update(g.split(',')[0].split('=')[1] for g in c.response[0]['attributes']['memberOf'] if g.endswith(ldap_basedn_groups))

        except:
            user = None

    else:
        user = None

    if user is None: return LdapUserAuthentication(False, "unknown", set())

    return LdapUserAuthentication(True, user, groups)
