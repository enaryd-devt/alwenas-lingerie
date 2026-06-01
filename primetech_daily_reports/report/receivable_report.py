from collections import defaultdict
from odoo import models, fields


class ReportReceivable(models.AbstractModel):
    _name = 'report.primetech_daily_reports.receivable_report_template'
    _description = 'Etat des Creances Partenaires'

    def _get_report_values(self, docids, data=None):

        wizard = self.env['primetech.receivable.report.wizard'].browse(docids)[:1]

        # Solde réel partenaire : toutes les écritures tiers
        balance_domain = [
            ('partner_id', '!=', False),
            ('parent_state', '=', 'posted'),
            ('date', '<=', wizard.report_date),
            ('account_id.account_type', 'in', [
                'asset_receivable',
                'liability_payable',
            ]),
        ]

        if wizard.company_id:
            balance_domain.append(('company_id', '=', wizard.company_id.id))

        if wizard.partner_ids:
            balance_domain.append(('partner_id', 'in', wizard.partner_ids.ids))

        balance_lines = self.env['account.move.line'].search(balance_domain)

        partners = defaultdict(lambda: {
            'partner_name': '',
            'phone': '',
            'email': '',
            'city': '',
            'balance': 0.0,
            'invoice_total': 0.0,
            'lines': [],
        })

        # Solde réel partenaire
        for line in balance_lines:

            partner = (
                line.partner_id.commercial_partner_id
                if wizard.commercial_partner_only
                else line.partner_id
            )

            key = partner.id

            partners[key]['partner_name'] = partner.name or ''
            partners[key]['phone'] = partner.phone or ''
            partners[key]['email'] = partner.email or ''
            partners[key]['city'] = partner.city or ''

            partners[key]['balance'] += (
                line.debit - line.credit
            )

        # Justification de la créance :
        # uniquement les factures ouvertes
        invoice_domain = [
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'in_invoice']),
            ('invoice_date', '<=', wizard.report_date),
            ('amount_residual', '>', 0),
        ]

        if wizard.company_id:
            invoice_domain.append(
                ('company_id', '=', wizard.company_id.id)
            )

        if wizard.partner_ids:
            invoice_domain.append(
                ('partner_id', 'in', wizard.partner_ids.ids)
            )

        invoices = self.env['account.move'].search(
            invoice_domain,
            order='partner_id,invoice_date'
        )

        total_open_invoices = 0.0

        for invoice in invoices:

            partner = (
                invoice.partner_id.commercial_partner_id
                if wizard.commercial_partner_only
                else invoice.partner_id
            )

            key = partner.id

            residual = invoice.amount_residual

            partners[key]['invoice_total'] += residual
            total_open_invoices += residual

            partners[key]['lines'].append({
                'date': invoice.invoice_date,
                'due_date': invoice.invoice_date_due,
                'number': invoice.name,
                'reference': invoice.ref or '',
                'amount_total': invoice.amount_total,
                'residual': residual,
            })

        partners_data = []

        for partner in partners.values():

            if (
                not wizard.include_zero_balance
                and abs(partner['balance']) < 0.01
            ):
                continue

            partners_data.append(partner)

        partners_data.sort(
            key=lambda x: x['balance'],
            reverse=True
        )

        return {
            'doc_ids': docids,
            'doc_model': 'primetech.receivable.report.wizard',
            'docs': wizard,
            'partners_data': partners_data,
            'partner_count': len(partners_data),
            'invoice_count': len(invoices),
            'total_open_invoices': total_open_invoices,
            'net_total': sum(
                p['balance'] for p in partners_data
            ),
            'currency': 'FCFA',
            'print_date': fields.Datetime.now(),
        }
