from datetime import datetime
from odoo import models


class ReportSales(models.AbstractModel):

    _name = 'report.primetech_daily_reports.sales_report_template'
    _description = 'Rapport Ventes'

    def _get_report_values(
        self,
        docids,
        data=None
    ):

        wizard = self.env[
            'primetech.sales.report.wizard'
        ].browse(docids)

        # =========================
        # CHANGEMENT ICI UNIQUEMENT
        # =========================

        sale_lines = self.env['sale.report'].search([

            ('date', '>=', wizard.date_from),
            ('date', '<=', wizard.date_to),
            ('company_id', '=', self.env.company.id),

        ])

        lines = []

        grand_total_ht = 0
        grand_total_ttc = 0

        show_discount = False

        seller_summary = {}
        customer_summary = {}
        product_summary = {}

        for line in sale_lines:

            # sale.report n'a pas de discount fiable
            # donc on laisse ton flag mais neutre
            if hasattr(line, 'discount') and line.discount:
                show_discount = True

            lines.append({

                'invoice':
                    line.order_id.name if line._fields.get('order_id') else '',

                'date':
                    line.date,

                'customer':
                    line.partner_id.name,

                'salesperson':
                    line.user_id.name or '',

                'product':
                    line.product_id.display_name,

                'qty':
                    line.product_uom_qty,

                'unit_price':
                    line.price_unit,

                'discount':
                    getattr(line, 'discount', 0),

                'total_ht':
                    line.price_subtotal,

                'total_ttc':
                    line.price_total if 'price_total' in line._fields else line.price_subtotal,

            })

            grand_total_ht += line.price_subtotal
            grand_total_ttc += (
                line.price_total
                if 'price_total' in line._fields
                else line.price_subtotal
            )

            seller = line.user_id.name or 'Non défini'

            seller_summary.setdefault(
                seller,
                {
                    'qty': 0,
                    'ca_ht': 0,
                    'ca_ttc': 0,
                }
            )

            seller_summary[seller]['qty'] += line.product_uom_qty
            seller_summary[seller]['ca_ht'] += line.price_subtotal
            seller_summary[seller]['ca_ttc'] += (
                line.price_total
                if 'price_total' in line._fields
                else line.price_subtotal
            )

            customer = line.partner_id.name

            customer_summary.setdefault(
                customer,
                {
                    'ca_ht': 0,
                    'ca_ttc': 0,
                }
            )

            customer_summary[customer]['ca_ht'] += line.price_subtotal
            customer_summary[customer]['ca_ttc'] += (
                line.price_total
                if 'price_total' in line._fields
                else line.price_subtotal
            )

            product = line.product_id.display_name

            product_summary.setdefault(
                product,
                {
                    'qty': 0,
                    'ca_ht': 0,
                }
            )

            product_summary[product]['qty'] += line.product_uom_qty
            product_summary[product]['ca_ht'] += line.price_subtotal

        return {

            'doc_ids': docids,

            'doc_model':
                'primetech.sales.report.wizard',

            'docs':
                wizard,

            'lines':
                lines,

            'grand_total_ht':
                grand_total_ht,

            'grand_total_ttc':
                grand_total_ttc,

            'show_discount':
                show_discount,

            'seller_summary':
                seller_summary,

            'customer_summary':
                customer_summary,

            'product_summary':
                product_summary,

            'invoice_count':
                len(sale_lines),

            'customer_count':
                len(customer_summary),

            'seller_count':
                len(seller_summary),

            'print_date':
                datetime.now(),
        }