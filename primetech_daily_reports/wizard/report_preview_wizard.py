from odoo import models, fields


class ReportPreviewWizard(models.TransientModel):
    _name = 'primetech.report.preview.wizard'
    _description = 'Prévisualisation Rapport'

    name = fields.Char()

    html_content = fields.Html(
        string='Aperçu',
        sanitize=False,
        readonly=True,
    )

    report_xmlid = fields.Char()

    wizard_id = fields.Integer()

    def action_print(self):

        wizard = self.env[
            'primetech.cash.flow.report.wizard'
        ].browse(self.wizard_id)

        return self.env.ref(
            self.report_xmlid
        ).report_action(wizard)
    
    
    def action_print(self):

        wizard = self.env[
            'primetech.receivable.report.wizard'
        ].browse(self.wizard_id)

        return self.env.ref(
            self.report_xmlid
        ).report_action(wizard)    
    
    def action_print(self):

        wizard = self.env[
            'primetech.sales.report.wizard'
        ].browse(self.wizard_id)

        return self.env.ref(
            self.report_xmlid
        ).report_action(wizard)   
