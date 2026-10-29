import json

import frappe
from frappe.utils.password import update_password


def doc_shortcut(doctype_name, label=None):
    return {"label": label or doctype_name, "link_to": doctype_name, "type": "DocType"}


def doc_link(doctype_name, label=None):
    return {"type": "Link", "label": label or doctype_name, "link_type": "DocType", "link_to": doctype_name}


def report_link(report_name, label=None):
    return {
        "type": "Link",
        "label": label or report_name,
        "link_type": "Report",
        "link_to": report_name,
        "is_query_report": 1,
    }


def slug_id(value):
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "-", "_"}:
            cleaned.append("-")
    return "".join(cleaned)[:60] or "block"


DEMO_CENTER = "Demo Center"
EXECUTIVE_DASHBOARD = "Executive Dashboard"
BRANCH_OPERATIONS = "Branch Operations"
SALES_COUNTER = "Sales Counter"
INVENTORY_HUB = "Inventory Hub"
FINANCE_DESK = "Finance Desk"
PEOPLE_PAYROLL = "People & Payroll"

DREAMWEAR_COMPANY = "Dream Wear"
DEMO_PASSWORD = "Demo@2026"
TIME_ZONE = "Asia/Aden"
LANGUAGE = "ar"

CHART_REVENUE_PULSE = "نبض المبيعات والربحية"
CHART_STOCK_BY_WAREHOUSE = "قيمة المخزون حسب المخزن"
CHART_TOP_CUSTOMERS = "أفضل العملاء"
CHART_TEAM_BY_BRANCH = "توزيع الفريق على الفروع"

CARD_NET_SALES = "صافي المبيعات"
CARD_PURCHASE_SPEND = "إجمالي المشتريات"
CARD_COLLECTIONS = "إجمالي المقبوضات"
CARD_SUPPLIER_PAYMENTS = "إجمالي المدفوعات"
CARD_STOCK_VALUE = "قيمة المخزون"
CARD_ACTIVE_ITEMS = "الأصناف النشطة"
CARD_ACTIVE_CUSTOMERS = "العملاء النشطون"
CARD_ACTIVE_SUPPLIERS = "الموردون النشطون"
CARD_EMPLOYEE_COUNT = "عدد الموظفين"
CARD_WAREHOUSE_COUNT = "عدد المخازن"

WORKSPACE_SEQUENCE = {
    DEMO_CENTER: 1,
    EXECUTIVE_DASHBOARD: 2,
    BRANCH_OPERATIONS: 3,
    SALES_COUNTER: 4,
    INVENTORY_HUB: 5,
    FINANCE_DESK: 6,
    PEOPLE_PAYROLL: 7,
    "Users": 90,
    "ERPNext Settings": 91,
}

HIDDEN_STANDARD_WORKSPACES = {
    "Build",
    "ERPNext Integrations",
    "Integrations",
    "Website",
    "Welcome Workspace",
}

VISIBLE_STANDARD_WORKSPACES = {
    "Home",
    "Selling",
    "Buying",
    "Stock",
    "Accounting",
    "Financial Reports",
    "Receivables",
    "Payables",
    "CRM",
    "HR",
    "Payroll",
    "Salary Payout",
    "Tax & Benefits",
    "Recruitment",
    "Employee Lifecycle",
    "Performance",
    "Shift & Attendance",
    "Expense Claims",
    "Leaves",
    "Projects",
    "Support",
    "Manufacturing",
    "Quality",
    "Assets",
    "Tools",
}

CUSTOM_DASHBOARD_CHARTS = [
    {
        "name": CHART_REVENUE_PULSE,
        "title": "نبض المبيعات والربحية",
        "source_name": "Profit and Loss",
        "color": "#0f766e",
        "roles": ["System Manager", "Sales Manager", "Accounts Manager"],
    },
    {
        "name": CHART_STOCK_BY_WAREHOUSE,
        "title": "قيمة المخزون حسب المخزن",
        "source_name": "Warehouse wise Stock Value",
        "color": "#1d4ed8",
        "roles": ["System Manager", "Stock Manager", "Stock User", "Accounts Manager"],
    },
    {
        "name": CHART_TOP_CUSTOMERS,
        "title": "أفضل العملاء",
        "source_name": "Top Customers",
        "color": "#b45309",
        "roles": ["System Manager", "Sales Manager", "Sales User", "Accounts Manager"],
    },
    {
        "name": CHART_TEAM_BY_BRANCH,
        "title": "توزيع الفريق على الفروع",
        "source_name": "Employees by Branch",
        "color": "#15803d",
        "roles": ["System Manager", "HR Manager", "HR User"],
    },
]

