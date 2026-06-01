{
    'name': 'PrimeTech Daily Reports',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Rapports journaliers de trésorerie, ventes et créances',
    'author': 'PrimeTech Services',
    'website': 'https://www.primetech.cm',
    'license': 'LGPL-3',

    'depends': [
        'account',
        'sale_management',
        'stock',
    ],

    'data': [

        'security/ir.model.access.csv',

        'views/cash_flow_report_views.xml',
        'views/sales_report_views.xml',
        'views/receivable_report_views.xml',

        'views/menu_views.xml',
        'views/report_preview_views.xml',

        'report/report_actions.xml',

        'report/cash_flow_report_templates.xml',
        'report/sales_report_templates.xml',
        'report/receivable_report_templates.xml',
    ],

    'assets': { 
        'web.report_assets_common': [ 
            'primetech_daily_reports/static/src/css/*.css',

            ],
    },      

    'installable': True,
    'application': False,
}