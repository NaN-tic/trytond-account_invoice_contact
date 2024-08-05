import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear, create_tax,
                                                 create_tax_code, get_accounts)
from trytond.modules.account_invoice.tests.tools import \
    set_fiscalyear_invoice_sequences
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install account_invoice_contact
        config = activate_modules('account_invoice_contact')

        # Create company
        _ = create_company()
        company = get_company()
        tax_identifier = company.party.identifiers.new()
        tax_identifier.type = 'eu_vat'
        tax_identifier.code = 'BE0897290877'
        company.party.save()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create tax
        tax = create_tax(Decimal('.10'))
        tax.save()
        invoice_base_code = create_tax_code(tax, 'base', 'invoice')
        invoice_base_code.save()
        invoice_tax_code = create_tax_code(tax, 'tax', 'invoice')
        invoice_tax_code.save()
        credit_note_base_code = create_tax_code(tax, 'base', 'credit')
        credit_note_base_code.save()
        credit_note_tax_code = create_tax_code(tax, 'tax', 'credit')
        credit_note_tax_code.save()

        # Create party
        Party = Model.get('party.party')
        party = Party(name='Party')
        party.save()
        party2 = Party(name='Party')
        party2.save()

        # Create Relation Types:
        RelationType = Model.get('party.relation.type')
        relation = RelationType()
        relation.name = 'Employee of'
        relation.save()

        # Account Configuration
        Config = Model.get('account.invoice.configuration')
        config = Config(1)
        config.relation_types.append(relation)
        config.save()

        # Create Relation All:
        RelationAll = Model.get('party.relation.all')
        relation1 = RelationAll()
        relation1.from_ = party2
        relation1.to = party
        relation1.type = relation
        relation1.save()
        party2.reload()
        self.assertEqual(len(party2.relations), 1)
        relation2 = RelationAll()
        relation2.from_ = party
        relation2.to = party2
        relation2.type = relation
        relation2.save()
        party.reload()
        self.assertEqual(len(party.relations), 1)

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.customer_taxes.append(tax)
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal('40')
        template.account_category = account_category
        template.save()
        product, = template.products

        # Create payment term
        PaymentTerm = Model.get('account.invoice.payment_term')
        payment_term = PaymentTerm(name='Term')
        line = payment_term.lines.new(type='percent', ratio=Decimal('.5'))
        delta, = line.relativedeltas
        delta.days = 20
        line = payment_term.lines.new(type='remainder')
        delta = line.relativedeltas.new(days=40)
        payment_term.save()

        # Create invoice
        Invoice = Model.get('account.invoice')
        InvoiceLine = Model.get('account.invoice.line')
        invoice = Invoice()
        invoice.party = party2
        invoice.payment_term = payment_term
        invoice.invoice_contact = party
        line = InvoiceLine()
        invoice.lines.append(line)
        line.product = product
        line.quantity = 5
        line.unit_price = Decimal('40')
        line = InvoiceLine()
        invoice.lines.append(line)
        line.account = revenue
        line.description = 'Test'
        line.quantity = 1
        line.unit_price = Decimal(20)
        self.assertEqual(invoice.untaxed_amount, Decimal('220.00'))
        self.assertEqual(invoice.tax_amount, Decimal('20.00'))
        self.assertEqual(invoice.total_amount, Decimal('240.00'))
        invoice.save()

        # Try replace active party
        replace = Wizard('party.replace', models=[party])
        replace.form.source = party
        replace.form.destination = party2
        replace.execute('replace')

        # Check fields have been replaced
        invoice.reload()
        self.assertEqual(invoice.invoice_contact, party2)