CUSTOM_NUMBER_CARDS = [
    {
        "name": CARD_NET_SALES,
        "label": "صافي المبيعات",
        "source_name": "Total Outgoing Bills",
        "color": "Green",
        "background_color": "#dcfce7",
    },
    {
        "name": CARD_PURCHASE_SPEND,
        "label": "إجمالي المشتريات",
        "source_name": "Total Incoming Bills",
        "color": "Orange",
        "background_color": "#ffedd5",
    },
    {
        "name": CARD_COLLECTIONS,
        "label": "إجمالي المقبوضات",
        "source_name": "Total Incoming Payment",
        "color": "Blue",
        "background_color": "#dbeafe",
    },
    {
        "name": CARD_SUPPLIER_PAYMENTS,
        "label": "إجمالي المدفوعات",
        "source_name": "Total Outgoing Payment",
        "color": "Red",
        "background_color": "#fee2e2",
    },
    {
        "name": CARD_STOCK_VALUE,
        "label": "قيمة المخزون",
        "source_name": "Total Stock Value",
        "color": "Blue",
        "background_color": "#e0f2fe",
    },
    {
        "name": CARD_ACTIVE_ITEMS,
        "label": "الأصناف النشطة",
        "source_name": "Total Active Items",
        "color": "Purple",
        "background_color": "#f3e8ff",
    },
    {
        "name": CARD_ACTIVE_CUSTOMERS,
        "label": "العملاء النشطون",
        "source_name": "Active Customers",
        "color": "Green",
        "background_color": "#dcfce7",
    },
    {
        "name": CARD_ACTIVE_SUPPLIERS,
        "label": "الموردون النشطون",
        "source_name": "Active Suppliers",
        "color": "Orange",
        "background_color": "#ffedd5",
    },
    {
        "name": CARD_EMPLOYEE_COUNT,
        "label": "عدد الموظفين",
        "source_name": "Total Employees",
        "color": "Green",
        "background_color": "#dcfce7",
    },
    {
        "name": CARD_WAREHOUSE_COUNT,
        "label": "عدد المخازن",
        "source_name": "Total Warehouses",
        "color": "Blue",
        "background_color": "#dbeafe",
    },
]

