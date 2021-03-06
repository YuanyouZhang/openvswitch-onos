from charmhelpers.core.reactive import hook
from charmhelpers.core.reactive import RelationBase
from charmhelpers.core.reactive import scopes


class ControllerAPIRequires(RelationBase):
    scope = scopes.GLOBAL
    auto_accessors = ['private-address', 'host', 'port',
                      'username', 'password']

    @hook('{requires:onos-controller-api}-relation-{joined,changed,departed}')
    def changed(self):
        self.set_state('{relation_name}.connected')
        if self.connection():
            self.set_state('{relation_name}.access.available')
        else:
            self.remove_state('{relation_name}.access.available')

    @hook('{requires:onos-controller-api}-relation-broken')
    def broken(self):
        self.remove_state('{relation_name}.connected')
        self.remove_state('{relation_name}.access.available')

    def connection(self):
        data = {
            'host': self.host() or self.private_address(),
            'port': self.port() or '8181',
            'username': self.username(),
            'password': self.password(),
        }
        if all(data.values()):
            return data
        else:
            return None
