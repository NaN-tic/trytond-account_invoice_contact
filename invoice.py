# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['ContactMixin', 'Configuration', 'ConfigurationRelationType',
    'Invoice']
__metaclass__ = PoolMeta


class ContactMixin:
    """
    Mixin to relate models with contacts.

    It assumes that the model has a field called party, which refers to the
    party of the model and enforces that the contact is related with the
    party with o relation type defined in contact_relations.

    The contact_relations fields, by default uses a config defined in
    a Singleton model. The name of the model must be set in the
    `_contact_config_name` property and it expects to have a relation_types
    Many2Many field to `party.relation.type` model.
    """
    _contact_config_name = None

    allowed_contacts = fields.Function(fields.One2Many('party.party',
            None, 'Allowed Contact',
            help='Allowed relation types for the related contact.'),
        'get_allowed_contacts')
    contact = fields.Many2One('party.party', 'Contact',
        domain=[
            ('id', 'in', Eval('allowed_contacts', [])),
            ],
        depends=['party', 'allowed_contacts'])

    def get_allowed_contacts(self, name):
        pool = Pool()
        Config = pool.get(self._contact_config_name)

        res = []
        if not self.party:
            return res

        config = Config(1)
        types = [r.id for r in config.relation_types]
        relations = self.party.relations
        if not relations:
            return res
        for relation in relations:
            if relation.type.id in types:
                res.append(relation.to.id)
        return res

    def on_change_party(self):
        res = super(ContactMixin, self).on_change_party()
        if self.party:
            allowed_contacts = self.get_allowed_contacts(None)
            res['allowed_contacts'] = allowed_contacts
            if len(allowed_contacts) == 1:
                res['contact'] = allowed_contacts[0]
        else:
            res['contact'] = None
            res['allowed_contacts'] = None
        return res


class ConfigurationRelationType(ModelSQL):
    'Invoice Configuration - Party relation type'
    __name__ = 'account.invoice.configuration-party.relation.type'

    relation = fields.Many2One('party.relation.type', 'Relation Type',
        required=True, select=True)
    config = fields.Many2One('account.invoice.configuration', 'Config',
        required=True, select=True)


class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Invoice Configuration'
    __name__ = 'account.invoice.configuration'

    relation_types = fields.Many2Many(
        'account.invoice.configuration-party.relation.type', 'config',
        'relation', 'Contact types')


class Invoice(ContactMixin):
    __name__ = 'account.invoice'
    _contact_config_name = 'account.invoice.configuration'

    def _credit(self):
        res = super(Invoice, self)._credit()
        if self.contact:
            res['contact'] = self.contact.id
        return res