WORKSPACE_DEFINITIONS = [
    {
        "name": DEMO_CENTER,
        "module": "Demo Standard",
        "icon": "home",
        "indicator_color": "green",
        "roles": [],
        "header": "مركز العرض",
        "subtitle": "الوصول الأسرع لأهم ما يحتاجه العميل أثناء العرض الحي",
        "charts": [CHART_TOP_CUSTOMERS, CHART_STOCK_BY_WAREHOUSE],
        "number_cards": [
            CARD_NET_SALES,
            CARD_STOCK_VALUE,
            CARD_ACTIVE_CUSTOMERS,
            CARD_ACTIVE_ITEMS,
        ],
        "shortcuts": [
            doc_shortcut("POS Invoice"),
            doc_shortcut("Sales Invoice"),
            doc_shortcut("Payment Entry"),
            doc_shortcut("Stock Entry"),
            doc_shortcut("Purchase Order"),
            doc_shortcut("Employee"),
            doc_shortcut("Accounts Settings"),
            doc_shortcut("Stock Settings"),
            doc_shortcut("Selling Settings"),
            doc_shortcut("Buying Settings"),
        ],
        "cards": [
            {
                "label": "Client Walkthrough",
                "links": [
                    doc_link("POS Profile"),
                    doc_link("Customer"),
                    doc_link("Item"),
                    doc_link("Warehouse"),
                ],
            },
            {
                "label": "Commercial Performance",
                "links": [
                    report_link("Sales Analytics"),
                    report_link("Gross Profit"),
                    report_link("Stock Balance"),
                    report_link("Profit and Loss Statement"),
                ],
            },
            {
                "label": "Operations Snapshot",
                "links": [
                    doc_link("Branch"),
                    doc_link("Supplier"),
                    doc_link("Payment Entry"),
                    doc_link("Salary Slip"),
                ],
            },
        ],
    },
    {
        "name": EXECUTIVE_DASHBOARD,
        "module": "Demo Standard",
        "icon": "dashboard",
        "indicator_color": "blue",
        "roles": ["System Manager", "Sales Manager", "Accounts Manager"],
        "header": "لوحة الإدارة التنفيذية",
        "subtitle": "مؤشرات المبيعات والربحية والمخزون على مستوى الشركة والفروع",
        "charts": [CHART_REVENUE_PULSE, CHART_STOCK_BY_WAREHOUSE],
        "number_cards": [
            CARD_NET_SALES,
            CARD_COLLECTIONS,
            CARD_STOCK_VALUE,
            CARD_ACTIVE_CUSTOMERS,
        ],
        "shortcuts": [
            doc_shortcut("Account", "Chart of Accounts"),
            doc_shortcut("Accounts Settings"),
            doc_shortcut("Sales Invoice"),
            doc_shortcut("Purchase Invoice"),
            doc_shortcut("Payment Entry"),
            doc_shortcut("Stock Entry"),
            doc_shortcut("Customer"),
            doc_shortcut("Supplier"),
        ],
        "cards": [
            {
                "label": "Performance Snapshot",
                "links": [
                    report_link("Sales Analytics"),
                    report_link("Gross Profit"),
                    report_link("Profit and Loss Statement"),
                    report_link("Customer Credit Balance"),
                ],
            },
            {
                "label": "Branch Control",
                "links": [
                    doc_link("Branch"),
                    doc_link("POS Profile"),
                    doc_link("Warehouse"),
                    doc_link("Sales Invoice"),
                ],
            },
            {
                "label": "Inventory Visibility",
                "links": [
                    report_link("Stock Balance"),
                    report_link("Stock Ledger"),
                    report_link("Item-wise Sales History"),
                    doc_link("Item"),
                ],
            },
        ],
    },
    {
        "name": BRANCH_OPERATIONS,
        "module": "Demo Standard",
        "icon": "retail",
        "indicator_color": "orange",
        "roles": ["Sales Manager", "Stock User", "Accounts User"],
        "header": "عمليات الفرع",
        "subtitle": "تشغيل الفرع يومياً بين المبيعات والتحصيل والمتابعة الميدانية",
        "charts": [CHART_TOP_CUSTOMERS],
        "number_cards": [
            CARD_NET_SALES,
            CARD_COLLECTIONS,
            CARD_ACTIVE_CUSTOMERS,
            CARD_ACTIVE_ITEMS,
        ],
        "shortcuts": [
            doc_shortcut("POS Invoice"),
            doc_shortcut("Sales Invoice"),
            doc_shortcut("Payment Entry"),
            doc_shortcut("Customer"),
            doc_shortcut("Item"),
            doc_shortcut("Stock Entry"),
        ],
        "cards": [
            {
                "label": "Daily Retail",
                "links": [
                    doc_link("POS Profile"),
                    report_link("Sales Analytics"),
                    report_link("Customer Credit Balance"),
                    doc_link("Item Price"),
                ],
            },
            {
                "label": "Branch Control",
                "links": [
                    doc_link("Warehouse"),
                    report_link("Stock Balance"),
                    doc_link("Branch"),
                    doc_link("Sales Invoice"),
                ],
            },
        ],
    },
    {
        "name": SALES_COUNTER,
        "module": "Demo Standard",
        "icon": "receipt",
        "indicator_color": "green",
        "roles": ["Sales User"],
        "header": "نقطة البيع",
        "subtitle": "واجهة مبسطة للكاشير تركز على الفوترة والتحصيل وخدمة العميل",
        "number_cards": [
            CARD_NET_SALES,
            CARD_ACTIVE_CUSTOMERS,
            CARD_ACTIVE_ITEMS,
        ],
        "shortcuts": [
            doc_shortcut("POS Invoice"),
            doc_shortcut("Sales Invoice"),
            doc_shortcut("Customer"),
            doc_shortcut("Item"),
            doc_shortcut("Payment Entry"),
            doc_shortcut("POS Profile"),
        ],
        "cards": [
            {
                "label": "Cash and Billing",
                "links": [
                    doc_link("POS Profile"),
                    doc_link("Mode of Payment"),
                    doc_link("Payment Entry"),
                    doc_link("Customer"),
                ],
            },
            {
                "label": "Product Lookup",
                "links": [
                    doc_link("Item"),
                    doc_link("Item Price"),
                    report_link("Stock Balance"),
                    doc_link("Sales Invoice"),
                ],
            },
        ],
    },
    {
        "name": INVENTORY_HUB,
        "module": "Demo Standard",
        "icon": "package",
        "indicator_color": "purple",
        "roles": ["Stock User", "Stock Manager", "Purchase User", "Purchase Manager"],
        "header": "مركز المخزون والمشتريات",
        "subtitle": "استلامات، تحويلات، متابعة الرصيد، وإعادة التوريد من مكان واحد",
        "charts": [CHART_STOCK_BY_WAREHOUSE],
        "number_cards": [
            CARD_STOCK_VALUE,
            CARD_ACTIVE_ITEMS,
            CARD_ACTIVE_SUPPLIERS,
            CARD_WAREHOUSE_COUNT,
        ],
        "shortcuts": [
            doc_shortcut("Item"),
            doc_shortcut("Warehouse"),
            doc_shortcut("Stock Entry"),
            doc_shortcut("Purchase Order"),
            doc_shortcut("Purchase Invoice"),
            doc_shortcut("Supplier"),
            doc_shortcut("Stock Settings"),
            doc_shortcut("Buying Settings"),
        ],
        "cards": [
            {
                "label": "Purchasing and Replenishment",
                "links": [
                    doc_link("Supplier"),
                    doc_link("Purchase Order"),
                    doc_link("Purchase Invoice"),
                    doc_link("Item"),
                ],
            },
            {
                "label": "Inventory Visibility",
                "links": [
                    report_link("Stock Balance"),
                    report_link("Stock Ledger"),
                    doc_link("Warehouse"),
                    report_link("Item-wise Sales History"),
                ],
            },
        ],
    },
    {
        "name": FINANCE_DESK,
        "module": "Demo Standard",
        "icon": "money-coins-1",
        "indicator_color": "blue",
        "roles": ["Accounts User", "Accounts Manager"],
        "header": "المكتب المالي",
        "subtitle": "فواتير، قيود، تحصيلات، وتقارير مالية جاهزة للعرض على العميل",
        "charts": [CHART_REVENUE_PULSE],
        "number_cards": [
            CARD_NET_SALES,
            CARD_PURCHASE_SPEND,
            CARD_COLLECTIONS,
            CARD_SUPPLIER_PAYMENTS,
        ],
        "shortcuts": [
            doc_shortcut("Account", "Chart of Accounts"),
            doc_shortcut("Accounts Settings"),
            doc_shortcut("Sales Invoice"),
            doc_shortcut("Purchase Invoice"),
            doc_shortcut("Payment Entry"),
            doc_shortcut("Journal Entry"),
            doc_shortcut("Customer"),
            doc_shortcut("Supplier"),
        ],
        "cards": [
            {
                "label": "Financial Control",
                "links": [
                    report_link("General Ledger"),
                    report_link("Profit and Loss Statement"),
                    report_link("Accounts Receivable"),
                    report_link("Accounts Payable"),
                ],
            },
            {
                "label": "Billing and Collections",
                "links": [
                    doc_link("Sales Invoice"),
                    doc_link("Purchase Invoice"),
                    doc_link("Payment Entry"),
                    report_link("Customer Credit Balance"),
                ],
            },
        ],
    },
    {
        "name": PEOPLE_PAYROLL,
        "module": "Demo Standard",
        "icon": "users",
        "indicator_color": "green",
        "roles": ["HR User", "HR Manager"],
        "header": "الموارد البشرية والرواتب",
        "subtitle": "بيانات الموظفين والرواتب في مساحة واحدة مناسبة للعرض السريع",
        "charts": [CHART_TEAM_BY_BRANCH],
        "number_cards": [CARD_EMPLOYEE_COUNT],
        "shortcuts": [
            doc_shortcut("Employee"),
            doc_shortcut("Salary Slip"),
            doc_shortcut("Department"),
            doc_shortcut("Designation"),
            doc_shortcut("Leave Application"),
            doc_shortcut("Attendance"),
            doc_shortcut("HR Settings"),
        ],
        "cards": [
            {
                "label": "HR Operations",
                "links": [
                    doc_link("Employee"),
                    doc_link("Department"),
                    doc_link("Designation"),
                    doc_link("Leave Application"),
                ],
            },
            {
                "label": "Payroll Control",
                "links": [
                    doc_link("Salary Slip"),
                    doc_link("Payroll Entry"),
                    doc_link("Employee Advance"),
                    doc_link("Attendance"),
                ],
            },
        ],
    },
]

