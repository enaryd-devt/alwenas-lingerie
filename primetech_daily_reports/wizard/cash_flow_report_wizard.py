from odoo import models, fields


class CashFlowReportWizard(models.TransientModel):
    _name = 'primetech.cash.flow.report.wizard'
    _description = 'Etat Journalier de Tresorerie'

    show_opening_balance = fields.Boolean(
    string="Calculer les soldes réels"
    )

    date_from = fields.Date(
        string='Date début',
        required=True
    )

    date_to = fields.Date(
        string='Date fin',
        required=True
    )

    journal_ids = fields.Many2many(
            'account.journal',
            string='Journaux',
            domain=[
                ('type', 'in', ['cash', 'bank', 'general'])
            ]
        )

    def action_print_report(self):
        return self.env.ref(
            'primetech_daily_reports.action_cash_flow_report'
        ).report_action(self)
    
    def action_preview_report(self):

        self.ensure_one()

        report = self.env.ref(
            'primetech_daily_reports.action_cash_flow_report'
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
                'primetech_daily_reports.action_cash_flow_report',
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