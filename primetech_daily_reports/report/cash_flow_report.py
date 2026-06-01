from odoo import models


class ReportCashFlow(models.AbstractModel):
    _name = 'report.primetech_daily_reports.cash_flow_report_template'
    _description = 'Rapport de Trésorerie'

    def _get_report_values(self, docids, data=None):

        wizard = self.env[
            'primetech.cash.flow.report.wizard'
        ].browse(docids[:1])

        if not wizard:
            return {
                'doc_ids': [],
                'doc_model': 'primetech.cash.flow.report.wizard',
                'docs': False,
                'lines': [],
                'total_in': 0.0,
                'total_out': 0.0,
                'balance': 0.0,
            }

        lines = []
        total_in = 0.0
        total_out = 0.0

        # --------------------------------------------------
        # PAIEMENTS
        # --------------------------------------------------

        payment_domain = [
            ('state', 'in', ['paid', 'posted']),
            ('date', '>=', wizard.date_from),
            ('date', '<=', wizard.date_to),
        ]

        if wizard.journal_ids:
            payment_domain.append(
                ('journal_id', 'in', wizard.journal_ids.ids)
            )

        payments = self.env[
            'account.payment'
        ].search(
            payment_domain,
            order='date asc, id asc'   # ✅ MODIFIÉ ICI
        )

        previous_payment_domain = [
            ('state', 'in', ['paid', 'posted']),
            ('date', '<', wizard.date_from),
        ]

        if wizard.journal_ids:
            previous_payment_domain.append(
                ('journal_id', 'in', wizard.journal_ids.ids)
            )

        previous_payments = self.env[
            'account.payment'
        ].search(previous_payment_domain)

        for payment in payments:

            amount = payment.amount or 0.0

            payment_type = (
                'Encaissement'
                if payment.payment_type == 'inbound'
                else 'Décaissement'
            )

            if payment.payment_type == 'inbound':
                total_in += amount
            else:
                total_out += amount

            invoice_names = []

            try:

                if payment.move_id:

                    for move_line in payment.move_id.line_ids:

                        matcheds = (
                            move_line.matched_debit_ids
                            | move_line.matched_credit_ids
                        )

                        for matched in matcheds:

                            debit_move = matched.debit_move_id.move_id
                            credit_move = matched.credit_move_id.move_id

                            for move in [debit_move, credit_move]:

                                if move.move_type in (
                                    'out_invoice',
                                    'in_invoice',
                                    'out_refund',
                                    'in_refund'
                                ):
                                    invoice_names.append(move.name)

            except Exception:
                pass

            invoice_names = ', '.join(
                sorted(set(invoice_names))
            )

            lines.append({
                'date': payment.date,
                'reference': (
                    payment.move_id.name
                    if payment.move_id
                    else ''
                ),
                'partner': (
                    payment.partner_id.name
                    if payment.partner_id
                    else ''
                ),
                'invoice': invoice_names,
                'type': payment_type,
                'amount': amount,
                'journal': (
                    payment.journal_id.name
                    if payment.journal_id
                    else ''
                ),
            })

        # --------------------------------------------------
        # RELEVES DE CAISSE / BANQUE
        # --------------------------------------------------

        statement_domain = [
            ('date', '>=', wizard.date_from),
            ('date', '<=', wizard.date_to),
        ]

        if wizard.journal_ids:
            statement_domain.append(
                ('journal_id', 'in', wizard.journal_ids.ids)
            )

        statement_lines = self.env[
            'account.bank.statement.line'
        ].search(
            statement_domain,
            order='date asc, id asc'   # ✅ MODIFIÉ ICI
        )

        previous_statement_domain = [
            ('date', '<', wizard.date_from),
        ]

        if wizard.journal_ids:
            previous_statement_domain.append(
                ('journal_id', 'in', wizard.journal_ids.ids)
            )

        previous_statements = self.env[
            'account.bank.statement.line'
        ].search(previous_statement_domain)

        for statement in statement_lines:

            amount = statement.amount or 0.0

            if amount == 0:
                continue

            flow_type = (
                'Encaissement'
                if amount > 0
                else 'Décaissement'
            )

            if amount > 0:
                total_in += amount
            else:
                total_out += abs(amount)

            lines.append({
                'date': statement.date,
                'reference': (
                    statement.payment_ref
                    or statement.name
                    or ''
                ),
                'partner': (
                    statement.partner_id.name
                    if statement.partner_id
                    else ''
                ),
                'invoice': '',
                'type': flow_type,
                'amount': abs(amount),
                'journal': (
                    statement.journal_id.name
                    if statement.journal_id
                    else ''
                ),
            })

        # --------------------------------------------------
        # SYNTHESE PAR JOURNAL
        # --------------------------------------------------

        journal_ids = set()

        for payment in payments:
            if payment.journal_id:
                journal_ids.add(payment.journal_id.id)

        for statement in statement_lines:
            if statement.payment_ids:
                continue

            if statement.journal_id:
                journal_ids.add(statement.journal_id.id)

        journals = self.env['account.journal'].browse(
            list(journal_ids)
        )

        journal_summary = []

        for journal in journals:

            in_amount = sum(
                line['amount']
                for line in lines
                if (
                    line['journal'] == journal.name
                    and line['type'] == 'Encaissement'
                )
            )

            out_amount = sum(
                line['amount']
                for line in lines
                if (
                    line['journal'] == journal.name
                    and line['type'] == 'Décaissement'
                )
            )

            opening_in = 0.0
            opening_out = 0.0

            for payment in previous_payments:

                if payment.journal_id != journal:
                    continue

                if payment.payment_type == 'inbound':
                    opening_in += payment.amount
                else:
                    opening_out += payment.amount

            for statement in previous_statements:

                if statement.journal_id != journal:
                    continue

                amount = statement.amount or 0.0

                if amount > 0:
                    opening_in += amount
                else:
                    opening_out += abs(amount)

            opening_balance = (
                opening_in
                - opening_out
            )

            closing_balance = (
                opening_balance
                + in_amount
                - out_amount
            )

            journal_summary.append({
                'name': journal.name,
                'opening': opening_balance,
                'in': in_amount,
                'out': out_amount,
                'closing': closing_balance,
            })

        journal_summary = sorted(
            journal_summary,
            key=lambda x: x['name']
        )

        summary_opening = sum(
            j['opening']
            for j in journal_summary
        )

        summary_in = sum(
            j['in']
            for j in journal_summary
        )

        summary_out = sum(
            j['out']
            for j in journal_summary
        )

        summary_closing = sum(
            j['closing']
            for j in journal_summary
        )

        return {
            'doc_ids': wizard.ids,
            'doc_model': 'primetech.cash.flow.report.wizard',
            'docs': wizard,
            'lines': lines,
            'total_in': total_in,
            'total_out': total_out,
            'balance': total_in - total_out,
            'payment_count': len(lines),
            'journal_summary': journal_summary,
            'summary_opening': summary_opening,
            'summary_in': summary_in,
            'summary_out': summary_out,
            'summary_closing': summary_closing,
        }