DREAMWEAR_USER_CONFIG = {
    "admin@dreamwear.yemenfrappe.com": {
        "first_name": "محمد",
        "username": "admin",
        "gender": "Male",
        "birth_date": "1987-01-15",
        "roles": [
            "System Manager",
            "HR Manager",
            "Accounts Manager",
            "Stock Manager",
            "Sales Manager",
            "Purchase Manager",
            "Employee",
        ],
        "default_workspace": EXECUTIVE_DASHBOARD,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00001",
        },
    },
    "manager_sanaa@dreamwear.yemenfrappe.com": {
        "first_name": "خالد",
        "username": "manager_sanaa",
        "gender": "Male",
        "birth_date": "1989-03-10",
        "roles": ["Sales Manager", "Stock User", "Accounts User", "Employee"],
        "default_workspace": BRANCH_OPERATIONS,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00009",
            "Branch": "Sanaa_Main",
            "Warehouse": "DW_Sanaa_Main_WH - DW",
            "Cost Center": "Sanaa_Main - DW",
        },
        "defaults": {
            "branch": "Sanaa_Main",
            "default_warehouse": "DW_Sanaa_Main_WH - DW",
            "cost_center": "Sanaa_Main - DW",
        },
    },
    "cashier_sanaa@dreamwear.yemenfrappe.com": {
        "first_name": "نور",
        "username": "cashier_sanaa",
        "gender": "Female",
        "birth_date": "1998-04-11",
        "roles": ["Sales User", "Employee"],
        "default_workspace": SALES_COUNTER,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00003",
            "Branch": "Sanaa_Main",
            "Warehouse": "DW_Sanaa_Main_WH - DW",
            "Cost Center": "Sanaa_Main - DW",
            "POS Profile": "DW_Sanaa_Main_POS",
        },
        "defaults": {
            "branch": "Sanaa_Main",
            "default_warehouse": "DW_Sanaa_Main_WH - DW",
            "cost_center": "Sanaa_Main - DW",
            "pos_profile": "DW_Sanaa_Main_POS",
            "is_pos": 1,
        },
    },
    "cashier_baous@dreamwear.yemenfrappe.com": {
        "first_name": "ليلى",
        "username": "cashier_baous",
        "gender": "Female",
        "birth_date": "1997-05-10",
        "roles": ["Sales User", "Employee"],
        "default_workspace": SALES_COUNTER,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00004",
            "Branch": "Bait_Baous",
            "Warehouse": "DW_Bait_Baous_WH - DW",
            "Cost Center": "Bait_Baous - DW",
            "POS Profile": "DW_Bait_Baous_POS",
        },
        "defaults": {
            "branch": "Bait_Baous",
            "default_warehouse": "DW_Bait_Baous_WH - DW",
            "cost_center": "Bait_Baous - DW",
            "pos_profile": "DW_Bait_Baous_POS",
            "is_pos": 1,
        },
    },
    "cashier_aden@dreamwear.yemenfrappe.com": {
        "first_name": "سارة",
        "username": "cashier_aden",
        "gender": "Female",
        "birth_date": "1992-02-01",
        "roles": ["Sales User", "Employee"],
        "default_workspace": SALES_COUNTER,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00005",
            "Branch": "Aden_Mansoura",
            "Warehouse": "DW_Aden_Mansoura_WH - DW",
            "Cost Center": "Aden_Mansoura - DW",
            "POS Profile": "DW_Aden_Mansoura_POS",
        },
        "defaults": {
            "branch": "Aden_Mansoura",
            "default_warehouse": "DW_Aden_Mansoura_WH - DW",
            "cost_center": "Aden_Mansoura - DW",
            "pos_profile": "DW_Aden_Mansoura_POS",
            "is_pos": 1,
        },
    },
    "cashier_mukalla@dreamwear.yemenfrappe.com": {
        "first_name": "فاطمة",
        "username": "cashier_mukalla",
        "gender": "Female",
        "birth_date": "1991-06-01",
        "roles": ["Sales User", "Employee"],
        "default_workspace": SALES_COUNTER,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00006",
            "Branch": "Mukalla_Fowa",
            "Warehouse": "DW_Mukalla_Fowa_WH - DW",
            "Cost Center": "Mukalla_Fowa - DW",
            "POS Profile": "DW_Mukalla_Fowa_POS",
        },
        "defaults": {
            "branch": "Mukalla_Fowa",
            "default_warehouse": "DW_Mukalla_Fowa_WH - DW",
            "cost_center": "Mukalla_Fowa - DW",
            "pos_profile": "DW_Mukalla_Fowa_POS",
            "is_pos": 1,
        },
    },
    "inventory@dreamwear.yemenfrappe.com": {
        "first_name": "سلمان",
        "username": "inventory",
        "gender": "Male",
        "birth_date": "1995-01-10",
        "roles": ["Stock User", "Purchase User", "Employee"],
        "default_workspace": INVENTORY_HUB,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00007",
            "Branch": "Sanaa_Main",
            "Warehouse": "DW_Central_WH - DW",
            "Cost Center": "Sanaa_Main - DW",
        },
        "defaults": {
            "branch": "Sanaa_Main",
            "default_warehouse": "DW_Central_WH - DW",
            "cost_center": "Sanaa_Main - DW",
        },
    },
    "inventory.aden@dreamwear.yemenfrappe.com": {
        "first_name": "إبراهيم",
        "gender": "Male",
        "birth_date": "1996-11-20",
        "roles": ["Stock User", "Purchase User", "Employee"],
        "default_workspace": INVENTORY_HUB,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00008",
            "Branch": "Aden_Mansoura",
            "Warehouse": "DW_Aden_Mansoura_WH - DW",
            "Cost Center": "Aden_Mansoura - DW",
        },
        "defaults": {
            "branch": "Aden_Mansoura",
            "default_warehouse": "DW_Aden_Mansoura_WH - DW",
            "cost_center": "Aden_Mansoura - DW",
        },
    },
    "accounts@dreamwear.yemenfrappe.com": {
        "first_name": "أحمد",
        "username": "accounts",
        "gender": "Male",
        "birth_date": "1990-09-20",
        "roles": ["Accounts User", "HR User", "Employee"],
        "default_workspace": FINANCE_DESK,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Employee": "HR-EMP-00002",
        },
    },
    "hr@dreamwear.yemenfrappe.com": {
        "first_name": "هدى",
        "username": "hr",
        "gender": "Female",
        "birth_date": "1993-07-14",
        "roles": ["HR Manager"],
        "default_workspace": PEOPLE_PAYROLL,
        "permissions": {"Company": DREAMWEAR_COMPANY},
    },
    "purchasing@dreamwear.yemenfrappe.com": {
        "first_name": "مازن",
        "username": "purchasing",
        "gender": "Male",
        "birth_date": "1991-10-08",
        "roles": ["Purchase Manager", "Stock User"],
        "default_workspace": INVENTORY_HUB,
        "permissions": {
            "Company": DREAMWEAR_COMPANY,
            "Warehouse": "DW_Central_WH - DW",
        },
        "defaults": {
            "default_warehouse": "DW_Central_WH - DW",
        },
    },
}


