# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import invoice
from . import party


def register():
    Pool.register(
        invoice.Configuration,
        invoice.ConfigurationRelationType,
        invoice.Invoice,
        module='account_invoice_contact', type_='model')
    Pool.register(
        party.PartyReplace,
        module='account_invoice_contact', type_='wizard')
