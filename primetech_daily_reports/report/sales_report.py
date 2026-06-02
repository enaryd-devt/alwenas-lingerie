from collections import defaultdict
from datetime import datetime
from odoo import models

class ReportSales(models.AbstractModel):
    _name = 'report.primetech_daily_reports.sales_report_template'
    _description = 'Rapport Ventes'

    def _get_report_values(self, docids, data=None):

        wizard = self.env[
            'primetech.sales.report.wizard'
        ].browse(docids)

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
        product_summary = {}
        weekly_customer_summary = defaultdict(dict)

        for line in sale_lines:

            if hasattr(line, 'discount') and line.discount:
                show_discount = True

            total_ttc = (
                line.price_total
                if 'price_total' in line._fields
                else line.price_subtotal
            )

    

            lines.append({
                'order':
                    line.order_reference or '',

                'date':
                    line.date,

                'customer':
                    line.partner_id.name or '',

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
                    total_ttc,
            })
            

            grand_total_ht += line.price_subtotal
            grand_total_ttc += total_ttc

            # =====================
            # Synthèse vendeur
            # =====================

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
            seller_summary[seller]['ca_ttc'] += total_ttc

            # =====================
            # Synthèse client / semaine
            # =====================

            customer = line.partner_id.name or 'Client inconnu'

            date_value = line.date.date() if hasattr(line.date, 'date') else line.date
            week_number = date_value.isocalendar()[1]
            year = date_value.year

            week_label = f"Semaine {week_number} - {year}"

            if customer not in weekly_customer_summary[week_label]:

                weekly_customer_summary[week_label][customer] = {
                    'ca_ht': 0,
                    'ca_ttc': 0,
                }

            weekly_customer_summary[week_label][customer]['ca_ht'] += (
                line.price_subtotal
            )

            weekly_customer_summary[week_label][customer]['ca_ttc'] += (
                total_ttc
            )

            # =====================
            # Synthèse article
            # =====================

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

        order_count = len(
            set(
                sale_lines.mapped('order_reference')
            )
        )
        customer_count = len(set(sale_lines.mapped('partner_id')))
        seller_count = len(set(sale_lines.mapped('user_id')))

        weekly_customer_summary = dict(
            sorted(
                weekly_customer_summary.items(),
                key=lambda x: (
                    int(x[0].split('-')[1].strip()),
                    int(x[0].split()[1])
                )
            )
        )

        total_commission = 0
        customer_totals = {}

        for week_data in weekly_customer_summary.values():

            for customer_data in week_data.values():

                customer_data['commission'] = 0

                if customer_data['ca_ht'] >= 150000:
                    customer_data['commission'] = customer_data['ca_ht'] * 0.015

                total_commission += customer_data['commission']

            
        seller_totals = {}

        for week_data in weekly_customer_summary.values():

            for seller_name, seller_data in week_data.items():

                if seller_name not in seller_totals:

                    seller_totals[seller_name] = {
                        'ca_ht': 0,
                        'commission': 0,
                    }

                seller_totals[seller_name]['ca_ht'] += seller_data['ca_ht']

                seller_totals[seller_name]['commission'] += (
                    seller_data.get('commission', 0)
                )


        top_commissions = sorted(
            seller_totals.items(),
            key=lambda x: x[1]['commission'],
            reverse=True
        )[:5]

        top_sellers = sorted(
            seller_totals.items(),
            key=lambda x: x[1]['ca_ht'],
            reverse=True
        )[:5]

        customer_count = len(
            set(
                sale_lines.mapped('partner_id')
            )
        )

        return {
            'customer_count': customer_count,

            'seller_totals': seller_totals,
            'top_sellers': top_sellers,
            'top_commissions': top_commissions,

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

            'weekly_customer_summary':
                dict(weekly_customer_summary),

            'product_summary':
                product_summary,

            'order_count':
                order_count,

            'customer_count':
                customer_count,

            'seller_count':
                seller_count,

            'print_date':
                datetime.now(),

            'total_commission': total_commission,
        }
    