def after_install():
    apply_demo_standard()


def after_migrate():
    apply_demo_standard()


def apply_demo_standard():
    frappe.db.set_single_value("System Settings", "language", LANGUAGE, update_modified=False)
    ensure_demo_insights()
    for definition in WORKSPACE_DEFINITIONS:
        ensure_workspace(definition)
    reorder_workspaces()
    tidy_standard_workspaces()
    frappe.clear_cache()


def configure_dreamwear_demo(password: str = DEMO_PASSWORD):
    apply_demo_standard()
    for email, config in DREAMWEAR_USER_CONFIG.items():
        ensure_demo_user(email, config, password)
        reset_managed_permissions(email)
        for allow, value in config.get("permissions", {}).items():
            ensure_user_permission(email, allow, value)
    frappe.clear_cache()


def ensure_workspace(definition):
    chart_names = get_existing_reference_names("Dashboard Chart", definition.get("charts", []))
    number_card_names = get_existing_reference_names("Number Card", definition.get("number_cards", []))
    shortcuts = filter_workspace_shortcuts(definition["shortcuts"])
    cards = filter_workspace_cards(definition["cards"])
    values = {
        "doctype": "Workspace",
        "label": definition["name"],
        "title": definition["name"],
        "module": definition["module"],
        "icon": definition["icon"],
        "indicator_color": definition["indicator_color"],
        "public": 1,
        "is_hidden": 0,
        "content": build_workspace_content(
            definition["header"],
            definition["subtitle"],
            chart_names,
            number_card_names,
            [shortcut["label"] for shortcut in shortcuts],
            [card["label"] for card in cards],
        ),
        "shortcuts": shortcuts,
        "links": build_workspace_links(cards),
        "charts": [{"chart_name": chart_name, "label": chart_name} for chart_name in chart_names],
        "number_cards": [
            {"number_card_name": number_card_name, "label": number_card_name}
            for number_card_name in number_card_names
        ],
        "quick_lists": [],
        "custom_blocks": [],
        "roles": [{"role": role} for role in definition["roles"]],
        "type": "Workspace",
        "parent_page": definition.get("parent_page") if definition.get("parent_page") and frappe.db.exists("Workspace", definition["parent_page"]) else None,

    }

    if frappe.db.exists("Workspace", definition["name"]):
        doc = frappe.get_doc("Workspace", definition["name"])
        for key, value in values.items():
            if key == "doctype":
                continue
            if key in {"shortcuts", "links", "charts", "number_cards", "quick_lists", "custom_blocks", "roles"}:
                doc.set(key, value)
            else:
                setattr(doc, key, value)
        doc.flags.ignore_version = True
        doc.save(ignore_permissions=True)
        return

    doc = frappe.get_doc(values)
    doc.flags.ignore_version = True
    doc.insert(ignore_permissions=True)


