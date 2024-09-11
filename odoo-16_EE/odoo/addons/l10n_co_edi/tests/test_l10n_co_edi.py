# coding: utf-8
from odoo import Command
from .common import TestCoEdiCommon
from odoo.tests import tagged
from odoo.tools import mute_logger, misc


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestColombianInvoice(TestCoEdiCommon):

    def l10n_co_assert_generated_file_equal(self, invoice, expected_values, applied_xpath=None):
        # Get the file that we generate instead of the response from carvajal
        invoice.action_post()
        xml_content = self.edi_format._l10n_co_edi_generate_xml(invoice)
        current_etree = self.get_xml_tree_from_string(xml_content)
        expected_etree = self.get_xml_tree_from_string(expected_values)
        if applied_xpath:
            expected_etree = self.with_applied_xpath(expected_etree, applied_xpath)
        self.assertXmlTreeEqual(current_etree, expected_etree)

    def test_invoice(self):
        '''Tests if we generate an accepted XML for an invoice and a credit note.'''
        with self.mock_carvajal():
            self.l10n_co_assert_generated_file_equal(self.invoice, self.expected_invoice_xml)

            # To stop a warning about "Tax Base Amount not computable
            # probably due to a change in an underlying tax " which seems
            # to be expected when generating refunds.
            with mute_logger('odoo.addons.account.models.account_invoice'):
                credit_note = self.invoice._reverse_moves(default_values_list=[])

            self.l10n_co_assert_generated_file_equal(credit_note, self.expected_credit_note_xml)

    def test_sugar_tax_invoice(self):
        ''' Tests if we generate an accepted XML for an invoice with products
            that have sugar tax applied.
        '''
        with self.mock_carvajal():
            self.l10n_co_assert_generated_file_equal(self.sugar_tax_invoice, self.expected_sugar_tax_invoice_xml)

    def test_invoice_tim_sections(self):
        ''' Tests the grouping of taxes inside the TIM section. There should be one TIM per CO tax type, and inside
        this TIM, one IMP per tax rate.
        '''
        with self.mock_carvajal():
            self.l10n_co_assert_generated_file_equal(self.invoice_tim, self.expected_invoice_tim_xml)

    def test_invoice_with_attachment_url(self):
        with self.mock_carvajal():
            self.invoice.l10n_co_edi_attachment_url = 'http://testing.te/test.zip'
            applied_xpath = '''
                <xpath expr="//ENC_16" position="after">
                    <ENC_17>http://testing.te/test.zip</ENC_17>
                </xpath>
            '''
            self.l10n_co_assert_generated_file_equal(self.invoice, self.expected_invoice_xml, applied_xpath)

    def test_invoice_carvajal_group_of_taxes(self):
        with self.mock_carvajal():
            self.invoice.write({
                'invoice_line_ids': [(1, self.invoice.invoice_line_ids.id, {
                    'tax_ids': [(6, 0, self.tax_group.ids)],
                    'name': 'Line 1',  # Otherwise it is recomputed
                })],
            })
            self.l10n_co_assert_generated_file_equal(self.invoice, self.expected_invoice_xml)

    def test_debit_note_creation_wizard(self):
        """ Test debit note is create succesfully """

        self.invoice.action_post()

        wizard = self.env['account.debit.note'].with_context(active_model="account.move", active_ids=self.invoice.ids).create({
            'l10n_co_edi_description_code_debit': '1',
            'copy_lines': True,
        })
        wizard.create_debit()

        debit_note = self.env['account.move'].search([
            ('debit_origin_id', '=', self.invoice.id),
        ])
        self.assertRecordValues(debit_note, [{'amount_total': 48750.0}])

    def test_invoice_withholded_taxes(self):
        company = self.company_data['company']

        withholded_15_on_19 = self.env.ref(f'l10n_co.{company.id}_l10n_co_tax_56')
        withholded_15_on_5 = self.env.ref(f'l10n_co.{company.id}_l10n_co_tax_55')

        invoice = self.env['account.move'].create({
            'partner_id': company.partner_id.id,
            'move_type': 'out_invoice',
            'ref': 'reference',
            'invoice_payment_term_id': self.env.ref('account.account_payment_term_end_following_month').id,
            'invoice_line_ids': [
                Command.create({
                    'quantity': 1,
                    'price_unit': 100.9,
                    'name': 'Line 1',
                    'tax_ids': [Command.set(withholded_15_on_19.ids)],
                }),
                Command.create({
                    'quantity': 1,
                    'price_unit': 101,
                    'name': 'Line 2',
                    'tax_ids': [Command.set(withholded_15_on_5.ids)],
                }),
            ]
        })

        expected_invoice_taxes_withholded = misc.file_open('l10n_co_edi/tests/invoice_taxes_withholded.xml', 'rb').read()

        with self.mock_carvajal():
            self.l10n_co_assert_generated_file_equal(invoice, expected_invoice_taxes_withholded)
