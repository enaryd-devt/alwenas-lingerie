from odoo import models, fields


class PartnerBalanceReportWizard(models.TransientModel):
    _name = 'primetech.receivable.report.wizard'
    _description = 'Etat des Soldes Partenaires'

    report_date = fields.Date(
        string='Situation au',
        required=True,
        default=fields.Date.context_today
    )

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
        required=True
    )

    partner_ids = fields.Many2many(
        'res.partner',
        string='Partenaires'
    )

    partner_type = fields.Selection(
        [
            ('customer', 'Clients'),
            ('supplier', 'Fournisseurs'),
            ('both', 'Tous les partenaires'),
        ],
        string='Type de partenaire',
        default='both',
        required=True
    )

    commercial_partner_only = fields.Boolean(
        string='Regrouper par société mère',
        default=True
    )

    show_overdue_only = fields.Boolean(
        string='Pièces échues uniquement'
    )

    show_details = fields.Boolean(
        string='Afficher le détail des pièces',
        default=True
    )

    include_zero_balance = fields.Boolean(
        string='Inclure les soldes nuls'
    )

    sort_by = fields.Selection(
        [
            ('name', 'Nom du partenaire'),
            ('balance_desc', 'Solde décroissant'),
            ('balance_asc', 'Solde croissant'),
        ],
        string='Tri',
        default='balance_desc'
    )


    def action_print_report(self):
        return self.env.ref(
            'primetech_daily_reports.action_receivable_report'
        ).report_action(self)
    
    def action_preview_report(self):

        self.ensure_one()

        report = self.env.ref(
            'primetech_daily_reports.action_receivable_report'
        )

        html = report._render_qweb_html(
            report.report_name,
            [self.id]          # <-- correction
        )[0]

        if isinstance(html, bytes):
            html = html.decode()

        preview = self.env[
            'primetech.report.preview.wizard'
        ].create({
            'name': 'Prévisualisation',
            'html_content': html,
            'report_xmlid':
                'primetech_daily_reports.action_receivable_report',
            'wizard_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model':
                'primetech.report.preview.wizard',
            'view_mode': 'form',
            'res_id': preview.id,
            'target': 'current',
        }