def filter_workspace_shortcuts(shortcuts):
    return [shortcut for shortcut in shortcuts if workspace_target_exists(shortcut.get("type"), shortcut.get("link_to"))]


def filter_workspace_cards(cards):
    filtered_cards = []
    for card in cards:
        links = [link for link in card.get("links", []) if workspace_target_exists(link.get("link_type"), link.get("link_to"))]
        if links:
            copied = dict(card)
            copied["links"] = links
            filtered_cards.append(copied)
    return filtered_cards


def workspace_target_exists(link_type, link_to):
    if not link_type or not link_to:
        return True
    if link_type == "DocType":
        return frappe.db.exists("DocType", link_to)
    if link_type == "Report":
        return frappe.db.exists("Report", link_to)
    if link_type == "Page":
        return frappe.db.exists("Page", link_to)
    if link_type == "Workspace":
        return frappe.db.exists("Workspace", link_to)
    return True


def ensure_demo_insights():
    for definition in CUSTOM_DASHBOARD_CHARTS:
        ensure_dashboard_chart(definition)
    for definition in CUSTOM_NUMBER_CARDS:
        ensure_number_card(definition)


def ensure_dashboard_chart(definition):
    if not frappe.db.exists("Dashboard Chart", definition["source_name"]):
        frappe.logger("demo_standard").warning(
            "Skipping demo dashboard chart %s because source chart %s is missing",
            definition["name"],
            definition["source_name"],
        )
        return
    source = frappe.get_doc("Dashboard Chart", definition["source_name"])
    values = {
        "doctype": "Dashboard Chart",
        "name": definition["name"],
        "chart_name": definition["title"],
        "module": "Demo Standard",
        "chart_type": source.chart_type,
        "report_name": source.report_name,
        "use_report_chart": source.use_report_chart,
        "x_field": source.x_field,
        "source": source.source,
        "document_type": source.document_type,
        "parent_document_type": source.parent_document_type,
        "based_on": source.based_on,
        "value_based_on": source.value_based_on,
        "group_by_type": source.group_by_type,
        "group_by_based_on": source.group_by_based_on,
        "aggregate_function_based_on": source.aggregate_function_based_on,
        "number_of_groups": source.number_of_groups,
        "is_public": 1,
        "heatmap_year": source.heatmap_year,
        "timespan": source.timespan,
        "from_date": source.from_date,
        "to_date": source.to_date,
        "time_interval": source.time_interval,
        "timeseries": source.timeseries,
        "type": source.type,
        "show_values_over_chart": source.show_values_over_chart,
        "currency": source.currency,
        "filters_json": source.filters_json,
        "dynamic_filters_json": source.dynamic_filters_json,
        "custom_options": source.custom_options,
        "color": definition.get("color"),
        "roles": [{"role": role} for role in definition.get("roles", [])],
        "y_axis": [
            {"y_field": axis.y_field, "color": axis.color}
            for axis in (source.y_axis or [])
        ],
    }

    if frappe.db.exists("Dashboard Chart", definition["name"]):
        doc = frappe.get_doc("Dashboard Chart", definition["name"])
        for key, value in values.items():
            if key == "doctype":
                continue
            if key in {"roles", "y_axis"}:
                doc.set(key, value)
            else:
                setattr(doc, key, value)
        doc.flags.ignore_version = True
        doc.save(ignore_permissions=True)
        return

    doc = frappe.get_doc(values)
    doc.flags.ignore_version = True
    doc.insert(ignore_permissions=True)


