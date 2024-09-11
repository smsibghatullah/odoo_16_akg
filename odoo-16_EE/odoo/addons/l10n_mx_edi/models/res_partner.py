# coding: utf-8

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # == Addenda ==
    l10n_mx_edi_addenda = fields.Many2one(
        comodel_name='ir.ui.view',
        string="Addenda",
        help="A view representing the addenda",
        domain=[('l10n_mx_edi_addenda_flag', '=', True)])
    l10n_mx_edi_addenda_doc = fields.Html(
        string="Addenda Documentation",
        help="How should be done the addenda for this customer (try to put human readable information here to help the "
             "invoice people to fill properly the fields in the invoice)")
    l10n_mx_edi_addenda_is_readonly = fields.Boolean(compute="_compute_l10n_mx_edi_addenda_is_readonly")
    l10n_mx_edi_addenda_name = fields.Char(related="l10n_mx_edi_addenda.name")

    def _compute_l10n_mx_edi_addenda_is_readonly(self):
        can_not_read = not self.env['ir.ui.view'].check_access_rights('read', raise_exception=False)
        for partner in self:
            partner.l10n_mx_edi_addenda_is_readonly = can_not_read

    def _l10n_mx_edi_get_customer_rfc(self):
        self.ensure_one()
        if self.country_id.code in (False, "MX"):
            if self.vat:
                return self.vat.strip()
            return "XAXX010101000"  # public and general
        return "XEXX010101000"  # foreign