def ensure_number_card(definition):
    if not frappe.db.exists("Number Card", definition["source_name"]):
        frappe.logger("demo_standard").warning(
            "Skipping demo number card %s because source card %s is missing",
            definition["name"],
            definition["source_name"],
        )
        return
    source = frappe.get_doc("Number Card", definition["source_name"])
    values = {
        "doctype": "Number Card",
        "name": definition["name"],
        "label": definition["label"],
        "module": "Demo Standard",
        "type": source.type,
        "report_name": source.report_name,
        "method": source.method,
        "function": source.function,
        "aggregate_function_based_on": source.aggregate_function_based_on,
        "document_type": source.document_type,
        "parent_document_type": source.parent_document_type,
        "report_field": source.report_field,
        "report_function": source.report_function,
        "is_public": 1,
        "currency": source.currency,
        "show_full_number": source.show_full_number,
        "filters_config": source.filters_config,
        "show_percentage_stats": source.show_percentage_stats,
        "stats_time_interval": source.stats_time_interval,
        "filters_json": source.filters_json,
        "dynamic_filters_json": source.dynamic_filters_json,
        "color": definition.get("color"),
        "background_color": definition.get("background_color"),
    }

    if frappe.db.exists("Number Card", definition["name"]):
        doc = frappe.get_doc("Number Card", definition["name"])
        for key, value in values.items():
            if key == "doctype":
                continue
            setattr(doc, key, value)
        doc.flags.ignore_version = True
        doc.save(ignore_permissions=True)
        return

    doc = frappe.get_doc(values)
    doc.flags.ignore_version = True
    doc.insert(ignore_permissions=True)


def reorder_workspaces():
    for name, sequence in WORKSPACE_SEQUENCE.items():
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "sequence_id", sequence, update_modified=False)


def tidy_standard_workspaces():
    for name in HIDDEN_STANDARD_WORKSPACES:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "is_hidden", 1, update_modified=False)

    for name in VISIBLE_STANDARD_WORKSPACES:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "is_hidden", 0, update_modified=False)

    for name in WORKSPACE_SEQUENCE:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "is_hidden", 0, update_modified=False)


def ensure_demo_user(email, config, password):
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.new_doc("User")
        user.email = email
        user.username = config.get("username") or email.split("@", 1)[0]
        user.send_welcome_email = 0
        user.user_type = "System User"

    user.enabled = 1
    user.email = email
    user.first_name = config["first_name"]
    user.language = LANGUAGE
    user.time_zone = TIME_ZONE
    user.desk_theme = "Light"
    user.default_workspace = config["default_workspace"]
    user.search_bar = 1
    user.notifications = 1
    user.list_sidebar = 1
    user.bulk_actions = 1
    user.view_switcher = 1
    user.form_sidebar = 1
    user.timeline = 1
    user.dashboard = 1

    if config.get("gender"):
        user.gender = config["gender"]
    if config.get("birth_date"):
        user.birth_date = config["birth_date"]
    if config.get("username"):
        user.username = config["username"]

    user.set("roles", [{"role": role} for role in config["roles"]])

    if user.is_new():
        user.insert(ignore_permissions=True)
    else:
        user.flags.ignore_version = True
        user.save(ignore_permissions=True)

    update_password(email, password, logout_all_sessions=False)
    set_user_defaults(email, config)


def set_user_defaults(user, config):
    defaults = {
        "lang": LANGUAGE,
        "language": LANGUAGE,
        "time_zone": TIME_ZONE,
        "company": DREAMWEAR_COMPANY,
        "currency": "YER",
        "desktop:home_page": "workspace",
        "is_pos": 1 if config.get("defaults", {}).get("is_pos") else 0,
    }

    defaults.update(config.get("defaults", {}))

    for key, value in defaults.items():
        frappe.defaults.set_user_default(key, value, user=user)

    if config.get("default_workspace"):
        frappe.db.set_value("User", user, "default_workspace", config["default_workspace"], update_modified=False)


def reset_managed_permissions(user):
    managed_allow = ["Company", "Employee", "Branch", "Warehouse", "Cost Center", "POS Profile"]
    names = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": ["in", managed_allow]},
        pluck="name",
    )
    for name in names:
        frappe.delete_doc("User Permission", name, ignore_permissions=True, force=1)


def ensure_user_permission(user, allow, for_value):
    if not for_value:
        return

    if frappe.db.exists("User Permission", {"user": user, "allow": allow, "for_value": for_value}):
        return

    frappe.get_doc(
        {
            "doctype": "User Permission",
            "user": user,
            "allow": allow,
            "for_value": for_value,
            "hide_descendants": 0,
            "apply_to_all_doctypes": 1,
        }
    ).insert(ignore_permissions=True)


def get_existing_reference_names(doctype, names):
    if not names:
        return []

    existing_names = frappe.get_all(doctype, filters={"name": ["in", names]}, pluck="name")
    existing = set(existing_names)
    return [name for name in names if name in existing]


def build_workspace_content(header, subtitle, chart_names, number_card_names, shortcut_names, card_names):
    content = [
        {
            "id": slug_id(f"{header}-header"),
            "type": "header",
            "data": {
                "text": f'<span class="h4"><b>{header}</b></span><br><span class="small text-muted">{subtitle}</span>',
                "col": 12,
            },
        }
    ]

    chart_col = 6 if len(chart_names) > 1 else 12
    for index, chart_name in enumerate(chart_names, start=1):
        content.append(
            {
                "id": slug_id(f"{header}-chart-{index}"),
                "type": "chart",
                "data": {"chart_name": chart_name, "col": chart_col},
            }
        )

    card_col = 3 if len(number_card_names) >= 4 else 4 if len(number_card_names) == 3 else 6
    for index, number_card_name in enumerate(number_card_names, start=1):
        content.append(
            {
                "id": slug_id(f"{header}-metric-{index}"),
                "type": "number_card",
                "data": {"number_card_name": number_card_name, "col": card_col},
            }
        )

    if chart_names or number_card_names:
        content.append({"id": slug_id(f"{header}-insight-spacer"), "type": "spacer", "data": {"col": 12}})

    shortcut_col = 2 if len(shortcut_names) >= 5 else 3
    for index, shortcut_name in enumerate(shortcut_names, start=1):
        content.append(
            {
                "id": slug_id(f"{header}-shortcut-{index}"),
                "type": "shortcut",
                "data": {"shortcut_name": shortcut_name, "col": shortcut_col},
            }
        )

    content.append({"id": slug_id(f"{header}-spacer"), "type": "spacer", "data": {"col": 12}})

    for index, card_name in enumerate(card_names, start=1):
        content.append(
            {
                "id": slug_id(f"{header}-card-{index}"),
                "type": "card",
                "data": {"card_name": card_name, "col": 4},
            }
        )

    return json.dumps(content, ensure_ascii=False)


def build_workspace_links(cards):
    links = []
    for card in cards:
        links.append({"type": "Card Break", "label": card["label"]})
        links.extend(card["links"])
    return links
