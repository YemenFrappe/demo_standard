from __future__ import annotations

import html
import json
import os
import re
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any

import frappe
import requests
from frappe.utils import add_days, add_months, cint, flt, get_datetime, getdate, now, nowdate, today

try:
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    from erpnext.controllers.sales_and_purchase_return import make_return_doc
except Exception:  # pragma: no cover - imports are available inside ERPNext runtime.
    get_payment_entry = None
    make_return_doc = None

from demo_standard.setup import (
    build_workspace_content,
    build_workspace_links,
    doc_link,
    doc_shortcut,
    report_link,
)


COMPANY = "Swiss Corner Watches"
COMPANY_AR = "الركن السويسري للساعات"
ABBR = "SCW"
MODULE = "Demo Standard"
PREFIX = "Swiss Corner"
MARKER = "DEMO-SC"
WORKSPACE = "الركن-السويسري"
WORKSPACE_LABEL = "الركن السويسري"
GUIDE_WORKSPACE = "Demo"
LEGACY_WORKSPACES = [
    "الركن السويسري",
    "Swiss Corner",
    "Swiss Corner Demo",
    "Demo Center",
    "Executive Dashboard",
    "Branch Operations",
    "Sales Counter",
    "Inventory Hub",
    "Finance Desk",
    "Invoicing",
    "People & Payroll",
    "POSNext",
    "Home",
    "People",
    "Tenure",
    "Accounting",
    "Payables",
    "Receivables",
    "Financial Reports",
    "WhatsApp Connector",
    "HR",
    "Recruitment",
    "Employee Lifecycle",
    "Performance",
    "Shift & Attendance",
    "Expense Claims",
    "Leaves",
    "Manufacturing",
    "Buying",
    "Stock",
    "Assets",
    "Quality",
    "Projects",
    "Support",
    "Tools",
    "CRM",
    "Selling",
    "Financial Management.",
    "Assets.",
    "Selling.",
    "Buying.",
    "Reports.",
    "Financial Reports.",
    "General Reports.",
    "Stock.",
    "HR Management",
    "HR File",
    "Recruitment.",
    "Employee Lifecycle.",
    "Shift & Attendance.",
    "Leaves.",
    "Performance.",
    "HR Financial",
    "Expense Claims.",
    "Loan Management.",
    "Payroll.",
    "Salary Payout.",
    "Project Management.",
    "CRM Management.",
    "Loans Management",
    "Payroll",
    "Salary Payout",
    "Tax & Benefits",
    "Users",
    "ERPNext Settings",
]
PRINT_FORMAT = "Swiss Corner Tax Invoice"
PRINT_STYLE = "Swiss Corner Premium Print Style"
LETTER_HEAD = "Swiss Corner Letter Head"
SAUDI_RIYAL_SYMBOL = "§"
TAX_TEMPLATE = "Swiss Corner VAT 15% - SCW"
ITEM_TAX_TEMPLATE = "Swiss Corner Item VAT 15% - SCW"
BUYING_PRICE_LIST = "شراء القياسية"
SELLING_PRICE_LIST = "البيع القياسية"
DEFAULT_UOM = "Nos"

SAFE_DEMO_NUMBERS = {
    "+966500000001",
    "+966500000002",
    "+966500000003",
    "+966500000004",
    "+966500000005",
    "+966500000006",
    "+966500000007",
    "+966500000008",
    "966500000001",
    "966500000002",
    "966500000003",
    "966500000004",
    "966500000005",
    "966500000006",
    "966500000007",
    "966500000008",
}


BRANCHES = [
    {
        "key": "riyadh",
        "branch": "Swiss Corner - الرياض",
        "label": "الركن السويسري - الرياض",
        "warehouse": "Swiss Corner - معرض الرياض",
        "cost_center": "Swiss Corner - الرياض",
        "pos_profile": "POS - الرياض",
        "cashier": "cashier_riyadh@swisscorner.demo",
        "username": "cashier_riyadh",
    },
    {
        "key": "jeddah",
        "branch": "Swiss Corner - جدة",
        "label": "الركن السويسري - جدة",
        "warehouse": "Swiss Corner - معرض جدة",
        "cost_center": "Swiss Corner - جدة",
        "pos_profile": "POS - جدة",
        "cashier": "cashier_jeddah@swisscorner.demo",
        "username": "cashier_jeddah",
    },
    {
        "key": "khobar",
        "branch": "Swiss Corner - الخبر",
        "label": "الركن السويسري - الخبر",
        "warehouse": "Swiss Corner - معرض الخبر",
        "cost_center": "Swiss Corner - الخبر",
        "pos_profile": "POS - الخبر",
        "cashier": "cashier_khobar@swisscorner.demo",
        "username": "cashier_khobar",
    },
    {
        "key": "madinah",
        "branch": "Swiss Corner - المدينة",
        "label": "الركن السويسري - المدينة",
        "warehouse": "Swiss Corner - معرض المدينة",
        "cost_center": "Swiss Corner - المدينة",
        "pos_profile": "POS - المدينة",
        "cashier": "cashier_madinah@swisscorner.demo",
        "username": "cashier_madinah",
    },
    {
        "key": "online",
        "branch": "Swiss Corner - المتجر الإلكتروني",
        "label": "الركن السويسري - المتجر الإلكتروني",
        "warehouse": "Swiss Corner - مخزن المتجر الإلكتروني",
        "cost_center": "Swiss Corner - المتجر الإلكتروني",
        "pos_profile": "POS - المتجر الإلكتروني",
        "cashier": "cashier_online@swisscorner.demo",
        "username": "cashier_online",
    },
    {
        "key": "service",
        "branch": "Swiss Corner - مركز الصيانة والضمان",
        "label": "الركن السويسري - مركز الصيانة والضمان",
        "warehouse": "Swiss Corner - مخزن الصيانة والضمان",
        "cost_center": "Swiss Corner - مركز الصيانة والضمان",
        "pos_profile": None,
        "cashier": None,
        "username": None,
    },
]

EXTRA_WAREHOUSES = [
    ("main", "Swiss Corner - المستودع الرئيسي - الرياض", None),
    ("returns", "Swiss Corner - مخزن البضائع المرتجعة", None),
    ("damaged", "Swiss Corner - مخزن التالف", None),
    ("transit", "Swiss Corner - مخزن التحويلات بين الفروع", "Transit"),
]

ITEM_GROUPS = [
    "ساعات رجالية",
    "ساعات نسائية",
    "ساعات كلاسيكية",
    "ساعات رياضية",
    "ساعات أوتوماتيك",
    "ساعات كوارتز",
    "ساعات فاخرة",
    "إكسسوارات ساعات",
    "سيور ساعات",
    "بطاريات ساعات",
    "خدمات صيانة",
    "ضمان وتمديد ضمان",
]

BRANDS = [
    "Swiss Corner",
    "Alpine Time",
    "Geneva Line",
    "Royale Watch Co",
    "Zurich Classic",
    "Crown Heritage",
]

IMAGE_SOURCES = [
    "https://cdn.files.salla.network/homepage/1857164815/338c09b2-e28b-400c-b62f-bb30faa367d2.webp",
    "https://cdn.files.salla.network/homepage/1857164815/97590d0c-6150-4c1b-a0f9-9ea4b2367d4e.webp",
    "https://cdn.files.salla.network/homepage/1857164815/b0aa6d49-b0b2-48b8-982d-e1f136a59919.webp",
    "https://cdn.files.salla.network/homepage/1857164815/99d1ae6e-be81-45e0-82ed-5897f6032958.webp",
    "https://cdn.files.salla.network/homepage/1857164815/30bb0da9-2e3f-40a0-967d-28bc9731494c.webp",
    "https://cdn.files.salla.network/homepage/1857164815/2ba0fbf0-a59f-4efe-aeaf-0a5cc9887359.webp",
    "https://cdn.files.salla.network/homepage/1857164815/eba7bb3b-eefb-48a9-90fb-847b86d4902b.webp",
    "https://cdn.files.salla.network/homepage/1857164815/3958ac2a-73c7-4f80-8b2f-52a305bd46a6.webp",
    "https://cdn.files.salla.network/homepage/1857164815/fb370e0c-fe46-4696-97a6-c6449ee6bce5.webp",
]

SWISS_CORNER_ASSETS = {
    "logo": "https://cdn.files.salla.network/homepage/1857164815/ef101e95-e4ff-4243-b05c-c18245666647.webp",
    "icon": "https://cdn.files.salla.network/theme/1857164815/f0e71af8-08c6-435d-b43e-bc7d65bba17f.webp",
    "social": "https://cdn.salla.sa/AzzZpA/1I6fiBcICAxGT4udeEZfKfIT3iCRixgCWxhrJE5x.png",
}

CLIENT_SAMPLE_BRANCH = {
    "key": "khamis",
    "branch": "Swiss Corner - خميس مشيط البلد",
    "label": "الركن السويسري - خميس مشيط البلد",
    "warehouse": "Swiss Corner - معرض خميس مشيط البلد",
    "cost_center": "Swiss Corner - خميس مشيط البلد",
    "pos_profile": "POS - خميس مشيط البلد",
    "cashier": "cashier_khamis@swisscorner.demo",
    "username": "cashier_khamis",
}

CLIENT_SAMPLE_ITEMS = [
    {"alt": "1170183M-8", "item_no": "001111170183-8", "brand": "Diamond Hill", "name": "دايموند هيل جلد فضي جلد اخضر ميناء فضي", "qty": 1, "selling": 586.00},
    {"alt": "102230M-5", "item_no": "0011112230-5", "brand": "Diamond Hill", "name": "دايموند هيل جلد فضي الميناء اسود", "qty": 2, "selling": 1113.00},
    {"alt": "12351M-1", "item_no": "0011112351-1", "brand": "Diamond Hill", "name": "دايموند هيل جلد فضي جلد ازرق الميناء فضي", "qty": 2, "selling": 751.00},
    {"alt": "1001MR-1", "item_no": "001121001-1", "brand": "Diamond Hill", "name": "دايموند هيل صقيل فضي مع برونزي الميناء فضي", "qty": 1, "selling": 823.00},
    {"alt": "1004M-08", "item_no": "001121004-08", "brand": "Diamond Hill", "name": "دايموند هيل صقيل فضي الميناء اخضر ارقام", "qty": 2, "selling": 1129.00},
    {"alt": "111749M-9", "item_no": "00112111749-9", "brand": "Diamond Hill", "name": "دايموند هيل صقيل فضي الميناء ازرق", "qty": 2, "selling": 1335.00},
    {"alt": "1122504M-8", "item_no": "001121122504-8", "brand": "Diamond Hill", "name": "دايموند هيل صقيل فضي الميناء اخضر", "qty": 3, "selling": 1116.00},
    {"alt": "125377M-9", "item_no": "00112125377-9", "brand": "Diamond Hill", "name": "دايموند هيل صقيل فضي الميناء ازرق", "qty": 1, "selling": 918.27},
    {"alt": "3725255M-9", "item_no": "03712125255-9", "brand": "Domaskinos", "name": "دوماسكينوس صقيل فضي الميناء ازرق", "qty": 1, "selling": 1164.00},
    {"alt": "3725372M-8", "item_no": "03712125372-8", "brand": "Domaskinos", "name": "دوماسكينوس صقيل فضي الميناء اخضر", "qty": 1, "selling": 1131.00},
    {"alt": "3729611M-9", "item_no": "03712129611-9", "brand": "Domaskinos", "name": "دوماسكينوس صقيل فضي الميناء ازرق", "qty": 1, "selling": 1257.00},
    {"alt": "373055MR-1", "item_no": "0371213055-1", "brand": "Domaskinos", "name": "دوماسكينوس صقيل فضي الميناء اسود اطار برونزي", "qty": 1, "selling": 1602.00},
    {"alt": "375010M-5", "item_no": "0371215010-5", "brand": "Domaskinos", "name": "دوماسكينوس صقيل فضي الميناء اسود", "qty": 2, "selling": 1697.00},
    {"alt": "373210M-9", "item_no": "0371313210-9", "brand": "Domaskinos", "name": "دوماسكينوس ربيل فضي الميناء ازرق", "qty": 2, "selling": 940.00},
    {"alt": "17929612M-9", "item_no": "17911129612-9", "brand": "GF", "name": "جي اف جلد فضي الميناء فضي جلد ازرق", "qty": 1, "selling": 1328.00},
    {"alt": "179170132M-8", "item_no": "17912110132-8", "brand": "GF", "name": "جي اف صقيل فضي الميناء اخضر", "qty": 1, "selling": 1697.00},
    {"alt": "179170175M-9", "item_no": "179121170175-9", "brand": "GF", "name": "جي اف صقيل فضي الميناء ازرق", "qty": 1, "selling": 1582.61},
    {"alt": "17925263MR-4", "item_no": "17912125263-4", "brand": "GF", "name": "جي اف صقيل فضي اطار برونزي الميناء رصاصي", "qty": 2, "selling": 1371.00},
    {"alt": "17925263M-5", "item_no": "17912125263-5", "brand": "GF", "name": "جي اف صقيل فضي الميناء اسود", "qty": 3, "selling": 1371.00},
    {"alt": "17925263M-9", "item_no": "17912125263-9", "brand": "GF", "name": "جي اف صقيل فضي الميناء ازرق", "qty": 2, "selling": 1438.00},
]

WATCH_ITEMS = [
    {
        "code": "DEMO-SC-WATCH-001",
        "name": "Swiss Corner Classic 40mm Black Leather",
        "brand": "Swiss Corner",
        "group": "ساعات كلاسيكية",
        "model": "SC-C40-BL",
        "collection": "Classic",
        "gender": "Men",
        "movement": "Quartz",
        "case_size": 40,
        "case_material": "Stainless Steel",
        "strap": "Black Leather",
        "glass": "Mineral",
        "water": "5 ATM",
        "warranty": 24,
        "purchase": 420,
        "selling": 899,
    },
    {
        "code": "DEMO-SC-WATCH-002",
        "name": "Swiss Corner Classic 36mm Rose Gold",
        "brand": "Swiss Corner",
        "group": "ساعات نسائية",
        "model": "SC-C36-RG",
        "collection": "Classic",
        "gender": "Women",
        "movement": "Quartz",
        "case_size": 36,
        "case_material": "Rose Gold Plated",
        "strap": "Rose Gold Mesh",
        "glass": "Mineral",
        "water": "3 ATM",
        "warranty": 24,
        "purchase": 390,
        "selling": 799,
    },
    {
        "code": "DEMO-SC-WATCH-003",
        "name": "Alpine Chronograph Steel Blue",
        "brand": "Alpine Time",
        "group": "ساعات رياضية",
        "model": "AT-CH44-BL",
        "collection": "Sport Chrono",
        "gender": "Men",
        "movement": "Chronograph",
        "case_size": 44,
        "case_material": "Stainless Steel",
        "strap": "Steel Bracelet",
        "glass": "Sapphire Coated",
        "water": "10 ATM",
        "warranty": 24,
        "purchase": 720,
        "selling": 1499,
    },
    {
        "code": "DEMO-SC-WATCH-004",
        "name": "Geneva Quartz Silver Mesh",
        "brand": "Geneva Line",
        "group": "ساعات كوارتز",
        "model": "GL-Q38-SM",
        "collection": "Urban Mesh",
        "gender": "Unisex",
        "movement": "Quartz",
        "case_size": 38,
        "case_material": "Brushed Steel",
        "strap": "Silver Mesh",
        "glass": "Mineral",
        "water": "3 ATM",
        "warranty": 18,
        "purchase": 260,
        "selling": 599,
    },
    {
        "code": "DEMO-SC-WATCH-005",
        "name": "Zurich Automatic Sapphire 42mm",
        "brand": "Zurich Classic",
        "group": "ساعات أوتوماتيك",
        "model": "ZC-A42-SAP",
        "collection": "Sapphire",
        "gender": "Men",
        "movement": "Automatic",
        "case_size": 42,
        "case_material": "316L Steel",
        "strap": "Steel Bracelet",
        "glass": "Sapphire",
        "water": "10 ATM",
        "warranty": 36,
        "purchase": 1150,
        "selling": 2499,
    },
    {
        "code": "DEMO-SC-WATCH-006",
        "name": "Royale Heritage Gold Edition",
        "brand": "Royale Watch Co",
        "group": "ساعات فاخرة",
        "model": "RW-HG40",
        "collection": "Heritage",
        "gender": "Men",
        "movement": "Automatic",
        "case_size": 40,
        "case_material": "Gold PVD",
        "strap": "Brown Leather",
        "glass": "Sapphire",
        "water": "5 ATM",
        "warranty": 36,
        "purchase": 1800,
        "selling": 3999,
    },
    {
        "code": "DEMO-SC-WATCH-007",
        "name": "Alpine Sport Rubber Strap 44mm",
        "brand": "Alpine Time",
        "group": "ساعات رياضية",
        "model": "AT-SP44-RB",
        "collection": "Outdoor",
        "gender": "Men",
        "movement": "Solar",
        "case_size": 44,
        "case_material": "Carbon Composite",
        "strap": "Black Rubber",
        "glass": "Hardened Mineral",
        "water": "20 ATM",
        "warranty": 24,
        "purchase": 540,
        "selling": 1199,
    },
    {
        "code": "DEMO-SC-WATCH-008",
        "name": "Swiss Corner Ladies Pearl Dial",
        "brand": "Swiss Corner",
        "group": "ساعات نسائية",
        "model": "SC-LP32",
        "collection": "Pearl",
        "gender": "Women",
        "movement": "Quartz",
        "case_size": 32,
        "case_material": "Polished Steel",
        "strap": "Pearl Steel",
        "glass": "Mineral",
        "water": "3 ATM",
        "warranty": 24,
        "purchase": 330,
        "selling": 749,
    },
    {
        "code": "DEMO-SC-WATCH-009",
        "name": "Zurich Moonphase Automatic",
        "brand": "Zurich Classic",
        "group": "ساعات أوتوماتيك",
        "model": "ZC-MP40",
        "collection": "Moonphase",
        "gender": "Unisex",
        "movement": "Automatic",
        "case_size": 40,
        "case_material": "316L Steel",
        "strap": "Navy Leather",
        "glass": "Sapphire",
        "water": "5 ATM",
        "warranty": 36,
        "purchase": 1250,
        "selling": 2799,
    },
    {
        "code": "DEMO-SC-WATCH-010",
        "name": "Crown Heritage Skeleton",
        "brand": "Crown Heritage",
        "group": "ساعات فاخرة",
        "model": "CH-SK42",
        "collection": "Skeleton",
        "gender": "Men",
        "movement": "Automatic",
        "case_size": 42,
        "case_material": "Stainless Steel",
        "strap": "Black Leather",
        "glass": "Sapphire",
        "water": "5 ATM",
        "warranty": 36,
        "purchase": 1500,
        "selling": 3299,
    },
]

SERVICE_ITEMS = [
    ("DEMO-SC-SERVICE-001", "Battery Replacement", "بطاريات ساعات", 15, 49, 0),
    ("DEMO-SC-SERVICE-002", "Strap Replacement", "سيور ساعات", 45, 149, 1),
    ("DEMO-SC-SERVICE-003", "Watch Cleaning Service", "خدمات صيانة", 0, 99, 0),
    ("DEMO-SC-SERVICE-004", "Warranty Inspection Service", "ضمان وتمديد ضمان", 0, 0, 0),
    ("DEMO-SC-ACCESSORY-001", "Swiss Corner Leather Strap 20mm", "سيور ساعات", 35, 129, 1),
    ("DEMO-SC-ACCESSORY-002", "Swiss Corner Premium Battery Pack", "بطاريات ساعات", 8, 39, 1),
]

SUPPLIERS = [
    "Swiss Corner Imports",
    "Gulf Watch Supplies",
    "Alpine Time Distribution",
    "Geneva Accessories Trading",
]

CUSTOMERS = [
    ("Swiss Corner - أحمد العتيبي", "أحمد العتيبي", "Retail Customers", "+966500000001"),
    ("Swiss Corner - خالد الغامدي", "خالد الغامدي", "VIP Customers", "+966500000002"),
    ("Swiss Corner - سارة القحطاني", "سارة القحطاني", "Retail Customers", "+966500000003"),
    ("Swiss Corner - نورة الحربي", "نورة الحربي", "VIP Customers", "+966500000004"),
    ("Swiss Corner - محمد الدوسري", "محمد الدوسري", "Warranty Customers", "+966500000005"),
    ("Swiss Corner - ريم الزهراني", "ريم الزهراني", "Online Customers", "+966500000006"),
    ("Swiss Corner - عميل المتجر الإلكتروني", "عميل المتجر الإلكتروني", "Online Customers", "+966500000007"),
    ("Swiss Corner - عميل نقدي POS", "عميل نقدي POS", "Walk-in Customers", "+966500000008"),
]

PAYMENT_MODES = [
    ("Cash", "Cash"),
    ("Mada", "Bank"),
    ("Visa / MasterCard", "Bank"),
    ("STC Pay", "Bank"),
    ("Bank Transfer", "Bank"),
]

REPORT_NAMES = [
    "Swiss Corner - Store Sales Report",
    "Swiss Corner - POS Sales Summary",
    "Swiss Corner - Inventory Movement by Store",
    "Swiss Corner - Serial Number Register",
    "Swiss Corner - Warranty Report",
    "Swiss Corner - Gross Profit by Store and Brand",
    "Swiss Corner - Fast and Slow Moving Watches",
    "Swiss Corner - Branch Transfer Summary",
    "Swiss Corner - WhatsApp Invoice Delivery Log",
]


def setup_swiss_corner_demo() -> dict[str, Any]:
    """Create or update the Swiss Corner watch retail demo."""
    result: dict[str, Any] = {"created": [], "updated": [], "skipped": [], "warnings": [], "errors": []}
    frappe.flags.in_swiss_corner_setup = True

    def step(label: str, fn):
        try:
            value = fn()
            result["updated"].append(label)
            frappe.db.commit()
            return value
        except Exception:
            frappe.db.rollback()
            result["errors"].append({"step": label, "traceback": frappe.get_traceback()})
            frappe.log_error(frappe.get_traceback(), f"Swiss Corner Demo Setup Failed: {label}")
            return None

    step("custom fields", ensure_custom_fields)
    accounts = step("company and accounts", ensure_company_and_accounts) or {}
    step("company display branding", ensure_company_display_branding)
    step("Saudi Riyal symbol", ensure_saudi_riyal_symbol)
    step("currency display metadata", ensure_currency_display_metadata)
    step("roles and users", lambda: ensure_roles_and_users(accounts))
    masters = step("branches warehouses POS suppliers customers items", lambda: ensure_master_data(accounts))
    step("client sample items from PDF", lambda: ensure_client_sample_from_pdf(accounts))
    step("reports", lambda: ensure_reports(accounts))
    step("official Swiss Corner brand assets", ensure_swiss_corner_brand_assets)
    step("site branding", ensure_swiss_corner_site_branding)
    step("print style", ensure_print_style)
    step("letter head", ensure_letter_head)
    step("print format", ensure_print_format)
    step("default print settings", ensure_default_print_settings)
    step("workspace dashboard", lambda: ensure_workspace_and_dashboard(accounts))
    step("whatsapp dry-run configuration", ensure_whatsapp_demo_settings)
    step("demo transactions", lambda: ensure_demo_transactions(accounts, masters or {}))
    step("client scripts", ensure_client_scripts)

    frappe.clear_cache()
    frappe.flags.in_swiss_corner_setup = False
    return result


def verify_swiss_corner_demo() -> dict[str, Any]:
    """Run lightweight smoke checks for the Swiss Corner demo."""
    operating_company = frappe.db.get_value("POS Profile", BRANCHES[0]["pos_profile"], "company") or (
        frappe.db.get_value("Company", {"country": "Saudi Arabia", "default_currency": "SAR"}, "name")
        or frappe.db.get_value("Company", {"country": "Saudi Arabia"}, "name")
    )
    from_date = add_days(today(), -180)
    to_date = today()
    result: dict[str, Any] = {"company": operating_company, "counts": {}, "reports": {}, "checks": {}, "errors": []}
    pos_profiles = [branch["pos_profile"] for branch in BRANCHES if branch.get("pos_profile")]
    pos_profiles.append(CLIENT_SAMPLE_BRANCH["pos_profile"])

    result["counts"] = {
        "branches": frappe.db.count("Branch", {"name": ["like", f"{PREFIX}%"]}),
        "warehouses": frappe.db.count("Warehouse", {"warehouse_name": ["like", f"{PREFIX}%"]}),
        "cost_centers": frappe.db.count("Cost Center", {"cost_center_name": ["like", f"{PREFIX}%"]}),
        "pos_profiles": frappe.db.count("POS Profile", {"name": ["like", "POS -%"]}),
        "items": frappe.db.count("Item", {"item_code": ["like", f"{MARKER}%"]}),
        "client_sample_items": frappe.db.count("Item", {"item_code": ["like", f"{MARKER}-CLIENT%"]}),
        "customers": frappe.db.count("Customer", {"customer_name": ["like", f"{PREFIX}%"]}),
        "suppliers": frappe.db.count("Supplier", {"supplier_name": ["in", SUPPLIERS]}),
        "serial_numbers": frappe.db.count("Serial No", {"item_code": ["like", f"{MARKER}-WATCH%"]}),
        "client_sample_serial_numbers": frappe.db.count("Serial No", {"item_code": ["like", f"{MARKER}-CLIENT%"]}),
        "stock_entries": frappe.db.count("Stock Entry", {"remarks": ["like", f"%{MARKER}%"], "docstatus": 1}),
        "purchase_receipts": frappe.db.count("Purchase Receipt", {"remarks": ["like", f"%{MARKER}%"], "docstatus": 1}),
        "purchase_invoices": frappe.db.count("Purchase Invoice", {"remarks": ["like", f"%{MARKER}%"], "docstatus": 1}),
        "pos_invoices": frappe.db.count("POS Invoice", {"remarks": ["like", f"%{MARKER}%"], "docstatus": 1}),
        "pos_openings": frappe.db.count("POS Opening Entry", {"pos_profile": ["in", pos_profiles], "docstatus": 1}),
        "pos_closings": frappe.db.count("POS Closing Entry", {"pos_profile": ["in", pos_profiles], "docstatus": 1}),
        "whatsapp_logs": frappe.db.count("WhatsApp Message Log", {"sc_reference_doctype": "Sales Invoice"}),
    }
    result["counts"]["client_sample_stock_qty"] = flt(
        frappe.db.sql(
            """
            select coalesce(sum(actual_qty), 0)
            from `tabBin`
            where item_code like %s
            """,
            (f"{MARKER}-CLIENT%",),
        )[0][0]
    )
    result["counts"]["sales_invoices"] = frappe.db.sql(
        """
        select count(distinct si.name)
        from `tabSales Invoice` si
        inner join `tabSales Invoice Item` sii on sii.parent = si.name
        where si.docstatus = 1
          and (ifnull(si.remarks, '') like %s or sii.item_code like %s)
        """,
        (f"%{MARKER}%", f"{MARKER}%"),
    )[0][0]

    report_filters = {
        "company": operating_company,
        "from_date": from_date,
        "to_date": to_date,
        "date_range": [from_date, to_date],
        "branch": "",
        "warehouse": "",
        "pos_profile": "",
        "customer_group": "",
        "cashier": "",
        "mode_of_payment": "",
        "item_group": "",
        "brand": "",
        "item": "",
        "status": "",
    }
    for report_name in REPORT_NAMES:
        try:
            from frappe.desk.query_report import run as run_report

            data = run_report(report_name, filters=report_filters)
            rows = data.get("result") or data.get("data") or []
            result["reports"][report_name] = {"ok": True, "rows": len(rows)}
        except Exception as exc:
            result["reports"][report_name] = {"ok": False, "error": str(exc)}
            result["errors"].append({"report": report_name, "traceback": frappe.get_traceback()})

    result["workspace"] = {"charts": {}, "number_cards": {}}
    for chart_name in ["Swiss Corner - Sales by Branch", "Swiss Corner - POS Profiles", "Swiss Corner - Invoice Trend"]:
        try:
            from frappe.desk.doctype.dashboard_chart.dashboard_chart import get as get_dashboard_chart

            chart_result = get_dashboard_chart(chart_name=chart_name, refresh=1)
            result["workspace"]["charts"][chart_name] = {
                "ok": True,
                "labels": len(chart_result.get("labels") or []),
                "datasets": len(chart_result.get("datasets") or []),
            }
        except Exception as exc:
            result["workspace"]["charts"][chart_name] = {"ok": False, "error": str(exc)}
            result["errors"].append({"dashboard_chart": chart_name, "traceback": frappe.get_traceback()})

    for card_name in ["Swiss Corner - Invoice Count", "Swiss Corner - Sales Total", "Swiss Corner - Serial Watches", "Swiss Corner - WhatsApp Logs"]:
        try:
            from frappe.desk.doctype.number_card.number_card import get_result as get_number_card_result

            card = frappe.get_doc("Number Card", card_name)
            value = get_number_card_result(card.as_dict(), card.filters_json)
            result["workspace"]["number_cards"][card_name] = {"ok": True, "value": value}
        except Exception as exc:
            result["workspace"]["number_cards"][card_name] = {"ok": False, "error": str(exc)}
            result["errors"].append({"number_card": card_name, "traceback": frappe.get_traceback()})

    try:
        from frappe.desk.desktop import get_desktop_page

        page = frappe.db.get_value(
            "Workspace",
            WORKSPACE,
            [
                "name",
                "title",
                "for_user",
                "parent_page",
                "content",
                "public",
                "module",
                "icon",
                "indicator_color",
                "is_hidden",
            ],
            as_dict=True,
        )
        page_data = get_desktop_page(json.dumps(page))
        result["workspace"]["desktop_page"] = {
            "ok": True,
            "charts": len(page_data.get("charts") or []),
            "number_cards": len(page_data.get("number_cards") or []),
            "shortcuts": len(page_data.get("shortcuts") or []),
            "cards": len(page_data.get("cards") or []),
        }
    except Exception as exc:
        result["workspace"]["desktop_page"] = {"ok": False, "error": str(exc)}
        result["errors"].append({"workspace_page": WORKSPACE, "traceback": frappe.get_traceback()})

    sample_invoice = frappe.db.sql(
        """
        select si.name
        from `tabSales Invoice` si
        inner join `tabSales Invoice Item` sii on sii.parent = si.name
        where si.docstatus = 1 and sii.item_code like %s
        order by si.posting_date desc, si.creation desc
        limit 1
        """,
        (f"{MARKER}%",),
    )
    if sample_invoice:
        invoice_name = sample_invoice[0][0]
        result["checks"]["sample_sales_invoice"] = invoice_name
        html_out = frappe.get_print("Sales Invoice", invoice_name, print_format=PRINT_FORMAT)
        result["checks"]["print_html_length"] = len(html_out or "")
        try:
            from frappe.utils.pdf import get_pdf

            result["checks"]["pdf_bytes"] = len(get_pdf(html_out))
        except Exception:
            result["checks"]["pdf_error"] = frappe.get_traceback()
        before = frappe.db.count("WhatsApp Message Log", {"sc_reference_doctype": "Sales Invoice", "sc_reference_name": invoice_name})
        log_name = process_whatsapp_invoice_notification(invoice_name)
        after = frappe.db.count("WhatsApp Message Log", {"sc_reference_doctype": "Sales Invoice", "sc_reference_name": invoice_name})
        process_whatsapp_invoice_notification(invoice_name)
        second_after = frappe.db.count("WhatsApp Message Log", {"sc_reference_doctype": "Sales Invoice", "sc_reference_name": invoice_name})
        result["checks"]["whatsapp_log"] = log_name
        result["checks"]["whatsapp_log_count_before"] = before
        result["checks"]["whatsapp_log_count_after"] = after
        result["checks"]["whatsapp_idempotent"] = second_after == after

    result["checks"]["negative_stock_bins"] = frappe.db.sql(
        """
        select count(*)
        from `tabBin`
        where item_code like %s and actual_qty < 0
        """,
        (f"{MARKER}%",),
    )[0][0]
    result["checks"]["workspace_exists"] = bool(frappe.db.exists("Workspace", WORKSPACE))
    result["checks"]["dashboard_exists"] = bool(frappe.db.exists("Dashboard", WORKSPACE))
    result["checks"]["print_format_exists"] = bool(frappe.db.exists("Print Format", PRINT_FORMAT))
    return result


def create_swiss_corner_submit_smoke_invoice() -> dict[str, Any]:
    """Create one small submitted Sales Invoice to test hooks outside setup mode."""
    accounts = ensure_company_and_accounts()
    ensure_whatsapp_demo_settings()
    existing = frappe.db.get_value(
        "Sales Invoice",
        {"remarks": ["like", f"%{MARKER} Submit Hook Smoke Test%"], "docstatus": 1},
        "name",
        order_by="creation desc",
    )
    if existing:
        log_name = process_whatsapp_invoice_notification(existing)
        return {"invoice": existing, "created": False, "whatsapp_log": log_name}

    item_code = (
        frappe.db.get_value("Item", {"item_code": ["like", f"{MARKER}-SERVICE%"], "is_stock_item": 0}, "name")
        or "DEMO-SC-SERVICE-004"
    )
    customer = frappe.db.get_value("Customer", {"customer_name": ["like", f"{PREFIX}%"]}, "name") or frappe.db.get_value("Customer", {}, "name")
    branch = BRANCHES[0]
    cost_center = cost_center_doc_name(branch["cost_center"]) or accounts.get("cost_center")
    doc = frappe.new_doc("Sales Invoice")
    doc.company = accounts["company"]
    doc.customer = customer
    doc.posting_date = today()
    doc.posting_time = "16:20:00"
    doc.set_posting_time = 1
    doc.due_date = today()
    doc.is_pos = 1
    doc.update_stock = 0
    doc.currency = "SAR"
    doc.selling_price_list = SELLING_PRICE_LIST
    doc.cost_center = cost_center
    doc.taxes_and_charges = get_sales_tax_template_name()
    doc.apply_discount_on = "Grand Total"
    doc.remarks = f"{MARKER} Submit Hook Smoke Test"
    set_if_field(doc, "sc_branch", branch["branch"])
    set_if_field(doc, "sc_pos_profile", branch["pos_profile"])
    set_if_field(doc, "sc_enable_whatsapp_invoice_notification", 1)
    set_if_field(doc, "custom_zatca_discount_reason", "Discount")
    doc.append(
        "items",
        {
            "item_code": item_code,
            "qty": 1,
            "rate": 99,
            "income_account": accounts.get("income"),
            "expense_account": accounts.get("expense"),
            "cost_center": cost_center,
            "custom_zatca_discount_reason": "Discount",
        },
    )
    doc.append("payments", {"mode_of_payment": "Cash", "amount": 113.85})
    submit_doc(doc)
    frappe.db.commit()
    log_name = process_whatsapp_invoice_notification(doc.name)
    frappe.db.commit()
    return {"invoice": doc.name, "created": True, "whatsapp_log": log_name}


def on_sales_invoice_submit(doc, method=None):
    """Queue WhatsApp invoice delivery for Swiss Corner invoices only."""
    if getattr(frappe.flags, "in_swiss_corner_setup", False):
        return
    if not is_swiss_invoice(doc):
        return
    if not has_field("Sales Invoice", "sc_enable_whatsapp_invoice_notification"):
        return
    if not cint(doc.get("sc_enable_whatsapp_invoice_notification", 1)):
        return
    if doc.get("sc_whatsapp_invoice_log"):
        return
    try:
        process_whatsapp_invoice_notification(doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Swiss Corner WhatsApp Immediate Failed {doc.name}")
    frappe.enqueue(
        "demo_standard.swiss_corner_demo.process_whatsapp_invoice_notification",
        queue="short",
        enqueue_after_commit=True,
        invoice_name=doc.name,
    )


def before_swiss_corner_invoice_submit(doc, method=None):
    """Keep Swiss Corner demo invoices out of live KSA/ZATCA submission hooks."""
    if getattr(frappe.flags, "in_swiss_corner_setup", False):
        return
    if not is_swiss_invoice(doc):
        return
    try:
        from ksa_compliance.standard_doctypes.sales_invoice import ignore_additional_fields_for_invoice

        ignore_additional_fields_for_invoice(doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Swiss Corner KSA Ignore Failed {doc.name}")


def process_whatsapp_invoice_notification(invoice_name: str) -> str | None:
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    if not is_swiss_invoice(invoice):
        return None
    if invoice.get("sc_whatsapp_invoice_log"):
        return invoice.get("sc_whatsapp_invoice_log")
    existing_log = frappe.db.get_value(
        "WhatsApp Message Log",
        {"sc_reference_doctype": "Sales Invoice", "sc_reference_name": invoice.name},
        "name",
        order_by="creation asc",
    )
    if existing_log:
        set_si_whatsapp_fields(invoice.name, frappe.db.get_value("WhatsApp Message Log", existing_log, "status") or "Dry Run", existing_log, 1, None)
        return existing_log

    settings = get_whatsapp_settings()
    if not cint(settings.get("sc_enable_invoice_notification", 1)):
        set_si_whatsapp_fields(invoice.name, "Disabled", None, 1, "WhatsApp invoice notifications disabled")
        return None

    recipient = resolve_customer_mobile(invoice.customer)
    message = build_invoice_whatsapp_message(invoice)
    attachment_url = None
    attachment_status = "Not Generated"
    try:
        attachment_url = create_invoice_attachment(invoice.name)
        attachment_status = "Generated"
    except Exception:
        attachment_status = "Failed"
        frappe.log_error(frappe.get_traceback(), "Swiss Corner WhatsApp Attachment Failed")

    dry_run_only = cint(settings.get("sc_demo_dry_run_only", 1))
    allowed_numbers = set(parse_lines(settings.get("sc_allowed_demo_numbers"))) or SAFE_DEMO_NUMBERS
    normalized = normalize_phone(recipient)
    is_allowed = normalized in allowed_numbers or normalized.replace("+", "") in allowed_numbers
    dry_run = dry_run_only or not is_allowed
    error = None

    if dry_run:
        status = "Dry Run"
        error = "Dry Run only; no WhatsApp message was sent."
        log_name = create_whatsapp_log(
            invoice=invoice,
            recipient=normalized or recipient or "NO-DEMO-MOBILE",
            message=message,
            attachment_url=attachment_url,
            attachment_status=attachment_status,
            status="Failed",
            dry_run=1,
            error=error,
        )
    else:
        try:
            from whatsapp_connector.whatsapp_connector.services.session_service import send_message
            from whatsapp_connector.whatsapp_connector.utils.whatsapp import resolve_session_name

            session_name = resolve_session_name()
            log_name = send_message(
                session_name=session_name,
                recipient=normalized,
                message_type="Document" if attachment_url else "Text",
                message=message,
                attachment_url=attachment_url,
            )
            apply_whatsapp_log_metadata(log_name, invoice, attachment_status, 0, None)
            status = frappe.db.get_value("WhatsApp Message Log", log_name, "status") or "Queued"
        except Exception as exc:
            error = str(exc)
            log_name = create_whatsapp_log(
                invoice=invoice,
                recipient=normalized or recipient or "NO-DEMO-MOBILE",
                message=message,
                attachment_url=attachment_url,
                attachment_status=attachment_status,
                status="Failed",
                dry_run=0,
                error=error,
            )
            status = "Failed"

    set_si_whatsapp_fields(invoice.name, status, log_name, int(dry_run), error)
    frappe.db.commit()
    return log_name


def ensure_custom_fields():
    custom_fields = [
        ("Company", "sc_company_arabic_name", "Arabic Company Name", "Data", "abbr"),
        ("Customer", "sc_whatsapp_number", "رقم الواتساب", "Data", "mobile_no"),
        ("Warehouse", "sc_branch", "Swiss Corner Branch", "Link", "company", "Branch"),
        ("POS Profile", "sc_branch", "Swiss Corner Branch", "Link", "warehouse", "Branch"),
        ("Sales Invoice", "sc_branch", "Swiss Corner Branch", "Link", "pos_profile", "Branch", None, 0, 0, 1),
        ("Sales Invoice", "sc_pos_profile", "Swiss Corner POS Profile", "Link", "sc_branch", "POS Profile", None, 0, 0, 1),
        (
            "Sales Invoice",
            "sc_enable_whatsapp_invoice_notification",
            "Enable WhatsApp Invoice Notification",
            "Check",
            "sc_pos_profile",
            None,
            "1",
            0,
            0,
            1,
        ),
        ("Sales Invoice", "sc_whatsapp_invoice_status", "WhatsApp Invoice Status", "Data", "sc_enable_whatsapp_invoice_notification", None, None, 1, 0, 1),
        ("Sales Invoice", "sc_whatsapp_invoice_log", "WhatsApp Invoice Log", "Link", "sc_whatsapp_invoice_status", "WhatsApp Message Log", None, 1, 0, 1),
        ("Sales Invoice", "sc_whatsapp_dry_run", "WhatsApp Dry Run", "Check", "sc_whatsapp_invoice_log", None, "0", 1, 0, 1),
        ("Sales Invoice", "sc_whatsapp_sent_at", "WhatsApp Sent At", "Datetime", "sc_whatsapp_dry_run", None, None, 1, 0, 1),
        ("Sales Invoice", "sc_whatsapp_error", "WhatsApp Error", "Small Text", "sc_whatsapp_sent_at", None, None, 1, 0, 1),
        ("POS Invoice", "sc_branch", "Swiss Corner Branch", "Link", "pos_profile", "Branch", None, 0, 0, 1),
        ("Item", "sc_watch_model", "Watch Model", "Data", "brand"),
        ("Item", "sc_collection", "Collection", "Data", "sc_watch_model"),
        ("Item", "sc_gender", "Gender", "Select", "sc_collection", "Men\nWomen\nUnisex"),
        ("Item", "sc_movement_type", "Movement Type", "Select", "sc_gender", "Quartz\nAutomatic\nSolar\nChronograph"),
        ("Item", "sc_case_size_mm", "Case Size MM", "Int", "sc_movement_type"),
        ("Item", "sc_case_material", "Case Material", "Data", "sc_case_size_mm"),
        ("Item", "sc_strap_type", "Strap Type", "Data", "sc_case_material"),
        ("Item", "sc_glass_type", "Glass Type", "Data", "sc_strap_type"),
        ("Item", "sc_water_resistance", "Water Resistance", "Data", "sc_glass_type"),
        ("Item", "sc_warranty_months", "Warranty Months", "Int", "sc_water_resistance"),
        ("Item", "sc_serial_required", "Serial Required", "Check", "sc_warranty_months", None, "0"),
        ("Item", "sc_demo_brand_segment", "Demo Brand Segment", "Data", "sc_serial_required"),
        ("Sales Invoice Item", "sc_warranty_start", "Warranty Start", "Date", "serial_no", None, None, 1, 0, 1),
        ("Sales Invoice Item", "sc_warranty_end", "Warranty End", "Date", "sc_warranty_start", None, None, 1, 0, 1),
        ("Serial No", "sc_purchase_date", "Purchase Date", "Date", "purchase_document_no"),
        ("Serial No", "sc_sold_date", "Sold Date", "Date", "sc_purchase_date"),
        ("Serial No", "sc_customer", "Customer", "Link", "sc_sold_date", "Customer"),
        ("Serial No", "sc_sales_invoice", "Sales Invoice", "Link", "sc_customer", "Sales Invoice"),
        ("Serial No", "sc_warranty_start", "Warranty Start", "Date", "sc_sales_invoice"),
        ("Serial No", "sc_warranty_end", "Warranty End", "Date", "sc_warranty_start"),
        ("Serial No", "sc_warranty_status", "Warranty Status", "Data", "sc_warranty_end"),
        ("WhatsApp Message Log", "sc_reference_doctype", "Reference DocType", "Link", "error_message", "DocType", None, 1, 0, 1),
        ("WhatsApp Message Log", "sc_reference_name", "Reference Name", "Dynamic Link", "sc_reference_doctype", "sc_reference_doctype", None, 1, 0, 1),
        ("WhatsApp Message Log", "sc_attachment_status", "Attachment Status", "Data", "sc_reference_name", None, None, 1, 0, 1),
        ("WhatsApp Message Log", "sc_dry_run", "Dry Run", "Check", "sc_attachment_status", None, "0", 1, 0, 1),
        ("WhatsApp Connector Settings", "sc_section_swiss_corner", "Swiss Corner Invoice Demo", "Section Break", "default_session"),
        ("WhatsApp Connector Settings", "sc_enable_invoice_notification", "Enable WhatsApp Invoice Notification", "Check", "sc_section_swiss_corner", None, "1"),
        ("WhatsApp Connector Settings", "sc_demo_dry_run_only", "Demo Dry Run Only", "Check", "sc_enable_invoice_notification", None, "1"),
        ("WhatsApp Connector Settings", "sc_allowed_demo_numbers", "Allowed Demo Numbers", "Small Text", "sc_demo_dry_run_only"),
        ("WhatsApp Connector Settings", "sc_invoice_print_format", "Invoice Print Format", "Link", "sc_allowed_demo_numbers", "Print Format"),
    ]
    for row in custom_fields:
        ensure_custom_field(*row)
    for doctype in {
        "Company",
        "Customer",
        "Warehouse",
        "POS Profile",
        "Sales Invoice",
        "Sales Invoice Item",
        "POS Invoice",
        "Item",
        "Serial No",
        "WhatsApp Message Log",
        "WhatsApp Connector Settings",
    }:
        frappe.clear_cache(doctype=doctype)


def ensure_company_and_accounts() -> dict[str, str | None]:
    global COMPANY, ABBR

    operating_company = (
        frappe.db.get_value("Company", {"country": "Saudi Arabia", "default_currency": "SAR"}, "name")
        or frappe.db.get_value("Company", {"country": "Saudi Arabia"}, "name")
        or frappe.db.get_value("Company", {}, "name")
    )
    if not operating_company:
        frappe.throw("No company exists on the site; Swiss Corner demo needs an existing company to stay safe.")

    company = frappe.get_doc("Company", operating_company)
    COMPANY = company.name
    ABBR = company.abbr or ABBR

    root_cost_center = (
        frappe.db.get_value("Cost Center", {"company": company.name, "is_group": 1}, "name", order_by="lft asc")
        or company.cost_center
    )
    demo_cost_center = root_cost_center
    if root_cost_center:
        demo_cost_center = ensure_cost_center("Swiss Corner - Cost Centers", root_cost_center, is_group=1)
    transaction_cost_center = demo_cost_center
    if demo_cost_center:
        transaction_cost_center = ensure_cost_center("Swiss Corner - Demo Operations", demo_cost_center, is_group=0)

    accounts = {
        "company": company.name,
        "demo_company": "Swiss Corner Watches",
        "base_company": company.name,
        "receivable": company.default_receivable_account or account_by_type("Receivable"),
        "payable": company.default_payable_account or account_by_type("Payable"),
        "cash": company.default_cash_account or account_by_type("Cash") or account_by_type(None, root_type="Asset"),
        "bank": company.default_bank_account or account_by_type("Bank") or account_by_type(None, root_type="Asset"),
        "income": company.default_income_account or account_by_type("Income Account", root_type="Income"),
        "expense": company.default_expense_account
        or account_by_type("Cost of Goods Sold", root_type="Expense")
        or account_by_type("Expense Account", root_type="Expense"),
        "stock": company.default_inventory_account or account_by_type("Stock", root_type="Asset"),
        "stock_adjustment": company.stock_adjustment_account or account_by_type("Stock Adjustment", root_type="Expense"),
        "tax": account_by_type("Tax", root_type="Liability"),
        "write_off": company.write_off_account or account_by_type(None, root_type="Expense"),
        "round_off": company.round_off_account or account_by_type("Round Off", root_type="Expense"),
        "cost_center_group": demo_cost_center,
        "cost_center": transaction_cost_center,
    }
    ensure_tax_templates(accounts)
    return accounts


def ensure_roles_and_users(accounts: dict[str, str | None]):
    for role_name in ["Store Manager", "Cashier", "Inventory Manager", "Accountant", "Demo Viewer"]:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)

    user_configs = [
        ("demo_manager@swisscorner.demo", "demo_manager", "مدير الديمو", ["System Manager", "Sales Manager", "Stock Manager", "Accounts Manager", "Store Manager", "Demo Viewer"]),
        ("demo_inventory@swisscorner.demo", "demo_inventory", "مسؤول المخزون", ["Stock User", "Stock Manager", "Inventory Manager", "Demo Viewer"]),
        ("demo_accountant@swisscorner.demo", "demo_accountant", "محاسب الديمو", ["Accounts User", "Accounts Manager", "Accountant", "Demo Viewer"]),
    ]
    for branch in BRANCHES:
        if branch.get("cashier"):
            user_configs.append((branch["cashier"], branch["username"], branch["label"], ["Sales User", "Cashier", "Demo Viewer"]))

    for email, username, first_name, roles in user_configs:
        ensure_user(email, username, first_name, roles, accounts)


def ensure_master_data(accounts: dict[str, str | None]) -> dict[str, Any]:
    ensure_customer_groups()
    ensure_branches_and_warehouses(accounts)
    ensure_payment_modes(accounts)
    ensure_brands()
    ensure_item_groups()
    ensure_suppliers()
    ensure_customers()
    ensure_items(accounts)
    ensure_pos_profiles(accounts)
    return {
        "warehouses": get_warehouse_map(),
        "cost_centers": get_cost_center_map(),
        "pos_profiles": {b["key"]: b["pos_profile"] for b in BRANCHES if b.get("pos_profile")},
    }


def ensure_client_sample_from_pdf(accounts: dict[str, str | None]):
    branch = CLIENT_SAMPLE_BRANCH
    if not frappe.db.exists("Branch", branch["branch"]):
        frappe.get_doc({"doctype": "Branch", "branch": branch["branch"]}).insert(ignore_permissions=True)

    parent_cc = accounts.get("cost_center_group") or accounts.get("cost_center")
    cost_center = ensure_cost_center(branch["cost_center"], parent_cc, is_group=0)
    all_wh = frappe.db.get_value("Warehouse", {"company": COMPANY, "is_group": 1}, "name")
    warehouse = ensure_warehouse(branch["warehouse"], all_wh, is_group=0, warehouse_type=None)
    if has_field("Warehouse", "sc_branch"):
        frappe.db.set_value("Warehouse", warehouse, "sc_branch", branch["branch"], update_modified=False)

    ensure_user(
        branch["cashier"],
        branch["username"],
        branch["label"],
        ["Sales User", "Cashier", "Demo Viewer"],
        accounts,
    )
    ensure_client_sample_pos_profile(accounts, branch, warehouse, cost_center)

    for brand in {item["brand"] for item in CLIENT_SAMPLE_ITEMS}:
        if not frappe.db.exists("Brand", brand):
            frappe.get_doc({"doctype": "Brand", "brand": brand}).insert(ignore_permissions=True)

    item_group = f"{PREFIX} - {ITEM_GROUPS[0]}"
    image_cache: dict[int, str | None] = {}
    for idx, row in enumerate(CLIENT_SAMPLE_ITEMS):
        code = client_sample_item_code(row["alt"])
        purchase = round(flt(row["selling"]) * 0.55, 2)
        defaults = {
            "company": COMPANY,
            "default_warehouse": warehouse,
            "default_supplier": SUPPLIERS[0],
            "income_account": accounts.get("income"),
            "expense_account": accounts.get("expense"),
            "selling_cost_center": cost_center,
            "buying_cost_center": cost_center,
        }
        doc = get_or_new_item(code, f"{row['brand']} {row['alt']} - {row['name']}", item_group)
        doc.is_stock_item = 1
        doc.has_serial_no = 1
        doc.serial_no_series = f"{MARKER}-CL-.#####"
        doc.stock_uom = DEFAULT_UOM
        doc.brand = row["brand"]
        doc.description = f"{row['name']} - Client sample from 28-04-2026 item report."
        doc.warranty_period = 24
        doc.valuation_rate = purchase
        set_if_field(doc, "sc_watch_model", row["alt"])
        set_if_field(doc, "sc_collection", "Client Sample 28-04-2026")
        set_if_field(doc, "sc_gender", "Men")
        set_if_field(doc, "sc_movement_type", "Quartz")
        set_if_field(doc, "sc_case_size_mm", 40)
        set_if_field(doc, "sc_case_material", "Silver Tone")
        set_if_field(doc, "sc_strap_type", infer_client_sample_strap(row["name"]))
        set_if_field(doc, "sc_glass_type", "Mineral")
        set_if_field(doc, "sc_water_resistance", "3 ATM")
        set_if_field(doc, "sc_warranty_months", 24)
        set_if_field(doc, "sc_serial_required", 1)
        set_if_field(doc, "sc_demo_brand_segment", "Client Sample PDF")
        doc.set("item_defaults", [defaults])
        doc.set(
            "barcodes",
            [
                {"barcode": row["alt"], "barcode_type": "Code 128"},
                {"barcode": row["item_no"], "barcode_type": "Code 128"},
            ],
        )
        item_tax_template = get_item_tax_template_name()
        if item_tax_template:
            doc.set("taxes", [{"item_tax_template": item_tax_template}])
        if idx not in image_cache:
            image_cache[idx] = fetch_item_image(idx, code)
        if image_cache.get(idx):
            doc.image = image_cache[idx]
        save_doc(doc)
        ensure_item_prices(code, purchase, flt(row["selling"]))

    ensure_client_sample_stock(accounts, warehouse, cost_center)


def ensure_client_sample_pos_profile(accounts, branch, warehouse, cost_center):
    walk_in = "Swiss Corner - عميل نقدي POS"
    payments = [{"mode_of_payment": mode, "default": 1 if mode == "Cash" else 0} for mode, _ in PAYMENT_MODES]
    profile_name = branch["pos_profile"]
    if frappe.db.exists("POS Profile", profile_name):
        doc = frappe.get_doc("POS Profile", profile_name)
    else:
        doc = frappe.get_doc({"doctype": "POS Profile", "name": profile_name})
    doc.company = COMPANY
    doc.customer = walk_in
    doc.warehouse = warehouse
    doc.currency = "SAR"
    doc.selling_price_list = SELLING_PRICE_LIST
    doc.write_off_account = accounts.get("write_off")
    doc.write_off_cost_center = cost_center
    doc.income_account = accounts.get("income")
    doc.expense_account = accounts.get("expense")
    doc.cost_center = cost_center
    doc.taxes_and_charges = get_sales_tax_template_name()
    doc.print_format = PRINT_FORMAT if frappe.db.exists("Print Format", PRINT_FORMAT) else None
    if has_field("POS Profile", "sc_branch"):
        doc.sc_branch = branch["branch"]
    doc.set("payments", payments)
    doc.set("applicable_for_users", [{"user": branch["cashier"]}])
    doc.set("customer_groups", [{"customer_group": g} for g in ["Retail Customers", "Walk-in Customers"] if frappe.db.exists("Customer Group", g)])
    doc.allow_rate_change = 1
    doc.allow_discount_change = 1
    doc.validate_stock_on_save = 1
    save_doc(doc)


def ensure_client_sample_stock(accounts, warehouse, cost_center):
    if frappe.db.exists("Stock Entry", {"remarks": ["like", f"%{MARKER} Client Sample PDF Stock 28-04-2026%"], "docstatus": 1}):
        return
    doc = frappe.new_doc("Stock Entry")
    doc.stock_entry_type = "Material Receipt"
    doc.company = COMPANY
    doc.posting_date = add_days(today(), -1)
    doc.posting_time = "10:05:00"
    doc.set_posting_time = 1
    doc.remarks = f"{MARKER} Client Sample PDF Stock 28-04-2026 - Khamis Mushait"
    for row in CLIENT_SAMPLE_ITEMS:
        code = client_sample_item_code(row["alt"])
        qty = cint(row["qty"])
        serials = [f"{MARKER}-CL-{safe_serial(row['alt'])}-{n:02d}" for n in range(1, qty + 1)]
        doc.append(
            "items",
            {
                "item_code": code,
                "qty": qty,
                "t_warehouse": warehouse,
                "basic_rate": round(flt(row["selling"]) * 0.55, 2),
                "serial_no": "\n".join(serials),
                "use_serial_batch_fields": 1,
                "cost_center": cost_center or accounts.get("cost_center"),
                "allow_zero_valuation_rate": 0,
            },
        )
    submit_doc(doc)


def client_sample_item_code(alternate_number: str) -> str:
    return f"{MARKER}-CLIENT-{safe_serial(alternate_number)}"


def safe_serial(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value.upper())[:30]


def infer_client_sample_strap(name: str) -> str:
    if "ربيل" in name:
        return "Rubber Strap"
    if "جلد" in name:
        return "Leather Strap"
    return "Metal Bracelet"


def ensure_customer_groups():
    parent = frappe.db.get_value("Customer Group", {"is_group": 1}, "name")
    for group in ["Retail Customers", "VIP Customers", "Online Customers", "Walk-in Customers", "Warranty Customers"]:
        if not frappe.db.exists("Customer Group", group):
            frappe.get_doc(
                {
                    "doctype": "Customer Group",
                    "customer_group_name": group,
                    "parent_customer_group": parent,
                    "is_group": 0,
                }
            ).insert(ignore_permissions=True)


def ensure_branches_and_warehouses(accounts: dict[str, str | None]):
    for branch in BRANCHES:
        if not frappe.db.exists("Branch", branch["branch"]):
            frappe.get_doc({"doctype": "Branch", "branch": branch["branch"]}).insert(ignore_permissions=True)
        ensure_cost_center(branch["cost_center"], accounts.get("cost_center_group") or accounts.get("cost_center"), is_group=0)

    all_wh = frappe.db.get_value("Warehouse", {"company": COMPANY, "is_group": 1}, "name")
    if not all_wh:
        all_wh = ensure_warehouse("Swiss Corner - كل المخازن", None, is_group=1, warehouse_type=None)

    for key, wh_name, wh_type in EXTRA_WAREHOUSES:
        ensure_warehouse(wh_name, all_wh, is_group=0, warehouse_type=wh_type)
    for branch in BRANCHES:
        wh = ensure_warehouse(branch["warehouse"], all_wh, is_group=0, warehouse_type=None)
        if has_field("Warehouse", "sc_branch"):
            frappe.db.set_value("Warehouse", wh, "sc_branch", branch["branch"], update_modified=False)


def ensure_payment_modes(accounts: dict[str, str | None]):
    zatca_means = {
        "Cash": "10",
        "Mada": "48",
        "Visa / MasterCard": "48",
        "STC Pay": "48",
        "Bank Transfer": "42",
    }
    for mode, mode_type in PAYMENT_MODES:
        if frappe.db.exists("Mode of Payment", mode):
            doc = frappe.get_doc("Mode of Payment", mode)
        else:
            doc = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": mode, "type": mode_type})
        doc.type = mode_type
        account = accounts.get("cash") if mode_type == "Cash" else accounts.get("bank") or accounts.get("cash")
        rows = [row for row in doc.get("accounts", []) if row.company != COMPANY]
        rows.append({"company": COMPANY, "default_account": account})
        doc.set("accounts", rows)
        if has_field("Mode of Payment", "custom_zatca_payment_means_code"):
            doc.set("custom_zatca_payment_means_code", zatca_means.get(mode, "48"))
        if doc.is_new():
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)


def ensure_pos_profiles(accounts: dict[str, str | None]):
    warehouse_map = get_warehouse_map()
    cc_map = get_cost_center_map()
    walk_in = "Swiss Corner - عميل نقدي POS"
    payments = [{"mode_of_payment": mode, "default": 1 if mode == "Cash" else 0} for mode, _ in PAYMENT_MODES]
    root_group = f"{PREFIX} - ساعات"
    for branch in BRANCHES:
        if not branch.get("pos_profile"):
            continue
        profile_name = branch["pos_profile"]
        if frappe.db.exists("POS Profile", profile_name):
            doc = frappe.get_doc("POS Profile", profile_name)
        else:
            doc = frappe.get_doc({"doctype": "POS Profile", "name": profile_name})
        doc.company = COMPANY
        doc.customer = walk_in
        doc.warehouse = warehouse_map[branch["key"]]
        doc.currency = "SAR"
        doc.selling_price_list = SELLING_PRICE_LIST
        doc.write_off_account = accounts.get("write_off")
        doc.write_off_cost_center = cc_map[branch["key"]]
        doc.income_account = accounts.get("income")
        doc.expense_account = accounts.get("expense")
        doc.cost_center = cc_map[branch["key"]]
        doc.taxes_and_charges = get_sales_tax_template_name()
        doc.print_format = PRINT_FORMAT if frappe.db.exists("Print Format", PRINT_FORMAT) else None
        if has_field("POS Profile", "sc_branch"):
            doc.sc_branch = branch["branch"]
        doc.set("payments", payments)
        doc.set("applicable_for_users", [{"user": branch["cashier"]}])
        if frappe.db.exists("Item Group", root_group):
            doc.set("item_groups", [{"item_group": root_group}])
        doc.set("customer_groups", [{"customer_group": g} for g in ["Retail Customers", "VIP Customers", "Online Customers", "Walk-in Customers"] if frappe.db.exists("Customer Group", g)])
        doc.allow_rate_change = 1
        doc.allow_discount_change = 1
        doc.validate_stock_on_save = 1
        save_doc(doc)


def ensure_brands():
    for brand in BRANDS:
        if not frappe.db.exists("Brand", brand):
            frappe.get_doc({"doctype": "Brand", "brand": brand}).insert(ignore_permissions=True)


def ensure_item_groups():
    root_parent = frappe.db.get_value("Item Group", {"is_group": 1}, "name")
    root = f"{PREFIX} - ساعات"
    if not frappe.db.exists("Item Group", root):
        frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": root,
                "parent_item_group": root_parent,
                "is_group": 1,
            }
        ).insert(ignore_permissions=True)
    for group in ITEM_GROUPS:
        name = f"{PREFIX} - {group}"
        if not frappe.db.exists("Item Group", name):
            frappe.get_doc(
                {
                    "doctype": "Item Group",
                    "item_group_name": name,
                    "parent_item_group": root,
                    "is_group": 0,
                }
            ).insert(ignore_permissions=True)


def ensure_suppliers():
    supplier_group = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or frappe.db.get_value("Supplier Group", {"is_group": 1}, "name")
    for supplier_name in SUPPLIERS:
        if frappe.db.exists("Supplier", supplier_name):
            doc = frappe.get_doc("Supplier", supplier_name)
        else:
            doc = frappe.get_doc({"doctype": "Supplier", "supplier_name": supplier_name})
        doc.supplier_group = supplier_group
        doc.supplier_type = "Company"
        if doc.is_new():
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)


def ensure_customers():
    for customer_code, customer_name, group, mobile in CUSTOMERS:
        if frappe.db.exists("Customer", customer_code):
            doc = frappe.get_doc("Customer", customer_code)
        else:
            doc = frappe.get_doc({"doctype": "Customer", "customer_name": customer_code})
        doc.customer_name = customer_code
        doc.customer_type = "Individual"
        doc.customer_group = group
        doc.territory = "Saudi Arabia"
        doc.mobile_no = mobile
        doc.default_currency = "SAR"
        doc.default_price_list = SELLING_PRICE_LIST
        if has_field("Customer", "customer_name_in_arabic"):
            doc.customer_name_in_arabic = customer_name
        if doc.is_new():
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)
        ensure_contact_for_customer(customer_code, customer_name, mobile)


def ensure_items(accounts: dict[str, str | None]):
    main_wh = get_warehouse_map()["main"]
    image_cache: dict[int, str | None] = {}
    for idx, item in enumerate(WATCH_ITEMS):
        group = f"{PREFIX} - {item['group']}"
        defaults = {
            "company": COMPANY,
            "default_warehouse": main_wh,
            "default_supplier": SUPPLIERS[idx % len(SUPPLIERS)],
            "income_account": accounts.get("income"),
            "expense_account": accounts.get("expense"),
            "selling_cost_center": accounts.get("cost_center"),
            "buying_cost_center": accounts.get("cost_center"),
        }
        doc = get_or_new_item(item["code"], item["name"], group)
        doc.brand = item["brand"]
        doc.is_stock_item = 1
        doc.has_serial_no = 1
        doc.serial_no_series = f"{MARKER}-{idx + 1:02d}-.#####"
        doc.stock_uom = DEFAULT_UOM
        doc.description = f"{item['name']} - demo watch item for {COMPANY_AR}."
        doc.warranty_period = item["warranty"]
        doc.valuation_rate = item["purchase"]
        set_if_field(doc, "sc_watch_model", item["model"])
        set_if_field(doc, "sc_collection", item["collection"])
        set_if_field(doc, "sc_gender", item["gender"])
        set_if_field(doc, "sc_movement_type", item["movement"])
        set_if_field(doc, "sc_case_size_mm", item["case_size"])
        set_if_field(doc, "sc_case_material", item["case_material"])
        set_if_field(doc, "sc_strap_type", item["strap"])
        set_if_field(doc, "sc_glass_type", item["glass"])
        set_if_field(doc, "sc_water_resistance", item["water"])
        set_if_field(doc, "sc_warranty_months", item["warranty"])
        set_if_field(doc, "sc_serial_required", 1)
        set_if_field(doc, "sc_demo_brand_segment", "Demo Watches")
        set_item_children(doc, defaults, item["code"])
        if idx not in image_cache:
            image_cache[idx] = fetch_item_image(idx, item["code"])
        if image_cache.get(idx):
            doc.image = image_cache[idx]
        save_doc(doc)
        ensure_item_prices(item["code"], item["purchase"], item["selling"])

    for code, name, group, purchase, selling, is_stock in SERVICE_ITEMS:
        doc = get_or_new_item(code, name, f"{PREFIX} - {group}")
        doc.is_stock_item = is_stock
        doc.has_serial_no = 0
        doc.stock_uom = DEFAULT_UOM
        doc.description = f"{name} - Swiss Corner demo service/accessory."
        doc.valuation_rate = purchase
        set_if_field(doc, "sc_serial_required", 0)
        set_if_field(doc, "sc_demo_brand_segment", "Demo Services" if not is_stock else "Demo Accessories")
        defaults = {
            "company": COMPANY,
            "default_warehouse": main_wh,
            "default_supplier": SUPPLIERS[0],
            "income_account": accounts.get("income"),
            "expense_account": accounts.get("expense"),
            "selling_cost_center": accounts.get("cost_center"),
            "buying_cost_center": accounts.get("cost_center"),
        }
        set_item_children(doc, defaults, code)
        save_doc(doc)
        ensure_item_prices(code, purchase, selling)


def ensure_reports(accounts: dict[str, str | None]):
    report_defs = get_report_definitions()
    for name, definition in report_defs.items():
        ensure_query_report(get_active_demo_report_name(name), definition)


def ensure_print_format():
    html_body = r"""
<style>
.sc-invoice { font-family: Arial, sans-serif; color: #1f2933; font-size: 11px; }
.sc-header { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #111827; padding-bottom:10px; margin-bottom:12px; }
.sc-brand-ar { font-size:20px; font-weight:700; direction:rtl; }
.sc-brand-en { font-size:16px; font-weight:700; letter-spacing:0; }
.sc-muted { color:#607080; }
.sc-grid { display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:12px; }
.sc-box { border:1px solid #d8dee6; padding:8px; border-radius:4px; }
.sc-table { width:100%; border-collapse:collapse; margin-top:8px; }
.sc-table th { background:#f3f5f7; color:#111827; border:1px solid #d8dee6; padding:6px; text-align:left; }
.sc-table td { border:1px solid #d8dee6; padding:6px; vertical-align:top; }
.sc-totals { width:42%; margin-left:auto; margin-top:12px; }
.sc-totals td { padding:5px; border-bottom:1px solid #e5e7eb; }
.sc-footer { margin-top:18px; border-top:1px solid #d8dee6; padding-top:10px; direction:rtl; }
.text-right { text-align:right; }
</style>
<div class="sc-invoice">
  <div class="sc-header">
    <div>
      <div class="sc-brand-ar">الركن السويسري للساعات</div>
      <div class="sc-brand-en">Swiss Corner Watches</div>
      <div class="sc-muted">Saudi Arabia | Demo Tax Invoice</div>
    </div>
    <div class="text-right">
      <h3 style="margin:0">Tax Invoice</h3>
      <div><b>No:</b> {{ doc.name }}</div>
      <div><b>Date:</b> {{ doc.posting_date }} {{ doc.posting_time or "" }}</div>
      <div><b>Branch:</b> {{ doc.sc_branch or doc.cost_center or "" }}</div>
      {% if doc.ksa_einv_qr %}<img src="{{ doc.ksa_einv_qr }}" style="width:84px;margin-top:6px">{% endif %}
    </div>
  </div>
  <div class="sc-grid">
    <div class="sc-box">
      <b>Customer</b><br>
      {{ doc.customer_name or doc.customer }}<br>
      <span class="sc-muted">{{ frappe.db.get_value("Customer", doc.customer, "mobile_no") or "" }}</span>
    </div>
    <div class="sc-box">
      <b>Payment</b><br>
      {% for p in doc.payments %}{{ p.mode_of_payment }}: {{ frappe.utils.fmt_money(p.amount, currency=doc.currency) }}<br>{% endfor %}
      <span class="sc-muted">Currency: {{ doc.currency }}</span>
    </div>
  </div>
  <table class="sc-table">
    <thead>
      <tr>
        <th>#</th><th>Item</th><th>Serial Numbers</th><th class="text-right">Qty</th><th class="text-right">Rate</th><th class="text-right">Discount</th><th class="text-right">Amount</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr>
        <td>{{ row.idx }}</td>
        <td>{{ row.item_name }}<br><span class="sc-muted">{{ row.item_code }}</span></td>
        <td>{{ (row.serial_no or "").replace("\n", "<br>") }}</td>
        <td class="text-right">{{ row.qty }}</td>
        <td class="text-right">{{ frappe.utils.fmt_money(row.rate, currency=doc.currency) }}</td>
        <td class="text-right">{{ frappe.utils.fmt_money(row.discount_amount or 0, currency=doc.currency) }}</td>
        <td class="text-right">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <table class="sc-totals">
    <tr><td>Net Total</td><td class="text-right">{{ frappe.utils.fmt_money(doc.net_total, currency=doc.currency) }}</td></tr>
    <tr><td>VAT</td><td class="text-right">{{ frappe.utils.fmt_money(doc.total_taxes_and_charges, currency=doc.currency) }}</td></tr>
    <tr><td><b>Grand Total</b></td><td class="text-right"><b>{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</b></td></tr>
  </table>
  <div class="sc-footer">
    شروط الضمان المختصرة: يرجى الاحتفاظ بالفاتورة والرقم التسلسلي للساعة. يغطي الضمان عيوب التصنيع ولا يشمل سوء الاستخدام أو الكسر أو التلف الناتج عن الماء خارج درجة المقاومة المحددة.
    <br>شكراً لتسوقكم من الركن السويسري للساعات.
  </div>
</div>
"""
    if frappe.db.exists("Print Format", PRINT_FORMAT):
        doc = frappe.get_doc("Print Format", PRINT_FORMAT)
    else:
        doc = frappe.get_doc({"doctype": "Print Format", "name": PRINT_FORMAT})
    doc.print_format_for = "DocType"
    doc.doc_type = "Sales Invoice"
    doc.module = MODULE
    doc.standard = "No"
    doc.custom_format = 1
    doc.print_format_type = "Jinja"
    doc.disabled = 0
    doc.html = html_body
    doc.margin_top = 8
    doc.margin_bottom = 8
    doc.margin_left = 8
    doc.margin_right = 8
    save_doc(doc)


def ensure_print_format():
    html_body = r"""
<style>
.sc-invoice { font-family: Arial, sans-serif; color: #181818; font-size: 11px; line-height: 1.45; }
.sc-top { background: #050505; color: #ffffff; padding: 12px 14px; border-bottom: 4px solid #b87433; }
.sc-logo { max-width: 170px; max-height: 54px; }
.sc-title { color: #b87433; font-size: 20px; font-weight: 700; margin: 0; text-transform: uppercase; }
.sc-ar { direction: rtl; text-align: right; }
.sc-muted { color:#6b7280; }
.sc-gold { color:#b87433; }
.sc-box { border:1px solid #e5e0d8; padding:8px; background:#fffdfa; }
.sc-table { width:100%; border-collapse:collapse; margin-top:8px; }
.sc-table th { background:#111111; color:#ffffff; border:1px solid #111111; padding:6px; text-align:left; }
.sc-table td { border:1px solid #e5e0d8; padding:6px; vertical-align:top; }
.sc-totals { width:42%; margin-left:auto; margin-top:12px; }
.sc-totals td { padding:5px; border-bottom:1px solid #e5e7eb; }
.sc-total-grand { background:#111111; color:#ffffff; }
.sc-footer { margin-top:18px; border-top:2px solid #b87433; padding-top:10px; direction:rtl; }
.sc-stamp { border:1px solid #b87433; color:#b87433; padding:6px; text-align:center; font-weight:700; }
.text-right { text-align:right; }
</style>
{% set logo = frappe.db.get_value("File", {"file_name": "swiss-corner-logo.webp"}, "file_url") %}
<div class="sc-invoice">
  <table style="width:100%; border-collapse:collapse; margin-bottom:12px;">
    <tr>
      <td class="sc-top" style="width:50%;">
        {% if logo %}<img src="{{ logo }}" class="sc-logo">{% else %}<b>Swiss Corner Watches</b>{% endif %}
        <div style="margin-top:6px; color:#d6d6d6;">Swiss Corner Watches | swisscorner.co</div>
      </td>
      <td class="sc-top sc-ar" style="width:50%;">
        <div style="font-size:18px; font-weight:700;">الركن السويسري للساعات</div>
        <div style="color:#d6d6d6;">فاتورة مبيعات / ضريبية للديمو</div>
      </td>
    </tr>
  </table>
  <table style="width:100%; border-collapse:collapse; margin-bottom:12px;">
    <tr>
      <td style="width:58%; vertical-align:top;">
        <h2 class="sc-title">Tax Invoice</h2>
        <div class="sc-muted">Professional retail/POS invoice with serial and warranty traceability.</div>
      </td>
      <td class="text-right" style="width:42%; vertical-align:top;">
        <div><b>No:</b> {{ doc.name }}</div>
        <div><b>Date:</b> {{ doc.posting_date }} {{ doc.posting_time or "" }}</div>
        <div><b>Branch:</b> {{ doc.sc_branch or doc.cost_center or "" }}</div>
        {% if doc.ksa_einv_qr %}<img src="{{ doc.ksa_einv_qr }}" style="width:84px;margin-top:6px">{% endif %}
      </td>
    </tr>
  </table>
  <table style="width:100%; border-collapse:separate; border-spacing:0 8px;">
    <tr>
      <td style="width:50%; vertical-align:top; padding-right:6px;">
        <div class="sc-box">
          <b class="sc-gold">Customer</b><br>
          {{ doc.customer_name or doc.customer }}<br>
          <span class="sc-muted">{{ frappe.db.get_value("Customer", doc.customer, "mobile_no") or "" }}</span>
        </div>
      </td>
      <td style="width:50%; vertical-align:top; padding-left:6px;">
        <div class="sc-box">
          <b class="sc-gold">Payment</b><br>
          {% for p in doc.payments %}{{ p.mode_of_payment }}: {{ frappe.utils.fmt_money(p.amount, currency=doc.currency) }}<br>{% endfor %}
          <span class="sc-muted">Currency: {{ doc.currency }}</span>
        </div>
      </td>
    </tr>
  </table>
  <table class="sc-table">
    <thead>
      <tr>
        <th>#</th><th>Item</th><th>Serial Numbers</th><th class="text-right">Qty</th><th class="text-right">Rate</th><th class="text-right">Discount</th><th class="text-right">Amount</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr>
        <td>{{ row.idx }}</td>
        <td>{{ row.item_name }}<br><span class="sc-muted">{{ row.item_code }}</span></td>
        <td>{{ (row.serial_no or "").replace("\n", "<br>") }}</td>
        <td class="text-right">{{ row.qty }}</td>
        <td class="text-right">{{ frappe.utils.fmt_money(row.rate, currency=doc.currency) }}</td>
        <td class="text-right">{{ frappe.utils.fmt_money(row.discount_amount or 0, currency=doc.currency) }}</td>
        <td class="text-right">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <table class="sc-totals">
    <tr><td>Net Total</td><td class="text-right">{{ frappe.utils.fmt_money(doc.net_total, currency=doc.currency) }}</td></tr>
    <tr><td>VAT</td><td class="text-right">{{ frappe.utils.fmt_money(doc.total_taxes_and_charges, currency=doc.currency) }}</td></tr>
    <tr class="sc-total-grand"><td><b>Grand Total</b></td><td class="text-right"><b>{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</b></td></tr>
  </table>
  <table style="width:100%; margin-top:14px;">
    <tr>
      <td style="width:60%;" class="sc-muted">Official demo identity inspired by swisscorner.co. WhatsApp invoice delivery remains in dry-run/test mode unless configured otherwise.</td>
      <td style="width:40%;"><div class="sc-stamp">Swiss Corner Watches</div></td>
    </tr>
  </table>
  <div class="sc-footer">
    شروط الضمان المختصرة: يرجى الاحتفاظ بالفاتورة والرقم التسلسلي للساعة. يغطي الضمان عيوب التصنيع ولا يشمل سوء الاستخدام أو الكسر أو التلف الناتج عن الماء خارج درجة المقاومة المحددة.
    <br>شكراً لتسوقكم من الركن السويسري للساعات.
  </div>
</div>
"""
    if frappe.db.exists("Print Format", PRINT_FORMAT):
        doc = frappe.get_doc("Print Format", PRINT_FORMAT)
    else:
        doc = frappe.get_doc({"doctype": "Print Format", "name": PRINT_FORMAT})
    doc.print_format_for = "DocType"
    doc.doc_type = "Sales Invoice"
    doc.module = MODULE
    doc.standard = "No"
    doc.custom_format = 1
    doc.print_format_type = "Jinja"
    doc.disabled = 0
    doc.html = html_body
    doc.margin_top = 8
    doc.margin_bottom = 8
    doc.margin_left = 8
    doc.margin_right = 8
    save_doc(doc)


def ensure_workspace_and_dashboard(accounts: dict[str, str | None]):
    chart_names = ensure_dashboard_charts(accounts)
    card_names = ensure_number_cards(accounts)
    ensure_dashboard_doc(chart_names, card_names)
    cards = [
        {
            "label": "Executive View | العرض التنفيذي",
            "links": [report_link(name) for name in REPORT_NAMES],
        },
        {
            "label": "POS and Sales | نقاط البيع والمبيعات",
            "links": [
                doc_link("POS Profile"),
                doc_link("POS Opening Entry"),
                doc_link("POS Closing Entry"),
                doc_link("Sales Invoice"),
                doc_link("POS Invoice"),
                doc_link("Customer"),
                doc_link("Payment Entry"),
            ],
        },
        {
            "label": "Inventory and Warranty | المخزون والضمان",
            "links": [
                doc_link("Item"),
                doc_link("Item Group"),
                doc_link("Brand"),
                doc_link("Warehouse"),
                doc_link("Stock Entry"),
                doc_link("Stock Reconciliation"),
                doc_link("Serial No"),
            ],
        },
        {
            "label": "WhatsApp and Print | واتساب والطباعة",
            "links": [
                doc_link("WhatsApp Message Log"),
                doc_link("WhatsApp Connector Settings"),
                doc_link("Print Format", PRINT_FORMAT),
                doc_link("Letter Head", LETTER_HEAD),
                report_link("Swiss Corner - WhatsApp Invoice Delivery Log"),
            ],
        },
    ]
    shortcuts = [
        doc_shortcut("Sales Invoice"),
        doc_shortcut("POS Invoice"),
        doc_shortcut("Item"),
        doc_shortcut("Serial No"),
        doc_shortcut("Warehouse"),
        doc_shortcut("POS Opening Entry"),
        doc_shortcut("POS Closing Entry"),
        doc_shortcut("WhatsApp Message Log"),
    ]
    if WORKSPACE != WORKSPACE_LABEL and not frappe.db.exists("Workspace", WORKSPACE) and frappe.db.exists("Workspace", WORKSPACE_LABEL):
        frappe.rename_doc("Workspace", WORKSPACE_LABEL, WORKSPACE, force=True)
    values = {
        "doctype": "Workspace",
        "name": WORKSPACE,
        "label": WORKSPACE_LABEL,
        "title": WORKSPACE_LABEL,
        "module": MODULE,
        "icon": "retail",
        "indicator_color": "orange",
        "public": 1,
        "is_hidden": 0,
        "sequence_id": 2,
        "content": build_workspace_content(
            WORKSPACE_LABEL,
            "مساحة تشغيل موحدة للمبيعات، نقاط البيع، المخزون، الأرقام التسلسلية، الضمان، الفواتير، وواتساب.",
            chart_names,
            card_names,
            [s["label"] for s in shortcuts],
            [c["label"] for c in cards],
        ),
        "shortcuts": shortcuts,
        "links": build_workspace_links(cards),
        "charts": [{"chart_name": name, "label": name} for name in chart_names],
        "number_cards": [{"number_card_name": name, "label": name} for name in card_names],
        "roles": [{"role": "System Manager"}, {"role": "Demo Viewer"}],
    }
    if frappe.db.exists("Workspace", WORKSPACE):
        doc = frappe.get_doc("Workspace", WORKSPACE)
        for key, value in values.items():
            if key == "doctype":
                continue
            if key in {"shortcuts", "links", "charts", "number_cards", "roles"}:
                doc.set(key, value)
            else:
                setattr(doc, key, value)
    else:
        doc = frappe.get_doc(values)
        save_doc(doc)
    frappe.db.set_value(
        "Workspace",
        WORKSPACE,
        {"label": WORKSPACE_LABEL, "title": WORKSPACE_LABEL},
        update_modified=False,
    )
    ensure_demo_guide_workspace(chart_names, card_names)
    hide_legacy_swiss_corner_workspaces()


def ensure_demo_guide_workspace(chart_names=None, card_names=None):
    html_content = """
<div class="sc-demo-start" dir="rtl">
  <style>
    .sc-demo-start{font-family:Inter,"Noto Sans Arabic",Arial,sans-serif;color:#16120d;max-width:1180px;margin:auto}
    .sc-demo-hero{border:1px solid #e8d6ba;border-radius:10px;background:#fffaf3;padding:28px 32px;box-shadow:0 8px 24px rgba(50,35,18,.06)}
    .sc-demo-brand{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:18px}
    .sc-demo-brand img{height:58px;max-width:230px;object-fit:contain}
    .sc-demo-eyebrow{color:#9b672e;font-weight:900;font-size:12px;letter-spacing:.08em;text-transform:uppercase}
    .sc-demo-title{font-size:30px;font-weight:900;line-height:1.45;margin:8px 0 12px;color:#111}
    .sc-demo-copy{font-size:16px;line-height:1.9;color:#5a4b3c;max-width:980px}
    .sc-demo-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
    .sc-demo-actions a{display:inline-flex;align-items:center;justify-content:center;border-radius:8px;padding:11px 16px;text-decoration:none!important;font-weight:850;border:1px solid #c79a5a;color:#111!important;background:#fff}
    .sc-demo-actions a.primary{background:#111;color:#fff!important;border-color:#111}
    .sc-demo-section{margin-top:22px}
    .sc-demo-section-title{font-size:20px;font-weight:900;margin:0 0 12px;color:#111}
    .sc-demo-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
    .sc-demo-feature{border:1px solid #e8d6ba;border-radius:8px;background:#fff;padding:18px;min-height:150px}
    .sc-demo-feature strong{display:block;font-size:17px;margin-bottom:8px;color:#111}
    .sc-demo-feature p{margin:0;color:#625344;line-height:1.75;font-size:14px}
    .sc-demo-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
    .sc-demo-step{border:1px solid #e8d6ba;border-radius:8px;background:#fff;padding:14px;min-height:126px}
    .sc-demo-step span{display:inline-flex;width:28px;height:28px;border-radius:50%;align-items:center;justify-content:center;background:#9b672e;color:#fff;font-weight:900;margin-bottom:10px}
    .sc-demo-step b{display:block;margin-bottom:6px;color:#111}
    .sc-demo-step div{font-size:13px;line-height:1.65;color:#625344}
    .sc-demo-note{border-inline-start:4px solid #9b672e;background:#fff;padding:14px 16px;margin-top:16px;color:#574737;line-height:1.8}
    @media(max-width:1000px){.sc-demo-grid,.sc-demo-flow{grid-template-columns:1fr 1fr}.sc-demo-title{font-size:24px}}
    @media(max-width:650px){.sc-demo-grid,.sc-demo-flow{grid-template-columns:1fr}.sc-demo-brand{align-items:flex-start;flex-direction:column}.sc-demo-hero{padding:22px}}
  </style>

  <div class="sc-demo-hero">
    <div class="sc-demo-brand">
      <img src="/files/swiss-corner-logo.webp" alt="Swiss Corner Watches">
      <div class="sc-demo-eyebrow">Swiss Corner Watches | Retail / POS Experience</div>
    </div>
    <div class="sc-demo-title">ابدأ العرض من هنا: تجربة تشغيل متكاملة لمتاجر الساعات</div>
    <div class="sc-demo-copy">
      هذا الديمو يوضح كيف يخدم النظام سلسلة متاجر ساعات في السعودية: بيع سريع من نقطة البيع،
      إدارة أرقام تسلسلية وضمان، متابعة مخزون الفروع، فواتير احترافية، رسائل واتساب، وتقارير تساعد الإدارة على اتخاذ القرار.
    </div>
    <div class="sc-demo-actions">
      <a class="primary" href="/app/point-of-sale">فتح نقطة البيع</a>
      <a href="/app/swiss-corner-demo">مساحة الركن السويسري</a>
      <a href="/app/branch-operations">عمليات الفروع</a>
      <a href="/app/inventory-hub">المخزون والضمان</a>
      <a href="/app/query-report/Swiss%20Corner%20-%20Store%20Sales%20Report">تقرير مبيعات الفروع</a>
    </div>
  </div>

  <div class="sc-demo-section">
    <div class="sc-demo-section-title">القيمة التي ستظهر للعميل</div>
    <div class="sc-demo-grid">
      <div class="sc-demo-feature"><strong>نقطة بيع غنية</strong><p>كاشير، ورديات، خصومات، كوبونات، عروض، تعدد طرق الدفع، وإيصال سريع بهوية الركن السويسري.</p></div>
      <div class="sc-demo-feature"><strong>مخزون مناسب للساعات</strong><p>أصناف بسيريال نمبر، تحويلات بين الفروع، مخزون منخفض، أصناف سريعة وبطيئة الحركة، وقيمة المخزون حسب المخزن.</p></div>
      <div class="sc-demo-feature"><strong>ضمان وخدمة ما بعد البيع</strong><p>ربط الفاتورة بالرقم التسلسلي، متابعة انتهاء الضمان، وخدمات صيانة مثل البطارية والسير والتنظيف.</p></div>
      <div class="sc-demo-feature"><strong>فواتير وواتساب</strong><p>قالب فاتورة احترافي PDF، زر/سجل إرسال واتساب، وحماية من تكرار الإرسال أو الإرسال لأرقام غير تجريبية.</p></div>
      <div class="sc-demo-feature"><strong>إدارة متعددة الفروع</strong><p>الرياض، جدة، الخبر، المدينة، المتجر الإلكتروني، ومركز الصيانة، مع تقارير مقارنة بين الفروع.</p></div>
      <div class="sc-demo-feature"><strong>تقارير تنفيذية</strong><p>مبيعات الفروع، ملخص POS، الربحية حسب الفرع والعلامة، حركة المخزون، وسجل واتساب للفواتير.</p></div>
    </div>
  </div>

  <div class="sc-demo-section">
    <div class="sc-demo-section-title">تسلسل العرض المقترح</div>
    <div class="sc-demo-flow">
      <div class="sc-demo-step"><span>1</span><b>ابدأ بالصورة العامة</b><div>افتح مساحة الركن السويسري واعرض المبيعات والفروع والمؤشرات.</div></div>
      <div class="sc-demo-step"><span>2</span><b>ادخل كتاجر/كاشير</b><div>افتح POS، اختر صنفًا، طبّق عرضًا أو كوبونًا، ثم أكمل الدفع.</div></div>
      <div class="sc-demo-step"><span>3</span><b>أضف عميلًا جديدًا</b><div>سجل رقم واتساب تجريبي، ثم اعتمد الفاتورة واطبعها.</div></div>
      <div class="sc-demo-step"><span>4</span><b>اعرض الأثر التشغيلي</b><div>افتح السيريال، الضمان، حركة المخزون، وتحويلات الفروع.</div></div>
      <div class="sc-demo-step"><span>5</span><b>اختم بالإدارة</b><div>اعرض الربحية، تقارير POS، وسجل رسائل واتساب.</div></div>
    </div>
    <div class="sc-demo-note">
      حساب العرض الرئيسي: <b>cashier_demo@swisscorner.demo</b>.
      استخدمه لتجربة البيع، بينما حسابات المدير والمخزون مناسبة للتقارير والتحويلات والإعدادات.
    </div>
  </div>
</div>
"""
    content = [
        {
            "id": "swiss-corner-demo-guide",
            "type": "header",
            "data": {"text": html_content, "col": 12},
        }
    ]
    values = {
        "doctype": "Workspace",
        "label": GUIDE_WORKSPACE,
        "title": "Demo",
        "module": MODULE,
        "icon": "rocket",
        "indicator_color": "orange",
        "public": 1,
        "is_hidden": 0,
        "sequence_id": 1,
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [],
        "links": [],
        "charts": [],
        "number_cards": [],
        "roles": [{"role": "System Manager"}, {"role": "Demo Viewer"}, {"role": "Cashier"}],
    }
    if frappe.db.exists("Workspace", GUIDE_WORKSPACE):
        doc = frappe.get_doc("Workspace", GUIDE_WORKSPACE)
        for key, value in values.items():
            if key == "doctype":
                continue
            if key in {"shortcuts", "links", "charts", "number_cards", "roles"}:
                doc.set(key, value)
            else:
                setattr(doc, key, value)
    else:
        doc = frappe.get_doc(values)
    save_doc(doc)


def hide_legacy_swiss_corner_workspaces():
    # Keep existing workspaces visible. The demo guide organizes entry points without
    # hiding ERPNext/Frappe workspaces that users may need during evaluation.
    return


def polish_swiss_corner_workspace_experience():
    """Polish the Demo guide and order visible workspaces without changing visibility."""
    ensure_demo_guide_workspace()
    preferred_order = [
        "Demo",
        WORKSPACE,
        "Swiss Corner Demo",
        "Demo Center",
        "Executive Dashboard",
        "POSNext",
        "Sales Counter",
        "Branch Operations",
        "Inventory Hub",
        "WhatsApp Connector",
        "Invoicing",
        "Selling.",
        "Stock.",
        "Financial Management.",
        "Reports.",
        "General Reports.",
        "Financial Reports.",
        "Accounting",
        "Payables",
        "Receivables",
        "Finance Desk",
        "Buying.",
        "Assets.",
        "HR Management",
        "HR File",
        "People & Payroll",
        "People",
        "Leaves",
        "Performance",
        "Recruitment",
        "Employee Lifecycle",
        "Shift & Attendance",
        "Expense Claims",
        "Payroll.",
        "Salary Payout.",
        "Tax & Benefits",
        "Manufacturing",
        "CRM Management.",
        "Project Management.",
        "Loans Management",
    ]

    applied = []
    sequence = 1
    for workspace_name in preferred_order:
        if not frappe.db.exists("Workspace", workspace_name):
            continue
        frappe.db.set_value("Workspace", workspace_name, "sequence_id", sequence, update_modified=False)
        applied.append({"name": workspace_name, "sequence_id": sequence})
        sequence += 1

    listed = set(preferred_order)
    visible_others = frappe.get_all(
        "Workspace",
        filters={"is_hidden": 0},
        fields=["name", "sequence_id"],
        order_by="sequence_id asc, name asc",
        limit_page_length=500,
    )
    for row in visible_others:
        if row.name in listed:
            continue
        frappe.db.set_value("Workspace", row.name, "sequence_id", sequence, update_modified=False)
        applied.append({"name": row.name, "sequence_id": sequence})
        sequence += 1

    hidden_rows = frappe.get_all(
        "Workspace",
        filters={"is_hidden": 1},
        fields=["name"],
        order_by="sequence_id asc, name asc",
        limit_page_length=500,
    )
    hidden_sequence = 900
    for row in hidden_rows:
        frappe.db.set_value("Workspace", row.name, "sequence_id", hidden_sequence, update_modified=False)
        hidden_sequence += 1

    frappe.db.commit()
    frappe.clear_cache()
    return {"ordered_visible": applied, "hidden_moved_to_bottom": len(hidden_rows)}


def restore_swiss_corner_workspace_visibility():
    """Restore workspaces previously hidden during demo sidebar cleanup."""
    restored = []
    for workspace_name in LEGACY_WORKSPACES:
        if workspace_name in {WORKSPACE, GUIDE_WORKSPACE}:
            continue
        if not frappe.db.exists("Workspace", workspace_name):
            continue
        frappe.db.set_value(
            "Workspace",
            workspace_name,
            {"is_hidden": 0, "public": 1},
            update_modified=False,
        )
        restored.append(workspace_name)
    frappe.db.commit()
    frappe.clear_cache()
    return {"restored": restored, "count": len(restored)}
    frappe.clear_cache()


def reorganize_swiss_corner_workspaces():
    accounts = ensure_company_and_accounts()
    ensure_workspace_and_dashboard(accounts)
    for email in [
        "demo_manager@swisscorner.demo",
        "cashier_demo@swisscorner.demo",
        "cashier_backup@swisscorner.demo",
        "demo_inventory@swisscorner.demo",
        "demo_accountant@swisscorner.demo",
    ]:
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
            if frappe.db.exists("Workspace", GUIDE_WORKSPACE):
                user.default_workspace = GUIDE_WORKSPACE
                save_doc(user)
    frappe.db.commit()
    frappe.clear_cache()
    return {
        "guide_workspace": GUIDE_WORKSPACE,
        "operations_workspace": WORKSPACE,
        "operations_route": "/app/الركن-السويسري",
        "hidden": LEGACY_WORKSPACES,
    }


def ensure_whatsapp_demo_settings():
    if not frappe.db.exists("DocType", "WhatsApp Connector Settings"):
        return
    settings = frappe.get_single("WhatsApp Connector Settings")
    if has_field("WhatsApp Connector Settings", "sc_enable_invoice_notification"):
        settings.sc_enable_invoice_notification = 1
    if has_field("WhatsApp Connector Settings", "sc_demo_dry_run_only"):
        settings.sc_demo_dry_run_only = 1
    if has_field("WhatsApp Connector Settings", "sc_allowed_demo_numbers"):
        settings.sc_allowed_demo_numbers = "\n".join(sorted(SAFE_DEMO_NUMBERS))
    if has_field("WhatsApp Connector Settings", "sc_invoice_print_format"):
        settings.sc_invoice_print_format = PRINT_FORMAT
    settings.save(ignore_permissions=True)
    if frappe.db.exists("DocType", "WhatsApp Message Template") and not frappe.db.exists("WhatsApp Message Template", "Swiss Corner Invoice Message"):
        frappe.get_doc(
            {
                "doctype": "WhatsApp Message Template",
                "template_name": "Swiss Corner Invoice Message",
                "is_active": 1,
                "is_default": 0,
                "available_for_doctype": "Sales Invoice",
                "description": "Arabic/English demo invoice delivery message for Swiss Corner Watches.",
                "message_template": build_template_text(),
            }
        ).insert(ignore_permissions=True)
    ensure_demo_whatsapp_session()


def ensure_demo_transactions(accounts: dict[str, str | None], masters: dict[str, Any]):
    if frappe.db.exists("Stock Entry", {"remarks": ["like", f"%{MARKER} Opening Stock%"]}):
        ensure_missing_pos_activity(accounts)
        update_serial_warranties()
        return
    if not frappe.db.get_value("Item", "DEMO-SC-WATCH-001", "is_stock_item"):
        return
    wh = get_warehouse_map()
    cc = get_cost_center_map()
    inventory: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    serial_item_map = {item["code"]: item for item in WATCH_ITEMS}
    opening_date = add_days(today(), -110)

    with temporarily_disable_ksa_invoice_submission():
        create_opening_stock(accounts, wh, inventory, opening_date)
        create_purchase_cycle(accounts, wh, inventory, add_days(opening_date, 18))
        create_stock_transfers(accounts, wh, inventory, add_days(opening_date, 28))
        create_stock_reconciliation(accounts, wh, add_days(opening_date, 45))
        sold_invoices = create_sales_activity(accounts, wh, cc, inventory, serial_item_map, add_days(opening_date, 55))
        create_returns(sold_invoices[:2], add_days(opening_date, 95))
        create_after_sales_movements(accounts, wh, inventory, add_days(opening_date, 100))
        create_pos_opening_closing(accounts, add_days(opening_date, 95))
    update_serial_warranties()


def ensure_missing_pos_activity(accounts):
    if frappe.db.exists("POS Invoice", {"remarks": ["like", f"%{MARKER} POS Invoice demo%"], "docstatus": 1}):
        return
    wh = get_warehouse_map()
    cc = get_cost_center_map()
    base_date = add_days(today(), -10)
    with temporarily_disable_ksa_invoice_submission():
        create_pos_invoices_from_available_stock(accounts, wh, cc, base_date)
        create_pos_opening_closing(accounts, base_date)


def create_opening_stock(accounts, wh, inventory, posting_date):
    doc = frappe.new_doc("Stock Entry")
    doc.stock_entry_type = "Material Receipt"
    doc.company = COMPANY
    doc.posting_date = posting_date
    doc.posting_time = "09:00:00"
    doc.set_posting_time = 1
    doc.remarks = f"{MARKER} Opening Stock - Swiss Corner Watches"
    distribution = [
        ("main", 3),
        ("riyadh", 2),
        ("jeddah", 2),
        ("khobar", 1),
        ("madinah", 1),
        ("online", 1),
    ]
    for item_index, item in enumerate(WATCH_ITEMS, start=1):
        serial_counter = 1
        for wh_key, qty in distribution:
            serials = []
            for _ in range(qty):
                serial = f"{MARKER}-{item_index:02d}-{serial_counter:04d}"
                serial_counter += 1
                serials.append(serial)
                inventory[item["code"]][wh_key].append(serial)
            doc.append(
                "items",
                {
                    "item_code": item["code"],
                    "qty": qty,
                    "t_warehouse": wh[wh_key],
                    "basic_rate": item["purchase"],
                    "serial_no": "\n".join(serials),
                    "use_serial_batch_fields": 1,
                    "cost_center": accounts.get("cost_center"),
                    "allow_zero_valuation_rate": 0,
                },
            )
    for code, name, group, purchase, selling, is_stock in SERVICE_ITEMS:
        if not is_stock:
            continue
        doc.append(
            "items",
            {
                "item_code": code,
                "qty": 45 if "STRAP" in code else 80,
                "t_warehouse": wh["main"],
                "basic_rate": purchase,
                "cost_center": accounts.get("cost_center"),
            },
        )
    submit_doc(doc)


def create_purchase_cycle(accounts, wh, inventory, posting_date):
    supplier = SUPPLIERS[0]
    pr = frappe.new_doc("Purchase Receipt")
    pr.company = COMPANY
    pr.supplier = supplier
    pr.posting_date = posting_date
    pr.posting_time = "10:30:00"
    pr.set_posting_time = 1
    pr.remarks = f"{MARKER} Purchase Receipt - replenishment"
    for item_index, item in enumerate(WATCH_ITEMS, start=1):
        serials = [f"{MARKER}-{item_index:02d}-P{n:03d}" for n in range(1, 3)]
        inventory[item["code"]]["main"].extend(serials)
        pr.append(
            "items",
            {
                "item_code": item["code"],
                "qty": 2,
                "warehouse": wh["main"],
                "rate": item["purchase"],
                "serial_no": "\n".join(serials),
                "use_serial_batch_fields": 1,
                "cost_center": accounts.get("cost_center"),
                "expense_account": accounts.get("expense"),
            },
        )
    submit_doc(pr)

    pi = frappe.new_doc("Purchase Invoice")
    pi.company = COMPANY
    pi.supplier = supplier
    pi.posting_date = posting_date
    pi.bill_no = f"{MARKER}-SUP-BILL-001"
    pi.bill_date = posting_date
    pi.due_date = add_days(posting_date, 30)
    pi.remarks = f"{MARKER} Purchase Invoice - supplier bill"
    for item in WATCH_ITEMS[:5]:
        pi.append(
            "items",
            {
                "item_code": item["code"],
                "qty": 2,
                "rate": item["purchase"],
                "expense_account": accounts.get("expense"),
                "cost_center": accounts.get("cost_center"),
            },
        )
    submit_doc(pi)


def create_stock_transfers(accounts, wh, inventory, posting_date):
    transfers = [
        ("main", "riyadh", WATCH_ITEMS[:4]),
        ("main", "jeddah", WATCH_ITEMS[4:8]),
        ("riyadh", "khobar", WATCH_ITEMS[:2]),
        ("jeddah", "online", WATCH_ITEMS[4:6]),
    ]
    for index, (source, target, items) in enumerate(transfers, start=1):
        doc = frappe.new_doc("Stock Entry")
        doc.stock_entry_type = "Material Transfer"
        doc.company = COMPANY
        doc.posting_date = add_days(posting_date, index)
        doc.posting_time = "13:00:00"
        doc.set_posting_time = 1
        doc.remarks = f"{MARKER} Branch Transfer {source} to {target}"
        for item in items:
            serial = pop_serial(inventory, item["code"], source)
            if not serial:
                continue
            inventory[item["code"]][target].append(serial)
            doc.append(
                "items",
                {
                    "item_code": item["code"],
                    "qty": 1,
                    "s_warehouse": wh[source],
                    "t_warehouse": wh[target],
                    "serial_no": serial,
                    "use_serial_batch_fields": 1,
                    "cost_center": accounts.get("cost_center"),
                },
            )
        if doc.items:
            submit_doc(doc)


def create_stock_reconciliation(accounts, wh, posting_date):
    if not frappe.db.exists("Item", "DEMO-SC-ACCESSORY-002"):
        return
    doc = frappe.new_doc("Stock Reconciliation")
    doc.company = COMPANY
    doc.purpose = "Stock Reconciliation"
    doc.posting_date = posting_date
    doc.posting_time = "16:00:00"
    doc.set_posting_time = 1
    doc.expense_account = accounts.get("stock_adjustment") or accounts.get("expense")
    doc.cost_center = accounts.get("cost_center")
    doc.remarks = f"{MARKER} Stock Reconciliation - battery count adjustment"
    doc.append(
        "items",
        {
            "item_code": "DEMO-SC-ACCESSORY-002",
            "warehouse": wh["main"],
            "qty": 76,
            "valuation_rate": 8,
        },
    )
    submit_doc(doc)


def create_sales_activity(accounts, wh, cc, inventory, serial_item_map, start_date):
    invoices = []
    customers = [row[0] for row in CUSTOMERS]
    sales_plan = [
        ("riyadh", WATCH_ITEMS[0], "Cash", 0),
        ("jeddah", WATCH_ITEMS[2], "Mada", 2),
        ("khobar", WATCH_ITEMS[4], "Visa / MasterCard", 4),
        ("madinah", WATCH_ITEMS[7], "Cash", 5),
        ("online", WATCH_ITEMS[8], "STC Pay", 7),
        ("riyadh", WATCH_ITEMS[6], "Mada", 9),
        ("jeddah", WATCH_ITEMS[1], "Visa / MasterCard", 11),
        ("khobar", WATCH_ITEMS[3], "Cash", 13),
        ("madinah", WATCH_ITEMS[5], "Bank Transfer", 16),
        ("online", WATCH_ITEMS[9], "STC Pay", 19),
        ("riyadh", WATCH_ITEMS[0], "Mada", 21),
        ("jeddah", WATCH_ITEMS[4], "Cash", 24),
        ("khobar", WATCH_ITEMS[2], "Visa / MasterCard", 27),
        ("madinah", WATCH_ITEMS[8], "Cash", 30),
        ("online", WATCH_ITEMS[6], "Bank Transfer", 33),
    ]
    for idx, (branch_key, item, mop, offset) in enumerate(sales_plan):
        serial = pop_serial(inventory, item["code"], branch_key)
        if not serial:
            continue
        customer = customers[idx % len(customers)]
        invoice = make_sales_invoice_doc(
            accounts=accounts,
            warehouse=wh[branch_key],
            cost_center=cc[branch_key],
            branch_key=branch_key,
            item=item,
            serial=serial,
            customer=customer,
            payment_mode=mop,
            posting_date=add_days(start_date, offset),
            discount=5 if idx in {2, 6, 12} else 0,
            is_pos=1,
        )
        invoices.append(invoice.name)
        mark_serial_sold(serial, invoice, item)

    vip_item = WATCH_ITEMS[5]
    serial = pop_serial(inventory, vip_item["code"], "riyadh")
    if serial:
        invoice = make_sales_invoice_doc(
            accounts=accounts,
            warehouse=wh["riyadh"],
            cost_center=cc["riyadh"],
            branch_key="riyadh",
            item=vip_item,
            serial=serial,
            customer="Swiss Corner - خالد الغامدي",
            payment_mode=None,
            posting_date=add_days(start_date, 35),
            discount=8,
            is_pos=0,
        )
        invoices.append(invoice.name)
        mark_serial_sold(serial, invoice, vip_item)
        if get_payment_entry:
            pe = get_payment_entry("Sales Invoice", invoice.name, bank_account=accounts.get("bank") or accounts.get("cash"))
            pe.posting_date = add_days(start_date, 36)
            pe.reference_no = f"{MARKER}-VIP-PAY"
            pe.reference_date = pe.posting_date
            pe.remarks = f"{MARKER} Payment Entry for VIP invoice"
            submit_doc(pe)

    create_pos_invoices(accounts, wh, cc, inventory, start_date)
    return invoices


def create_pos_invoices(accounts, wh, cc, inventory, start_date):
    customers = [row[0] for row in CUSTOMERS]
    for idx, branch in enumerate([b for b in BRANCHES if b.get("pos_profile")], start=1):
        item = WATCH_ITEMS[(idx + 2) % len(WATCH_ITEMS)]
        serial = pop_serial(inventory, item["code"], branch["key"])
        if not serial:
            continue
        doc = frappe.new_doc("POS Invoice")
        doc.owner = branch["cashier"]
        doc.company = COMPANY
        doc.customer = customers[idx % len(customers)]
        doc.posting_date = add_days(start_date, 40 + idx)
        doc.posting_time = "19:30:00"
        doc.set_posting_time = 1
        doc.due_date = doc.posting_date
        doc.pos_profile = branch["pos_profile"]
        opening = ensure_pos_opening(branch, doc.posting_date, accounts)
        doc.pos_opening_entry = opening.name
        doc.is_pos = 1
        doc.currency = "SAR"
        doc.selling_price_list = SELLING_PRICE_LIST
        doc.set_warehouse = wh[branch["key"]]
        doc.cost_center = cc[branch["key"]]
        doc.taxes_and_charges = get_sales_tax_template_name()
        set_if_field(doc, "sc_branch", branch["branch"])
        doc.remarks = f"{MARKER} POS Invoice demo"
        doc.append(
            "items",
            {
                "item_code": item["code"],
                "qty": 1,
                "rate": item["selling"],
                "warehouse": wh[branch["key"]],
                "serial_no": serial,
                "use_serial_batch_fields": 1,
                "income_account": accounts.get("income"),
                "expense_account": accounts.get("expense"),
                "cost_center": cc[branch["key"]],
            },
        )
        doc.append("payments", {"mode_of_payment": "Cash" if idx % 2 else "Mada", "amount": item["selling"] * 1.15})
        submit_doc(doc)


def create_pos_invoices_from_available_stock(accounts, wh, cc, base_date):
    customers = [row[0] for row in CUSTOMERS]
    for idx, branch in enumerate([b for b in BRANCHES if b.get("pos_profile")], start=1):
        found = find_available_watch_serial(wh[branch["key"]])
        if not found:
            continue
        item_code, serial = found
        item = next((row for row in WATCH_ITEMS if row["code"] == item_code), WATCH_ITEMS[0])
        posting_date = add_days(base_date, idx)
        doc = frappe.new_doc("POS Invoice")
        doc.owner = branch["cashier"]
        doc.company = COMPANY
        doc.customer = customers[idx % len(customers)]
        doc.posting_date = posting_date
        doc.posting_time = "19:30:00"
        doc.set_posting_time = 1
        doc.due_date = posting_date
        doc.pos_profile = branch["pos_profile"]
        opening = ensure_pos_opening(branch, posting_date, accounts)
        doc.pos_opening_entry = opening.name
        doc.is_pos = 1
        doc.currency = "SAR"
        doc.selling_price_list = SELLING_PRICE_LIST
        doc.set_warehouse = wh[branch["key"]]
        doc.cost_center = cc[branch["key"]]
        doc.taxes_and_charges = get_sales_tax_template_name()
        set_if_field(doc, "sc_branch", branch["branch"])
        doc.remarks = f"{MARKER} POS Invoice demo"
        doc.append(
            "items",
            {
                "item_code": item_code,
                "qty": 1,
                "rate": item["selling"],
                "warehouse": wh[branch["key"]],
                "serial_no": serial,
                "use_serial_batch_fields": 1,
                "income_account": accounts.get("income"),
                "expense_account": accounts.get("expense"),
                "cost_center": cc[branch["key"]],
            },
        )
        doc.append("payments", {"mode_of_payment": "Cash" if idx % 2 else "Mada", "amount": item["selling"] * 1.15})
        submit_doc(doc)


def find_available_watch_serial(warehouse):
    row = frappe.db.sql(
        """
        select item_code, name
        from `tabSerial No`
        where item_code like %s
          and warehouse = %s
          and ifnull(status, '') not in ('Inactive', 'Delivered', 'Consumed')
        order by creation
        limit 1
        """,
        (f"{MARKER}-WATCH%", warehouse),
        as_dict=True,
    )
    if row:
        return row[0].item_code, row[0].name
    return None


def ensure_pos_opening(branch, posting_date, accounts):
    opening_name = frappe.db.get_value(
        "POS Opening Entry",
        {
            "pos_profile": branch["pos_profile"],
            "user": branch["cashier"],
            "posting_date": posting_date,
            "docstatus": 1,
            "status": "Open",
        },
        "name",
    )
    if opening_name:
        return frappe.get_doc("POS Opening Entry", opening_name)

    opening = frappe.new_doc("POS Opening Entry")
    opening.company = COMPANY
    opening.pos_profile = branch["pos_profile"]
    opening.user = branch["cashier"]
    opening.posting_date = posting_date
    opening.period_start_date = get_datetime(f"{posting_date} 09:00:00")
    opening.set_posting_date = 1
    opening.remarks = f"{MARKER} POS Opening"
    for mode, _mode_type in PAYMENT_MODES:
        opening.append("balance_details", {"mode_of_payment": mode, "opening_amount": 500 if mode == "Cash" else 0})
    submit_doc(opening)
    return opening


def make_sales_invoice_doc(accounts, warehouse, cost_center, branch_key, item, serial, customer, payment_mode, posting_date, discount=0, is_pos=1):
    branch = next(b for b in BRANCHES if b["key"] == branch_key)
    doc = frappe.new_doc("Sales Invoice")
    doc.company = COMPANY
    doc.customer = customer
    doc.posting_date = posting_date
    doc.posting_time = "18:00:00"
    doc.set_posting_time = 1
    doc.due_date = posting_date if is_pos else add_days(posting_date, 7)
    doc.is_pos = is_pos
    doc.update_stock = 1
    doc.pos_profile = branch["pos_profile"] if is_pos else None
    doc.currency = "SAR"
    doc.selling_price_list = SELLING_PRICE_LIST
    doc.set_warehouse = warehouse
    doc.cost_center = cost_center
    doc.taxes_and_charges = get_sales_tax_template_name()
    doc.apply_discount_on = "Grand Total"
    doc.additional_discount_percentage = discount
    doc.remarks = f"{MARKER} Sales Invoice demo"
    set_if_field(doc, "sc_branch", branch["branch"])
    set_if_field(doc, "sc_pos_profile", branch["pos_profile"])
    set_if_field(doc, "sc_enable_whatsapp_invoice_notification", 1)
    set_if_field(doc, "custom_zatca_discount_reason", "Discount")
    doc.append(
        "items",
        {
            "item_code": item["code"],
            "qty": 1,
            "rate": item["selling"],
            "warehouse": warehouse,
            "serial_no": serial,
            "use_serial_batch_fields": 1,
            "income_account": accounts.get("income"),
            "expense_account": accounts.get("expense"),
            "cost_center": cost_center,
            "custom_zatca_discount_reason": "Discount",
        },
    )
    if is_pos and payment_mode:
        doc.append("payments", {"mode_of_payment": payment_mode, "amount": item["selling"] * (1.15) * (1 - discount / 100)})
    submit_doc(doc)
    process_whatsapp_invoice_notification(doc.name)
    return frappe.get_doc("Sales Invoice", doc.name)


def create_returns(invoices, posting_date):
    if not make_return_doc:
        return
    for idx, invoice_name in enumerate(invoices):
        try:
            ret = make_return_doc("Sales Invoice", invoice_name)
            ret.posting_date = add_days(posting_date, idx)
            ret.posting_time = "11:15:00"
            ret.set_posting_time = 1
            ret.remarks = f"{MARKER} Sales Return / Credit Note"
            submit_doc(ret)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Swiss Corner Return Failed {invoice_name}")


def create_after_sales_movements(accounts, wh, inventory, posting_date):
    moves = [("riyadh", "damaged", WATCH_ITEMS[1], "Damaged Stock Movement"), ("jeddah", "service", WATCH_ITEMS[3], "Warranty Service Movement")]
    for idx, (source, target, item, label) in enumerate(moves):
        serial = pop_serial(inventory, item["code"], source)
        if not serial:
            continue
        doc = frappe.new_doc("Stock Entry")
        doc.stock_entry_type = "Material Transfer"
        doc.company = COMPANY
        doc.posting_date = add_days(posting_date, idx)
        doc.posting_time = "14:00:00"
        doc.set_posting_time = 1
        doc.remarks = f"{MARKER} {label}"
        doc.append(
            "items",
            {
                "item_code": item["code"],
                "qty": 1,
                "s_warehouse": wh[source],
                "t_warehouse": wh[target],
                "serial_no": serial,
                "use_serial_batch_fields": 1,
                "cost_center": accounts.get("cost_center"),
            },
        )
        submit_doc(doc)


def create_pos_opening_closing(accounts, posting_date):
    from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import make_closing_entry_from_opening

    for idx, branch in enumerate([b for b in BRANCHES if b.get("pos_profile")], start=1):
        opening = ensure_pos_opening(branch, add_days(posting_date, idx), accounts)
        if frappe.db.exists("POS Closing Entry", {"pos_opening_entry": opening.name, "docstatus": ["!=", 2]}):
            continue
        closing = make_closing_entry_from_opening(opening)
        closing.period_end_date = get_datetime(f"{opening.posting_date} 23:30:00")
        closing.posting_date = opening.posting_date
        closing.remarks = f"{MARKER} POS Closing"
        for row in closing.payment_reconciliation:
            row.closing_amount = flt(row.expected_amount)
        try:
            submit_doc(closing)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Swiss Corner POS Closing Failed {opening.name}")


def ensure_client_scripts():
    sales_script = """
frappe.ui.form.on('Sales Invoice', {
    validate(frm) {
        if (!frm.doc.items) return;
        const missing = frm.doc.items.filter(row => (row.item_code || '').startsWith('DEMO-SC-WATCH') && !row.serial_no);
        if (missing.length) {
            frappe.msgprint(__('Swiss Corner demo watch items should include Serial Numbers before submit.'));
        }
        if (frm.doc.sc_enable_whatsapp_invoice_notification && frm.doc.customer && !frm.doc.contact_mobile) {
            frappe.show_alert({message: __('Swiss Corner WhatsApp demo uses the Customer mobile number or records Dry Run.'), indicator: 'orange'});
        }
    }
});
"""
    ensure_client_script("Swiss Corner - Sales Invoice Serial and WhatsApp Hint", "Sales Invoice", sales_script, view="Form")

    list_script = r"""
(function () {
    const SAR_SYMBOL = "\u00A7";
    const money = (value) => {
        const amount = Number(value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        return `<span class="demo-saudi-currency">${SAR_SYMBOL} ${amount}</span>`;
    };
    const normalize = () => {
        document.querySelectorAll(".list-row, .list-row-head, .datatable, .report-wrapper").forEach((el) => {
            if (el.innerHTML && el.innerHTML.includes("$")) {
                el.innerHTML = el.innerHTML.replace(/\$/g, SAR_SYMBOL);
            }
        });
    };
    frappe.listview_settings["Sales Invoice"] = Object.assign(frappe.listview_settings["Sales Invoice"] || {}, {
        formatters: Object.assign((frappe.listview_settings["Sales Invoice"] || {}).formatters || {}, {
            grand_total(value) {
                return money(value);
            },
            rounded_total(value) {
                return money(value);
            },
            outstanding_amount(value) {
                return money(value);
            }
        }),
        onload(listview) {
            setTimeout(normalize, 150);
            listview.page.wrapper.on("render_complete", () => setTimeout(normalize, 50));
        },
        refresh() {
            setTimeout(normalize, 150);
        }
    });
})();
"""
    ensure_client_script("Swiss Corner - Sales Invoice SAR List Formatter", "Sales Invoice", list_script, view="List")

    pos_list_script = list_script.replace('"Sales Invoice"', '"POS Invoice"').replace("Sales Invoice", "POS Invoice")
    ensure_client_script("Swiss Corner - POS Invoice SAR List Formatter", "POS Invoice", pos_list_script, view="List")


def get_demo_report_company() -> str | None:
    return (
        frappe.db.get_value("Company", COMPANY, "name")
        or frappe.defaults.get_global_default("company")
        or frappe.db.get_value("Company", {}, "name")
    )


def get_report_definitions() -> dict[str, dict[str, Any]]:
    default_from = add_days(today(), -180)
    default_company = get_demo_report_company()
    common_filters = [
        {"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "default": default_company, "mandatory": 1},
        {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date", "default": str(default_from), "mandatory": 1},
        {"fieldname": "to_date", "label": "To Date", "fieldtype": "Date", "default": today(), "mandatory": 1},
    ]
    return {
        "Swiss Corner - Store Sales Report": {
            "ref_doctype": "Sales Invoice",
            "filters": common_filters,
            "columns": [
                col("store", "Store / Branch", "Data", 180),
                col("sales_amount", "Sales Amount", "Currency", 130),
                col("vat", "VAT", "Currency", 100),
                col("grand_total", "Grand Total", "Currency", 130),
                col("discount", "Discount", "Currency", 100),
                col("gross_profit", "Gross Profit", "Currency", 130),
                col("number_of_invoices", "Number of Invoices", "Int", 120),
                col("average_invoice_value", "Average Invoice Value", "Currency", 150),
            ],
            "query": """
select
    coalesce(si.sc_branch, si.cost_center, 'Swiss Corner') as store,
    sum(si.base_net_total) as sales_amount,
    sum(si.base_total_taxes_and_charges) as vat,
    sum(si.base_grand_total) as grand_total,
    sum(si.discount_amount) as discount,
    sum(si.base_net_total - ifnull(cost.total_cost, 0)) as gross_profit,
    count(distinct si.name) as number_of_invoices,
    avg(si.base_grand_total) as average_invoice_value
from `tabSales Invoice` si
left join (
    select parent, sum(abs(qty) * ifnull(incoming_rate, 0)) total_cost
    from `tabSales Invoice Item`
    group by parent
) cost on cost.parent = si.name
where si.docstatus = 1
  and si.company = %(company)s
  and si.posting_date between %(from_date)s and %(to_date)s
group by coalesce(si.sc_branch, si.cost_center, 'Swiss Corner')
order by grand_total desc
""",
        },
        "Swiss Corner - POS Sales Summary": {
            "ref_doctype": "POS Invoice",
            "filters": common_filters,
            "columns": [
                col("pos_profile", "POS Profile", "Link", 180, "POS Profile"),
                col("cashier", "Cashier", "Link", 180, "User"),
                col("opening_amount", "Opening Amount", "Currency", 120),
                col("cash_sales", "Cash Sales", "Currency", 120),
                col("mada_sales", "Mada Sales", "Currency", 120),
                col("card_sales", "Card Sales", "Currency", 120),
                col("stc_pay", "STC Pay", "Currency", 120),
                col("total_sales", "Total Sales", "Currency", 120),
                col("returns", "Returns", "Currency", 120),
                col("closing_difference", "Closing Difference", "Currency", 140),
            ],
            "query": """
select
    pi.pos_profile,
    pi.owner as cashier,
    ifnull(opening.opening_amount, 0) as opening_amount,
    sum(case when p.mode_of_payment = 'Cash' then p.amount else 0 end) as cash_sales,
    sum(case when p.mode_of_payment = 'Mada' then p.amount else 0 end) as mada_sales,
    sum(case when p.mode_of_payment = 'Visa / MasterCard' then p.amount else 0 end) as card_sales,
    sum(case when p.mode_of_payment = 'STC Pay' then p.amount else 0 end) as stc_pay,
    sum(p.amount) as total_sales,
    sum(case when pi.is_return = 1 then abs(pi.grand_total) else 0 end) as returns,
    ifnull(closing.difference, 0) as closing_difference
from `tabPOS Invoice` pi
left join `tabSales Invoice Payment` p on p.parent = pi.name and p.parenttype = 'POS Invoice'
left join (
    select parent, sum(opening_amount) opening_amount from `tabPOS Opening Entry Detail` group by parent
) opening_total on 1=1
left join `tabPOS Opening Entry` poe on poe.pos_profile = pi.pos_profile and poe.user = pi.owner and poe.docstatus = 1
left join (
    select parent, sum(opening_amount) opening_amount from `tabPOS Opening Entry Detail` group by parent
) opening on opening.parent = poe.name
left join `tabPOS Closing Entry` pce on pce.pos_opening_entry = poe.name and pce.docstatus = 1
left join (
    select parent, sum(difference) difference from `tabPOS Closing Entry Detail` group by parent
) closing on closing.parent = pce.name
where pi.docstatus = 1
  and pi.company = %(company)s
  and pi.posting_date between %(from_date)s and %(to_date)s
group by pi.pos_profile, pi.owner
order by total_sales desc
""",
        },
        "Swiss Corner - Inventory Movement by Store": {
            "ref_doctype": "Stock Ledger Entry",
            "filters": common_filters,
            "columns": [
                col("warehouse", "Warehouse", "Link", 220, "Warehouse"),
                col("item_code", "Item", "Link", 190, "Item"),
                col("brand", "Brand", "Link", 130, "Brand"),
                col("opening_qty", "Opening Qty", "Float", 100),
                col("purchased_qty", "Purchased Qty", "Float", 110),
                col("transferred_in", "Transferred In", "Float", 110),
                col("transferred_out", "Transferred Out", "Float", 110),
                col("sold_qty", "Sold Qty", "Float", 100),
                col("returned_qty", "Returned Qty", "Float", 100),
                col("damaged_qty", "Damaged Qty", "Float", 100),
                col("closing_qty", "Closing Qty", "Float", 100),
                col("stock_value", "Stock Value", "Currency", 120),
            ],
            "query": """
select
    sle.warehouse,
    sle.item_code,
    item.brand,
    sum(case when sle.posting_date < %(from_date)s then sle.actual_qty else 0 end) as opening_qty,
    sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.voucher_type = 'Purchase Receipt' and sle.actual_qty > 0 then sle.actual_qty else 0 end) as purchased_qty,
    sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.voucher_type = 'Stock Entry' and sle.actual_qty > 0 then sle.actual_qty else 0 end) as transferred_in,
    abs(sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.voucher_type = 'Stock Entry' and sle.actual_qty < 0 then sle.actual_qty else 0 end)) as transferred_out,
    abs(sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.voucher_type in ('Sales Invoice','POS Invoice') and sle.actual_qty < 0 then sle.actual_qty else 0 end)) as sold_qty,
    sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.voucher_type in ('Sales Invoice','POS Invoice') and sle.actual_qty > 0 then sle.actual_qty else 0 end) as returned_qty,
    sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.warehouse like '%%التالف%%' and sle.actual_qty > 0 then sle.actual_qty else 0 end) as damaged_qty,
    sum(case when sle.posting_date <= %(to_date)s then sle.actual_qty else 0 end) as closing_qty,
    max(sle.stock_value) as stock_value
from `tabStock Ledger Entry` sle
join `tabItem` item on item.name = sle.item_code
where sle.company = %(company)s
  and sle.item_code like 'DEMO-SC%%'
group by sle.warehouse, sle.item_code, item.brand
order by sle.warehouse, item.brand, sle.item_code
""",
        },
        "Swiss Corner - Serial Number Register": {
            "ref_doctype": "Serial No",
            "filters": [],
            "columns": [
                col("serial_no", "Serial Number", "Link", 170, "Serial No"),
                col("item_code", "Item", "Link", 190, "Item"),
                col("brand", "Brand", "Link", 130, "Brand"),
                col("model", "Model", "Data", 110),
                col("warehouse", "Current Warehouse", "Link", 220, "Warehouse"),
                col("purchase_date", "Purchase Date", "Date", 110),
                col("sold_date", "Sold Date", "Date", 110),
                col("customer", "Customer", "Link", 180, "Customer"),
                col("warranty_start", "Warranty Start", "Date", 110),
                col("warranty_end", "Warranty End", "Date", 110),
                col("status", "Status", "Data", 110),
            ],
            "query": """
select
    sn.name as serial_no,
    sn.item_code,
    item.brand,
    item.sc_watch_model as model,
    sn.warehouse,
    sn.sc_purchase_date as purchase_date,
    sn.sc_sold_date as sold_date,
    sn.sc_customer as customer,
    sn.sc_warranty_start as warranty_start,
    sn.sc_warranty_end as warranty_end,
    coalesce(sn.sc_warranty_status, sn.status) as status
from `tabSerial No` sn
left join `tabItem` item on item.name = sn.item_code
where sn.item_code like 'DEMO-SC-WATCH%%'
order by sn.item_code, sn.name
""",
        },
        "Swiss Corner - Warranty Report": {
            "ref_doctype": "Serial No",
            "filters": [],
            "columns": [
                col("customer", "Customer", "Link", 190, "Customer"),
                col("mobile", "Mobile", "Data", 120),
                col("invoice", "Invoice", "Link", 170, "Sales Invoice"),
                col("item_code", "Item", "Link", 190, "Item"),
                col("serial_no", "Serial Number", "Link", 170, "Serial No"),
                col("warranty_end_date", "Warranty End Date", "Date", 120),
                col("days_remaining", "Days Remaining", "Int", 110),
                col("warranty_status", "Warranty Status", "Data", 130),
            ],
            "query": """
select
    sn.sc_customer as customer,
    cust.mobile_no as mobile,
    sn.sc_sales_invoice as invoice,
    sn.item_code,
    sn.name as serial_no,
    sn.sc_warranty_end as warranty_end_date,
    datediff(sn.sc_warranty_end, curdate()) as days_remaining,
    case
        when sn.sc_warranty_end is null then 'Not Sold'
        when sn.sc_warranty_end < curdate() then 'Expired'
        when datediff(sn.sc_warranty_end, curdate()) <= 30 then 'Expiring Soon'
        else 'Active'
    end as warranty_status
from `tabSerial No` sn
left join `tabCustomer` cust on cust.name = sn.sc_customer
where sn.item_code like 'DEMO-SC-WATCH%%'
order by sn.sc_warranty_end asc
""",
        },
        "Swiss Corner - Gross Profit by Store and Brand": {
            "ref_doctype": "Sales Invoice",
            "filters": common_filters,
            "columns": [
                col("store", "Store / Branch", "Data", 180),
                col("brand", "Brand", "Link", 150, "Brand"),
                col("sales_amount", "Sales Amount", "Currency", 130),
                col("cost_amount", "Cost Amount", "Currency", 130),
                col("gross_profit", "Gross Profit", "Currency", 130),
                col("gross_margin", "Gross Margin %", "Float", 120),
            ],
            "query": """
select
    coalesce(si.sc_branch, si.cost_center, 'Swiss Corner') as store,
    item.brand,
    sum(sii.base_net_amount) as sales_amount,
    sum(abs(sii.qty) * ifnull(sii.incoming_rate, 0)) as cost_amount,
    sum(sii.base_net_amount - abs(sii.qty) * ifnull(sii.incoming_rate, 0)) as gross_profit,
    round(sum(sii.base_net_amount - abs(sii.qty) * ifnull(sii.incoming_rate, 0)) / nullif(sum(sii.base_net_amount),0) * 100, 2) as gross_margin
from `tabSales Invoice` si
join `tabSales Invoice Item` sii on sii.parent = si.name
left join `tabItem` item on item.name = sii.item_code
where si.docstatus = 1
  and si.company = %(company)s
  and si.posting_date between %(from_date)s and %(to_date)s
  and sii.item_code like 'DEMO-SC%%'
group by coalesce(si.sc_branch, si.cost_center, 'Swiss Corner'), item.brand
order by gross_profit desc
""",
        },
        "Swiss Corner - Fast and Slow Moving Watches": {
            "ref_doctype": "Item",
            "filters": common_filters,
            "columns": [
                col("item_code", "Item", "Link", 190, "Item"),
                col("item_name", "Item Name", "Data", 220),
                col("brand", "Brand", "Link", 140, "Brand"),
                col("sold_qty", "Sold Qty", "Float", 100),
                col("closing_qty", "Closing Qty", "Float", 100),
                col("movement_class", "Movement Class", "Data", 130),
            ],
            "query": """
select
    item.name as item_code,
    item.item_name,
    item.brand,
    abs(sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.voucher_type in ('Sales Invoice','POS Invoice') and sle.actual_qty < 0 then sle.actual_qty else 0 end)) as sold_qty,
    sum(case when sle.posting_date <= %(to_date)s then sle.actual_qty else 0 end) as closing_qty,
    case
        when abs(sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.voucher_type in ('Sales Invoice','POS Invoice') and sle.actual_qty < 0 then sle.actual_qty else 0 end)) >= 3 then 'Fast Moving'
        when abs(sum(case when sle.posting_date between %(from_date)s and %(to_date)s and sle.voucher_type in ('Sales Invoice','POS Invoice') and sle.actual_qty < 0 then sle.actual_qty else 0 end)) = 0 then 'Slow Moving'
        else 'Normal'
    end as movement_class
from `tabItem` item
left join `tabStock Ledger Entry` sle on sle.item_code = item.name and sle.company = %(company)s
where item.name like 'DEMO-SC-WATCH%%'
group by item.name, item.item_name, item.brand
order by sold_qty desc, closing_qty asc
""",
        },
        "Swiss Corner - Branch Transfer Summary": {
            "ref_doctype": "Stock Entry",
            "filters": common_filters,
            "columns": [
                col("stock_entry", "Stock Entry", "Link", 170, "Stock Entry"),
                col("posting_date", "Date", "Date", 110),
                col("from_warehouse", "From Warehouse", "Link", 220, "Warehouse"),
                col("to_warehouse", "To Warehouse", "Link", 220, "Warehouse"),
                col("item_code", "Item", "Link", 190, "Item"),
                col("qty", "Qty", "Float", 90),
            ],
            "query": """
select
    se.name as stock_entry,
    se.posting_date,
    sed.s_warehouse as from_warehouse,
    sed.t_warehouse as to_warehouse,
    sed.item_code,
    sed.qty
from `tabStock Entry` se
join `tabStock Entry Detail` sed on sed.parent = se.name
where se.docstatus = 1
  and se.company = %(company)s
  and se.stock_entry_type = 'Material Transfer'
  and se.posting_date between %(from_date)s and %(to_date)s
  and sed.item_code like 'DEMO-SC%%'
order by se.posting_date desc, se.name desc
""",
        },
        "Swiss Corner - WhatsApp Invoice Delivery Log": {
            "ref_doctype": "WhatsApp Message Log",
            "filters": common_filters,
            "columns": [
                col("invoice", "Invoice", "Link", 170, "Sales Invoice"),
                col("customer", "Customer", "Link", 190, "Customer"),
                col("mobile", "Mobile", "Data", 130),
                col("message_status", "Message Status", "Data", 120),
                col("sent_at", "Sent At", "Datetime", 160),
                col("attachment_status", "Attachment Status", "Data", 130),
                col("error", "Error", "Data", 260),
            ],
            "query": """
select
    si.name as invoice,
    si.customer,
    cust.mobile_no as mobile,
    coalesce(if(wal.sc_dry_run = 1, 'Dry Run', wal.status), si.sc_whatsapp_invoice_status) as message_status,
    coalesce(wal.creation, si.sc_whatsapp_sent_at) as sent_at,
    wal.sc_attachment_status as attachment_status,
    coalesce(wal.error_message, si.sc_whatsapp_error) as error
from `tabSales Invoice` si
left join `tabCustomer` cust on cust.name = si.customer
left join `tabWhatsApp Message Log` wal on wal.name = si.sc_whatsapp_invoice_log
where si.docstatus = 1
  and si.company = %(company)s
  and si.posting_date between %(from_date)s and %(to_date)s
  and (si.name like 'SINV%%' or si.remarks like '%%DEMO-SC%%')
order by coalesce(wal.creation, si.modified) desc
""",
        },
    }


def ensure_query_report(name: str, definition: dict[str, Any]):
    if frappe.db.exists("Report", name):
        doc = frappe.get_doc("Report", name)
    else:
        doc = frappe.get_doc({"doctype": "Report", "report_name": name, "name": name})
    doc.ref_doctype = definition["ref_doctype"]
    doc.is_standard = "No"
    doc.module = MODULE
    doc.report_type = "Query Report"
    doc.add_total_row = 1
    doc.disabled = 0
    doc.query = definition["query"]
    doc.set("filters", definition.get("filters", []))
    doc.set("columns", definition.get("columns", []))
    doc.set("roles", [{"role": "System Manager"}, {"role": "Demo Viewer"}])
    save_doc(doc)


def get_active_demo_report_name(name: str) -> str:
    generic_names = globals().get("GENERIC_REPORT_RENAMES", {})
    renamed = generic_names.get(name)
    if renamed and frappe.db.exists("Report", renamed):
        return renamed
    return name


def fix_demo_query_report_filters():
    """Repair custom Query Reports that used optional SQL placeholders.

    Frappe omits empty optional filters from Query Report requests. A SQL query
    that references an omitted filter such as %(status)s raises KeyError before
    it reaches the database. This routine reapplies the safe report definitions
    to the current report names, including renamed Arabic reports.
    """
    updated = []
    report_defs = get_report_definitions()
    generic_names = globals().get("GENERIC_REPORT_RENAMES", {})
    for source_name, definition in report_defs.items():
        candidates = [source_name]
        renamed = generic_names.get(source_name)
        if renamed and renamed not in candidates:
            candidates.insert(0, renamed)

        touched = False
        for report_name in candidates:
            if frappe.db.exists("Report", report_name):
                ensure_query_report(report_name, definition)
                updated.append(report_name)
                touched = True

        if not touched:
            ensure_query_report(source_name, definition)
            updated.append(source_name)

    frappe.db.commit()
    return {"updated": updated, "count": len(updated)}


def ensure_dashboard_charts(accounts):
    def chart_filters(doctype):
        return json.dumps([[doctype, "company", "=", COMPANY, False], [doctype, "docstatus", "=", 1, False]])

    definitions = [
        {
            "name": "Swiss Corner - Sales by Branch",
            "chart_type": "Group By",
            "document_type": "Sales Invoice",
            "group_by_based_on": "sc_branch",
            "group_by_type": "Sum",
            "aggregate_function_based_on": "grand_total",
            "type": "Bar",
            "filters_json": chart_filters("Sales Invoice"),
        },
        {
            "name": "Swiss Corner - POS Profiles",
            "chart_type": "Group By",
            "document_type": "POS Invoice",
            "group_by_based_on": "pos_profile",
            "group_by_type": "Sum",
            "aggregate_function_based_on": "grand_total",
            "type": "Donut",
            "filters_json": chart_filters("POS Invoice"),
        },
        {
            "name": "Swiss Corner - Invoice Trend",
            "chart_type": "Sum",
            "document_type": "Sales Invoice",
            "based_on": "posting_date",
            "value_based_on": "grand_total",
            "timeseries": 1,
            "timespan": "Last Quarter",
            "time_interval": "Weekly",
            "type": "Line",
            "filters_json": chart_filters("Sales Invoice"),
        },
    ]
    out = []
    for d in definitions:
        if frappe.db.exists("Dashboard Chart", d["name"]):
            doc = frappe.get_doc("Dashboard Chart", d["name"])
        else:
            doc = frappe.get_doc({"doctype": "Dashboard Chart", "chart_name": d["name"]})
        for key, value in d.items():
            if key == "name":
                continue
            setattr(doc, key, value)
        doc.is_public = 1
        doc.color = "#0f766e"
        save_doc(doc)
        out.append(d["name"])
    return out


def ensure_number_cards(accounts):
    definitions = [
        (
            "Swiss Corner - Invoice Count",
            "Sales Invoice",
            "Count",
            None,
            [["Sales Invoice", "company", "=", COMPANY, False], ["Sales Invoice", "docstatus", "=", 1, False]],
            "Blue",
        ),
        (
            "Swiss Corner - Sales Total",
            "Sales Invoice",
            "Sum",
            "grand_total",
            [["Sales Invoice", "company", "=", COMPANY, False], ["Sales Invoice", "docstatus", "=", 1, False]],
            "Green",
        ),
        (
            "Swiss Corner - Serial Watches",
            "Serial No",
            "Count",
            None,
            [["Serial No", "item_code", "like", "DEMO-SC-WATCH%", False]],
            "Purple",
        ),
        (
            "Swiss Corner - WhatsApp Logs",
            "WhatsApp Message Log",
            "Count",
            None,
            [["WhatsApp Message Log", "sc_reference_doctype", "=", "Sales Invoice", False]],
            "Orange",
        ),
    ]
    out = []
    for name, doctype, function, based_on, filters, color in definitions:
        if frappe.db.exists("Number Card", name):
            doc = frappe.get_doc("Number Card", name)
        else:
            doc = frappe.get_doc({"doctype": "Number Card", "label": name})
        doc.type = "Document Type"
        doc.document_type = doctype
        doc.function = function
        doc.aggregate_function_based_on = based_on
        doc.is_public = 1
        doc.show_full_number = 1
        doc.filters_json = json.dumps(filters)
        doc.color = color
        save_doc(doc)
        out.append(name)
    return out


def ensure_dashboard_doc(chart_names, card_names):
    if frappe.db.exists("Dashboard", WORKSPACE):
        doc = frappe.get_doc("Dashboard", WORKSPACE)
    else:
        doc = frappe.get_doc({"doctype": "Dashboard", "dashboard_name": WORKSPACE})
    doc.is_standard = 0
    doc.set("charts", [{"chart": name, "width": "Half"} for name in chart_names])
    doc.set("cards", [{"card": name} for name in card_names])
    save_doc(doc)


def ensure_swiss_corner_brand_assets():
    for key, url in SWISS_CORNER_ASSETS.items():
        extension = os.path.splitext(url.split("?", 1)[0])[1] or ".webp"
        file_name = f"swiss-corner-{key}{extension}"
        upload_public_file_from_url(url, file_name)


def ensure_swiss_corner_site_branding():
    logo = frappe.db.get_value("File", {"file_name": "swiss-corner-logo.webp"}, "file_url") or "/files/swiss-corner-logo.webp"
    icon = frappe.db.get_value("File", {"file_name": "swiss-corner-icon.webp"}, "file_url") or "/files/swiss-corner-icon.webp"
    theme_name = "Swiss Corner Gold"
    gold = ensure_color("Swiss Corner Gold", "#b87433")
    black = ensure_color("Swiss Corner Black", "#050505")
    ink = ensure_color("Swiss Corner Ink", "#181818")
    ivory = ensure_color("Swiss Corner Ivory", "#f7f3ee")
    light_gold = ensure_color("Swiss Corner Light Gold", "#fff7ed")

    if frappe.db.exists("Website Theme", theme_name):
        theme = frappe.get_doc("Website Theme", theme_name)
    else:
        theme = frappe.get_doc({"doctype": "Website Theme", "theme": theme_name})
    theme.module = MODULE
    theme.custom = 1
    theme.primary_color = gold
    theme.text_color = ink
    theme.light_color = light_gold
    theme.dark_color = black
    theme.background_color = ivory
    theme.button_rounded_corners = 1
    theme.button_shadows = 0
    theme.custom_overrides = """
$primary: #b87433;
$secondary: #050505;
$body-color: #181818;
$body-bg: #f7f3ee;
$border-radius: 10px;
"""
    theme.custom_scss = """
@font-face {
	font-family: "Cairo Saudi";
	src: url("/assets/demo_standard/fonts/Cairo-Regular-Saudi.ttf");
	unicode-range: U+00A7;
}
body,
button,
input,
select,
textarea,
.web-footer,
.navbar,
.page_content,
.currency,
.money,
[data-fieldtype="Currency"] {
	font-family: "Cairo Saudi", "Almarai", "Noto Sans Arabic", "Segoe UI", sans-serif !important;
}
.btn-primary {
	background-color: #111111;
	border-color: #111111;
}
.btn-primary:hover,
.btn-primary:focus {
	background-color: #b87433;
	border-color: #b87433;
}
"""
    save_doc(theme)

    settings = frappe.get_single("Website Settings")
    settings.app_name = "Swiss Corner Watches"
    settings.app_logo = logo
    settings.splash_image = logo
    settings.favicon = icon
    settings.footer_logo = logo if has_field("Website Settings", "footer_logo") else getattr(settings, "footer_logo", None)
    settings.website_theme = theme_name
    settings.brand_html = f'<img src="{logo}" alt="Swiss Corner Watches" style="height:42px; max-width:190px;">'
    settings.copyright = "Swiss Corner Watches"
    settings.title_prefix = "Swiss Corner"
    save_doc(settings)


def ensure_color(name: str, value: str) -> str:
    if frappe.db.exists("Color", name):
        doc = frappe.get_doc("Color", name)
    else:
        doc = frappe.get_doc({"doctype": "Color", "name": name})
    doc.color = value
    save_doc(doc)
    return doc.name


def upload_public_file_from_url(url: str, file_name: str, attached_to_doctype: str | None = None, attached_to_name: str | None = None) -> str | None:
    filters = {"file_name": file_name}
    if attached_to_doctype and attached_to_name:
        filters.update({"attached_to_doctype": attached_to_doctype, "attached_to_name": attached_to_name})
    existing = frappe.db.get_value("File", filters, "file_url")
    if existing:
        return existing
    try:
        response = requests.get(url, timeout=30, headers={"User-Agent": "Swiss Corner ERPNext Demo"})
        response.raise_for_status()
        file_doc = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": file_name,
                "content": response.content,
                "is_private": 0,
                "attached_to_doctype": attached_to_doctype,
                "attached_to_name": attached_to_name,
            }
        )
        file_doc.insert(ignore_permissions=True)
        return file_doc.file_url
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Swiss Corner Asset Fetch Failed {file_name}")
        return None


def get_template_name(doctype: str, title: str) -> str | None:
    return (
        frappe.db.get_value(doctype, {"company": COMPANY, "title": title}, "name")
        or frappe.db.exists(doctype, title)
        or frappe.db.exists(doctype, f"{title} - {ABBR}")
    )


def get_sales_tax_template_name() -> str | None:
    return get_template_name("Sales Taxes and Charges Template", TAX_TEMPLATE)


def get_item_tax_template_name() -> str | None:
    return get_template_name("Item Tax Template", ITEM_TAX_TEMPLATE)


def ensure_tax_templates(accounts):
    sales_tax_template = get_sales_tax_template_name()
    if accounts.get("tax") and not sales_tax_template:
        doc = frappe.get_doc({"doctype": "Sales Taxes and Charges Template", "title": TAX_TEMPLATE, "company": COMPANY})
        doc.append(
            "taxes",
            {
                "charge_type": "On Net Total",
                "account_head": accounts.get("tax"),
                "description": "VAT 15%",
                "rate": 15,
            },
        )
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
    item_tax_template = get_item_tax_template_name()
    if accounts.get("tax") and not item_tax_template:
        doc = frappe.get_doc({"doctype": "Item Tax Template", "title": ITEM_TAX_TEMPLATE, "company": COMPANY})
        doc.append("taxes", {"tax_type": accounts.get("tax"), "tax_rate": 15})
        doc.insert(ignore_permissions=True, ignore_if_duplicate=True)


def get_warehouse_map() -> dict[str, str]:
    mapping = {}
    for key, wh_name, _wh_type in EXTRA_WAREHOUSES:
        mapping[key] = warehouse_doc_name(wh_name)
    for branch in BRANCHES:
        mapping[branch["key"]] = warehouse_doc_name(branch["warehouse"])
    return mapping


def get_cost_center_map() -> dict[str, str]:
    return {branch["key"]: cost_center_doc_name(branch["cost_center"]) for branch in BRANCHES}


def ensure_warehouse(warehouse_name, parent_warehouse, is_group=0, warehouse_type=None):
    existing = frappe.db.get_value("Warehouse", {"warehouse_name": warehouse_name, "company": COMPANY}, "name")
    if existing:
        doc = frappe.get_doc("Warehouse", existing)
    else:
        doc = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": warehouse_name, "company": COMPANY})
    doc.parent_warehouse = parent_warehouse
    doc.is_group = is_group
    doc.warehouse_type = warehouse_type
    save_doc(doc)
    return doc.name


def ensure_cost_center(cost_center_name, parent, is_group=0):
    existing = frappe.db.get_value("Cost Center", {"cost_center_name": cost_center_name, "company": COMPANY}, "name")
    if existing:
        doc = frappe.get_doc("Cost Center", existing)
    else:
        doc = frappe.get_doc({"doctype": "Cost Center", "cost_center_name": cost_center_name, "company": COMPANY})
    doc.parent_cost_center = parent
    doc.is_group = is_group
    save_doc(doc)
    return doc.name


def cost_center_doc_name(cost_center_name):
    return frappe.db.get_value("Cost Center", {"cost_center_name": cost_center_name, "company": COMPANY}, "name")


def warehouse_doc_name(warehouse_name):
    return frappe.db.get_value("Warehouse", {"warehouse_name": warehouse_name, "company": COMPANY}, "name")


def account_by_type(account_type=None, root_type=None):
    filters = {"company": COMPANY, "is_group": 0}
    if account_type:
        filters["account_type"] = account_type
    if root_type:
        filters["root_type"] = root_type
    return frappe.db.get_value("Account", filters, "name", order_by="lft asc")


@contextmanager
def temporarily_disable_ksa_company_after_insert():
    """Bypass KSA company after_insert hooks for this demo company only.

    The installed KSA app expects root accounts to exist on Company.after_insert,
    while ERPNext creates the chart later in Company.on_update. Skipping these
    regional helper hooks during this one insert avoids a false setup failure and
    keeps ZATCA integration inactive for the demo company.
    """
    patched = []
    targets = [
        ("ksa.saudi_arabia.wizard.operations.setup_tax_templates", "setup_templates"),
        ("ksa.saudi_arabia.setup", "create_company_settings"),
        ("erpnext.setup.doctype.company.company", "Company.set_mode_of_payment_account"),
    ]
    try:
        import importlib

        for module_path, attr in targets:
            try:
                if "." in attr:
                    class_name, method_name = attr.split(".", 1)
                    module = importlib.import_module(module_path)
                    klass = getattr(module, class_name, None)
                    original = getattr(klass, method_name, None) if klass else None
                    if original:
                        patched.append((klass, method_name, original))
                        setattr(klass, method_name, lambda *args, **kwargs: None)
                    continue
                module = importlib.import_module(module_path)
                original = getattr(module, attr, None)
                if original:
                    patched.append((module, attr, original))
                    setattr(module, attr, lambda *args, **kwargs: None)
            except Exception:
                continue
        yield
    finally:
        for module, attr, original in patched:
            setattr(module, attr, original)


@contextmanager
def temporarily_disable_ksa_invoice_submission():
    """Skip KSA/ZATCA submit hooks while building dry-run demo invoices."""
    patched = []
    targets = [
        ("ksa_compliance.standard_doctypes.sales_invoice", "create_sales_invoice_additional_fields_doctype"),
        ("ksa_compliance.standard_doctypes.payment_entry.payment_entry", "create_prepayment_invoice_additional_fields_doctype"),
    ]
    try:
        import importlib

        for module_path, attr in targets:
            try:
                module = importlib.import_module(module_path)
                original = getattr(module, attr, None)
                if original:
                    patched.append((module, attr, original))
                    setattr(module, attr, lambda *args, **kwargs: None)
            except Exception:
                continue
        yield
    finally:
        for module, attr, original in patched:
            setattr(module, attr, original)


def ensure_user(email, username, first_name, roles, accounts):
    if frappe.db.exists("User", email):
        doc = frappe.get_doc("User", email)
    else:
        doc = frappe.new_doc("User")
        doc.email = email
        doc.send_welcome_email = 0
        doc.user_type = "System User"
    doc.enabled = 1
    doc.username = username
    doc.first_name = first_name
    doc.language = "ar"
    doc.desk_theme = "Light"
    doc.time_zone = "Asia/Riyadh"
    if frappe.db.exists("Workspace", GUIDE_WORKSPACE):
        doc.default_workspace = GUIDE_WORKSPACE
    elif frappe.db.exists("Workspace", WORKSPACE):
        doc.default_workspace = WORKSPACE
    doc.set("roles", [{"role": role} for role in roles if frappe.db.exists("Role", role)])
    save_doc(doc)
    frappe.defaults.set_user_default("company", COMPANY, user=email)
    frappe.defaults.set_user_default("currency", "SAR", user=email)


def get_or_new_item(code, name, item_group):
    if frappe.db.exists("Item", code):
        doc = frappe.get_doc("Item", code)
    else:
        doc = frappe.get_doc({"doctype": "Item", "item_code": code})
    doc.item_name = name
    doc.item_group = item_group
    return doc


def set_item_children(doc, defaults, barcode):
    doc.set("item_defaults", [defaults])
    doc.set("barcodes", [{"barcode": barcode, "barcode_type": "Code 128"}])
    item_tax_template = get_item_tax_template_name()
    if item_tax_template:
        doc.set("taxes", [{"item_tax_template": item_tax_template}])


def ensure_item_prices(item_code, purchase_rate, selling_rate):
    for price_list, rate in [(BUYING_PRICE_LIST, purchase_rate), (SELLING_PRICE_LIST, selling_rate)]:
        if not frappe.db.exists("Price List", price_list):
            continue
        existing = frappe.db.exists("Item Price", {"item_code": item_code, "price_list": price_list, "currency": "SAR"})
        if existing:
            doc = frappe.get_doc("Item Price", existing)
        else:
            doc = frappe.get_doc({"doctype": "Item Price", "item_code": item_code, "price_list": price_list, "currency": "SAR"})
        doc.price_list_rate = rate
        save_doc(doc)


def fetch_item_image(index: int, item_code: str) -> str | None:
    source = IMAGE_SOURCES[index % len(IMAGE_SOURCES)]
    try:
        if source.startswith("http") and not source.startswith("https://unsplash.com/"):
            extension = os.path.splitext(source.split("?", 1)[0])[1] or ".webp"
            return upload_public_file_from_url(source, f"{item_code.lower()}{extension}", "Item", item_code)
        response = requests.get(source, timeout=20, headers={"User-Agent": "Swiss Corner ERPNext Demo"})
        response.raise_for_status()
        matches = re.findall(r"https://images\.unsplash\.com/[^\"\\]+", response.text)
        if not matches:
            return None
        image_url = html.unescape(matches[0]).split(" ")[0]
        image_url = image_url.split("?")[0] + "?auto=format&fit=crop&w=800&q=80"
        image_response = requests.get(image_url, timeout=20, headers={"User-Agent": "Swiss Corner ERPNext Demo"})
        image_response.raise_for_status()
        file_name = f"{item_code.lower()}.jpg"
        existing = frappe.db.get_value("File", {"file_name": file_name, "attached_to_doctype": "Item", "attached_to_name": item_code}, "file_url")
        if existing:
            return existing
        file_doc = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": file_name,
                "content": image_response.content,
                "is_private": 0,
                "attached_to_doctype": "Item",
                "attached_to_name": item_code,
            }
        )
        file_doc.insert(ignore_permissions=True)
        return file_doc.file_url
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Swiss Corner Image Fetch Failed {item_code}")
        return None


def submit_doc(doc):
    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = False
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc


def save_doc(doc):
    doc.flags.ignore_permissions = True
    doc.flags.ignore_version = True
    if doc.is_new() or not doc.get("name") or not frappe.db.exists(doc.doctype, doc.name):
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)
    return doc


def pop_serial(inventory, item_code, warehouse_key):
    if inventory[item_code][warehouse_key]:
        return inventory[item_code][warehouse_key].pop(0)
    return None


def mark_serial_sold(serial, invoice, item):
    start = invoice.posting_date
    end = add_days(start, cint(item.get("warranty", 24)) * 30)
    updates = {
        "sc_sold_date": start,
        "sc_customer": invoice.customer,
        "sc_sales_invoice": invoice.name,
        "sc_warranty_start": start,
        "sc_warranty_end": end,
        "sc_warranty_status": "Active",
    }
    for field, value in updates.items():
        if has_field("Serial No", field) and frappe.db.exists("Serial No", serial):
            frappe.db.set_value("Serial No", serial, field, value, update_modified=False)


def update_serial_warranties():
    for serial in frappe.get_all("Serial No", filters={"item_code": ["like", "DEMO-SC-WATCH%"]}, pluck="name"):
        doc = frappe.get_doc("Serial No", serial)
        if has_field("Serial No", "sc_purchase_date") and not doc.get("sc_purchase_date"):
            doc.sc_purchase_date = frappe.db.get_value("Stock Ledger Entry", {"serial_no": ["like", f"%{serial}%"], "actual_qty": [">", 0]}, "posting_date", order_by="posting_date asc")
        if has_field("Serial No", "sc_warranty_status") and doc.get("sc_warranty_end"):
            doc.sc_warranty_status = "Expired" if str(doc.sc_warranty_end) < nowdate() else "Active"
        doc.save(ignore_permissions=True)


def ensure_contact_for_customer(customer_code, display_name, mobile):
    existing = frappe.db.get_value("Dynamic Link", {"link_doctype": "Customer", "link_name": customer_code, "parenttype": "Contact"}, "parent")
    if existing:
        doc = frappe.get_doc("Contact", existing)
    else:
        doc = frappe.get_doc({"doctype": "Contact", "first_name": display_name})
        doc.append("links", {"link_doctype": "Customer", "link_name": customer_code})
    doc.first_name = display_name
    doc.set("phone_nos", [{"phone": mobile, "is_primary_mobile_no": 1}])
    save_doc(doc)


def ensure_client_script(name, dt, script, view="Form"):
    if frappe.db.exists("Client Script", name):
        doc = frappe.get_doc("Client Script", name)
    else:
        doc = frappe.get_doc({"doctype": "Client Script", "name": name})
    doc.dt = dt
    if has_field("Client Script", "view"):
        doc.view = view
    doc.enabled = 1
    doc.script = script
    save_doc(doc)


def ensure_custom_field(
    dt,
    fieldname,
    label,
    fieldtype,
    insert_after=None,
    options=None,
    default=None,
    read_only=0,
    hidden=0,
    allow_on_submit=0,
):
    if frappe.get_meta(dt).get_field(fieldname):
        return
    name = f"{dt}-{fieldname}"
    if frappe.db.exists("Custom Field", name):
        return
    doc = frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": dt,
            "fieldname": fieldname,
            "label": label,
            "fieldtype": fieldtype,
            "insert_after": insert_after,
            "options": options,
            "default": default,
            "read_only": read_only,
            "hidden": hidden,
            "allow_on_submit": allow_on_submit,
        }
    )
    doc.flags.ignore_validate = True
    doc.insert(ignore_permissions=True)


def has_field(dt, fieldname):
    try:
        return bool(frappe.get_meta(dt).get_field(fieldname))
    except Exception:
        return False


def set_if_field(doc, fieldname, value):
    if has_field(doc.doctype, fieldname):
        doc.set(fieldname, value)


def col(fieldname, label, fieldtype, width=120, options=None):
    row = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, "width": width}
    if fieldtype == "Currency" and not options:
        options = "SAR"
    if options:
        row["options"] = options
    return row


def is_swiss_invoice(doc):
    if doc.company == COMPANY:
        return True
    if (doc.get("remarks") or "").find(MARKER) >= 0:
        return True
    return any((row.item_code or "").startswith("DEMO-SC") for row in doc.get("items", []))


def get_whatsapp_settings():
    if frappe.db.exists("DocType", "WhatsApp Connector Settings"):
        return frappe.get_single("WhatsApp Connector Settings").as_dict()
    return frappe._dict({"sc_enable_invoice_notification": 1, "sc_demo_dry_run_only": 1})


def resolve_customer_mobile(customer):
    mobile = frappe.db.get_value("Customer", customer, "sc_whatsapp_number") if has_field("Customer", "sc_whatsapp_number") else None
    if not mobile:
        mobile = frappe.db.get_value("Customer", customer, "mobile_no")
    if mobile:
        return mobile
    contact = frappe.db.get_value("Dynamic Link", {"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"}, "parent")
    if contact:
        return frappe.db.get_value("Contact Phone", {"parent": contact, "is_primary_mobile_no": 1}, "phone")
    return None


def normalize_phone(phone):
    value = (phone or "").strip().replace(" ", "")
    if not value:
        return ""
    if value.startswith("+"):
        return "+" + "".join(ch for ch in value[1:] if ch.isdigit())
    return "".join(ch for ch in value if ch.isdigit())


def parse_lines(value):
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def build_invoice_whatsapp_message(invoice):
    customer_name = invoice.customer_name or invoice.customer
    amount = f"{flt(invoice.grand_total):,.2f} {invoice.currency}"
    return f"""مرحباً {customer_name}،
شكراً لاختياركم الركن السويسري للساعات.

فاتورتكم جاهزة:
رقم الفاتورة: {invoice.name}
المبلغ الإجمالي: {amount}

تم إرفاق نسخة PDF من الفاتورة الضريبية مع هذه الرسالة.
لخدمة الضمان وما بعد البيع، يرجى الاحتفاظ برقم الفاتورة والأرقام التسلسلية الموضحة في الفاتورة.

نسعد بخدمتكم دائماً.
الركن السويسري للساعات
swisscorner.co

Dear {customer_name},
Thank you for shopping at Swiss Corner Watches.

Invoice No: {invoice.name}
Total Amount: {amount}

Your tax invoice PDF is attached.
Please keep the invoice and the watch serial number for warranty and after-sales service.

Swiss Corner Watches
swisscorner.co"""


def build_template_text():
    return """مرحباً {{ doc.customer_name or doc.customer }}،
شكراً لتسوقكم من الركن السويسري للساعات.
رقم فاتورتكم: {{ doc.name }}
المبلغ: {{ doc.grand_total }} {{ doc.currency }}
تم إرفاق الفاتورة الضريبية مع هذه الرسالة.
للضمان أو خدمة ما بعد البيع يرجى الاحتفاظ برقم الفاتورة والرقم التسلسلي للساعة.
نسعد بخدمتكم دائماً.

Dear {{ doc.customer_name or doc.customer }},
Thank you for shopping at Swiss Corner Watches.
Invoice No: {{ doc.name }}
Amount: {{ doc.grand_total }} {{ doc.currency }}
Your tax invoice is attached.
Please keep the invoice and watch serial number for warranty and after-sales service."""


def create_invoice_attachment(invoice_name):
    from whatsapp_connector.whatsapp_connector.utils.whatsapp import create_print_attachment_file

    return create_print_attachment_file(
        doctype="Sales Invoice",
        docname=invoice_name,
        print_format=PRINT_FORMAT,
        file_name=f"{invoice_name}-{PRINT_FORMAT}",
    )


def ensure_demo_whatsapp_session():
    if not frappe.db.exists("DocType", "WhatsApp Session"):
        return None
    existing = frappe.db.get_value("WhatsApp Session", {"session_name": "Swiss Corner Demo Dry Run"}, "name")
    if existing:
        return existing
    doc = frappe.get_doc(
        {
            "doctype": "WhatsApp Session",
            "session_name": "Swiss Corner Demo Dry Run",
            "status_text": "DEMO",
            "session_id": "swiss-corner-demo-dry-run",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def create_whatsapp_log(invoice, recipient, message, attachment_url, attachment_status, status, dry_run, error):
    session = ensure_demo_whatsapp_session()
    log = frappe.get_doc(
        {
            "doctype": "WhatsApp Message Log",
            "session": session,
            "recipient": recipient,
            "status": status,
            "message_type": "Document" if attachment_url else "Text",
            "message_content": message,
            "attachment": attachment_url,
            "error_message": error,
        }
    )
    set_if_field(log, "sc_reference_doctype", "Sales Invoice")
    set_if_field(log, "sc_reference_name", invoice.name)
    set_if_field(log, "sc_attachment_status", attachment_status)
    set_if_field(log, "sc_dry_run", dry_run)
    log.insert(ignore_permissions=True, ignore_mandatory=True)
    return log.name


def apply_whatsapp_log_metadata(log_name, invoice, attachment_status, dry_run, error):
    if not log_name or not frappe.db.exists("WhatsApp Message Log", log_name):
        return
    updates = {}
    if has_field("WhatsApp Message Log", "sc_reference_doctype"):
        updates["sc_reference_doctype"] = "Sales Invoice"
    if has_field("WhatsApp Message Log", "sc_reference_name"):
        updates["sc_reference_name"] = invoice.name
    if has_field("WhatsApp Message Log", "sc_attachment_status"):
        updates["sc_attachment_status"] = attachment_status
    if has_field("WhatsApp Message Log", "sc_dry_run"):
        updates["sc_dry_run"] = dry_run
    if error:
        updates["error_message"] = error
    if updates:
        frappe.db.set_value("WhatsApp Message Log", log_name, updates, update_modified=False)


def set_si_whatsapp_fields(invoice_name, status, log_name, dry_run, error):
    updates = {}
    if has_field("Sales Invoice", "sc_whatsapp_invoice_status"):
        updates["sc_whatsapp_invoice_status"] = status
    if has_field("Sales Invoice", "sc_whatsapp_invoice_log"):
        updates["sc_whatsapp_invoice_log"] = log_name
    if has_field("Sales Invoice", "sc_whatsapp_dry_run"):
        updates["sc_whatsapp_dry_run"] = dry_run
    if has_field("Sales Invoice", "sc_whatsapp_sent_at"):
        updates["sc_whatsapp_sent_at"] = now()
    if has_field("Sales Invoice", "sc_whatsapp_error"):
        updates["sc_whatsapp_error"] = error
    if updates:
        frappe.db.set_value("Sales Invoice", invoice_name, updates, update_modified=False)


def ensure_company_display_branding():
    """Keep the legal Company document safe while showing the demo brand clearly."""
    if not COMPANY or not frappe.db.exists("Company", COMPANY):
        return
    updates = {}
    if has_field("Company", "company_name"):
        updates["company_name"] = "الركن السويسري للساعات"
    if has_field("Company", "sc_company_arabic_name"):
        updates["sc_company_arabic_name"] = "الركن السويسري للساعات"
    if has_field("Company", "country"):
        updates["country"] = "Saudi Arabia"
    if has_field("Company", "default_currency"):
        updates["default_currency"] = "SAR"
    if updates:
        frappe.db.set_value("Company", COMPANY, updates, update_modified=False)
        frappe.clear_cache(doctype="Company")


def ensure_saudi_riyal_symbol():
    if frappe.db.exists("Currency", "SAR"):
        frappe.db.set_value("Currency", "SAR", "symbol", SAUDI_RIYAL_SYMBOL, update_modified=False)
        frappe.clear_cache(doctype="Currency")
    if frappe.db.exists("DocType", "Global Defaults"):
        defaults = frappe.get_single("Global Defaults")
        if has_field("Global Defaults", "default_currency"):
            defaults.default_currency = "SAR"
        if has_field("Global Defaults", "country"):
            defaults.country = "Saudi Arabia"
        save_doc(defaults)


def ensure_currency_display_metadata():
    """Force SAR context on common list/form currency fields used in the demo."""
    for dt in ("Sales Invoice", "POS Invoice"):
        for fieldname in ("grand_total", "rounded_total", "outstanding_amount", "paid_amount", "base_grand_total"):
            if has_field(dt, fieldname):
                ensure_property_setter(
                    doc_type=dt,
                    property_name="options",
                    value="SAR",
                    property_type="Data",
                    field_name=fieldname,
                )
        frappe.clear_cache(doctype=dt)


def ensure_property_setter(doc_type, property_name, value, property_type="Data", field_name=None):
    name = f"{doc_type}-{field_name or 'main'}-{property_name}"
    if frappe.db.exists("Property Setter", name):
        doc = frappe.get_doc("Property Setter", name)
    else:
        doc = frappe.get_doc({"doctype": "Property Setter", "name": name})
    doc.doctype_or_field = "DocField" if field_name else "DocType"
    doc.doc_type = doc_type
    doc.field_name = field_name
    doc.property = property_name
    doc.property_type = property_type
    doc.value = value
    doc.module = MODULE
    save_doc(doc)


def sc_money(value, currency="SAR"):
    text = frappe.utils.fmt_money(value or 0, currency=currency or "SAR")
    return (
        text.replace("SAR", SAUDI_RIYAL_SYMBOL)
        .replace("ر.س", SAUDI_RIYAL_SYMBOL)
        .replace("ريال", SAUDI_RIYAL_SYMBOL)
    )


def swiss_corner_print_css():
    return r"""
@font-face {
    font-family: "Cosma Saudi Riyal Symbol";
    src: url("/assets/demo_standard/fonts/Cairo-Regular-Saudi.ttf");
    unicode-range: U+00A7;
}
.print-format,
.print-format * {
    font-family: "Cosma Saudi Riyal Symbol", "InterVariable", "Inter", "Noto Sans Arabic", "Noto Naskh Arabic", "DejaVu Sans", Arial, sans-serif !important;
    letter-spacing: normal !important;
    word-spacing: normal !important;
}
.print-format { padding: 0.16in !important; background: #f6f1ea !important; }
.sc-invoice { color: #211c17; font-size: 10.5px; line-height: 1.55; direction: rtl; background: #fffdfa; padding: 10px; border: 1px solid #ead9c4; }
.sc-ltr { direction: ltr; text-align: left; }
.sc-rtl { direction: rtl; text-align: right; }
.sc-hero { width: 100%; border-collapse: collapse; background: #fff8ef; color: #211c17; border: 1px solid #e3c9a7; border-top: 6px solid #b87433; }
.sc-hero td { padding: 13px 16px; vertical-align: middle; }
.sc-logo { max-height: 54px; max-width: 190px; }
.sc-kicker { color: #9a6427; font-size: 10px; text-transform: uppercase; font-weight: 800; }
.sc-title { margin: 0; color: #211c17; font-size: 22px; font-weight: 900; }
.sc-subtitle { color: #6b6258; font-size: 11px; margin-top: 4px; }
.sc-strip { height: 6px; background: #b87433; }
.sc-panel { border: 1px solid #e6d7c3; background: #fffaf3; padding: 9px 10px; min-height: 76px; }
.sc-panel-title { color: #8a5a24; font-size: 10px; font-weight: 900; text-transform: uppercase; margin-bottom: 5px; }
.sc-meta { width: 100%; border-collapse: separate; border-spacing: 0 9px; margin: 11px 0 8px; }
.sc-meta td { width: 33.33%; padding: 0 4px; vertical-align: top; }
.sc-items { width: 100%; border-collapse: collapse; margin-top: 8px; table-layout: fixed; }
.sc-items th { background: #efe2d1; color: #211c17; border: 1px solid #dcc5a8; border-bottom: 2px solid #b87433; padding: 7px 5px; font-size: 9.5px; font-weight: 900; }
.sc-items td { border: 1px solid #ead9c4; padding: 7px 5px; vertical-align: top; word-wrap: break-word; background: #fffdfa; }
.sc-items tbody tr:nth-child(even) td { background: #fffaf3; }
.sc-muted { color: #6b6258; }
.sc-gold { color: #b87433; }
.sc-num { direction: ltr; text-align: left; white-space: nowrap; font-family: "Cosma Saudi Riyal Symbol", "Inter", "DejaVu Sans", Arial, sans-serif !important; }
.sc-totals { width: 46%; margin-right: auto; margin-left: 0; border-collapse: collapse; margin-top: 13px; background: #fffdfa; border: 1px solid #ead9c4; }
.sc-totals td { border-bottom: 1px solid #ead9c4; padding: 8px 9px; }
.sc-grand td { background: #b87433; color: #fff; font-weight: 900; border-bottom: 0; }
.sc-note { margin-top: 12px; border: 1px solid #ead9c4; border-right: 4px solid #b87433; background: #fffaf3; padding: 10px; font-size: 10px; color: #4b4036; }
.sc-stamp { border: 1px solid #b87433; color: #8a5a24; text-align: center; padding: 10px; font-weight: 900; background: #fff8ef; }
.sc-col-idx { width: 4%; }
.sc-col-item { width: 27%; }
.sc-col-serial { width: 18%; }
.sc-col-warranty { width: 14%; }
.sc-col-qty { width: 7%; }
.sc-col-rate { width: 11%; }
.sc-col-discount { width: 9%; }
.sc-col-amount { width: 10%; }
"""


def ensure_print_style():
    css = swiss_corner_print_css()
    if frappe.db.exists("Print Style", PRINT_STYLE):
        doc = frappe.get_doc("Print Style", PRINT_STYLE)
    else:
        doc = frappe.get_doc({"doctype": "Print Style", "print_style_name": PRINT_STYLE})
    doc.print_style_name = PRINT_STYLE
    doc.disabled = 0
    doc.css = css
    save_doc(doc)
    if frappe.db.exists("DocType", "Print Settings"):
        settings = frappe.get_single("Print Settings")
        if has_field("Print Settings", "print_style"):
            settings.print_style = PRINT_STYLE
            save_doc(settings)


def ensure_letter_head():
    logo = frappe.db.get_value("File", {"file_name": "swiss-corner-logo.webp"}, "file_url") or "/files/swiss-corner-logo.webp"
    content = f"""
<div style="width:100%; border-bottom:3px solid #b87433; padding-bottom:10px; margin-bottom:12px; font-family:'Cosma Saudi Riyal Symbol','Noto Sans Arabic',Arial,sans-serif;">
  <table style="width:100%; border-collapse:collapse;">
    <tr>
      <td style="width:42%; text-align:left; vertical-align:middle;">
        <img src="{logo}" style="height:54px; max-width:210px;">
      </td>
      <td style="width:58%; text-align:right; vertical-align:middle; direction:rtl;">
        <div style="font-size:20px; font-weight:800; color:#111;">الركن السويسري للساعات</div>
        <div style="font-size:11px; color:#8a5a24;">Swiss Corner Watches | swisscorner.co</div>
      </td>
    </tr>
  </table>
</div>
"""
    footer = """
<div style="border-top:1px solid #e6d7c3; padding-top:6px; font-size:9px; color:#6b6258; direction:rtl; text-align:center;">
  شكراً لتسوقكم من الركن السويسري للساعات | Thank you for shopping at Swiss Corner Watches
</div>
"""
    if frappe.db.exists("Letter Head", LETTER_HEAD):
        doc = frappe.get_doc("Letter Head", LETTER_HEAD)
    else:
        doc = frappe.get_doc({"doctype": "Letter Head", "letter_head_name": LETTER_HEAD})
    doc.letter_head_name = LETTER_HEAD
    doc.source = "HTML"
    doc.content = content
    doc.footer = footer
    doc.is_default = 1
    doc.disabled = 0
    save_doc(doc)
    frappe.db.set_value("Letter Head", LETTER_HEAD, {"source": "HTML", "content": content, "footer": footer}, update_modified=False)
    if COMPANY and frappe.db.exists("Company", COMPANY) and has_field("Company", "default_letter_head"):
        frappe.db.set_value("Company", COMPANY, "default_letter_head", LETTER_HEAD, update_modified=False)
        frappe.clear_cache(doctype="Company")


def ensure_default_print_settings():
    if frappe.db.exists("DocType", "Print Settings"):
        settings = frappe.get_single("Print Settings")
        if has_field("Print Settings", "print_style"):
            settings.print_style = PRINT_STYLE
        if has_field("Print Settings", "with_letterhead"):
            settings.with_letterhead = 1
        save_doc(settings)
    property_name = "Sales Invoice-main-default_print_format"
    if frappe.db.exists("Property Setter", property_name):
        setter = frappe.get_doc("Property Setter", property_name)
    else:
        setter = frappe.get_doc({"doctype": "Property Setter", "name": property_name})
    setter.doctype_or_field = "DocType"
    setter.doc_type = "Sales Invoice"
    setter.property = "default_print_format"
    setter.property_type = "Data"
    setter.value = PRINT_FORMAT
    setter.module = MODULE
    save_doc(setter)
    frappe.clear_cache(doctype="Sales Invoice")


def ensure_print_format():
    html_body = r"""
<style>
""" + swiss_corner_print_css() + r"""
</style>
{% set logo = frappe.db.get_value("File", {"file_name": "swiss-corner-logo.webp"}, "file_url") or "/files/swiss-corner-logo.webp" %}
{% set whatsapp = frappe.db.get_value("Customer", doc.customer, "sc_whatsapp_number") or frappe.db.get_value("Customer", doc.customer, "mobile_no") or doc.contact_mobile or "" %}
{% set company_ar = "الركن السويسري للساعات" %}
{% set company_en = "Swiss Corner Watches" %}
{% macro money(value) -%}
{{ frappe.utils.fmt_money(value or 0, currency=doc.currency).replace("SAR", "§").replace("ر.س", "§").replace("ريال", "§") }}
{%- endmacro %}
<div class="sc-invoice">
  <table class="sc-hero">
    <tr>
      <td class="sc-ltr" style="width: 42%;">
        <img class="sc-logo" src="{{ logo }}">
        <div class="sc-subtitle">swisscorner.co | Saudi Retail POS Demo</div>
      </td>
      <td class="sc-rtl" style="width: 58%;">
        <div class="sc-kicker">فاتورة مبيعات</div>
        <h1 class="sc-title">{{ company_ar }}</h1>
        <div class="sc-subtitle">{{ company_en }} - Tax Invoice / Demo</div>
      </td>
    </tr>
  </table>

  <table class="sc-meta">
    <tr>
      <td>
        <div class="sc-panel">
          <div class="sc-panel-title">بيانات الفاتورة</div>
          <b>{{ doc.name }}</b><br>
          التاريخ: {{ doc.posting_date }} {{ doc.posting_time or "" }}<br>
          الفرع: {{ doc.sc_branch or doc.cost_center or "-" }}<br>
          العملة: <span class="sc-num">{{ doc.currency }}</span>
        </div>
      </td>
      <td>
        <div class="sc-panel">
          <div class="sc-panel-title">العميل</div>
          <b>{{ doc.customer_name or doc.customer }}</b><br>
          رقم الجوال: <span class="sc-num">{{ whatsapp or "-" }}</span><br>
          المجموعة: {{ doc.customer_group or "-" }}
        </div>
      </td>
      <td>
        <div class="sc-panel">
          <div class="sc-panel-title">الدفع والضريبة</div>
          {% if doc.payments %}
            {% for p in doc.payments %}{{ p.mode_of_payment }}: <span class="sc-num">{{ money(p.amount) }}</span><br>{% endfor %}
          {% else %}
            طريقة الدفع: {{ doc.mode_of_payment or "-" }}<br>
          {% endif %}
          VAT: <span class="sc-num">{{ money(doc.total_taxes_and_charges) }}</span>
        </div>
      </td>
    </tr>
  </table>

  <table class="sc-items">
    <colgroup>
      <col class="sc-col-idx">
      <col class="sc-col-item">
      <col class="sc-col-serial">
      <col class="sc-col-warranty">
      <col class="sc-col-qty">
      <col class="sc-col-rate">
      <col class="sc-col-discount">
      <col class="sc-col-amount">
    </colgroup>
    <thead>
      <tr>
        <th>#</th>
        <th>الصنف / Item</th>
        <th>الأرقام التسلسلية</th>
        <th>الضمان</th>
        <th class="sc-num">الكمية</th>
        <th class="sc-num">السعر</th>
        <th class="sc-num">الخصم</th>
        <th class="sc-num">الإجمالي</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr>
        <td class="sc-num">{{ row.idx }}</td>
        <td>
          <b>{{ row.item_name }}</b><br>
          <span class="sc-muted sc-ltr">{{ row.item_code }}</span>
        </td>
        <td class="sc-ltr">{{ (row.serial_no or "-").replace("\n", "<br>") }}</td>
        <td>
          {% if row.sc_warranty_start or row.sc_warranty_end %}
            {{ row.sc_warranty_start or "-" }}<br><span class="sc-muted">إلى {{ row.sc_warranty_end or "-" }}</span>
          {% else %}-{% endif %}
        </td>
        <td class="sc-num">{{ row.qty }}</td>
        <td class="sc-num">{{ money(row.rate) }}</td>
        <td class="sc-num">{{ money(row.discount_amount or 0) }}</td>
        <td class="sc-num"><b>{{ money(row.amount) }}</b></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <table class="sc-totals">
    <tr><td>الصافي / Net Total</td><td class="sc-num">{{ money(doc.net_total) }}</td></tr>
    <tr><td>الخصم / Discount</td><td class="sc-num">{{ money(doc.discount_amount or 0) }}</td></tr>
    <tr><td>ضريبة القيمة المضافة / VAT</td><td class="sc-num">{{ money(doc.total_taxes_and_charges) }}</td></tr>
    <tr class="sc-grand"><td>الإجمالي / Grand Total</td><td class="sc-num">{{ money(doc.grand_total) }}</td></tr>
  </table>

  <table style="width:100%; margin-top:14px; border-collapse:collapse;">
    <tr>
      <td style="width:62%; vertical-align:top;">
        <div class="sc-note">
          شروط الضمان المختصرة: يرجى الاحتفاظ بالفاتورة والرقم التسلسلي للساعة. يغطي الضمان عيوب التصنيع ولا يشمل سوء الاستخدام أو الكسر أو التلف الناتج عن الماء خارج درجة المقاومة المحددة.
          <br>شكراً لتسوقكم من الركن السويسري للساعات. نسعد بخدمتكم دائماً.
        </div>
      </td>
      <td style="width:20%; vertical-align:top; padding-right:8px;">
        {% if doc.ksa_einv_qr %}<img src="{{ doc.ksa_einv_qr }}" style="width:88px;">{% endif %}
      </td>
      <td style="width:18%; vertical-align:top;">
        <div class="sc-stamp">Swiss Corner<br>Watches</div>
      </td>
    </tr>
  </table>
</div>
"""
    if frappe.db.exists("Print Format", PRINT_FORMAT):
        doc = frappe.get_doc("Print Format", PRINT_FORMAT)
    else:
        doc = frappe.get_doc({"doctype": "Print Format", "name": PRINT_FORMAT})
    doc.print_format_for = "DocType"
    doc.doc_type = "Sales Invoice"
    doc.module = MODULE
    doc.standard = "No"
    doc.custom_format = 1
    doc.print_format_type = "Jinja"
    doc.disabled = 0
    doc.html = html_body
    doc.margin_top = 6
    doc.margin_bottom = 6
    doc.margin_left = 6
    doc.margin_right = 6
    if has_field("Print Format", "print_style"):
        doc.print_style = PRINT_STYLE
    save_doc(doc)


def ensure_client_scripts():
    sales_script = """
frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('إرسال الفاتورة واتساب'), () => {
                frappe.call({
                    method: 'demo_standard.swiss_corner_demo.send_sales_invoice_whatsapp_now',
                    args: { invoice_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __('جاري تجهيز رسالة واتساب والفاتورة PDF...'),
                    callback(r) {
                        const data = r.message || {};
                        const status = data.status || frm.doc.sc_whatsapp_invoice_status || 'Queued';
                        const dry = data.dry_run ? ' - Dry Run' : '';
                        frappe.show_alert({ message: __('WhatsApp Invoice: ') + status + dry, indicator: data.error ? 'red' : 'green' });
                        frm.reload_doc();
                    }
                });
            }, __('WhatsApp'));
        }
    },
    validate(frm) {
        if (!frm.doc.items) return;
        const missing = frm.doc.items.filter(row => (row.item_code || '').startsWith('DEMO-SC-WATCH') && !row.serial_no);
        if (missing.length) {
            frappe.msgprint(__('Swiss Corner demo watch items should include Serial Numbers before submit.'));
        }
        if (frm.doc.sc_enable_whatsapp_invoice_notification && frm.doc.customer && !frm.doc.contact_mobile) {
            frappe.show_alert({message: __('ضع رقم الواتساب في بطاقة العميل أو رقم الجوال قبل إرسال الفاتورة.'), indicator: 'orange'});
        }
    }
});
"""
    ensure_client_script("Swiss Corner - Sales Invoice Serial and WhatsApp Hint", "Sales Invoice", sales_script, view="Form")

    list_script = r"""
(function () {
    const SAR_SYMBOL = "\u00A7";
    const money = (value) => {
        const amount = Number(value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        return `<span class="demo-saudi-currency">${SAR_SYMBOL} ${amount}</span>`;
    };
    const normalize = () => {
        document.querySelectorAll(".list-row, .list-row-head, .datatable, .report-wrapper").forEach((el) => {
            if (el.innerHTML && el.innerHTML.includes("$")) {
                el.innerHTML = el.innerHTML.replace(/\$/g, SAR_SYMBOL);
            }
        });
    };
    frappe.listview_settings["Sales Invoice"] = Object.assign(frappe.listview_settings["Sales Invoice"] || {}, {
        formatters: Object.assign((frappe.listview_settings["Sales Invoice"] || {}).formatters || {}, {
            grand_total(value) {
                return money(value);
            },
            rounded_total(value) {
                return money(value);
            },
            outstanding_amount(value) {
                return money(value);
            }
        }),
        onload(listview) {
            setTimeout(normalize, 150);
            listview.page.wrapper.on("render_complete", () => setTimeout(normalize, 50));
        },
        refresh() {
            setTimeout(normalize, 150);
        }
    });
})();
"""
    ensure_client_script("Swiss Corner - Sales Invoice SAR List Formatter", "Sales Invoice", list_script, view="List")
    ensure_client_script(
        "Swiss Corner - POS Invoice SAR List Formatter",
        "POS Invoice",
        list_script.replace('"Sales Invoice"', '"POS Invoice"').replace("Sales Invoice", "POS Invoice"),
        view="List",
    )


def resolve_customer_mobile(customer):
    mobile = None
    if has_field("Customer", "sc_whatsapp_number"):
        mobile = frappe.db.get_value("Customer", customer, "sc_whatsapp_number")
    if mobile:
        return mobile
    mobile = frappe.db.get_value("Customer", customer, "mobile_no")
    if mobile:
        return mobile
    contact = frappe.db.get_value("Dynamic Link", {"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"}, "parent")
    if contact:
        return frappe.db.get_value("Contact Phone", {"parent": contact, "is_primary_mobile_no": 1}, "phone")
    return None


@frappe.whitelist()
def send_sales_invoice_whatsapp_now(invoice_name):
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    if invoice.docstatus != 1:
        frappe.throw("لا يمكن إرسال واتساب إلا بعد اعتماد فاتورة المبيعات.")
    if not cint(invoice.get("sc_enable_whatsapp_invoice_notification", 1)):
        frappe.throw("إشعار واتساب غير مفعّل لهذه الفاتورة.")
    log_name = process_whatsapp_invoice_notification(invoice.name)
    invoice.reload()
    return {
        "invoice": invoice.name,
        "log": log_name,
        "status": invoice.get("sc_whatsapp_invoice_status"),
        "dry_run": cint(invoice.get("sc_whatsapp_dry_run")),
        "error": invoice.get("sc_whatsapp_error"),
    }


def boot_session(bootinfo):
    """Make SAR formatting deterministic in Desk boot data."""
    try:
        bootinfo.sysdefaults = bootinfo.get("sysdefaults") or {}
        bootinfo.sysdefaults["currency"] = "SAR"
        bootinfo.currency_symbols = bootinfo.get("currency_symbols") or {}
        bootinfo.currency_symbols["SAR"] = SAUDI_RIYAL_SYMBOL
        currency_info = bootinfo.get("currency_info") or {}
        if currency_info.get("SAR"):
            currency_info["SAR"]["symbol"] = SAUDI_RIYAL_SYMBOL
        bootinfo.currency_info = currency_info
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Swiss Corner SAR Boot Patch Failed")


def cleanup_posawesome_customizations():
    """Remove leftover POS Awesome customizations from this site only."""
    removed = {
        "custom_fields": [],
        "property_setters": [],
        "client_scripts": [],
        "custom_scripts": [],
        "workspaces": [],
    }
    touched_doctypes = set()

    custom_fields = frappe.get_all(
        "Custom Field",
        filters=[["fieldname", "like", "posa%"]],
        fields=["name", "dt"],
        limit_page_length=1000,
    )
    for row in custom_fields:
        if row.dt:
            touched_doctypes.add(row.dt)
        frappe.delete_doc("Custom Field", row.name, ignore_permissions=True, force=True)
        removed["custom_fields"].append(row.name)

    property_setters = frappe.get_all(
        "Property Setter",
        filters=[["name", "like", "%posa%"]],
        fields=["name", "doc_type"],
        limit_page_length=1000,
    )
    for row in property_setters:
        if row.doc_type:
            touched_doctypes.add(row.doc_type)
        frappe.delete_doc("Property Setter", row.name, ignore_permissions=True, force=True)
        removed["property_setters"].append(row.name)

    client_scripts = frappe.get_all(
        "Client Script",
        filters=[["name", "like", "%POSA%"]],
        fields=["name", "dt"],
        limit_page_length=1000,
    )
    for row in client_scripts:
        if row.dt:
            touched_doctypes.add(row.dt)
        frappe.delete_doc("Client Script", row.name, ignore_permissions=True, force=True)
        removed["client_scripts"].append(row.name)

    if frappe.db.exists("DocType", "Custom Script"):
        custom_scripts = frappe.get_all(
            "Custom Script",
            filters=[["name", "like", "%POSA%"]],
            fields=["name", "dt"],
            limit_page_length=1000,
        )
        for row in custom_scripts:
            if row.dt:
                touched_doctypes.add(row.dt)
            frappe.delete_doc("Custom Script", row.name, ignore_permissions=True, force=True)
            removed["custom_scripts"].append(row.name)

    workspaces = frappe.get_all(
        "Workspace",
        filters=[["title", "like", "%POS Awesome%"]],
        fields=["name"],
        limit_page_length=1000,
    )
    for row in workspaces:
        frappe.delete_doc("Workspace", row.name, ignore_permissions=True, force=True)
        removed["workspaces"].append(row.name)

    frappe.db.commit()
    for doctype in sorted(touched_doctypes):
        frappe.clear_cache(doctype=doctype)
    frappe.clear_cache()
    return {
        "removed": removed,
        "counts": {key: len(value) for key, value in removed.items()},
        "touched_doctypes": sorted(touched_doctypes),
    }


def reset_swiss_corner_demo_passwords(password="SwissCorner@2026"):
    """Reset only Swiss Corner demo users to a shared temporary password."""
    from frappe.utils.password import update_password

    users = [
        "demo_manager@swisscorner.demo",
        "demo_accountant@swisscorner.demo",
        "demo_inventory@swisscorner.demo",
        "cashier_demo@swisscorner.demo",
        "cashier_backup@swisscorner.demo",
        "cashier_riyadh@swisscorner.demo",
        "cashier_jeddah@swisscorner.demo",
        "cashier_khobar@swisscorner.demo",
        "cashier_madinah@swisscorner.demo",
        "cashier_online@swisscorner.demo",
        "cashier_khamis@swisscorner.demo",
    ]
    updated = []
    missing = []
    for user in users:
        if not frappe.db.exists("User", user):
            missing.append(user)
            continue
        frappe.db.set_value("User", user, "enabled", 1, update_modified=False)
        frappe.db.set_value("User", user, "desk_theme", "Light", update_modified=False)
        update_password(user, password, logout_all_sessions=True)
        updated.append(user)
    frappe.db.commit()
    return {"updated": updated, "missing": missing, "password": password}


def hide_posnext_compat_posa_fields():
    """Hide POSNext compatibility fields that still use the legacy posa_ prefix."""
    fieldnames = [
        "posa_pos_opening_shift",
        "posa_is_printed",
        "posa_block_sale_beyond_available_qty",
        "posa_allow_delete",
        "posa_cash_mode_of_payment",
    ]
    rows = frappe.get_all(
        "Custom Field",
        filters=[["fieldname", "in", fieldnames]],
        fields=["name", "dt", "fieldname"],
        limit_page_length=1000,
    )
    updated = []
    touched_doctypes = set()
    for row in rows:
        doc = frappe.get_doc("Custom Field", row.name)
        doc.hidden = 1
        doc.print_hide = 1
        doc.no_copy = 1
        doc.in_list_view = 0
        doc.in_standard_filter = 0
        doc.in_preview = 0
        save_doc(doc)
        if row.dt:
            touched_doctypes.add(row.dt)
        updated.append(row.name)
    frappe.db.commit()
    for doctype in sorted(touched_doctypes):
        frappe.clear_cache(doctype=doctype)
    frappe.clear_cache()
    return {"hidden": updated, "count": len(updated), "touched_doctypes": sorted(touched_doctypes)}


def setup_posnext_swiss_corner_showcase():
    """Configure POSNext demo data for Swiss Corner POS walkthroughs."""
    if "pos_next" not in frappe.get_installed_apps():
        frappe.throw("POSNext is not installed on this site.")

    accounts = ensure_company_and_accounts()
    ensure_posnext_roles()
    wallet_mop = ensure_posnext_wallet_mode(accounts)
    loyalty_program = ensure_posnext_loyalty_program(accounts)
    campaign = ensure_posnext_campaign()

    profiles = [b for b in BRANCHES + [CLIENT_SAMPLE_BRANCH] if b.get("pos_profile") and frappe.db.exists("POS Profile", b["pos_profile"])]
    updated_profiles = []
    settings = []
    shifts = []
    for branch in profiles:
        updated_profiles.append(configure_posnext_profile(branch, accounts, wallet_mop))
        settings.append(ensure_posnext_settings(branch["pos_profile"], accounts, loyalty_program))
        if branch.get("cashier"):
            shifts.append(ensure_posnext_open_shift(branch, accounts))

    offers = ensure_posnext_promotions_and_coupons(campaign)
    wallets = ensure_posnext_customer_wallets(accounts)
    hide_result = hide_posnext_compat_posa_fields()
    frappe.db.commit()
    frappe.clear_cache()
    return {
        "pos_profiles": updated_profiles,
        "pos_settings": settings,
        "open_shifts": shifts,
        "offers_and_coupons": offers,
        "wallets": wallets,
        "hidden_posa_fields": hide_result,
    }


def setup_posnext_pos_display_fixes():
    """Polish POSNext storefront data for cashier demo use."""
    if "pos_next" not in frappe.get_installed_apps():
        frappe.throw("POSNext is not installed on this site.")

    accounts = ensure_company_and_accounts()
    permissions = ensure_posnext_cashier_serial_bundle_permissions()
    receipt = ensure_posnext_receipt_print_format()
    whatsapp = ensure_whatsapp_client_demo_settings()
    updated_profiles = ensure_posnext_profile_item_visibility()
    extra_stock = ensure_posnext_branch_demo_stock(accounts)
    frappe.db.commit()
    frappe.clear_cache()
    return {
        "updated_profiles": updated_profiles,
        "extra_stock": extra_stock,
        "receipt": receipt,
        "whatsapp": whatsapp,
        "permissions": permissions,
    }


def ensure_posnext_cashier_serial_bundle_permissions():
    """Allow POSNext cashiers to complete serialized-item sales without broad stock access."""
    doctype = "Serial and Batch Bundle"
    role = "POSNext Cashier"
    if not frappe.db.exists("DocType", doctype):
        return {"status": "missing_doctype", "doctype": doctype}
    if not frappe.db.exists("Role", role):
        return {"status": "missing_role", "role": role}

    from frappe.permissions import add_permission, update_permission_property

    if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
        add_permission(doctype, role, 0)
    for permission_type in ("read", "write", "create", "submit", "cancel"):
        update_permission_property(doctype, role, 0, permission_type, 1)
    for permission_type in ("delete", "amend"):
        update_permission_property(doctype, role, 0, permission_type, 0)
    frappe.clear_cache(doctype=doctype)
    return {"status": "updated", "doctype": doctype, "role": role}


def fix_posnext_cashier_payment_and_whatsapp():
    """Keep sales-person capture visible but optional, and enable WhatsApp invoice logging."""
    updated_settings = []
    if frappe.db.exists("DocType", "POS Settings"):
        for row in frappe.get_all("POS Settings", fields=["name", "pos_profile"], limit_page_length=500):
            frappe.db.set_value("POS Settings", row.name, "enable_sales_persons", "Multiple", update_modified=False)
            updated_settings.append({"name": row.name, "pos_profile": row.pos_profile})

    if frappe.db.exists("DocType", "WhatsApp Connector Settings"):
        settings = frappe.get_single("WhatsApp Connector Settings")
        if has_field("WhatsApp Connector Settings", "sc_enable_invoice_notification"):
            settings.sc_enable_invoice_notification = 1
        if has_field("WhatsApp Connector Settings", "sc_invoice_print_format"):
            settings.sc_invoice_print_format = PRINT_FORMAT
        settings.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()
    return {
        "pos_settings_sales_persons_optional_multiple": updated_settings,
        "whatsapp_invoice_hook": "immediate_with_background_idempotency",
        "whatsapp_mobile_priority": "Customer.sc_whatsapp_number then Customer.mobile_no",
    }


def setup_swiss_corner_client_cashier_demo(password="demo@2026"):
    """Create two customer-facing cashier users and make the main one demo-rich."""
    if "pos_next" not in frappe.get_installed_apps():
        frappe.throw("POSNext is not installed on this site.")

    from frappe.utils.password import update_password

    accounts = ensure_company_and_accounts()
    setup_posnext_pos_display_fixes()

    main_user = "cashier_demo@swisscorner.demo"
    backup_user = "cashier_backup@swisscorner.demo"
    active_users = [main_user, backup_user]
    old_cashiers = [
        "cashier_riyadh@swisscorner.demo",
        "cashier_jeddah@swisscorner.demo",
        "cashier_khobar@swisscorner.demo",
        "cashier_madinah@swisscorner.demo",
        "cashier_online@swisscorner.demo",
        "cashier_khamis@swisscorner.demo",
    ]

    roles = ["Desk User", "Sales User", "Cashier", "POSNext Cashier", "Demo Viewer"]
    ensure_user(main_user, "cashier_demo", "Swiss Corner Demo Cashier", roles, accounts)
    ensure_user(backup_user, "cashier_backup", "Swiss Corner Backup Cashier", roles, accounts)

    for user in active_users:
        frappe.db.set_value("User", user, "enabled", 1, update_modified=False)
        frappe.db.set_value("User", user, "desk_theme", "Light", update_modified=False)
        update_password(user, password, logout_all_sessions=True)

    disabled = []
    for user in old_cashiers:
        if frappe.db.exists("User", user):
            frappe.db.set_value("User", user, "enabled", 0, update_modified=False)
            disabled.append(user)

    profile_name = BRANCHES[0]["pos_profile"]
    profile = frappe.get_doc("POS Profile", profile_name)
    profile.set("applicable_for_users", [{"user": user} for user in active_users])
    groups = frappe.get_all(
        "Item Group",
        filters={"name": ["like", f"{PREFIX} - %"], "is_group": 0},
        pluck="name",
        order_by="name",
        limit_page_length=200,
    )
    if groups:
        profile.set("item_groups", [{"item_group": group} for group in groups])
    if has_field("POS Profile", "custom_brands_table"):
        profile.set("custom_brands_table", [])
    if has_field("POS Profile", "hide_unavailable_items"):
        profile.hide_unavailable_items = 1
    if has_field("POS Profile", "posa_block_sale_beyond_available_qty"):
        profile.posa_block_sale_beyond_available_qty = 1
    save_doc(profile)

    openings = []
    for user in active_users:
        branch = dict(BRANCHES[0])
        branch["cashier"] = user
        openings.append(ensure_posnext_open_shift(branch, accounts))

    frappe.db.commit()
    frappe.clear_cache()
    return {
        "main_user": main_user,
        "backup_user": backup_user,
        "password": password,
        "pos_profile": profile_name,
        "open_shifts": openings,
        "disabled_old_cashiers": disabled,
    }


def ensure_posnext_receipt_print_format():
    """Brand the compact POSNext receipt for Swiss Corner cashier printing."""
    name = "POS Next Receipt"
    if not frappe.db.exists("Print Format", name):
        return "missing"
    doc = frappe.get_doc("Print Format", name)
    doc.doc_type = "Sales Invoice"
    doc.custom_format = 1
    doc.print_format_type = "Jinja"
    doc.default_print_language = "ar"
    doc.html = POSNEXT_RECEIPT_HTML
    save_doc(doc)
    return name


def ensure_whatsapp_client_demo_settings():
    """Use the connected demo WhatsApp session when available, guarded by allowed numbers."""
    if not frappe.db.exists("DocType", "WhatsApp Connector Settings"):
        return {"status": "missing_settings"}
    settings = frappe.get_single("WhatsApp Connector Settings")
    if has_field("WhatsApp Connector Settings", "sc_enable_invoice_notification"):
        settings.sc_enable_invoice_notification = 1
    if has_field("WhatsApp Connector Settings", "sc_invoice_print_format"):
        settings.sc_invoice_print_format = PRINT_FORMAT
    if has_field("WhatsApp Connector Settings", "sc_demo_dry_run_only"):
        settings.sc_demo_dry_run_only = 0
    connected = None
    if frappe.db.exists("DocType", "WhatsApp Session"):
        connected = frappe.db.get_value("WhatsApp Session", {"status_text": "CONNECTED"}, "name", order_by="modified desc")
    if connected and has_field("WhatsApp Connector Settings", "default_session"):
        settings.default_session = connected
    if has_field("WhatsApp Connector Settings", "sc_allowed_demo_numbers") and not settings.get("sc_allowed_demo_numbers"):
        settings.sc_allowed_demo_numbers = "\n".join(sorted(SAFE_DEMO_NUMBERS))
    settings.save(ignore_permissions=True)
    return {"default_session": connected or settings.get("default_session"), "dry_run_only": cint(settings.get("sc_demo_dry_run_only"))}


POSNEXT_RECEIPT_HTML = r"""
<style>
@page { size: 80mm auto; margin: 0; }
@font-face {
    font-family: "SwissCornerSAR";
    src: url("/assets/universal_standard/fonts/Cairo-Regular-Saudi.ttf") format("truetype"),
         url("https://cdn.jsdelivr.net/gh/UsmanSanawar/Cairo-with-Saudi-Currency@main/Cairo-Regular-Saudi.ttf") format("truetype");
    unicode-range: U+00A7;
}
body {
    width: 80mm;
    max-width: 80mm;
    margin: 0 auto;
    padding: 8px 10px;
    background: #fffaf3;
    color: #111;
    font-family: "SwissCornerSAR", "Noto Sans Arabic", "DejaVu Sans", Arial, sans-serif;
    font-size: 10.5px;
    line-height: 1.45;
}
.sc-center { text-align: center; }
.sc-logo { max-width: 48mm; max-height: 18mm; margin: 0 auto 4px; display: block; }
.sc-title-ar { font-size: 15px; font-weight: 800; margin-top: 2px; }
.sc-title-en { font-size: 10px; font-weight: 700; letter-spacing: .2px; }
.sc-gold { color: #b87433; }
.sc-muted { color: #666; }
.sc-divider { border-top: 1px dashed #8c7358; margin: 9px 0; }
.sc-solid { border-top: 2px solid #111; margin: 9px 0; }
.sc-row { display: table; width: 100%; margin: 3px 0; }
.sc-row span:first-child { display: table-cell; width: 54%; text-align: left; }
.sc-row span:last-child { display: table-cell; width: 46%; text-align: right; font-weight: 700; }
.sc-info { direction: rtl; text-align: right; font-size: 10px; }
.sc-item { margin-bottom: 8px; }
.sc-item-name { font-weight: 800; font-size: 10.5px; direction: rtl; text-align: right; }
.sc-item-code { color: #666; font-size: 9px; direction: ltr; text-align: left; }
.sc-serial { background: #f3eadf; border: 1px solid #e1cdb6; border-radius: 4px; padding: 4px; margin-top: 4px; direction: ltr; }
.sc-total span { font-size: 14px; font-weight: 900; }
.sc-footer { text-align: center; font-size: 9px; color: #5a4a3b; }
.sc-thanks { font-size: 11px; font-weight: 800; color: #111; }
@media print { body { padding: 5mm; } }
</style>

{%- set currency_symbol = frappe.db.get_value("Currency", doc.currency, "symbol") or doc.currency -%}
{%- set whatsapp = frappe.db.get_value("Customer", doc.customer, "sc_whatsapp_number") or frappe.db.get_value("Customer", doc.customer, "mobile_no") or doc.contact_mobile or "" -%}
{%- set branch = doc.get("sc_branch") -%}
{%- if not branch and doc.pos_profile -%}
    {%- set branch = frappe.db.get_value("POS Profile", doc.pos_profile, "sc_branch") -%}
{%- endif -%}

<div class="sc-center">
    <img class="sc-logo" src="/files/swiss-corner-logo.webp">
    <div class="sc-title-ar">الركن السويسري للساعات</div>
    <div class="sc-title-en">SWISS CORNER WATCHES</div>
    <div class="sc-gold" style="font-size: 10px; font-weight: 700;">TAX INVOICE / فاتورة ضريبية</div>
    <div class="sc-muted">Saudi Retail POS Demo</div>
</div>

<div class="sc-divider"></div>

<div class="sc-info">
    <b>رقم الفاتورة:</b> <span dir="ltr">{{ doc.name }}</span><br>
    <b>التاريخ:</b> <span dir="ltr">{{ doc.posting_date }} {{ (doc.posting_time|string).split(".")[0] if doc.posting_time else "" }}</span><br>
    <b>العميل:</b> {{ doc.customer_name or doc.customer }}<br>
    <b>الجوال / واتساب:</b> <span dir="ltr">{{ whatsapp or "-" }}</span><br>
    {%- if branch -%}<b>الفرع:</b> {{ branch }}<br>{%- endif -%}
</div>

<div class="sc-divider"></div>

{%- for item in doc.items -%}
<div class="sc-item">
    <div class="sc-item-name">{{ item.item_name }}</div>
    <div class="sc-item-code">{{ item.item_code }}</div>
    <div class="sc-row">
        <span>{{ "%.0f"|format(item.qty) }} x {{ currency_symbol }} {{ "%.2f"|format(item.rate or item.price_list_rate or 0) }}</span>
        <span>{{ currency_symbol }} {{ "%.2f"|format(item.amount or (item.qty * (item.rate or item.price_list_rate or 0))) }}</span>
    </div>
    {%- if item.discount_amount or item.discount_percentage -%}
    <div class="sc-row sc-muted">
        <span>Discount / الخصم</span>
        <span>{{ currency_symbol }} {{ "%.2f"|format(item.discount_amount or 0) }}</span>
    </div>
    {%- endif -%}
    {%- if item.serial_no -%}
    <div class="sc-serial">
        <b>Serial No:</b><br>{{ item.serial_no | replace("\n", "<br>") }}
    </div>
    {%- endif -%}
</div>
{%- endfor -%}

<div class="sc-divider"></div>

<div class="sc-row"><span>Subtotal / الصافي</span><span>{{ currency_symbol }} {{ "%.2f"|format(doc.net_total or doc.total or 0) }}</span></div>
{%- if doc.discount_amount -%}
<div class="sc-row"><span>Discount / الخصم</span><span>{{ currency_symbol }} {{ "%.2f"|format(doc.discount_amount or 0) }}</span></div>
{%- endif -%}
<div class="sc-row"><span>VAT / الضريبة</span><span>{{ currency_symbol }} {{ "%.2f"|format(doc.total_taxes_and_charges or 0) }}</span></div>
<div class="sc-solid"></div>
<div class="sc-row sc-total"><span>TOTAL / الإجمالي</span><span>{{ currency_symbol }} {{ "%.2f"|format(doc.grand_total or 0) }}</span></div>

{%- if doc.payments -%}
<div class="sc-divider"></div>
<div style="font-weight:800;">Payments / المدفوعات</div>
{%- for payment in doc.payments -%}
<div class="sc-row"><span>{{ payment.mode_of_payment }}</span><span>{{ currency_symbol }} {{ "%.2f"|format(payment.amount or 0) }}</span></div>
{%- endfor -%}
{%- endif -%}

<div class="sc-solid"></div>
<div class="sc-footer">
    <div class="sc-thanks">شكراً لتسوقكم من الركن السويسري</div>
    <div>Thank you for shopping at Swiss Corner Watches</div>
    <div>احتفظ بالفاتورة والرقم التسلسلي للضمان وخدمة ما بعد البيع.</div>
    <div>swisscorner.co</div>
</div>
"""


def ensure_posnext_profile_item_visibility():
    updated = []
    groups = frappe.get_all(
        "Item Group",
        filters={"name": ["like", f"{PREFIX} - %"], "is_group": 0},
        pluck="name",
        order_by="name",
        limit_page_length=200,
    )
    profile_branches = [b for b in BRANCHES + [CLIENT_SAMPLE_BRANCH] if b.get("pos_profile") and frappe.db.exists("POS Profile", b["pos_profile"])]
    for branch in profile_branches:
        profile = frappe.get_doc("POS Profile", branch["pos_profile"])
        if groups:
            profile.set("item_groups", [{"item_group": group} for group in groups])
        if has_field("POS Profile", "hide_unavailable_items"):
            profile.hide_unavailable_items = 1
        if has_field("POS Profile", "posa_block_sale_beyond_available_qty"):
            profile.posa_block_sale_beyond_available_qty = 1
        if has_field("POS Profile", "custom_brands_table"):
            profile.set("custom_brands_table", [])
        save_doc(profile)
        updated.append(profile.name)
    return updated


def ensure_posnext_branch_demo_stock(accounts):
    marker = f"{MARKER} POSNext storefront extra stock"
    if frappe.db.exists("Stock Entry", {"remarks": ["like", f"%{marker}%"], "docstatus": 1}):
        return "already_exists"

    wh = get_warehouse_map()
    cc = get_cost_center_map()
    doc = frappe.new_doc("Stock Entry")
    doc.stock_entry_type = "Material Receipt"
    doc.company = COMPANY
    doc.posting_date = today()
    doc.posting_time = "10:30:00"
    doc.set_posting_time = 1
    doc.remarks = f"{marker} - richer POS grid and serial selection"

    branch_keys = ["riyadh", "jeddah", "khobar", "madinah", "online"]
    client_rows = CLIENT_SAMPLE_ITEMS[:20]
    for branch_key in branch_keys:
        warehouse = wh.get(branch_key)
        if not warehouse:
            continue
        for idx, row in enumerate(client_rows, start=1):
            item_code = client_sample_item_code(row["alt"])
            if not frappe.db.exists("Item", item_code):
                continue
            serial = f"{MARKER}-PX-{branch_key.upper()}-{safe_serial(row['alt'])}-{idx:02d}"
            if frappe.db.exists("Serial No", serial):
                continue
            doc.append(
                "items",
                {
                    "item_code": item_code,
                    "qty": 1,
                    "t_warehouse": warehouse,
                    "basic_rate": round(flt(row["selling"]) * 0.55, 2),
                    "serial_no": serial,
                    "use_serial_batch_fields": 1,
                    "cost_center": cc.get(branch_key) or accounts.get("cost_center"),
                    "allow_zero_valuation_rate": 0,
                },
            )

        for item_code, qty in [("DEMO-SC-ACCESSORY-001", 12), ("DEMO-SC-ACCESSORY-002", 18), ("DEMO-SC-SERVICE-002", 10)]:
            if frappe.db.exists("Item", item_code):
                doc.append(
                    "items",
                    {
                        "item_code": item_code,
                        "qty": qty,
                        "t_warehouse": warehouse,
                        "basic_rate": frappe.db.get_value("Item Price", {"item_code": item_code, "buying": 1}, "price_list_rate") or 25,
                        "cost_center": cc.get(branch_key) or accounts.get("cost_center"),
                        "allow_zero_valuation_rate": 0,
                    },
                )

    if not doc.items:
        return "no_items_to_add"
    submit_doc(doc)
    return doc.name


def get_operating_company():
    return (
        frappe.db.get_value("POS Profile", BRANCHES[0]["pos_profile"], "company")
        or frappe.db.get_value("Company", {"country": "Saudi Arabia", "default_currency": "SAR"}, "name")
        or frappe.db.get_value("Company", {"country": "Saudi Arabia"}, "name")
        or frappe.db.get_value("Company", {}, "name")
    )


def swiss_corner_item_group_root():
    return (
        frappe.db.get_value("Item Group", {"name": ["like", f"{PREFIX} - %"], "is_group": 1}, "name")
        or frappe.db.get_value("Item Group", {"name": f"{PREFIX} - ساعات"}, "name")
    )


def swiss_corner_item_group_like(text):
    names = frappe.get_all(
        "Item Group",
        filters=[["name", "like", f"{PREFIX} - %{text}%"], ["is_group", "=", 0]],
        pluck="name",
        limit_page_length=1,
    )
    return names[0] if names else None


def ensure_posnext_roles():
    role_map = {
        "demo_manager@swisscorner.demo": ["POSNext Cashier", "Nexus POS Manager"],
        "demo_accountant@swisscorner.demo": ["Nexus POS Manager"],
        "demo_inventory@swisscorner.demo": ["Nexus POS Manager"],
    }
    for branch in BRANCHES + [CLIENT_SAMPLE_BRANCH]:
        if branch.get("cashier"):
            role_map.setdefault(branch["cashier"], []).append("POSNext Cashier")

    for user, roles in role_map.items():
        if not frappe.db.exists("User", user):
            continue
        doc = frappe.get_doc("User", user)
        existing = {row.role for row in doc.roles}
        for role in roles:
            if frappe.db.exists("Role", role) and role not in existing:
                doc.append("roles", {"role": role})
        doc.enabled = 1
        save_doc(doc)


def ensure_posnext_wallet_mode(accounts):
    mop_name = "Swiss Corner Wallet"
    if frappe.db.exists("Mode of Payment", mop_name):
        doc = frappe.get_doc("Mode of Payment", mop_name)
    else:
        doc = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": mop_name})
    doc.enabled = 1
    doc.type = "General"
    if has_field("Mode of Payment", "is_wallet_payment"):
        doc.is_wallet_payment = 1
    if has_field("Mode of Payment", "custom_zatca_payment_means_code"):
        doc.custom_zatca_payment_means_code = "1"
    doc.set("accounts", [])
    account = accounts.get("cash") or accounts.get("receivable")
    if account:
        doc.append("accounts", {"company": get_operating_company(), "default_account": account})
    save_doc(doc)
    return mop_name


def ensure_posnext_loyalty_program(accounts):
    name = "Swiss Corner VIP Rewards"
    if frappe.db.exists("Loyalty Program", name):
        doc = frappe.get_doc("Loyalty Program", name)
    else:
        doc = frappe.get_doc({"doctype": "Loyalty Program", "loyalty_program_name": name})
    doc.loyalty_program_name = name
    doc.loyalty_program_type = "Single Tier Program"
    doc.from_date = add_days(today(), -30)
    doc.to_date = add_days(today(), 365)
    doc.customer_group = "VIP Customers" if frappe.db.exists("Customer Group", "VIP Customers") else None
    doc.auto_opt_in = 1
    doc.conversion_factor = 0.05
    doc.expiry_duration = 365
    doc.company = get_operating_company()
    doc.expense_account = accounts.get("expense")
    doc.cost_center = accounts.get("cost_center")
    doc.set("collection_rules", [])
    doc.append("collection_rules", {"tier_name": "VIP", "min_spent": 0, "collection_factor": 1})
    save_doc(doc)
    return name


def ensure_posnext_campaign():
    name = "Swiss Corner POSNext Demo Campaign"
    if frappe.db.exists("Campaign", name):
        doc = frappe.get_doc("Campaign", name)
    else:
        doc = frappe.get_doc({"doctype": "Campaign", "campaign_name": name})
    doc.campaign_name = name
    doc.description = "POSNext demo campaign for Swiss Corner offers, coupons, wallets, and loyalty."
    save_doc(doc)
    return name


def configure_posnext_profile(branch, accounts, wallet_mop):
    profile = frappe.get_doc("POS Profile", branch["pos_profile"])
    profile.ignore_pricing_rule = 0
    profile.allow_rate_change = 1
    profile.allow_discount_change = 1
    profile.allow_partial_payment = 1
    profile.print_receipt_on_order_complete = 0
    profile.validate_stock_on_save = 1
    profile.disable_grand_total_to_default_mop = 0
    profile.write_off_limit = profile.write_off_limit or 10
    if has_field("POS Profile", "posa_cash_mode_of_payment"):
        profile.posa_cash_mode_of_payment = "Cash" if frappe.db.exists("Mode of Payment", "Cash") else "نقد - Cash"
    if has_field("POS Profile", "posa_block_sale_beyond_available_qty"):
        profile.posa_block_sale_beyond_available_qty = 1
    if has_field("POS Profile", "posa_allow_delete"):
        profile.posa_allow_delete = 1
    if has_field("POS Profile", "custom_allow_select_sales_order"):
        profile.custom_allow_select_sales_order = 1
    if has_field("POS Profile", "use_customer_credit"):
        profile.use_customer_credit = 1
    if has_field("POS Profile", "hide_expected_amount"):
        profile.hide_expected_amount = 0
    if has_field("POS Profile", "pose_use_limit_search"):
        profile.pose_use_limit_search = 1
    if has_field("POS Profile", "campaign"):
        profile.campaign = "Swiss Corner POSNext Demo Campaign"

    payments = [
        {"mode_of_payment": "Cash", "default": 1, "allow_in_returns": 1},
        {"mode_of_payment": "Mada", "default": 0, "allow_in_returns": 1},
        {"mode_of_payment": "Visa / MasterCard", "default": 0, "allow_in_returns": 1},
        {"mode_of_payment": "STC Pay", "default": 0, "allow_in_returns": 1},
        {"mode_of_payment": "Bank Transfer", "default": 0, "allow_in_returns": 0},
        {"mode_of_payment": wallet_mop, "default": 0, "allow_in_returns": 1},
    ]
    profile.set("payments", [row for row in payments if frappe.db.exists("Mode of Payment", row["mode_of_payment"])])
    if branch.get("cashier"):
        users = [{"user": branch["cashier"]}]
        if branch.get("key") == "riyadh":
            for user in ["cashier_demo@swisscorner.demo", "cashier_backup@swisscorner.demo"]:
                if frappe.db.exists("User", user):
                    users.append({"user": user})
        profile.set("applicable_for_users", users)
    root_group = swiss_corner_item_group_root()
    if frappe.db.exists("Item Group", root_group):
        profile.set("item_groups", [{"item_group": root_group}])
    if has_field("POS Profile", "custom_brands_table"):
        profile.set("custom_brands_table", [])
    profile.set(
        "customer_groups",
        [{"customer_group": group} for group in ["Retail Customers", "VIP Customers", "Online Customers", "Walk-in Customers"] if frappe.db.exists("Customer Group", group)],
    )
    save_doc(profile)
    return profile.name


def ensure_posnext_settings(pos_profile, accounts, loyalty_program):
    existing = frappe.db.get_value("POS Settings", {"pos_profile": pos_profile}, "name")
    if existing:
        doc = frappe.get_doc("POS Settings", existing)
    else:
        doc = frappe.get_doc({"doctype": "POS Settings"})
    doc.pos_profile = pos_profile
    doc.enabled = 1
    doc.enable_loyalty_program = 1
    doc.default_loyalty_program = loyalty_program
    doc.wallet_account = accounts.get("receivable") or accounts.get("cash")
    doc.auto_create_wallet = 1
    doc.loyalty_to_wallet = 1
    doc.allow_user_to_edit_additional_discount = 1
    doc.allow_user_to_edit_item_discount = 1
    doc.allow_user_to_edit_rate = 1
    doc.use_percentage_discount = 1
    doc.max_discount_allowed = 25
    doc.allow_credit_sale = 1
    doc.allow_customer_credit_payment = 1
    doc.allow_return = 1
    doc.allow_partial_payment = 1
    doc.use_exact_amount = 0
    doc.enable_sales_persons = "Multiple"
    doc.default_card_view = 1
    doc.display_item_code = 1
    doc.show_customer_balance = 1
    doc.hide_expected_amount = 0
    doc.display_discount_percentage = 1
    doc.display_discount_amount = 1
    doc.show_variants_as_items = 1
    doc.allow_sales_order = 1
    doc.allow_select_sales_order = 1
    doc.create_only_sales_order = 0
    doc.allow_return_without_invoice = 1
    doc.return_validity_days = 30
    doc.allow_free_batch_return = 1
    doc.allow_print_draft_invoices = 1
    doc.decimal_precision = "2"
    doc.tax_inclusive = 0
    doc.allow_customer_purchase_order = 1
    doc.allow_duplicate_customer_names = 0
    doc.fetch_coupon = 1
    doc.allow_print_last_invoice = 1
    doc.silent_print = 0
    doc.use_delivery_charges = 1
    doc.auto_set_delivery_charges = 0
    doc.use_limit_search = 1
    doc.search_limit = 80
    doc.allow_submissions_in_background_job = 1
    doc.allow_delete_offline_invoice = 1
    doc.allow_change_posting_date = 1
    doc.input_qty = 1
    doc.allow_negative_stock = 0
    doc.enable_session_lock = 1
    doc.session_lock_timeout = 15
    if hasattr(doc, "barcode_rules"):
        doc.set("barcode_rules", [])
        for rule in ["20", "21", "22"]:
            doc.append("barcode_rules", {"barcode_rule": rule, "disable": 0})
    save_doc(doc)
    return doc.name


def ensure_posnext_open_shift(branch, accounts):
    user = branch.get("cashier")
    profile = branch.get("pos_profile")
    if not user or not profile:
        return None
    existing = frappe.db.get_value(
        "POS Opening Shift",
        {"user": user, "pos_profile": profile, "docstatus": 1, "status": "Open", "pos_closing_shift": ["is", "not set"]},
        "name",
    )
    if existing:
        return existing
    doc = frappe.get_doc({"doctype": "POS Opening Shift"})
    doc.company = get_operating_company()
    doc.pos_profile = profile
    doc.user = user
    doc.posting_date = today()
    doc.period_start_date = now()
    doc.set("balance_details", [])
    for mode, amount in [("Cash", 1000), ("Mada", 0), ("Visa / MasterCard", 0), ("STC Pay", 0), ("Swiss Corner Wallet", 0)]:
        if frappe.db.exists("Mode of Payment", mode):
            doc.append("balance_details", {"mode_of_payment": mode, "amount": amount})
    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc.name


def ensure_posnext_promotions_and_coupons(campaign):
    created = {"pricing_rules": [], "pos_coupons": [], "pos_offers": []}
    root_group = swiss_corner_item_group_root()
    straps_group = swiss_corner_item_group_like("سيور")
    battery_item = "DEMO-SC-SERVICE-001" if frappe.db.exists("Item", "DEMO-SC-SERVICE-001") else None

    rules = [
        {
            "name": "Swiss Corner POSNext - Zurich Brand 10%",
            "title": "Zurich Classic 10% POS Discount",
            "apply_on": "Brand",
            "brand": "Zurich Classic",
            "discount_percentage": 10,
            "min_amt": 1000,
            "priority": "8",
        },
        {
            "name": "Swiss Corner POSNext - Basket 5%",
            "title": "Basket 5% above SAR 2500",
            "apply_on": "Transaction",
            "discount_percentage": 5,
            "min_amt": 2500,
            "priority": "7",
        },
        {
            "name": "Swiss Corner POSNext - VIP Coupon 15%",
            "title": "VIP Coupon 15%",
            "apply_on": "Item Group",
            "item_group": root_group,
            "discount_percentage": 15,
            "min_amt": 1500,
            "coupon_code_based": 1,
            "priority": "10",
        },
    ]
    if battery_item and frappe.db.exists("Item Group", straps_group):
        rules.append(
            {
                "name": "Swiss Corner POSNext - Strap Free Service",
                "title": "Buy straps and get inspection service",
                "apply_on": "Item Group",
                "item_group": straps_group,
                "price_or_product_discount": "Product",
                "free_item": battery_item,
                "free_qty": 1,
                "min_qty": 2,
                "priority": "6",
            }
        )

    for rule in rules:
        existing_rule = (
            frappe.db.get_value("Pricing Rule", {"title": rule["title"]}, "name", order_by="creation asc")
            or (rule["name"] if frappe.db.exists("Pricing Rule", rule["name"]) else None)
        )
        doc = frappe.get_doc("Pricing Rule", existing_rule) if existing_rule else frappe.get_doc({"doctype": "Pricing Rule"})
        doc.title = rule["title"]
        doc.disable = 0
        doc.selling = 1
        doc.buying = 0
        doc.company = get_operating_company()
        doc.currency = "SAR"
        doc.apply_on = rule["apply_on"]
        doc.price_or_product_discount = rule.get("price_or_product_discount", "Price")
        doc.rate_or_discount = "Discount Percentage"
        doc.discount_percentage = rule.get("discount_percentage", 0)
        doc.min_amt = rule.get("min_amt", 0)
        doc.min_qty = rule.get("min_qty", 0)
        doc.valid_from = add_days(today(), -15)
        doc.valid_upto = add_days(today(), 120)
        doc.priority = rule.get("priority", "5")
        doc.coupon_code_based = rule.get("coupon_code_based", 0)
        if has_field("Pricing Rule", "pos_only"):
            doc.pos_only = 1
        doc.set("brands", [])
        doc.set("item_groups", [])
        doc.set("items", [])
        if rule.get("brand") and frappe.db.exists("Brand", rule["brand"]):
            doc.append("brands", {"brand": rule["brand"]})
        if rule.get("item_group") and frappe.db.exists("Item Group", rule["item_group"]):
            doc.append("item_groups", {"item_group": rule["item_group"]})
        if rule.get("free_item"):
            doc.free_item = rule["free_item"]
            doc.free_qty = rule.get("free_qty", 1)
            doc.free_item_uom = DEFAULT_UOM
        save_doc(doc)
        created["pricing_rules"].append(doc.name)
    disable_duplicate_posnext_pricing_rules([rule["title"] for rule in rules])

    coupons = [
        ("Swiss Corner POSNext Coupon VIP15", "SCVIP15", "Promotional", None, "Percentage", 15, 0, 1500, 500, 200),
        ("Swiss Corner POSNext Coupon ONLINE10", "SCONLINE10", "Promotional", first_customer("Online Customers"), "Percentage", 10, 0, 500, 250, 300),
        ("Swiss Corner POSNext Gift Card 250", "SCGIFT250", "Gift Card", first_customer("VIP Customers"), "Amount", 0, 250, 0, 250, 1),
    ]
    for name, code, coupon_type, customer, discount_type, percent, amount, min_amount, max_amount, max_use in coupons:
        doc = frappe.get_doc("POS Coupon", name) if frappe.db.exists("POS Coupon", name) else frappe.get_doc({"doctype": "POS Coupon", "coupon_name": name})
        doc.coupon_name = name
        doc.coupon_code = code
        doc.coupon_type = coupon_type
        doc.disabled = 0
        doc.company = get_operating_company()
        doc.campaign = campaign
        doc.customer = customer if customer and frappe.db.exists("Customer", customer) else None
        doc.discount_type = discount_type
        doc.discount_percentage = percent
        doc.discount_amount = amount
        doc.min_amount = min_amount
        doc.max_amount = max_amount
        doc.apply_on = "Grand Total"
        doc.valid_from = add_days(today(), -15)
        doc.valid_upto = add_days(today(), 120)
        doc.maximum_use = max_use
        doc.one_use = 1 if coupon_type == "Gift Card" else 0
        doc.description = f"Swiss Corner POSNext demo coupon {code}."
        save_doc(doc)
        created["pos_coupons"].append(doc.name)

    pos_offers = [
        ("Swiss Corner POSNext Auto Basket Offer", "Transaction", "Grand Total", None, 0, 3000, 7, 0),
        ("Swiss Corner POSNext Coupon Watch Offer", "Item Group", "Item Price", root_group, 0, 1200, 12, 1),
    ]
    for title, apply_on, offer_type, item_group, min_qty, min_amt, percent, coupon_based in pos_offers:
        doc = frappe.get_doc("POS Offer", title) if frappe.db.exists("POS Offer", title) else frappe.get_doc({"doctype": "POS Offer", "title": title})
        doc.title = title
        doc.disable = 0
        doc.apply_on = apply_on
        doc.offer = offer_type
        doc.company = get_operating_company()
        doc.item_group = item_group if item_group and frappe.db.exists("Item Group", item_group) else None
        doc.min_qty = min_qty
        doc.min_amt = min_amt
        doc.valid_from = add_days(today(), -15)
        doc.valid_upto = add_days(today(), 120)
        doc.discount_type = "Discount Percentage"
        doc.discount_percentage = percent
        doc.auto = 0 if coupon_based else 1
        doc.coupon_based = coupon_based
        doc.description = "Swiss Corner POSNext showcase offer."
        save_doc(doc)
        created["pos_offers"].append(doc.name)
    return created


def disable_duplicate_posnext_pricing_rules(titles):
    for title in titles:
        rows = frappe.get_all(
            "Pricing Rule",
            filters={"title": title},
            fields=["name", "creation"],
            order_by="creation asc",
            limit_page_length=100,
        )
        for row in rows[1:]:
            frappe.db.set_value("Pricing Rule", row.name, "disable", 1, update_modified=False)


def first_customer(customer_group=None):
    filters = {}
    if customer_group and frappe.db.exists("Customer Group", customer_group):
        filters["customer_group"] = customer_group
    return frappe.db.get_value("Customer", filters, "name", order_by="modified desc") if filters else frappe.db.get_value("Customer", {}, "name")


def ensure_posnext_customer_wallets(accounts):
    customers = []
    for group in ["VIP Customers", "Online Customers"]:
        name = first_customer(group)
        if name and name not in customers:
            customers.append(name)
    if not customers:
        return []
    wallet_names = []
    for idx, customer in enumerate(customers):
        wallet_name = f"{customer}-WALLET"
        if frappe.db.exists("Wallet", wallet_name):
            wallet = frappe.get_doc("Wallet", wallet_name)
        else:
            wallet = frappe.get_doc({"doctype": "Wallet", "customer": customer})
        wallet.customer = customer
        wallet.status = "Active"
        wallet.company = get_operating_company()
        wallet.account = accounts.get("receivable") or accounts.get("cash")
        wallet.current_balance = 500 - (idx * 150)
        wallet.available_balance = wallet.current_balance
        save_doc(wallet)
        wallet_names.append(wallet.name)

        tx_name = f"Swiss Corner POSNext Wallet Top-up - {customer}"
        existing = frappe.db.get_value("Wallet Transaction", {"remarks": tx_name, "wallet": wallet.name}, "name")
        if not existing:
            tx = frappe.get_doc({"doctype": "Wallet Transaction"})
            tx.transaction_type = "Credit"
            tx.wallet = wallet.name
            tx.customer = customer
            tx.company = get_operating_company()
            tx.posting_date = today()
            tx.amount = wallet.current_balance
            tx.source_type = "Manual Adjustment"
            tx.source_account = accounts.get("expense") or wallet.account
            tx.cost_center = accounts.get("cost_center")
            tx.remarks = tx_name
            tx.insert(ignore_permissions=True)
            tx.submit()
        wallet.reload()
        wallet.update_balance()
    return wallet_names


# ---------------------------------------------------------------------------
# Swiss Corner presentation workspaces - final customer demo polish.
# These definitions intentionally live at the end of the module so they override
# earlier setup helpers without changing the older migration history above.


def swiss_corner_chart_filters(doctype):
    company = get_operating_company()
    filters = [[doctype, "company", "=", company, False], [doctype, "docstatus", "=", 1, False]]
    if doctype == "Sales Invoice":
        filters.append([doctype, "title", "like", "Swiss Corner%", False])
    elif doctype == "POS Invoice":
        filters.append([doctype, "pos_profile", "like", "POS - %", False])
    return json.dumps(filters, ensure_ascii=False)


def ensure_dashboard_charts(accounts):
    definitions = [
        {
            "name": "Swiss Corner - Sales by Branch",
            "chart_type": "Group By",
            "document_type": "Sales Invoice",
            "group_by_based_on": "customer_group",
            "group_by_type": "Sum",
            "aggregate_function_based_on": "grand_total",
            "type": "Bar",
            "filters_json": swiss_corner_chart_filters("Sales Invoice"),
            "title": "المبيعات حسب شرائح العملاء",
        },
        {
            "name": "Swiss Corner - POS Profiles",
            "chart_type": "Group By",
            "document_type": "POS Invoice",
            "group_by_based_on": "pos_profile",
            "group_by_type": "Sum",
            "aggregate_function_based_on": "grand_total",
            "type": "Donut",
            "filters_json": swiss_corner_chart_filters("POS Invoice"),
            "title": "مبيعات نقاط البيع",
        },
        {
            "name": "Swiss Corner - Invoice Trend",
            "chart_type": "Sum",
            "document_type": "Sales Invoice",
            "based_on": "posting_date",
            "value_based_on": "grand_total",
            "timeseries": 1,
            "timespan": "Last Quarter",
            "time_interval": "Weekly",
            "type": "Line",
            "filters_json": swiss_corner_chart_filters("Sales Invoice"),
            "title": "اتجاه الفواتير",
        },
    ]
    out = []
    for d in definitions:
        if frappe.db.exists("Dashboard Chart", d["name"]):
            doc = frappe.get_doc("Dashboard Chart", d["name"])
        else:
            doc = frappe.get_doc({"doctype": "Dashboard Chart", "chart_name": d["name"]})
        doc.chart_name = d["name"]
        doc.chart_type = d["chart_type"]
        doc.document_type = d["document_type"]
        doc.type = d["type"]
        doc.filters_json = d["filters_json"]
        doc.is_public = 1
        doc.color = "#b77a2b"
        for optional in ("group_by_based_on", "group_by_type", "aggregate_function_based_on", "based_on", "value_based_on", "timeseries", "timespan", "time_interval"):
            if optional in d:
                setattr(doc, optional, d[optional])
            elif hasattr(doc, optional):
                setattr(doc, optional, None)
        save_doc(doc)
        out.append(d["name"])
    return out


def ensure_number_cards(accounts):
    company = get_operating_company()
    sales_filters = [
        ["Sales Invoice", "company", "=", company, False],
        ["Sales Invoice", "docstatus", "=", 1, False],
        ["Sales Invoice", "title", "like", "Swiss Corner%", False],
    ]
    pos_filters = [
        ["POS Invoice", "company", "=", company, False],
        ["POS Invoice", "docstatus", "=", 1, False],
        ["POS Invoice", "pos_profile", "like", "POS - %", False],
    ]
    definitions = [
        ("Swiss Corner - Invoice Count", "Sales Invoice", "Count", None, sales_filters, "Blue"),
        ("Swiss Corner - Sales Total", "Sales Invoice", "Sum", "grand_total", sales_filters, "Green"),
        ("Swiss Corner - POS Invoice Count", "POS Invoice", "Count", None, pos_filters, "Purple"),
        ("Swiss Corner - POS Sales Total", "POS Invoice", "Sum", "grand_total", pos_filters, "Orange"),
        ("Swiss Corner - Serial Watches", "Serial No", "Count", None, [["Serial No", "item_code", "like", "DEMO-SC-WATCH%", False]], "Purple"),
        ("Swiss Corner - WhatsApp Logs", "WhatsApp Message Log", "Count", None, [["WhatsApp Message Log", "sc_reference_doctype", "=", "Sales Invoice", False]], "Orange"),
    ]
    out = []
    for name, doctype, function, based_on, filters, color in definitions:
        if frappe.db.exists("Number Card", name):
            doc = frappe.get_doc("Number Card", name)
        else:
            doc = frappe.get_doc({"doctype": "Number Card", "label": name})
        doc.label = name
        doc.type = "Document Type"
        doc.document_type = doctype
        doc.function = function
        doc.aggregate_function_based_on = based_on
        doc.is_public = 1
        doc.show_full_number = 1
        doc.filters_json = json.dumps(filters, ensure_ascii=False)
        doc.color = color
        save_doc(doc)
        out.append(name)
    return out


def ensure_demo_guide_workspace(chart_names=None, card_names=None):
    html_content = """
<div class="sc-demo-start" dir="rtl">
  <style>
    .sc-demo-start{font-family:Inter,"Noto Sans Arabic",Arial,sans-serif;color:#17120d;max-width:1180px;margin:auto}
    .sc-demo-hero{border:1px solid #e4cfae;border-radius:12px;background:#fffaf3;padding:30px 34px;box-shadow:0 10px 28px rgba(40,28,14,.08)}
    .sc-demo-brand{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:18px}
    .sc-demo-brand img{height:58px;max-width:240px;object-fit:contain}
    .sc-demo-eyebrow{color:#a36823;font-weight:900;font-size:12px;letter-spacing:.08em;text-transform:uppercase}
    .sc-demo-title{font-size:32px;font-weight:900;line-height:1.45;margin:8px 0 12px;color:#111}
    .sc-demo-copy{font-size:16px;line-height:2;color:#514437;max-width:1040px}
    .sc-demo-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}
    .sc-demo-actions a{display:inline-flex;align-items:center;justify-content:center;border-radius:8px;padding:11px 16px;text-decoration:none!important;font-weight:850;border:1px solid #c79a5a;color:#111!important;background:#fff}
    .sc-demo-actions a.primary{background:#111;color:#fff!important;border-color:#111}
    .sc-demo-band{margin-top:18px;border:1px solid #ead8bd;border-radius:10px;background:#fff;padding:18px 20px;line-height:1.9}
    .sc-demo-section{margin-top:22px}
    .sc-demo-section-title{font-size:21px;font-weight:900;margin:0 0 12px;color:#111}
    .sc-demo-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
    .sc-demo-feature{border:1px solid #ead8bd;border-radius:10px;background:#fff;padding:18px;min-height:154px}
    .sc-demo-feature strong{display:block;font-size:17px;margin-bottom:8px;color:#111}
    .sc-demo-feature p{margin:0;color:#5d5042;line-height:1.8;font-size:14px}
    .sc-demo-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
    .sc-demo-step{border:1px solid #ead8bd;border-radius:10px;background:#fff;padding:14px;min-height:132px}
    .sc-demo-step span{display:inline-flex;width:28px;height:28px;border-radius:50%;align-items:center;justify-content:center;background:#b77a2b;color:#fff;font-weight:900;margin-bottom:10px}
    .sc-demo-step b{display:block;margin-bottom:6px;color:#111}
    .sc-demo-step div{font-size:13px;line-height:1.7;color:#5d5042}
    .sc-demo-note{border-inline-start:4px solid #b77a2b;background:#fff;padding:14px 16px;margin-top:16px;color:#574737;line-height:1.9}
    @media(max-width:1000px){.sc-demo-grid,.sc-demo-flow{grid-template-columns:1fr 1fr}.sc-demo-title{font-size:24px}}
    @media(max-width:650px){.sc-demo-grid,.sc-demo-flow{grid-template-columns:1fr}.sc-demo-brand{align-items:flex-start;flex-direction:column}.sc-demo-hero{padding:22px}}
  </style>
  <div class="sc-demo-hero">
    <div class="sc-demo-brand">
      <img src="/files/swiss-corner-logo.webp" alt="Swiss Corner Watches">
      <div class="sc-demo-eyebrow">Swiss Corner Watches | Retail POS Demo</div>
    </div>
    <div class="sc-demo-title">ابدأ العرض من هنا: قصة تشغيل متجر ساعات من أول البيع حتى الضمان</div>
    <div class="sc-demo-copy">
      هذه الصفحة هي سكربت العرض الرسمي. لا تبدأ من القوائم الجانبية؛ ابدأ من هنا ثم انتقل بالتسلسل:
      لوحة المؤشرات، تجربة الكاشير، إضافة عميل ورقم واتساب، اعتماد الفاتورة، ثم تقارير المخزون والضمان والربحية.
    </div>
    <div class="sc-demo-actions">
      <a class="primary" href="/app/swiss-corner-demo">1. لوحة مؤشرات الركن السويسري</a>
      <a href="/app/point-of-sale">2. فتح نقطة البيع</a>
      <a href="/app/query-report/Swiss%20Corner%20-%20Store%20Sales%20Report">3. تقرير مبيعات الفروع</a>
      <a href="/app/query-report/Swiss%20Corner%20-%20Serial%20Number%20Register">4. سجل السيريال والضمان</a>
      <a href="/app/query-report/Swiss%20Corner%20-%20WhatsApp%20Invoice%20Delivery%20Log">5. سجل واتساب</a>
    </div>
  </div>
  <div class="sc-demo-band">
    <b>الفكرة التي نشرحها للعميل:</b>
    ERPNext مع POSNext يدير سلسلة متاجر ساعات متعددة الفروع: مخزون بسيريال نمبر، بيع سريع، كوبونات وعروض، فواتير PDF بهوية العميل، واتساب آمن، وتقارير تشغيلية وإدارية من نفس البيانات.
  </div>
  <div class="sc-demo-section">
    <div class="sc-demo-section-title">ماذا تعرض في كل جزء؟</div>
    <div class="sc-demo-grid">
      <div class="sc-demo-feature"><strong>1. الإدارة التنفيذية</strong><p>افتح لوحة المؤشرات واعرض إجمالي المبيعات، عدد الفواتير، مبيعات POS، عدد الساعات التسلسلية، ورسائل واتساب.</p></div>
      <div class="sc-demo-feature"><strong>2. تجربة الكاشير</strong><p>ادخل بحساب الكاشير، اختر صنفًا، جرّب كوبون أو عرض، أتم الدفع نقدي/مدى/بطاقة، ثم اطبع الإيصال.</p></div>
      <div class="sc-demo-feature"><strong>3. العميل والواتساب</strong><p>أضف عميلًا جديدًا وضع رقم واتساب تجريبيًا مسموحًا، ثم اعتمد الفاتورة واعرض سجل الإرسال أو وضع Dry Run.</p></div>
      <div class="sc-demo-feature"><strong>4. المخزون والسيريال</strong><p>اعرض أن الساعة لا تباع ككمية فقط، بل برقم تسلسلي، مع موقعها الحالي وتاريخ الشراء والبيع والضمان.</p></div>
      <div class="sc-demo-feature"><strong>5. الفروع والتحويلات</strong><p>اعرض تحويل المخزون بين الرياض وجدة والخبر والمتجر الإلكتروني ومخازن الصيانة والتالف.</p></div>
      <div class="sc-demo-feature"><strong>6. التقارير والقرار</strong><p>اختم بتقارير الربحية، الأصناف السريعة والبطيئة، مبيعات كل فرع، وملخص نقطة البيع حسب طرق الدفع.</p></div>
    </div>
  </div>
  <div class="sc-demo-section">
    <div class="sc-demo-section-title">تسلسل عرض مختصر أمام العميل</div>
    <div class="sc-demo-flow">
      <div class="sc-demo-step"><span>1</span><b>افتح اللوحة</b><div>ابدأ بلوحة مؤشرات الركن السويسري ووضح الصورة العامة.</div></div>
      <div class="sc-demo-step"><span>2</span><b>بع ساعة</b><div>افتح POS، اختر صنفًا، وأكمل الدفع بدون تعقيد.</div></div>
      <div class="sc-demo-step"><span>3</span><b>أضف عميلًا</b><div>ضع رقم واتساب تجريبي في حقل رقم الواتساب.</div></div>
      <div class="sc-demo-step"><span>4</span><b>اطبع وأرسل</b><div>اعرض الفاتورة الاحترافية وسجل واتساب.</div></div>
      <div class="sc-demo-step"><span>5</span><b>اختم بالتقارير</b><div>اعرض المبيعات، المخزون، السيريال، الضمان، والربحية.</div></div>
    </div>
    <div class="sc-demo-note">
      حساب الكاشير الرئيسي للعرض: <b>cashier_demo@swisscorner.demo</b>.
      حساب المدير لعرض النظام كاملًا: <b>demo_manager@swisscorner.demo</b>.
      استخدم أرقام واتساب تجريبية فقط حتى لا يتم إرسال رسائل حقيقية لعميل غير مقصود.
    </div>
  </div>
</div>
"""
    content = [{"id": "swiss-corner-demo-guide", "type": "header", "data": {"text": html_content, "col": 12}}]
    values = {
        "doctype": "Workspace",
        "label": GUIDE_WORKSPACE,
        "title": "Demo",
        "module": MODULE,
        "icon": "rocket",
        "indicator_color": "orange",
        "public": 1,
        "is_hidden": 0,
        "sequence_id": 1,
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [],
        "links": [],
        "charts": [],
        "number_cards": [],
        "roles": [{"role": "System Manager"}, {"role": "Demo Viewer"}, {"role": "Cashier"}],
    }
    doc = frappe.get_doc("Workspace", GUIDE_WORKSPACE) if frappe.db.exists("Workspace", GUIDE_WORKSPACE) else frappe.get_doc(values)
    for key, value in values.items():
        if key == "doctype":
            continue
        if key in {"shortcuts", "links", "charts", "number_cards", "roles"}:
            doc.set(key, value)
        else:
            setattr(doc, key, value)
    save_doc(doc)


def ensure_swiss_corner_demo_dashboard_workspace(chart_names=None, card_names=None):
    chart_names = chart_names or ensure_dashboard_charts({})
    card_names = card_names or ensure_number_cards({})
    cards = [
        {
            "label": "مسار العرض السريع",
            "links": [
                report_link("Swiss Corner - Store Sales Report", "تقرير مبيعات الفروع"),
                report_link("Swiss Corner - POS Sales Summary", "ملخص نقطة البيع"),
                report_link("Swiss Corner - Serial Number Register", "سجل الأرقام التسلسلية"),
                report_link("Swiss Corner - Warranty Report", "تقرير الضمان"),
                report_link("Swiss Corner - WhatsApp Invoice Delivery Log", "سجل واتساب"),
            ],
        },
        {
            "label": "العمليات اليومية",
            "links": [
                doc_link("Sales Invoice", "فواتير المبيعات"),
                doc_link("POS Invoice", "فواتير نقطة البيع"),
                doc_link("Customer", "العملاء"),
                doc_link("Item", "الأصناف"),
                doc_link("Serial No", "الأرقام التسلسلية"),
                doc_link("Stock Entry", "حركة المخزون"),
            ],
        },
    ]
    shortcuts = [
        doc_shortcut("Sales Invoice", "فاتورة مبيعات"),
        doc_shortcut("POS Invoice", "فاتورة نقطة بيع"),
        doc_shortcut("Item", "الصنف"),
        doc_shortcut("Serial No", "رقم تسلسلي"),
        doc_shortcut("Warehouse", "المستودع"),
        doc_shortcut("WhatsApp Message Log", "سجل واتساب"),
    ]
    content = build_workspace_content(
        "ديمو الركن السويسري",
        "لوحة عرض عملية: مؤشرات مبيعات، نقاط بيع، مخزون بسيريال نمبر، ضمان، وفواتير واتساب.",
        chart_names,
        card_names,
        [s["label"] for s in shortcuts],
        [c["label"] for c in cards],
    )
    values = {
        "doctype": "Workspace",
        "name": "Swiss Corner Demo",
        "label": "ديمو الركن السويسري",
        "title": "ديمو الركن السويسري",
        "module": MODULE,
        "icon": "retail",
        "indicator_color": "orange",
        "public": 1,
        "is_hidden": 0,
        "sequence_id": 2,
        "content": content,
        "shortcuts": shortcuts,
        "links": build_workspace_links(cards),
        "charts": [{"chart_name": name, "label": name} for name in chart_names],
        "number_cards": [{"number_card_name": name, "label": name} for name in card_names],
        "roles": [{"role": "System Manager"}, {"role": "Demo Viewer"}, {"role": "Cashier"}],
    }
    doc = frappe.get_doc("Workspace", "Swiss Corner Demo") if frappe.db.exists("Workspace", "Swiss Corner Demo") else frappe.get_doc(values)
    for key, value in values.items():
        if key == "doctype":
            continue
        if key in {"shortcuts", "links", "charts", "number_cards", "roles"}:
            doc.set(key, value)
        else:
            setattr(doc, key, value)
    save_doc(doc)


def ensure_workspace_and_dashboard(accounts: dict[str, str | None]):
    chart_names = ensure_dashboard_charts(accounts)
    card_names = ensure_number_cards(accounts)
    ensure_dashboard_doc(chart_names, card_names)
    ensure_demo_guide_workspace(chart_names, card_names)
    ensure_swiss_corner_demo_dashboard_workspace(chart_names, card_names)
    polish_swiss_corner_workspace_experience()
    return {"charts": chart_names, "number_cards": card_names}


def repair_swiss_corner_workspace_presentation():
    accounts = ensure_company_and_accounts()
    result = ensure_workspace_and_dashboard(accounts)
    for email in [
        "demo_manager@swisscorner.demo",
        "cashier_demo@swisscorner.demo",
        "cashier_backup@swisscorner.demo",
        "demo_inventory@swisscorner.demo",
        "demo_accountant@swisscorner.demo",
    ]:
        if frappe.db.exists("User", email):
            frappe.db.set_value("User", email, "default_workspace", GUIDE_WORKSPACE, update_modified=False)
    frappe.db.commit()
    frappe.clear_cache()
    return result


# Keep the public demo route and smoke verification focused on /app/swiss-corner-demo.
WORKSPACE = "Swiss Corner Demo"


def _demo_report_url(report_name: str) -> str:
    return f"/app/query-report/{report_name}"


def _demo_presentation_card(number, title, show, say, links):
    if isinstance(links, tuple):
        links = [links]
    buttons = "".join(
        f'<a class="demo-pres-link" href="{href}">{label}</a>'
        for label, href in links
    )
    return f"""
      <article class="demo-pres-card" tabindex="0">
        <span class="demo-pres-number">{number}</span>
        <h3>{title}</h3>
        <ul>
          <li><b>ماذا نعرض:</b> {show}</li>
        </ul>
        <p class="demo-pres-note"><b>للمقدم:</b> {say}</p>
        <div class="demo-pres-card-actions">{buttons}</div>
      </article>
    """


def _demo_feature_card(title, points, note, link_label, href):
    items = "".join(f"<li>{point}</li>" for point in points[:3])
    return f"""
      <article class="demo-pres-feature">
        <h3>{title}</h3>
        <ul>{items}</ul>
        <p>{note}</p>
        <a href="{href}">{link_label}</a>
      </article>
    """


def _demo_score_card(label, score):
    return f"""
      <article class="demo-pres-score">
        <span>{label}</span>
        <strong>{score}/10</strong>
      </article>
    """


def get_demo_presentation_html():
    flow_cards = [
        _demo_presentation_card(
            "01",
            "البداية التنفيذية",
            "لوحة المؤشرات العامة.",
            "هنا نعطي العميل الصورة الكاملة قبل الدخول في التفاصيل.",
            ("فتح اللوحة", "/app/swiss-corner-demo"),
        ),
        _demo_presentation_card(
            "02",
            "تجربة البيع",
            "POS وتجربة الكاشير.",
            "نبدأ من واقع الفرع: بيع سريع، منتج، عميل، وفاتورة.",
            ("فتح نقطة البيع", "/app/point-of-sale"),
        ),
        _demo_presentation_card(
            "03",
            "المخزون",
            "حركة المخزون حسب المتجر.",
            "كل عملية بيع تؤثر مباشرة على المخزون.",
            ("فتح التقرير", _demo_report_url("حركة المخزون حسب المتجر")),
        ),
        _demo_presentation_card(
            "04",
            "الأرقام التسلسلية",
            "تتبع كل ساعة برقمها التسلسلي.",
            "كل ساعة يمكن تتبعها من دخولها حتى بيعها وخدمة ما بعد البيع.",
            ("فتح السجل", _demo_report_url("سجل الأرقام التسلسلية")),
        ),
        _demo_presentation_card(
            "05",
            "الضمان",
            "تقرير الضمان.",
            "الضمان مرتبط بالفاتورة والرقم التسلسلي، وهذا يقلل الأخطاء.",
            ("فتح الضمان", _demo_report_url("تقرير الضمان")),
        ),
        _demo_presentation_card(
            "06",
            "واتساب تجريبي",
            "سجل تسليم فواتير واتساب Dry Run.",
            "هذا وضع تجريبي آمن لتوضيح الفكرة بدون إرسال فعلي.",
            ("فتح السجل", _demo_report_url("سجل تسليم فواتير واتساب")),
        ),
        _demo_presentation_card(
            "07",
            "الموارد البشرية",
            "الموظفين، الحضور، الرواتب.",
            "النظام لا يدير البيع فقط، بل يدير الفريق التشغيلي أيضًا.",
            [
                ("الموظفون", "/app/employee"),
                ("الحضور", "/app/attendance"),
                ("الرواتب", "/app/salary-slip"),
            ],
        ),
        _demo_presentation_card(
            "08",
            "الخلاصة الإدارية",
            "الربحية والمنتجات السريعة والبطيئة.",
            "نختم بالأرقام التي تساعد الإدارة على اتخاذ القرار.",
            [
                ("الربحية", _demo_report_url("الربحية حسب الفرع والعلامة")),
                ("حركة المنتجات", _demo_report_url("الساعات السريعة والبطيئة الحركة")),
            ],
        ),
    ]
    feature_cards = [
        _demo_feature_card("إدارة فروع متعددة", ["متاجر متعددة", "تحليل حسب الفرع", "رؤية موحدة للإدارة"], "اربط الحديث بنمو سلسلة متاجر الساعات.", "لوحة العرض", "/app/swiss-corner-demo"),
        _demo_feature_card("نقطة بيع سريعة", ["واجهة كاشير", "بيع مباشر", "تجربة قريبة من الواقع"], "اعرض سرعة اختيار المنتج وإتمام الدفع.", "فتح POS", "/app/point-of-sale"),
        _demo_feature_card("مخزون مترابط", ["حركة مخزون واضحة", "متاجر ومستودعات", "لا توجد فوضى في الكميات"], "بيّن أن البيع لا ينفصل عن الرصيد.", "حركة المخزون", _demo_report_url("حركة المخزون حسب المتجر")),
        _demo_feature_card("تتبع الأرقام التسلسلية", ["تتبع كل ساعة", "ربط بالبيع", "مفيد للضمان"], "هذه نقطة قوية في قطاع الساعات.", "سجل الأرقام", _demo_report_url("سجل الأرقام التسلسلية")),
        _demo_feature_card("ضمان وخدمة ما بعد البيع", ["ضمان حسب المنتج", "ربط بالفاتورة", "سهولة الرجوع للسجل"], "اجعلها قصة خدمة بعد البيع.", "تقرير الضمان", _demo_report_url("تقرير الضمان")),
        _demo_feature_card("تقارير تنفيذية", ["مبيعات الفروع", "ربحية", "منتجات سريعة وبطيئة الحركة"], "اختم بها لإظهار قيمة القرار الإداري.", "مبيعات الفروع", _demo_report_url("تقرير مبيعات الفروع")),
        _demo_feature_card("موارد بشرية", ["موظفين", "حضور", "رواتب"], "وسّع العرض من المبيعات إلى تشغيل الفريق.", "الموظفون", "/app/employee"),
        _demo_feature_card("واتساب تجريبي آمن", ["Dry Run", "سجل إرسال", "بدون إرسال فعلي"], "وضّح أنه عرض آمن للفكرة فقط.", "سجل واتساب", _demo_report_url("سجل تسليم فواتير واتساب")),
    ]
    scores = [
        _demo_score_card("نقطة البيع", 8),
        _demo_score_card("المخزون", 8),
        _demo_score_card("الأرقام التسلسلية", 8),
        _demo_score_card("التقارير", 8),
        _demo_score_card("الضمان", 8),
        _demo_score_card("واتساب التجريبي", 7),
        _demo_score_card("الموارد البشرية", 7),
        _demo_score_card("تجربة العرض", 9),
    ]
    nav_links = [
        ("ابدأ من هنا", "/app/swiss-corner-demo"),
        ("التالي: POS", "/app/point-of-sale"),
        ("التالي: المخزون", _demo_report_url("حركة المخزون حسب المتجر")),
        ("التالي: الأرقام التسلسلية", _demo_report_url("سجل الأرقام التسلسلية")),
        ("التالي: الضمان", _demo_report_url("تقرير الضمان")),
        ("التالي: واتساب", _demo_report_url("سجل تسليم فواتير واتساب")),
        ("التالي: HR", "/app/employee"),
        ("إنهاء العرض بالتقارير", _demo_report_url("الربحية حسب الفرع والعلامة")),
    ]
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in nav_links)
    return f"""
<div class="demo-presentation" dir="rtl">
  <section class="demo-pres-hero">
    <div class="demo-pres-hero-copy">
      <span class="demo-pres-kicker">Dashboard Presentation</span>
      <h1>رحلة ديمو الركن السويسري</h1>
      <p>لوحة بداية العرض: من البيع داخل الفرع إلى المخزون، الأرقام التسلسلية، الضمان، الموارد البشرية، والتقارير التنفيذية.</p>
      <div class="demo-pres-actions">
        <a class="primary" href="/app/swiss-corner-demo">ابدأ العرض</a>
        <a href="/app/point-of-sale">افتح نقطة البيع</a>
        <a href="{_demo_report_url("تقرير مبيعات الفروع")}">التقارير التنفيذية</a>
      </div>
    </div>
    <aside class="demo-pres-hero-panel">
      <span>Retail Watch Chain</span>
      <strong>من الفرع إلى الإدارة</strong>
      <small>ابدأ بالقصة، ثم انتقل خطوة بخطوة.</small>
    </aside>
  </section>

  <section class="demo-pres-section">
    <div class="demo-pres-section-head">
      <span>01</span>
      <h2>مسار العرض</h2>
    </div>
    <div class="demo-pres-flow">
      {''.join(flow_cards)}
    </div>
  </section>

  <section class="demo-pres-section">
    <div class="demo-pres-section-head">
      <span>02</span>
      <h2>ماذا يميز الديمو؟</h2>
    </div>
    <div class="demo-pres-features">
      {''.join(feature_cards)}
    </div>
  </section>

  <section class="demo-pres-section demo-pres-split">
    <div>
      <div class="demo-pres-section-head">
        <span>03</span>
        <h2>جاهزية العرض</h2>
      </div>
      <div class="demo-pres-scores">
        {''.join(scores)}
      </div>
    </div>
    <article class="demo-pres-reminder">
      <h2>تذكير أثناء العرض</h2>
      <ul>
        <li>ابدأ بالقصة: سلسلة ساعات متعددة الفروع.</li>
        <li>لا تبدأ بالتقارير؛ ابدأ برحلة العميل.</li>
        <li>اربط دائمًا بين POS والمخزون والرقم التسلسلي.</li>
        <li>وضّح أن واتساب في وضع Dry Run آمن.</li>
        <li>اختم بقيمة التقارير للإدارة.</li>
      </ul>
    </article>
  </section>

  <section class="demo-pres-section">
    <div class="demo-pres-section-head">
      <span>04</span>
      <h2>أزرار التنقل الذكي</h2>
    </div>
    <nav class="demo-pres-smart-nav" aria-label="مسار تنقل العرض">
      {nav}
    </nav>
  </section>
</div>
"""


def setup_demo_presentation_workspace():
    html_content = get_demo_presentation_html()
    content = [{"id": "demo-presentation-dashboard", "type": "header", "data": {"text": html_content, "col": 12}}]
    values = {
        "doctype": "Workspace",
        "name": GUIDE_WORKSPACE,
        "label": GUIDE_WORKSPACE,
        "title": "Demo",
        "module": MODULE,
        "icon": "rocket",
        "indicator_color": "orange",
        "public": 1,
        "is_hidden": 0,
        "sequence_id": 1,
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [],
        "links": [],
        "charts": [],
        "number_cards": [],
        "quick_lists": [],
        "custom_blocks": [],
        "roles": [{"role": "System Manager"}, {"role": "Demo Viewer"}, {"role": "Cashier"}],
    }
    doc = frappe.get_doc("Workspace", GUIDE_WORKSPACE) if frappe.db.exists("Workspace", GUIDE_WORKSPACE) else frappe.get_doc(values)
    for key, value in values.items():
        if key == "doctype":
            continue
        if key in {"shortcuts", "links", "charts", "number_cards", "quick_lists", "custom_blocks", "roles"}:
            doc.set(key, value)
        else:
            setattr(doc, key, value)
    save_doc(doc)
    frappe.clear_cache()
    return {"workspace": GUIDE_WORKSPACE, "route": "/app/demo"}


def ensure_demo_guide_workspace(chart_names=None, card_names=None):
    return setup_demo_presentation_workspace()


def _sc_slide_actions(actions):
    return "".join(
        f'<button class="sc-slide-action sc-open-link" type="button" data-href="{href}">{label}</button>'
        for label, href in actions
    )


def _sc_slide(index, eyebrow, title, subtitle, points, note, actions=None, extra=""):
    actions = actions or []
    point_html = "".join(f"<li>{point}</li>" for point in points[:3])
    active_class = " is-active" if index == 1 else ""
    return f"""
      <section class="sc-slide{active_class}" data-title="{eyebrow}" data-open="{actions[0][1] if actions else ''}">
        <div class="sc-slide-stage">
          <div class="sc-slide-main">
            <span class="sc-slide-index">{index:02d}</span>
            <span class="sc-slide-eyebrow">{eyebrow}</span>
            <h2>{title}</h2>
            {f'<p class="sc-slide-subtitle">{subtitle}</p>' if subtitle else ''}
            <ul class="sc-slide-points">{point_html}</ul>
            {extra}
          </div>
          <aside class="sc-speaker-note">
            <span>ملاحظة المقدم</span>
            <p>{note}</p>
          </aside>
        </div>
        <div class="sc-slide-actions">
          {_sc_slide_actions(actions)}
        </div>
      </section>
    """


def get_demo_presentation_html():
    slides = [
        _sc_slide(
            1,
            "Dashboard Presentation",
            "رحلة ديمو الركن السويسري",
            "عرض حي لإدارة سلسلة ساعات: من البيع داخل الفرع إلى المخزون، الرقم التسلسلي، الضمان، والتقارير التنفيذية.",
            [],
            "ابدأ بهدوء. هذه شريحة افتتاح فقط، لا تدخل في التفاصيل.",
            [],
            """
            <div class="sc-opening-cards">
              <span>بيع داخل الفرع</span>
              <span>مخزون ورقم تسلسلي</span>
              <span>تقارير للإدارة</span>
            </div>
            <button class="sc-start-button sc-next" type="button" data-action="next">ابدأ العرض</button>
            """,
        ),
        _sc_slide(
            2,
            "القصة",
            "السيناريو الذي سنعرضه",
            "",
            [
                "سلسلة متاجر ساعات بعدة فروع.",
                "كل ساعة لها رقم تسلسلي.",
                "الإدارة تريد رؤية المبيعات والمخزون والضمان من مكان واحد.",
            ],
            "ابدأ بالقصة قبل الدخول في الشاشات. اجعل العميل يشعر أن النظام يحاكي واقعه.",
            [("التالي: لوحة الإدارة", "/app/swiss-corner-demo")],
        ),
        _sc_slide(
            3,
            "الإدارة",
            "أولًا: الصورة الإدارية",
            "",
            [
                "مؤشرات عامة للإدارة.",
                "مبيعات حسب الفروع.",
                "بداية سريعة قبل التفاصيل.",
            ],
            "هنا نعطي العميل الصورة الكاملة، ثم ننتقل إلى رحلة البيع الفعلية.",
            [("فتح لوحة الإدارة", "/app/swiss-corner-demo")],
        ),
        _sc_slide(
            4,
            "POS",
            "ثانيًا: تجربة الكاشير",
            "",
            [
                "بيع سريع من نقطة البيع.",
                "اختيار منتج وعميل.",
                "فاتورة مرتبطة بالمخزون.",
            ],
            "لا تشرح كل خصائص POS. ركز على سرعة البيع وقرب التجربة من واقع الفرع.",
            [("فتح نقطة البيع", "/app/point-of-sale")],
        ),
        _sc_slide(
            5,
            "المخزون",
            "ثالثًا: ماذا يحدث بعد البيع؟",
            "",
            [
                "المخزون يتأثر مباشرة.",
                "كل ساعة قابلة للتتبع.",
                "الرقم التسلسلي يربط البيع بالضمان.",
            ],
            "اربط دائمًا بين POS والمخزون والرقم التسلسلي. هذه هي نقطة القوة في ديمو الساعات.",
            [
                ("حركة المخزون", _demo_report_url("حركة المخزون حسب المتجر")),
                ("سجل الأرقام التسلسلية", _demo_report_url("سجل الأرقام التسلسلية")),
            ],
        ),
        _sc_slide(
            6,
            "الضمان",
            "رابعًا: الضمان بعد البيع",
            "",
            [
                "ضمان حسب المنتج.",
                "مرتبط بالفاتورة.",
                "سهولة الرجوع للسجل.",
            ],
            "اشرح أن الضمان ليس ورقة منفصلة، بل جزء من رحلة البيع وخدمة العميل.",
            [("فتح تقرير الضمان", _demo_report_url("تقرير الضمان"))],
        ),
        _sc_slide(
            7,
            "واتساب تجريبي",
            "خامسًا: إشعارات واتساب بدون إرسال فعلي",
            "",
            [
                "Dry Run فقط.",
                "سجل محاولات واضح.",
                "لا يوجد إرسال حقيقي أثناء العرض.",
            ],
            "أكد للعميل أن هذا وضع تجريبي آمن، ولا يتم إرسال رسائل فعلية.",
            [("فتح سجل واتساب التجريبي", _demo_report_url("سجل تسليم فواتير واتساب"))],
        ),
        _sc_slide(
            8,
            "HR",
            "سادسًا: الفريق التشغيلي",
            "",
            [
                "الموظفون.",
                "الحضور.",
                "الرواتب.",
            ],
            "وضح أن النظام لا يدير المبيعات فقط، بل يدير الفريق الذي يشغل الفروع.",
            [
                ("الموظفون", "/app/employee"),
                ("الحضور", "/app/attendance"),
                ("الرواتب", "/app/salary-slip"),
            ],
        ),
        _sc_slide(
            9,
            "التقارير",
            "أخيرًا: الأرقام التي تساعد الإدارة",
            "",
            [
                "ربحية حسب الفرع والعلامة.",
                "منتجات سريعة وبطيئة الحركة.",
                "قرارات مبنية على بيانات.",
            ],
            "اختم هنا. هذه هي القيمة الإدارية: رؤية واضحة بدل متابعة يدوية.",
            [
                ("الربحية", _demo_report_url("الربحية حسب الفرع والعلامة")),
                ("حركة المنتجات", _demo_report_url("الساعات السريعة والبطيئة الحركة")),
            ],
        ),
        _sc_slide(
            10,
            "الخلاصة",
            "النتيجة",
            "",
            [
                "رحلة بيع مترابطة.",
                "مخزون ورقم تسلسلي وضمان.",
                "تقارير واضحة للإدارة.",
            ],
            "اسأل العميل: أي جزء تريد أن ندخل فيه بتفصيل أكثر؟",
            [("فتح لوحة الإدارة", "/app/swiss-corner-demo")],
            '<button class="sc-reset-button sc-restart" type="button" data-action="restart">إعادة العرض</button>',
        ),
    ]
    title_values = [
        "الافتتاحية",
        "القصة",
        "الإدارة",
        "الكاشير",
        "المخزون",
        "الضمان",
        "واتساب",
        "الموارد البشرية",
        "التقارير",
        "النهاية",
    ]
    titles = "".join(
        f'<span class="{"is-active" if index == 0 else ""}">{title}</span>'
        for index, title in enumerate(title_values)
    )
    return f"""
<div class="sc-presentation-deck" dir="rtl" data-current="0">
  <div class="sc-deck-shell">
    <header class="sc-deck-topbar">
      <div>
        <span class="sc-deck-badge">Presentation Deck</span>
        <strong>ديمو الركن السويسري</strong>
      </div>
      <button class="sc-present-toggle sc-present-mode-button" type="button" data-action="present">وضع العرض</button>
    </header>
    <div class="sc-progress-track" aria-hidden="true"><span class="sc-progress-fill"></span></div>
    <main class="sc-slides" aria-live="polite">
      {''.join(slides)}
    </main>
    <footer class="sc-deck-footer">
      <button class="sc-deck-btn sc-prev" type="button" data-action="prev">السابق</button>
      <div class="sc-slide-meta">
        <span class="sc-counter">1 / 10</span>
        <div class="sc-slide-titles">{titles}</div>
      </div>
      <button class="sc-deck-btn primary sc-open-current" type="button" data-action="open">افتح الجزء الحالي</button>
      <button class="sc-deck-btn primary sc-next-footer" type="button" data-action="next">التالي</button>
    </footer>
  </div>
</div>
"""


DEMO_PRESENTATION_BLOCK = "Demo Presentation Deck"


def get_demo_presentation_style():
    css = ""
    try:
        css_path = frappe.get_app_path("demo_standard", "public", "css", "demo_standard.css")
        with open(css_path, encoding="utf-8") as css_file:
            css = css_file.read()
        start = css.find(".sc-presentation-deck")
        css = css[start:] if start >= 0 else css
    except Exception:
        css = ""

    return (
        css
        + """
:host {
  display: block;
  width: 100%;
}
.sc-presentation-deck.is-presenting {
  max-width: none;
  min-height: 100vh;
  padding: 12px;
}
.sc-presentation-deck.is-presenting .sc-deck-shell {
  min-height: calc(100vh - 24px);
}
.sc-presentation-deck.is-presenting .sc-slides,
.sc-presentation-deck.is-presenting .sc-slide {
  min-height: calc(100vh - 170px);
}
"""
    )


def get_demo_presentation_script():
    return r"""
const isInternalDemoHref = (href) => href && (href === "/app/point-of-sale" || href.startsWith("/app/"));
const deck = root_element.querySelector(".sc-presentation-deck");
if (!deck || deck.__scDeckReady) {
  return;
}
deck.__scDeckReady = true;

const getSlides = () => Array.from(deck.querySelectorAll(".sc-slide"));
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const getCurrent = () => {
  const slides = getSlides();
  const activeIndex = slides.findIndex((slide) => slide.classList.contains("is-active"));
  const savedIndex = Number(deck.dataset.current || 0);
  return clamp(Number.isFinite(savedIndex) ? savedIndex : activeIndex, 0, Math.max(slides.length - 1, 0));
};

const getCurrentOpenHref = () => {
  const slides = getSlides();
  const activeSlide = slides[getCurrent()];
  const firstAction = activeSlide?.querySelector(".sc-slide-action[data-href], .sc-open-link[data-href]");
  return firstAction?.dataset.href || activeSlide?.dataset.open || "";
};

const render = (index) => {
  const slides = getSlides();
  if (!slides.length) return;
  const current = clamp(Number(index ?? deck.dataset.current ?? 0), 0, slides.length - 1);
  deck.dataset.current = String(current);
  slides.forEach((slide, slideIndex) => {
    slide.classList.toggle("is-active", slideIndex === current);
  });
  root_element.querySelectorAll(".sc-slide-titles span").forEach((pill, pillIndex) => {
    pill.classList.toggle("is-active", pillIndex === current);
  });
  const progress = root_element.querySelector(".sc-progress-fill");
  if (progress) progress.style.width = `${((current + 1) / slides.length) * 100}%`;
  const counter = root_element.querySelector(".sc-counter");
  if (counter) counter.textContent = `${current + 1} / ${slides.length}`;
  const prevBtn = root_element.querySelector('[data-action="prev"], .sc-prev');
  const nextBtn = root_element.querySelector('[data-action="next"].sc-next-footer, .sc-next-footer');
  if (prevBtn) prevBtn.disabled = current === 0;
  if (nextBtn) nextBtn.disabled = current === slides.length - 1;
  const openBtn = root_element.querySelector('[data-action="open"], .sc-open-current');
  const href = getCurrentOpenHref();
  if (openBtn) {
    openBtn.disabled = !isInternalDemoHref(href);
    openBtn.dataset.href = href || "";
  }
};

const go = (deltaOrIndex, absolute = false) => {
  render(absolute ? deltaOrIndex : getCurrent() + deltaOrIndex);
};

const openHref = (href) => {
  if (isInternalDemoHref(href)) window.location.href = href;
};

const setPresenting = (active) => {
  deck.classList.toggle("is-presenting", active);
  document.body.classList.toggle("sc-presentation-mode", active);
  root_element.querySelectorAll(".sc-present-toggle, .sc-present-mode-button").forEach((button) => {
    button.textContent = active ? "\u0625\u0646\u0647\u0627\u0621 \u0648\u0636\u0639 \u0627\u0644\u0639\u0631\u0636" : "\u0648\u0636\u0639 \u0627\u0644\u0639\u0631\u0636";
  });
};

root_element.addEventListener("click", (event) => {
  const button = event.target.closest("button, [data-href]");
  if (!button || !root_element.contains(button)) return;
  const action = button.dataset.action || "";
  if (action === "next" || button.classList.contains("sc-next") || button.classList.contains("sc-next-footer")) {
    event.preventDefault();
    go(1);
    return;
  }
  if (action === "prev" || button.classList.contains("sc-prev")) {
    event.preventDefault();
    go(-1);
    return;
  }
  if (action === "restart" || button.classList.contains("sc-restart")) {
    event.preventDefault();
    go(0, true);
    return;
  }
  if (action === "present" || button.classList.contains("sc-present-mode-button")) {
    event.preventDefault();
    setPresenting(!deck.classList.contains("is-presenting"));
    button.blur();
    return;
  }
  if (action === "open" || button.classList.contains("sc-open-current")) {
    event.preventDefault();
    openHref(button.dataset.href || getCurrentOpenHref());
    return;
  }
  if (button.dataset.href || button.classList.contains("sc-open-link")) {
    event.preventDefault();
    openHref(button.dataset.href);
  }
});

window.__scActivePresentationDeck = { go, render, setPresenting };
if (!window.__scPresentationKeyboardBound) {
  window.__scPresentationKeyboardBound = true;
  document.addEventListener("keydown", (event) => {
    const api = window.__scActivePresentationDeck;
    if (!api) return;
    const tag = document.activeElement?.tagName;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      api.go(1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      api.go(-1);
    } else if (event.key === "Enter") {
      event.preventDefault();
      api.go(1);
    } else if (event.key === "Escape") {
      api.setPresenting(false);
    }
  });
}

render(0);
"""


def ensure_demo_presentation_custom_block():
    values = {
        "doctype": "Custom HTML Block",
        "name": DEMO_PRESENTATION_BLOCK,
        "html": get_demo_presentation_html(),
        "style": get_demo_presentation_style(),
        "script": get_demo_presentation_script(),
        "private": 0,
        "roles": [],
    }
    doc = (
        frappe.get_doc("Custom HTML Block", DEMO_PRESENTATION_BLOCK)
        if frappe.db.exists("Custom HTML Block", DEMO_PRESENTATION_BLOCK)
        else frappe.get_doc(values)
    )
    for key, value in values.items():
        if key == "doctype":
            continue
        if key == "roles":
            doc.set(key, value)
        else:
            setattr(doc, key, value)
    save_doc(doc)
    return doc


def _demo_record_count(doctype, filters=None):
    try:
        if not frappe.db.exists("DocType", doctype):
            return 0
        return frappe.db.count(doctype, filters or {})
    except Exception:
        return 0


def _demo_existing_report_count(report_names):
    total = 0
    for report_name in report_names:
        if frappe.db.exists("Report", report_name):
            total += 1
    return total


def _demo_sample_url(doctype, filters=None, route=None):
    try:
        if not frappe.db.exists("DocType", doctype):
            return ""
        records = frappe.get_all(
            doctype,
            filters=filters or {},
            pluck="name",
            order_by="modified desc",
            limit=1,
        )
        if not records:
            return ""
        route = route or doctype.lower().replace(" ", "-")
        return f"/app/{route}/{records[0]}"
    except Exception:
        return ""


def _demo_kpis():
    report_names = [
        "تقرير مبيعات الفروع",
        "ملخص مبيعات نقطة البيع",
        "حركة المخزون حسب المتجر",
        "سجل الأرقام التسلسلية",
        "تقرير الضمان",
        "الربحية حسب الفرع والعلامة",
        "الساعات السريعة والبطيئة الحركة",
        "ملخص تحويلات الفروع",
        "سجل تسليم فواتير واتساب",
    ]
    return [
        ("إجمالي الفواتير", _demo_record_count("Sales Invoice", {"company": COMPANY}), "فاتورة بيع"),
        ("الفروع", _demo_record_count("Branch", {"name": ["like", f"{PREFIX}%"]}), "فرع تشغيلي"),
        ("نقاط البيع", _demo_record_count("POS Profile", {"company": COMPANY}), "POS Profile"),
        ("الأصناف", _demo_record_count("Item", {"item_code": ["like", f"{MARKER}%"]}), "صنف ديمو"),
        ("الأرقام التسلسلية", _demo_record_count("Serial No", {"item_code": ["like", f"{MARKER}%"]}), "Serial No"),
        ("عملاء الديمو", _demo_record_count("Customer", {"name": ["like", f"{PREFIX}%"]}), "عميل"),
        ("تقارير العرض", _demo_existing_report_count(report_names), "تقرير جاهز"),
        ("سجلات واتساب", _demo_record_count("WhatsApp Message Log"), "Dry Run / Log"),
    ]


def _demo_action(label, href, tone=""):
    tone_class = f" {tone}" if tone else ""
    return f'<a class="scx-action{tone_class}" href="{html.escape(href)}">{html.escape(label)}</a>'


def _demo_feature_card(title, body, icon, href, label="فتح"):
    return f"""
      <article class="scx-feature-card">
        <div class="scx-icon">{icon}</div>
        <h3>{html.escape(title)}</h3>
        <p>{html.escape(body)}</p>
        {_demo_action(label, href)}
      </article>
    """


def _demo_journey_step(number, title, say, href, label="Open"):
    return f"""
      <article class="scx-step">
        <span class="scx-step-number">{number:02d}</span>
        <div>
          <h3>{html.escape(title)}</h3>
          <p>{html.escape(say)}</p>
        </div>
        {_demo_action(label, href, "compact")}
      </article>
    """


def get_demo_presentation_html():
    sample_invoice_url = _demo_sample_url("Sales Invoice", {"company": COMPANY}, "sales-invoice") or "/app/sales-invoice"
    sample_serial_url = _demo_sample_url("Serial No", {"item_code": ["like", f"{MARKER}%"]}, "serial-no") or "/app/serial-no"
    sample_employee_url = _demo_sample_url("Employee", {"company": COMPANY}, "employee") or "/app/employee"

    kpi_cards = "".join(
        f"""
        <article class="scx-kpi-card">
          <span>{html.escape(label)}</span>
          <strong>{value}</strong>
          <small>{html.escape(caption)}</small>
        </article>
        """
        for label, value, caption in _demo_kpis()
    )

    features = "".join(
        [
            _demo_feature_card("نظرة تنفيذية", "لوحة بداية منظمة تعطي صورة سريعة عن الديمو ومسار العرض.", "⌁", "/app/swiss-corner-demo", "لوحة الإدارة"),
            _demo_feature_card("المبيعات ونقطة البيع", "بيع داخل الفرع، عميل، منتجات، طرق دفع، وفاتورة مباشرة.", "POS", "/app/point-of-sale", "افتح POS"),
            _demo_feature_card("المخزون والتحويلات", "حركة المخزون بين الفروع والمتاجر مع رؤية تشغيلية واضحة.", "▦", _demo_report_url("حركة المخزون حسب المتجر"), "تقرير المخزون"),
            _demo_feature_card("الأرقام التسلسلية", "تتبع الساعة من دخولها وحتى البيع وخدمة ما بعد البيع.", "#", _demo_report_url("سجل الأرقام التسلسلية"), "سجل Serial"),
            _demo_feature_card("الضمان", "ربط الضمان بالفاتورة والرقم التسلسلي لتسهيل الرجوع للسجل.", "✓", _demo_report_url("تقرير الضمان"), "تقرير الضمان"),
            _demo_feature_card("الفواتير والطباعة", "قالب فاتورة احترافي يصلح للعرض والطباعة والإرسال.", "PDF", sample_invoice_url, "فاتورة نموذجية"),
            _demo_feature_card("واتساب الفواتير", "سجل تسليم تجريبي آمن يوضح الفكرة بدون إرسال فعلي.", "WA", _demo_report_url("سجل تسليم فواتير واتساب"), "سجل واتساب"),
            _demo_feature_card("الموارد البشرية", "موظفون، حضور، ورواتب كجزء من تشغيل الفروع.", "HR", "/app/employee", "الموظفون"),
        ]
    )

    journey = "".join(
        [
            _demo_journey_step(1, "Executive Overview", "ابدأ بصورة إدارية مختصرة قبل الدخول في التفاصيل.", "/app/swiss-corner-demo", "افتح"),
            _demo_journey_step(2, "Store / Branch Sales", "اعرض اختلاف أداء الفروع ومؤشرات البيع.", _demo_report_url("تقرير مبيعات الفروع"), "افتح"),
            _demo_journey_step(3, "POS Experience", "انتقل لتجربة الكاشير: منتج، عميل، دفع، فاتورة.", "/app/point-of-sale", "افتح"),
            _demo_journey_step(4, "Inventory & Serials", "اربط البيع بتأثيره على المخزون والرقم التسلسلي.", _demo_report_url("سجل الأرقام التسلسلية"), "افتح"),
            _demo_journey_step(5, "Warranty & After-sales", "وضح رحلة الضمان وخدمة ما بعد البيع.", _demo_report_url("تقرير الضمان"), "افتح"),
            _demo_journey_step(6, "Print Format & Invoice", "افتح فاتورة نموذجية وبيّن جودة الطباعة.", sample_invoice_url, "افتح"),
            _demo_journey_step(7, "WhatsApp Delivery Log", "اعرض سجل التسليم التجريبي والفكرة التشغيلية.", _demo_report_url("سجل تسليم فواتير واتساب"), "افتح"),
            _demo_journey_step(8, "HR / Operations", "اختم جانب تشغيل الفريق: موظفين، حضور، رواتب.", sample_employee_url, "افتح"),
            _demo_journey_step(9, "Business Value", "اختم بالربحية والمنتجات السريعة والبطيئة.", _demo_report_url("الربحية حسب الفرع والعلامة"), "افتح"),
        ]
    )

    nav_links = [
        ("لوحة الإدارة", "/app/swiss-corner-demo"),
        ("نقطة البيع", "/app/point-of-sale"),
        ("تقرير مبيعات الفروع", _demo_report_url("تقرير مبيعات الفروع")),
        ("ملخص POS", _demo_report_url("ملخص مبيعات نقطة البيع")),
        ("حركة المخزون", _demo_report_url("حركة المخزون حسب المتجر")),
        ("سجل Serial", _demo_report_url("سجل الأرقام التسلسلية")),
        ("تقرير الضمان", _demo_report_url("تقرير الضمان")),
        ("سجل واتساب", _demo_report_url("سجل تسليم فواتير واتساب")),
        ("فاتورة نموذجية", sample_invoice_url),
        ("رقم تسلسلي جاهز", sample_serial_url),
        ("الموظفون", "/app/employee"),
        ("الحضور", "/app/attendance"),
        ("الرواتب", "/app/salary-slip"),
        ("الربحية", _demo_report_url("الربحية حسب الفرع والعلامة")),
        ("المنتجات السريعة والبطيئة", _demo_report_url("الساعات السريعة والبطيئة الحركة")),
    ]
    smart_nav = "".join(
        f'<a class="scx-nav-chip" href="{html.escape(href)}">{html.escape(label)}</a>'
        for label, href in nav_links
    )

    return f"""
<div class="scx-demo-start" dir="rtl">
  <section class="scx-hero" aria-label="Demo opening">
    <div class="scx-hero-copy">
      <span class="scx-badge">Executive Demo Start Page</span>
      <h1>Swiss Corner Watches<br><em>الركن السويسري للساعات</em></h1>
      <p>واجهة بداية العرض: رحلة Retail كاملة من الفرع إلى المخزون، الرقم التسلسلي، الضمان، الفاتورة، واتساب، والتقارير التنفيذية.</p>
      <div class="scx-hero-actions">
        {_demo_action("ابدأ العرض", "#scx-journey", "primary")}
        {_demo_action("افتح نقطة البيع", "/app/point-of-sale")}
        {_demo_action("لوحة الإدارة", "/app/swiss-corner-demo")}
      </div>
    </div>
    <div class="scx-hero-panel">
      <span>Start Here</span>
      <strong>مسار عرض واضح، روابط مباشرة، ومؤشرات جاهزة للحديث التنفيذي.</strong>
      <small>ابدأ بالقصة التجارية، ثم انتقل إلى رحلة البيع، ثم اختم بقيمة التقارير للإدارة.</small>
    </div>
  </section>

  <section class="scx-section">
    <div class="scx-section-head">
      <span>What will be shown</span>
      <h2>ماذا سنعرض في هذا الديمو؟</h2>
    </div>
    <div class="scx-feature-grid">{features}</div>
  </section>

  <section class="scx-section" id="scx-journey">
    <div class="scx-section-head">
      <span>Recommended Demo Flow</span>
      <h2>رحلة العرض المقترحة</h2>
    </div>
    <div class="scx-journey">{journey}</div>
  </section>

  <section class="scx-section scx-snapshot">
    <div class="scx-section-head">
      <span>Executive Snapshot</span>
      <h2>لقطة تنفيذية سريعة</h2>
    </div>
    <div class="scx-kpi-grid">{kpi_cards}</div>
  </section>

  <section class="scx-section">
    <div class="scx-section-head">
      <span>Smart Navigation Hub</span>
      <h2>مركز التنقل السريع أثناء العرض</h2>
    </div>
    <div class="scx-nav-grid">{smart_nav}</div>
  </section>

  <section class="scx-notes">
    <div>
      <span>Presenter Notes</span>
      <h2>ملاحظات مقدم العرض</h2>
    </div>
    <ul>
      <li>ابدأ بالقصة: سلسلة ساعات متعددة الفروع تحتاج رؤية موحدة.</li>
      <li>اربط دائمًا بين POS والمخزون والرقم التسلسلي والضمان.</li>
      <li>واتساب في وضع Dry Run آمن للعرض، بدون إرسال فعلي.</li>
      <li>الفاتورة المعروضة PDF/Print Demo، وأي اعتماد ضريبي رسمي يحتاج تهيئة منفصلة.</li>
      <li>اختم بقيمة التقارير: قرارات أسرع، رقابة أعلى، وتشغيل أوضح.</li>
    </ul>
  </section>
</div>
"""


def get_demo_presentation_style():
    return """
:host {
  display: block;
  width: 100%;
}
.scx-demo-start {
  --scx-navy: #101827;
  --scx-navy-2: #172235;
  --scx-gold: #c9973f;
  --scx-cream: #f8f3ea;
  --scx-soft: #fffaf2;
  --scx-border: #e6d6bd;
  --scx-muted: #667085;
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding: 10px 4px 34px;
  direction: rtl;
  text-align: right;
  color: #182230;
  font-family: "InterVariable", "Inter", "Noto Sans Arabic", "Noto Naskh Arabic", "DejaVu Sans", sans-serif;
}
.scx-demo-start * {
  box-sizing: border-box;
}
.scx-hero {
  min-height: 390px;
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.7fr);
  gap: 22px;
  align-items: stretch;
  padding: 28px;
  border: 1px solid rgba(201, 151, 63, 0.38);
  border-radius: 28px;
  background:
    radial-gradient(circle at 12% 14%, rgba(201,151,63,.22), transparent 34%),
    linear-gradient(135deg, var(--scx-navy), var(--scx-navy-2));
  box-shadow: 0 26px 70px rgba(16, 24, 39, 0.16);
  overflow: hidden;
}
.scx-hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}
.scx-badge,
.scx-section-head span,
.scx-notes span {
  width: fit-content;
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 5px 11px;
  border-radius: 999px;
  background: rgba(201,151,63,.16);
  color: #8f641d;
  border: 1px solid rgba(201,151,63,.28);
  font-size: 12px;
  font-weight: 900;
}
.scx-hero .scx-badge {
  background: rgba(255,255,255,.08);
  color: #f5d995;
}
.scx-hero h1 {
  margin: 22px 0 12px;
  color: #fff;
  font-size: clamp(34px, 5vw, 62px);
  line-height: 1.18;
  font-weight: 950;
  letter-spacing: 0;
}
.scx-hero h1 em {
  color: #f8dfae;
  font-style: normal;
  font-size: .72em;
}
.scx-hero p {
  max-width: 820px;
  margin: 0;
  color: #d9e1ee;
  font-size: 17px;
  line-height: 1.85;
}
.scx-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 26px;
}
.scx-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 9px 15px;
  border: 1px solid var(--scx-border);
  border-radius: 13px;
  background: #fff;
  color: var(--scx-navy);
  text-decoration: none;
  font-size: 14px;
  font-weight: 900;
  transition: transform .14s ease, border-color .14s ease, background .14s ease;
}
.scx-action:hover {
  transform: translateY(-1px);
  border-color: var(--scx-gold);
  background: #fff7e8;
  text-decoration: none;
}
.scx-action.primary {
  background: var(--scx-gold);
  border-color: var(--scx-gold);
  color: #101827;
}
.scx-action.compact {
  min-width: 86px;
  min-height: 34px;
  padding: 7px 12px;
}
.scx-hero-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 18px;
  padding: 24px;
  border-radius: 22px;
  background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.16);
  color: #fff;
}
.scx-hero-panel span {
  color: #f8dfae;
  font-size: 13px;
  font-weight: 950;
  text-transform: uppercase;
}
.scx-hero-panel strong {
  font-size: 26px;
  line-height: 1.45;
}
.scx-hero-panel small {
  color: #d8e0eb;
  font-size: 14px;
  line-height: 1.8;
}
.scx-section {
  margin-top: 26px;
  padding: 24px;
  border: 1px solid var(--scx-border);
  border-radius: 24px;
  background: linear-gradient(180deg, #fff, var(--scx-soft));
  box-shadow: 0 18px 44px rgba(16, 24, 39, .06);
}
.scx-section-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: end;
  margin-bottom: 18px;
}
.scx-section-head h2,
.scx-notes h2 {
  margin: 0;
  color: var(--scx-navy);
  font-size: 25px;
  line-height: 1.35;
  font-weight: 950;
}
.scx-feature-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}
.scx-feature-card,
.scx-kpi-card,
.scx-step {
  border: 1px solid #eadcc8;
  border-radius: 18px;
  background: rgba(255,255,255,.92);
  box-shadow: 0 12px 28px rgba(16,24,39,.045);
}
.scx-feature-card {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
}
.scx-icon {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #fff4df;
  color: #7d551c;
  border: 1px solid #ead3a9;
  font-weight: 950;
}
.scx-feature-card h3,
.scx-step h3 {
  margin: 0;
  color: var(--scx-navy);
  font-size: 17px;
  font-weight: 950;
}
.scx-feature-card p,
.scx-step p {
  flex: 1;
  margin: 0;
  color: var(--scx-muted);
  font-size: 14px;
  line-height: 1.75;
}
.scx-journey {
  display: grid;
  gap: 10px;
}
.scx-step {
  display: grid;
  grid-template-columns: 54px minmax(0,1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 14px;
}
.scx-step-number {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: var(--scx-navy);
  color: #f7d99a;
  font-weight: 950;
}
.scx-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.scx-kpi-card {
  padding: 18px;
}
.scx-kpi-card span {
  display: block;
  color: #667085;
  font-size: 13px;
  font-weight: 800;
}
.scx-kpi-card strong {
  display: block;
  margin: 8px 0 4px;
  color: var(--scx-navy);
  font-size: 32px;
  line-height: 1;
  font-weight: 950;
}
.scx-kpi-card small {
  color: #8f641d;
  font-size: 12px;
  font-weight: 800;
}
.scx-nav-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.scx-nav-chip {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 8px 13px;
  border: 1px solid #ead6b8;
  border-radius: 999px;
  background: #fff;
  color: #1d2939;
  text-decoration: none;
  font-size: 13px;
  font-weight: 850;
}
.scx-nav-chip:hover {
  background: #fff4df;
  border-color: var(--scx-gold);
  text-decoration: none;
}
.scx-notes {
  margin-top: 26px;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 18px;
  padding: 22px;
  border-radius: 24px;
  border: 1px solid rgba(201,151,63,.36);
  background: #101827;
  color: #fff;
}
.scx-notes h2 {
  margin-top: 10px;
  color: #fff;
}
.scx-notes ul {
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
  list-style: none;
}
.scx-notes li {
  position: relative;
  padding: 11px 14px;
  border-radius: 14px;
  background: rgba(255,255,255,.07);
  color: #e5edf8;
  font-size: 14px;
  line-height: 1.75;
}
@media (max-width: 1080px) {
  .scx-feature-grid,
  .scx-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .scx-hero,
  .scx-notes {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 720px) {
  .scx-demo-start {
    padding: 0 0 24px;
  }
  .scx-hero,
  .scx-section,
  .scx-notes {
    border-radius: 18px;
    padding: 18px;
  }
  .scx-feature-grid,
  .scx-kpi-grid,
  .scx-notes ul {
    grid-template-columns: 1fr;
  }
  .scx-step {
    grid-template-columns: 44px minmax(0,1fr);
  }
  .scx-step .scx-action {
    grid-column: 1 / -1;
    width: 100%;
  }
}
"""


def get_demo_presentation_script():
    return """
const root = root_element;
root.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener('click', (event) => {
    const target = root.querySelector(link.getAttribute('href'));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});
root.querySelectorAll('a[href^="/app/"], a[href="/app/point-of-sale"]').forEach((link) => {
  link.setAttribute('target', '_self');
});
"""


def setup_demo_presentation_workspace():
    ensure_demo_presentation_custom_block()
    content = [
        {
            "id": "sc-presentation-deck",
            "type": "custom_block",
            "data": {"custom_block_name": DEMO_PRESENTATION_BLOCK, "col": 12},
        }
    ]
    values = {
        "doctype": "Workspace",
        "name": GUIDE_WORKSPACE,
        "label": GUIDE_WORKSPACE,
        "title": "Demo",
        "module": MODULE,
        "icon": "rocket",
        "indicator_color": "orange",
        "public": 1,
        "is_hidden": 0,
        "sequence_id": 1,
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [],
        "links": [],
        "charts": [],
        "number_cards": [],
        "quick_lists": [],
        "custom_blocks": [{"custom_block_name": DEMO_PRESENTATION_BLOCK, "label": DEMO_PRESENTATION_BLOCK}],
        "roles": [{"role": "System Manager"}, {"role": "Demo Viewer"}, {"role": "Cashier"}],
    }
    doc = frappe.get_doc("Workspace", GUIDE_WORKSPACE) if frappe.db.exists("Workspace", GUIDE_WORKSPACE) else frappe.get_doc(values)
    for key, value in values.items():
        if key == "doctype":
            continue
        if key in {"shortcuts", "links", "charts", "number_cards", "quick_lists", "custom_blocks", "roles"}:
            doc.set(key, value)
        else:
            setattr(doc, key, value)
    save_doc(doc)
    frappe.clear_cache()
    return {"workspace": GUIDE_WORKSPACE, "route": "/app/demo", "slides": 10, "block": DEMO_PRESENTATION_BLOCK}


def ensure_demo_guide_workspace(chart_names=None, card_names=None):
    return setup_demo_presentation_workspace()


SC_PRESENTATION_SLIDES = [
    {
        "key": "intro",
        "label": "البداية",
        "badge": "ERPNext Demo",
        "title": "ERPNext كمنصة موحدة لإدارة المؤسسة",
        "description": "منصة واحدة تربط الفروع، المبيعات، المخزون، الحسابات، الموارد البشرية، والتقارير التنفيذية.",
        "points": [
            "إدارة تشغيلية ومالية في بيئة واحدة",
            "بيانات مترابطة بدل الأنظمة المنفصلة",
            "قابل للتوسع والربط مع بيئات أخرى",
        ],
        "actions": [{"label": "ابدأ العرض", "action": "next", "primary": True}],
        "route": "",
    },
    {
        "key": "scope",
        "label": "النطاق",
        "badge": "Demo Scope",
        "title": "ماذا سنعرض اليوم؟",
        "description": "عرض مركز على الجوانب الأكثر تأثيرًا في تشغيل سلسلة فروع Retail.",
        "points": [
            "الإدارة المالية والتجارية للفروع",
            "نقاط البيع وتشغيل الفروع",
            "الموارد البشرية والتكاملات والتقارير",
        ],
        "actions": [{"label": "التالي: الإدارة المالية", "action": "next", "primary": True}],
        "route": "/app/accounting",
    },
    {
        "key": "finance",
        "label": "المالية",
        "badge": "Finance",
        "title": "الإدارة المالية والتجارية",
        "description": "من العمليات اليومية إلى مخرجات مالية تساعد الإدارة على القرار.",
        "points": [
            "تقارير مالية ومحاسبية",
            "تحليل مبيعات وربحية الفروع",
            "قوائم أسعار، عروض، وكوبونات",
        ],
        "actions": [
            {"label": "افتح المكتب المالي", "route": "/app/accounting", "primary": True},
            {"label": "تقرير مبيعات الفروع", "route": _demo_report_url("تقرير مبيعات الفروع")},
        ],
        "route": "/app/accounting",
    },
    {
        "key": "branches",
        "label": "الفروع",
        "badge": "Branches",
        "title": "إدارة الفروع والمبيعات",
        "description": "رؤية موحدة لأداء الفروع بدل المتابعة اليدوية المتفرقة.",
        "points": [
            "مبيعات حسب الفرع",
            "أداء المنتجات والعلامات",
            "مؤشرات تساعد الإدارة على المقارنة",
        ],
        "actions": [
            {"label": "لوحة الإدارة التنفيذية", "route": "/app/swiss-corner-demo", "primary": True},
            {"label": "الربحية حسب الفرع والعلامة", "route": _demo_report_url("الربحية حسب الفرع والعلامة")},
        ],
        "route": "/app/swiss-corner-demo",
    },
    {
        "key": "pos",
        "label": "POS",
        "badge": "Point of Sale",
        "title": "نقاط البيع وتشغيل الفرع",
        "description": "تجربة كاشير سريعة مع أثر مباشر على المخزون والحسابات.",
        "points": [
            "بيع سريع ومرتجعات",
            "دفع متعدد وكوبونات",
            "فتح وإغلاق نقطة البيع",
        ],
        "actions": [{"label": "فتح نقطة البيع", "route": "/app/point-of-sale", "primary": True}],
        "route": "/app/point-of-sale",
    },
    {
        "key": "stock_serial",
        "label": "المخزون",
        "badge": "Inventory",
        "title": "المخزون والرقم التسلسلي",
        "description": "تتبع كل ساعة من دخولها إلى بيعها وخدمة ما بعد البيع.",
        "points": [
            "حركة مخزون واضحة",
            "بيع بالرقم التسلسلي",
            "ربط البيع بالمخزون والضمان",
        ],
        "actions": [
            {"label": "حركة المخزون", "route": _demo_report_url("حركة المخزون حسب المتجر"), "primary": True},
            {"label": "سجل الأرقام التسلسلية", "route": _demo_report_url("سجل الأرقام التسلسلية")},
        ],
        "route": _demo_report_url("حركة المخزون حسب المتجر"),
    },
    {
        "key": "warranty",
        "label": "الضمان",
        "badge": "After Sales",
        "title": "الضمان وخدمة ما بعد البيع",
        "description": "تحويل الضمان من إجراء منفصل إلى جزء من رحلة البيع.",
        "points": [
            "ضمان مرتبط بالفاتورة",
            "رجوع سريع لسجل المنتج",
            "تقليل الأخطاء في خدمة العميل",
        ],
        "actions": [{"label": "تقرير الضمان", "route": _demo_report_url("تقرير الضمان"), "primary": True}],
        "route": _demo_report_url("تقرير الضمان"),
    },
    {
        "key": "hr",
        "label": "HR",
        "badge": "People Operations",
        "title": "إدارة الموارد البشرية",
        "description": "إدارة الفريق التشغيلي الذي يدير الفروع والمبيعات.",
        "points": [
            "ملفات الموظفين والفروع",
            "حضور، غياب، إجازات، وأذونات",
            "سلف، رواتب، وربط بصمة عند الحاجة",
        ],
        "actions": [
            {"label": "الموظفون", "route": "/app/employee", "primary": True},
            {"label": "الحضور", "route": "/app/attendance"},
            {"label": "الرواتب", "route": "/app/salary-slip"},
        ],
        "route": "/app/employee",
    },
    {
        "key": "integrations",
        "label": "التكاملات",
        "badge": "Integrations",
        "title": "التكاملات والأتمتة",
        "description": "النظام قابل للربط مع القنوات الخارجية دون عزل البيانات.",
        "points": [
            "واتساب تجريبي آمن Dry Run",
            "متاجر إلكترونية وأنظمة خارجية",
            "قابلية الأتمتة والدمج مع الذكاء الاصطناعي",
        ],
        "actions": [{"label": "سجل واتساب التجريبي", "route": _demo_report_url("سجل تسليم فواتير واتساب"), "primary": True}],
        "route": _demo_report_url("سجل تسليم فواتير واتساب"),
    },
    {
        "key": "executive",
        "label": "الخلاصة",
        "badge": "Executive Value",
        "title": "الخلاصة التنفيذية",
        "description": "كل عملية داخل النظام تتحول في النهاية إلى رؤية إدارية واضحة.",
        "points": [
            "داشبورد وتقارير حسب الدور",
            "Workspaces وصلاحيات للمستخدمين",
            "قرارات مبنية على بيانات فعلية",
        ],
        "actions": [
            {"label": "لوحة الإدارة", "route": "/app/swiss-corner-demo", "primary": True},
            {"label": "إعادة العرض", "action": "reset"},
        ],
        "route": "/app/swiss-corner-demo",
    },
]


def _sc_deck_button(action):
    attrs = ['class="sc-btn{}"'.format(" sc-btn-primary" if action.get("primary") else ""), 'type="button"']
    if action.get("action"):
        attrs.append(f'data-sc-action="{html.escape(action["action"])}"')
    if action.get("route"):
        attrs.append(f'data-sc-route="{html.escape(action["route"])}"')
    return f"<button {' '.join(attrs)}>{html.escape(action['label'])}</button>"


def _sc_deck_slide(slide, index):
    is_active = " is-active" if index == 0 else ""
    points = "".join(f"<li>{html.escape(point)}</li>" for point in slide["points"][:3])
    actions = "".join(_sc_deck_button(action) for action in slide.get("actions", [])[:3])
    return f"""
    <section class="sc-slide{is_active}" data-sc-slide="{index}" data-sc-key="{html.escape(slide['key'])}" data-current-route="{html.escape(slide.get('route') or '')}">
      <div class="sc-slide-content">
        <span class="sc-slide-badge">{html.escape(slide['badge'])}</span>
        <h2>{html.escape(slide['title'])}</h2>
        <p class="sc-slide-description">{html.escape(slide['description'])}</p>
        <ul class="sc-slide-points">{points}</ul>
      </div>
      <div class="sc-actions">{actions}</div>
    </section>
    """


def get_demo_presentation_html():
    slides = "".join(_sc_deck_slide(slide, index) for index, slide in enumerate(SC_PRESENTATION_SLIDES))
    tabs = "".join(
        f'<button class="sc-slide-tab{" is-active" if index == 0 else ""}" type="button" data-sc-goto="{index}">{html.escape(slide["label"])}</button>'
        for index, slide in enumerate(SC_PRESENTATION_SLIDES)
    )
    return f"""
<div class="sc-presentation-deck" dir="rtl" data-sc-current="0">
  <div class="sc-deck-frame">
    <header class="sc-deck-header">
      <div>
        <span class="sc-deck-kicker">Presentation Deck</span>
        <h1>عرض ديمو ERPNext التشغيلي</h1>
      </div>
      <button class="sc-btn sc-btn-ghost" type="button" data-sc-action="presentation-mode">وضع العرض</button>
    </header>
    <div class="sc-progress" aria-hidden="true"><span class="sc-progress-bar"></span></div>
    <main class="sc-slides" aria-live="polite">{slides}</main>
    <footer class="sc-deck-footer">
      <button class="sc-btn" type="button" data-sc-action="prev">السابق</button>
      <div class="sc-deck-status">
        <strong class="sc-counter">1 / {len(SC_PRESENTATION_SLIDES)}</strong>
        <nav class="sc-slide-tabs" aria-label="شرائح العرض">{tabs}</nav>
      </div>
      <button class="sc-btn sc-btn-primary" type="button" data-sc-action="open-current">افتح الجزء الحالي</button>
      <button class="sc-btn sc-btn-primary" type="button" data-sc-action="next">التالي</button>
    </footer>
  </div>
</div>
"""


def get_demo_presentation_style():
    css = ""
    try:
        css_path = frappe.get_app_path("demo_standard", "public", "css", "demo_standard.css")
        with open(css_path, encoding="utf-8") as css_file:
            source = css_file.read()
        start_marker = "/* SC_PRESENTATION_DECK_START */"
        end_marker = "/* SC_PRESENTATION_DECK_END */"
        start = source.find(start_marker)
        end = source.find(end_marker)
        if start >= 0 and end > start:
            css = source[start + len(start_marker) : end]
    except Exception:
        css = ""
    return css


def get_demo_presentation_script():
    return r"""
(function () {
  const deck = root_element.querySelector(".sc-presentation-deck");
  if (!deck) return;

  const internal = (route) => route && (route === "/app/point-of-sale" || route.indexOf("/app/") === 0);
  const slides = () => Array.from(deck.querySelectorAll(".sc-slide"));
  const clamp = (value) => {
    const count = slides().length || 1;
    const number = Number(value);
    return Math.max(0, Math.min(count - 1, Number.isFinite(number) ? number : 0));
  };
  const current = () => clamp(deck.dataset.scCurrent || deck.dataset.current || 0);
  const route = () => {
    const active = slides()[current()];
    const button = active && active.querySelector("[data-sc-route]");
    return (button && button.dataset.scRoute) || (active && active.dataset.currentRoute) || "";
  };
  const setMode = (active) => {
    document.body.classList.toggle("sc-presentation-mode", !!active);
    deck.classList.toggle("sc-presentation-mode", !!active);
    deck.classList.toggle("is-presenting", !!active);
    deck.querySelectorAll('[data-sc-action="presentation-mode"]').forEach((button) => {
      button.textContent = active ? "إنهاء وضع العرض" : "وضع العرض";
    });
  };
  const render = (index) => {
    const list = slides();
    if (!list.length) return;
    const next = clamp(index);
    deck.dataset.scCurrent = String(next);
    deck.dataset.current = String(next);
    list.forEach((slide, slideIndex) => {
      const active = slideIndex === next;
      slide.classList.toggle("is-active", active);
      slide.setAttribute("aria-hidden", active ? "false" : "true");
    });
    deck.querySelectorAll(".sc-slide-tab").forEach((tab, tabIndex) => {
      const active = tabIndex === next;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-current", active ? "step" : "false");
    });
    const counter = deck.querySelector(".sc-counter");
    const progress = deck.querySelector(".sc-progress-bar");
    const open = deck.querySelector('[data-sc-action="open-current"]');
    const prev = deck.querySelector('[data-sc-action="prev"]');
    const nextButton = deck.querySelector('[data-sc-action="next"]');
    if (counter) counter.textContent = `${next + 1} / ${list.length}`;
    if (progress) progress.style.width = `${((next + 1) / list.length) * 100}%`;
    if (prev) prev.disabled = next === 0;
    if (nextButton) nextButton.disabled = next === list.length - 1;
    if (open) {
      const target = route();
      open.disabled = !internal(target);
      open.dataset.scRoute = target || "";
    }
    window.__activeScPresentationDeck = deck;
  };
  const go = (value, absolute) => render(absolute ? value : current() + Number(value || 0));
  const openRoute = (target) => {
    if (!internal(target)) return;
    if (target.indexOf("/app/query-report/") === 0 && window.frappe && frappe.set_route) {
      frappe.set_route("query-report", decodeURIComponent(target.replace("/app/query-report/", "")));
      return;
    }
    window.location.href = encodeURI(target);
  };

  if (deck.dataset.blockController !== "1") {
    deck.dataset.blockController = "1";
    deck.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button || !deck.contains(button)) return;
      const action = button.dataset.scAction || "";
      if (!action && button.dataset.scGoto === undefined && !button.dataset.scRoute) return;
      event.preventDefault();
      event.stopPropagation();
      if (button.dataset.scGoto !== undefined) return go(button.dataset.scGoto, true);
      if (action === "next") return go(1);
      if (action === "prev") return go(-1);
      if (action === "reset") return go(0, true);
      if (action === "presentation-mode") return setMode(!deck.classList.contains("sc-presentation-mode") && !deck.classList.contains("is-presenting"));
      if (action === "open-current") return openRoute(button.dataset.scRoute || route());
      return openRoute(button.dataset.scRoute);
    }, true);
  }

  window.__scDemoDeckRender = render;
  window.__scDemoDeckSetMode = setMode;

  if (!window.__scDemoDeckKeyboard) {
    window.__scDemoDeckKeyboard = true;
    document.addEventListener("keydown", (event) => {
      const activeDeck = window.__activeScPresentationDeck || deck;
      if (!activeDeck || !document.body.contains(activeDeck.getRootNode().host || activeDeck)) return;
      const tag = document.activeElement && document.activeElement.tagName;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
      if (event.key === "Enter" || event.key === "ArrowLeft") {
        event.preventDefault();
        const index = Number(activeDeck.dataset.scCurrent || activeDeck.dataset.current || 0) + 1;
        window.__scDemoDeckRender(index);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        const index = Number(activeDeck.dataset.scCurrent || activeDeck.dataset.current || 0) - 1;
        window.__scDemoDeckRender(index);
      } else if (event.key === "Escape") {
        window.__scDemoDeckSetMode(false);
      }
    }, true);
  }

  render(current());
})();
"""


# ---------------------------------------------------------------------------
# Swiss Corner HR and payroll demo.


HR_DEPARTMENTS = [
    "Swiss Corner - Retail Operations",
    "Swiss Corner - Finance and Accounting",
    "Swiss Corner - Inventory and Logistics",
    "Swiss Corner - HR and Admin",
    "Swiss Corner - After Sales and Warranty",
    "Swiss Corner - E-Commerce",
    "Swiss Corner - Procurement",
]

HR_DESIGNATIONS = [
    "Swiss Corner Store Manager",
    "Swiss Corner Cashier",
    "Swiss Corner Sales Consultant",
    "Swiss Corner Watch Technician",
    "Swiss Corner Inventory Officer",
    "Swiss Corner Accountant",
    "Swiss Corner HR Officer",
    "Swiss Corner E-Commerce Specialist",
    "Swiss Corner Buyer",
]

HR_EMPLOYEES = [
    ("DEMO-SC-EMP-001", "عبدالله", "الرحمن", "Male", "Swiss Corner Store Manager", "Swiss Corner - Retail Operations", "الركن السويسري - الرياض", 12500),
    ("DEMO-SC-EMP-002", "نواف", "العتيبي", "Male", "Swiss Corner Cashier", "Swiss Corner - Retail Operations", "الركن السويسري - الرياض", 6200),
    ("DEMO-SC-EMP-003", "سارة", "القحطاني", "Female", "Swiss Corner Sales Consultant", "Swiss Corner - Retail Operations", "الركن السويسري - الرياض", 7600),
    ("DEMO-SC-EMP-004", "خالد", "الغامدي", "Male", "Swiss Corner Store Manager", "Swiss Corner - Retail Operations", "الركن السويسري - جدة", 11800),
    ("DEMO-SC-EMP-005", "ريم", "الزهراني", "Female", "Swiss Corner Cashier", "Swiss Corner - Retail Operations", "الركن السويسري - جدة", 6100),
    ("DEMO-SC-EMP-006", "محمد", "الدوسري", "Male", "Swiss Corner Sales Consultant", "Swiss Corner - Retail Operations", "الركن السويسري - الخبر", 7300),
    ("DEMO-SC-EMP-007", "نورة", "الحربي", "Female", "Swiss Corner Sales Consultant", "Swiss Corner - Retail Operations", "الركن السويسري - المدينة", 7100),
    ("DEMO-SC-EMP-008", "فيصل", "الشهري", "Male", "Swiss Corner Watch Technician", "Swiss Corner - After Sales and Warranty", "الركن السويسري - مركز الصيانة والضمان", 8800),
    ("DEMO-SC-EMP-009", "ماجد", "العمري", "Male", "Swiss Corner Inventory Officer", "Swiss Corner - Inventory and Logistics", "الركن السويسري - الرياض", 8400),
    ("DEMO-SC-EMP-010", "هند", "المطيري", "Female", "Swiss Corner Accountant", "Swiss Corner - Finance and Accounting", "الركن السويسري - الرياض", 9600),
    ("DEMO-SC-EMP-011", "عبدالعزيز", "السبيعي", "Male", "Swiss Corner E-Commerce Specialist", "Swiss Corner - E-Commerce", "الركن السويسري - المتجر الإلكتروني", 7900),
    ("DEMO-SC-EMP-012", "جواهر", "المالكي", "Female", "Swiss Corner HR Officer", "Swiss Corner - HR and Admin", "الركن السويسري - الرياض", 9000),
]


def setup_swiss_corner_hr_demo():
    """Create HR, payroll, attendance, recruiting, and HR accounting demo data."""
    accounts = ensure_company_and_accounts()
    result = {
        "departments": ensure_hr_departments(),
        "designations": ensure_hr_designations(),
        "employment_types": ensure_hr_employment_types(),
        "holiday_list": ensure_hr_holiday_list(),
        "shift_types": ensure_hr_shift_types(),
    }
    employees = ensure_hr_employees(accounts, result["holiday_list"])
    result["employees"] = employees
    result["attendance"] = ensure_hr_attendance(employees)
    result["leaves"] = ensure_hr_leave_data(employees)
    result["salary_components"] = ensure_hr_salary_components(accounts)
    result["salary_structure"] = ensure_hr_salary_structure(accounts)
    result["payroll"] = ensure_hr_salary_assignments_and_slips(employees, result["salary_structure"])
    result["expenses"] = ensure_hr_expense_claims(accounts, employees)
    result["recruiting"] = ensure_hr_recruiting_demo()
    result["accounting"] = ensure_hr_accounting_entries(accounts)
    result["reports"] = ensure_hr_reports()
    add_hr_to_swiss_corner_workspace()
    add_hr_to_demo_guide()
    frappe.db.commit()
    frappe.clear_cache()
    return result


def ensure_hr_departments():
    out = []
    company = get_operating_company()
    for name in HR_DEPARTMENTS:
        existing = frappe.db.get_value("Department", {"department_name": name}, "name") or (name if frappe.db.exists("Department", name) else None)
        if existing:
            doc = frappe.get_doc("Department", existing)
        else:
            doc = frappe.get_doc({"doctype": "Department", "name": name, "department_name": name, "company": company})
        doc.department_name = name
        if has_field("Department", "company"):
            doc.company = company
        save_doc(doc)
        out.append(doc.name)
    return out


def ensure_hr_designations():
    out = []
    for name in HR_DESIGNATIONS:
        if frappe.db.exists("Designation", name):
            doc = frappe.get_doc("Designation", name)
        else:
            doc = frappe.get_doc({"doctype": "Designation", "name": name, "designation_name": name})
        doc.designation_name = name
        save_doc(doc)
        out.append(doc.name)
    return out


def ensure_hr_employment_types():
    out = []
    for name in ["Swiss Corner Full Time", "Swiss Corner Part Time", "Swiss Corner Contract"]:
        if frappe.db.exists("Employment Type", name):
            doc = frappe.get_doc("Employment Type", name)
        else:
            doc = frappe.get_doc({"doctype": "Employment Type", "name": name, "employee_type_name": name})
        doc.employee_type_name = name
        save_doc(doc)
        out.append(doc.name)
    return out


def ensure_hr_holiday_list():
    year_start = getdate(today()).replace(month=1, day=1)
    year_end = getdate(today()).replace(month=12, day=31)
    name = f"Swiss Corner Holidays {year_start.year}"
    if frappe.db.exists("Holiday List", name):
        doc = frappe.get_doc("Holiday List", name)
    else:
        doc = frappe.get_doc({"doctype": "Holiday List", "name": name, "holiday_list_name": name})
    doc.holiday_list_name = name
    doc.from_date = year_start
    doc.to_date = year_end
    if has_field("Holiday List", "weekly_off"):
        doc.weekly_off = "Friday"
    existing = {str(row.holiday_date) for row in doc.get("holidays", [])}
    day = year_start
    while day <= year_end:
        if day.weekday() == 4 and str(day) not in existing:
            doc.append("holidays", {"holiday_date": day, "description": "Friday Weekly Off"})
        day = add_days(day, 1)
    for holiday_date, description in [
        (year_start.replace(month=2, day=22), "Saudi Founding Day"),
        (year_start.replace(month=9, day=23), "Saudi National Day"),
    ]:
        if str(holiday_date) not in {str(row.holiday_date) for row in doc.get("holidays", [])}:
            doc.append("holidays", {"holiday_date": holiday_date, "description": description})
    save_doc(doc)
    return doc.name


def ensure_hr_shift_types():
    out = []
    shifts = [
        ("Swiss Corner Morning Shift", "09:00:00", "17:00:00"),
        ("Swiss Corner Evening Shift", "14:00:00", "22:00:00"),
        ("Swiss Corner Office Shift", "08:30:00", "16:30:00"),
    ]
    for name, start_time, end_time in shifts:
        if frappe.db.exists("Shift Type", name):
            doc = frappe.get_doc("Shift Type", name)
        else:
            doc = frappe.get_doc({"doctype": "Shift Type", "name": name, "shift_type_name": name})
        doc.start_time = start_time
        doc.end_time = end_time
        if has_field("Shift Type", "enable_auto_attendance"):
            doc.enable_auto_attendance = 0
        save_doc(doc)
        out.append(doc.name)
    return out


def ensure_hr_employees(accounts, holiday_list):
    company = get_operating_company()
    out = []
    joining = add_days(today(), -420)
    for index, (code, first_name, last_name, gender, designation, department, branch, base) in enumerate(HR_EMPLOYEES, start=1):
        department_link = frappe.db.get_value("Department", {"department_name": department}, "name") or department
        employee_email = f"employee{index:02d}@swisscorner.demo"
        existing_employee = frappe.db.get_value("Employee", {"personal_email": employee_email}, "name")
        if not existing_employee and has_field("Employee", "employee_number"):
            existing_employee = frappe.db.get_value("Employee", {"employee_number": code}, "name")
        if existing_employee:
            doc = frappe.get_doc("Employee", existing_employee)
        else:
            doc = frappe.get_doc({"doctype": "Employee"})
        doc.first_name = first_name
        doc.last_name = last_name
        doc.employee_name = f"{first_name} {last_name}"
        if has_field("Employee", "employee_number"):
            doc.employee_number = code
        doc.gender = gender
        doc.date_of_birth = add_days(today(), -(9000 + index * 180))
        doc.date_of_joining = add_days(joining, index * 12)
        doc.company = company
        doc.status = "Active"
        doc.designation = designation
        doc.department = department_link
        if has_field("Employee", "branch") and frappe.db.exists("Branch", branch):
            doc.branch = branch
        if has_field("Employee", "employment_type"):
            doc.employment_type = "Swiss Corner Full Time"
        if has_field("Employee", "holiday_list"):
            doc.holiday_list = holiday_list
        if has_field("Employee", "cell_number"):
            doc.cell_number = f"+96650000{index:04d}"
        if has_field("Employee", "personal_email"):
            doc.personal_email = employee_email
        if has_field("Employee", "default_shift"):
            doc.default_shift = "Swiss Corner Office Shift" if "Accountant" in designation or "HR" in designation else "Swiss Corner Morning Shift"
        save_doc(doc)
        out.append({"employee": doc.name, "name": doc.employee_name, "base": base, "designation": designation, "department": department, "branch": branch})
    return out


def ensure_hr_attendance(employees):
    created = []
    company = get_operating_company()
    statuses = ["Present", "Present", "Present", "Present", "Half Day", "Present", "Present"]
    for emp in employees:
        shift = "Swiss Corner Office Shift" if "Accountant" in emp["designation"] or "HR" in emp["designation"] else "Swiss Corner Morning Shift"
        for offset in range(1, 22):
            attendance_date = add_days(today(), -offset)
            if getdate(attendance_date).weekday() == 4:
                continue
            status = statuses[offset % len(statuses)]
            existing = frappe.db.get_value("Attendance", {"employee": emp["employee"], "attendance_date": attendance_date}, "name")
            if existing:
                doc = frappe.get_doc("Attendance", existing)
            else:
                doc = frappe.get_doc({"doctype": "Attendance", "employee": emp["employee"], "attendance_date": attendance_date})
            doc.company = company
            doc.status = status
            if has_field("Attendance", "shift"):
                doc.shift = shift
            if has_field("Attendance", "working_hours"):
                doc.working_hours = 4 if status == "Half Day" else 8
            if doc.docstatus == 0:
                save_doc(doc)
                try_submit_doc(doc)
            created.append(doc.name)
        ensure_hr_checkins_for_employee(emp["employee"], shift)
    return {"records": len(set(created))}


def ensure_hr_checkins_for_employee(employee, shift):
    base_date = getdate(add_days(today(), -1))
    times = [f"{base_date} 09:01:00", f"{base_date} 17:04:00"]
    for log_type, time_value in zip(["IN", "OUT"], times):
        if frappe.db.exists("Employee Checkin", {"employee": employee, "time": time_value, "log_type": log_type}):
            continue
        doc = frappe.get_doc({"doctype": "Employee Checkin", "employee": employee, "time": time_value, "log_type": log_type})
        if has_field("Employee Checkin", "shift"):
            doc.shift = shift
        save_doc(doc)


def ensure_hr_leave_data(employees):
    leave_types = []
    for name, is_lwp in [("Swiss Corner Annual Leave", 0), ("Swiss Corner Sick Leave", 0), ("Swiss Corner Unpaid Leave", 1)]:
        if frappe.db.exists("Leave Type", name):
            doc = frappe.get_doc("Leave Type", name)
        else:
            doc = frappe.get_doc({"doctype": "Leave Type", "name": name, "leave_type_name": name})
        doc.leave_type_name = name
        doc.is_lwp = is_lwp
        if has_field("Leave Type", "include_holiday"):
            doc.include_holiday = 0
        save_doc(doc)
        leave_types.append(name)
    allocations, applications = [], []
    year_start = getdate(today()).replace(month=1, day=1)
    year_end = getdate(today()).replace(month=12, day=31)
    for emp in employees:
        for leave_type, qty in [("Swiss Corner Annual Leave", 21), ("Swiss Corner Sick Leave", 10)]:
            existing = frappe.db.get_value("Leave Allocation", {"employee": emp["employee"], "leave_type": leave_type, "from_date": year_start}, "name")
            if existing:
                alloc = frappe.get_doc("Leave Allocation", existing)
            else:
                alloc = frappe.get_doc({"doctype": "Leave Allocation", "employee": emp["employee"], "leave_type": leave_type, "from_date": year_start, "to_date": year_end})
            alloc.new_leaves_allocated = qty
            alloc.carry_forward = 0
            save_doc(alloc)
            if alloc.docstatus == 0:
                try_submit_doc(alloc)
            allocations.append(alloc.name)
    for emp in employees[:4]:
        leave_date = getdate(add_days(today(), 20 + len(applications)))
        while leave_date.weekday() == 4:
            leave_date = add_days(leave_date, 1)
        existing = frappe.db.get_value("Leave Application", {"employee": emp["employee"], "from_date": leave_date, "to_date": leave_date}, "name")
        if existing:
            app = frappe.get_doc("Leave Application", existing)
        else:
            app = frappe.get_doc({"doctype": "Leave Application", "employee": emp["employee"], "leave_type": "Swiss Corner Annual Leave", "from_date": leave_date, "to_date": leave_date})
        app.company = get_operating_company()
        app.description = "Swiss Corner demo annual leave."
        if has_field("Leave Application", "status"):
            app.status = "Approved"
        save_doc(app)
        if app.docstatus == 0:
            try_submit_doc(app)
        applications.append(app.name)
    return {"leave_types": leave_types, "allocations": len(set(allocations)), "applications": len(set(applications))}


def ensure_hr_salary_components(accounts):
    components = [
        ("Swiss Corner Basic Salary", "Earning", accounts.get("expense")),
        ("Swiss Corner Housing Allowance", "Earning", accounts.get("expense")),
        ("Swiss Corner Transport Allowance", "Earning", accounts.get("expense")),
        ("Swiss Corner Sales Commission", "Earning", accounts.get("expense")),
        ("Swiss Corner GOSI Deduction", "Deduction", accounts.get("payable")),
        ("Swiss Corner Advance Deduction", "Deduction", accounts.get("payable")),
    ]
    out = []
    for name, component_type, account in components:
        if frappe.db.exists("Salary Component", name):
            doc = frappe.get_doc("Salary Component", name)
        else:
            doc = frappe.get_doc({"doctype": "Salary Component", "name": name, "salary_component": name})
        doc.salary_component = name
        doc.type = component_type
        if has_field("Salary Component", "depends_on_payment_days"):
            doc.depends_on_payment_days = 0
        if has_field("Salary Component", "is_tax_applicable"):
            doc.is_tax_applicable = 0
        if hasattr(doc, "accounts") and account:
            doc.set("accounts", [{"company": get_operating_company(), "account": account}])
        save_doc(doc)
        out.append(doc.name)
    return out


def ensure_hr_salary_structure(accounts):
    name = "Swiss Corner Monthly Payroll"
    if frappe.db.exists("Salary Structure", name):
        doc = frappe.get_doc("Salary Structure", name)
        if doc.docstatus == 1:
            return doc.name
    else:
        doc = frappe.get_doc({"doctype": "Salary Structure", "name": name})
    doc.name = name
    if has_field("Salary Structure", "salary_structure_name"):
        doc.salary_structure_name = name
    doc.company = get_operating_company()
    doc.currency = "SAR"
    doc.payroll_frequency = "Monthly"
    doc.is_active = "Yes"
    doc.set("earnings", [])
    for component, amount in [
        ("Swiss Corner Basic Salary", 0),
        ("Swiss Corner Housing Allowance", 0),
        ("Swiss Corner Transport Allowance", 0),
        ("Swiss Corner Sales Commission", 0),
    ]:
        doc.append("earnings", {"salary_component": component, "amount": amount})
    doc.set("deductions", [])
    doc.append("deductions", {"salary_component": "Swiss Corner GOSI Deduction", "amount": 0})
    save_doc(doc)
    if doc.docstatus == 0:
        try_submit_doc(doc)
    return doc.name


def ensure_hr_salary_assignments_and_slips(employees, salary_structure):
    assignments, slips = [], []
    start_date = getdate(today()).replace(day=1)
    end_date = add_days(add_months(start_date, 1), -1)
    for emp in employees:
        existing = frappe.db.get_value("Salary Structure Assignment", {"employee": emp["employee"], "salary_structure": salary_structure}, "name")
        if existing:
            assignment = frappe.get_doc("Salary Structure Assignment", existing)
        else:
            assignment = frappe.get_doc({"doctype": "Salary Structure Assignment", "employee": emp["employee"], "salary_structure": salary_structure})
        assignment.company = get_operating_company()
        assignment.from_date = start_date
        assignment.base = emp["base"]
        save_doc(assignment)
        if assignment.docstatus == 0:
            try_submit_doc(assignment)
        assignments.append(assignment.name)

        existing_slip = frappe.db.get_value("Salary Slip", {"employee": emp["employee"], "start_date": start_date, "end_date": end_date}, "name")
        if existing_slip:
            slip = frappe.get_doc("Salary Slip", existing_slip)
            if slip.docstatus == 1:
                slips.append({"name": slip.name, "docstatus": slip.docstatus})
                continue
        else:
            slip = frappe.get_doc({"doctype": "Salary Slip", "employee": emp["employee"], "salary_structure": salary_structure, "start_date": start_date, "end_date": end_date})
        base = emp["base"]
        slip.company = get_operating_company()
        slip.posting_date = today()
        slip.payroll_frequency = "Monthly"
        slip.currency = "SAR"
        slip.set("earnings", [])
        for component, amount in [
            ("Swiss Corner Basic Salary", round(base * 0.65, 2)),
            ("Swiss Corner Housing Allowance", round(base * 0.2, 2)),
            ("Swiss Corner Transport Allowance", round(base * 0.1, 2)),
            ("Swiss Corner Sales Commission", 450 if "Sales" in emp["designation"] or "Cashier" in emp["designation"] else 0),
        ]:
            slip.append("earnings", {"salary_component": component, "amount": amount})
        deduction = round(base * 0.09, 2)
        slip.set("deductions", [{"salary_component": "Swiss Corner GOSI Deduction", "amount": deduction}])
        if has_field("Salary Slip", "cost_center"):
            slip.cost_center = accounts.get("cost_center")
        save_doc(slip)
        if slip.docstatus == 0:
            try_submit_doc(slip)
        slips.append({"name": slip.name, "docstatus": slip.docstatus})
    return {"assignments": len(set(assignments)), "salary_slips": slips}


def ensure_hr_expense_claims(accounts, employees):
    for name, account in [("Swiss Corner Travel", accounts.get("expense")), ("Swiss Corner Staff Meal", accounts.get("expense")), ("Swiss Corner Customer Hospitality", accounts.get("expense"))]:
        if frappe.db.exists("Expense Claim Type", name):
            doc = frappe.get_doc("Expense Claim Type", name)
        else:
            doc = frappe.get_doc({"doctype": "Expense Claim Type", "name": name, "expense_type": name})
        doc.expense_type = name
        if has_field("Expense Claim Type", "default_account") and account:
            doc.default_account = account
        save_doc(doc)
    claims = []
    for idx, emp in enumerate(employees[:5], start=1):
        marker = f"Swiss Corner HR Demo Expense {emp['employee']}"
        existing = frappe.db.get_value("Expense Claim", {"remark": marker}, "name")
        if existing:
            claim = frappe.get_doc("Expense Claim", existing)
        else:
            claim = frappe.get_doc({"doctype": "Expense Claim", "employee": emp["employee"]})
        claim.company = get_operating_company()
        claim.posting_date = add_days(today(), -idx)
        claim.remark = marker
        if has_field("Expense Claim", "payable_account") and accounts.get("payable"):
            claim.payable_account = accounts.get("payable")
        claim.set("expenses", [])
        claim.append(
            "expenses",
            {
                "expense_date": add_days(today(), -idx),
                "expense_type": "Swiss Corner Travel" if idx % 2 else "Swiss Corner Customer Hospitality",
                "description": "Swiss Corner demo branch operations expense.",
                "amount": 180 + (idx * 55),
                "sanctioned_amount": 180 + (idx * 55),
                "default_account": accounts.get("expense"),
                "cost_center": accounts.get("cost_center"),
            },
        )
        save_doc(claim)
        if claim.docstatus == 0:
            try_submit_doc(claim)
        claims.append({"name": claim.name, "docstatus": claim.docstatus})
    return claims


def ensure_hr_recruiting_demo():
    out = {"job_openings": [], "applicants": []}
    openings = [
        ("Swiss Corner Sales Consultant - Riyadh", "Swiss Corner Sales Consultant", 2),
        ("Swiss Corner Watch Technician - Warranty Center", "Swiss Corner Watch Technician", 1),
        ("Swiss Corner E-Commerce Specialist", "Swiss Corner E-Commerce Specialist", 1),
    ]
    for title, designation, vacancies in openings:
        if frappe.db.exists("Job Opening", title):
            doc = frappe.get_doc("Job Opening", title)
        else:
            doc = frappe.get_doc({"doctype": "Job Opening", "job_title": title})
        doc.job_title = title
        if has_field("Job Opening", "designation"):
            doc.designation = designation
        if has_field("Job Opening", "company"):
            doc.company = get_operating_company()
        if has_field("Job Opening", "status"):
            doc.status = "Open"
        if has_field("Job Opening", "planned_vacancies"):
            doc.planned_vacancies = vacancies
        save_doc(doc)
        out["job_openings"].append(doc.name)
    applicants = [
        ("Swiss Corner Applicant - Abdulmalik", "abdulmalik.applicant@swisscorner.demo", "Swiss Corner Sales Consultant - Riyadh", "Replied"),
        ("Swiss Corner Applicant - Lama", "lama.applicant@swisscorner.demo", "Swiss Corner Watch Technician - Warranty Center", "Open"),
        ("Swiss Corner Applicant - Omar", "omar.applicant@swisscorner.demo", "Swiss Corner E-Commerce Specialist", "Accepted"),
    ]
    for name, email, opening, status in applicants:
        existing = frappe.db.get_value("Job Applicant", {"email_id": email}, "name")
        if existing:
            doc = frappe.get_doc("Job Applicant", existing)
        else:
            doc = frappe.get_doc({"doctype": "Job Applicant", "applicant_name": name, "email_id": email})
        doc.applicant_name = name
        doc.email_id = email
        if has_field("Job Applicant", "job_title"):
            doc.job_title = opening
        if has_field("Job Applicant", "status"):
            doc.status = status
        save_doc(doc)
        out["applicants"].append(doc.name)
    return out


def ensure_hr_accounting_entries(accounts):
    if not accounts.get("expense"):
        return {"skipped": "missing expense or payable account"}
    payroll_payable = get_non_party_liability_account() or accounts.get("bank") or accounts.get("cash")
    if not payroll_payable:
        return {"skipped": "missing payable/bank account"}
    total_payroll = sum(row[7] for row in HR_EMPLOYEES)
    entries = [
        ("Swiss Corner HR Demo Payroll Accrual", total_payroll, accounts.get("expense"), payroll_payable),
        ("Swiss Corner HR Demo Expense Claim Accrual", 1725, accounts.get("expense"), payroll_payable),
    ]
    out = []
    for title, amount, debit_account, credit_account in entries:
        existing = frappe.db.get_value("Journal Entry", {"user_remark": title, "docstatus": ["!=", 2]}, "name")
        if existing:
            out.append(existing)
            continue
        doc = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Journal Entry", "company": get_operating_company(), "posting_date": today(), "user_remark": title})
        doc.append("accounts", {"account": debit_account, "debit_in_account_currency": amount, "credit_in_account_currency": 0, "cost_center": accounts.get("cost_center")})
        doc.append("accounts", {"account": credit_account, "debit_in_account_currency": 0, "credit_in_account_currency": amount, "cost_center": accounts.get("cost_center")})
        save_doc(doc)
        if doc.docstatus == 0:
            try_submit_doc(doc)
        out.append(doc.name)
    return out


def get_non_party_liability_account():
    rows = frappe.db.sql(
        """
        select name
        from `tabAccount`
        where company = %s
          and is_group = 0
          and root_type = 'Liability'
          and coalesce(account_type, '') not in ('Receivable', 'Payable')
        order by lft asc
        limit 1
        """,
        (get_operating_company(),),
    )
    return rows[0][0] if rows else None


def ensure_hr_reports():
    reports = {
        "Swiss Corner - HR Headcount by Branch": {
            "ref_doctype": "Employee",
            "query": """
                select
                    coalesce(branch, 'No Branch') as "Branch:Data:220",
                    department as "Department:Link/Department:240",
                    count(name) as "Employees:Int:120",
                    sum(case when status = 'Active' then 1 else 0 end) as "Active:Int:100"
                from `tabEmployee`
                where personal_email like 'employee%%@swisscorner.demo'
                group by coalesce(branch, 'No Branch'), department
                order by 1, 2
            """,
        },
        "Swiss Corner - Attendance Summary": {
            "ref_doctype": "Attendance",
            "query": """
                select
                    e.branch as "Branch:Data:220",
                    a.status as "Status:Data:120",
                    count(a.name) as "Attendance Records:Int:150",
                    round(avg(coalesce(a.working_hours, 0)), 2) as "Avg Hours:Float:120"
                from `tabAttendance` a
                inner join `tabEmployee` e on e.name = a.employee
                where a.docstatus < 2 and a.attendance_date >= date_sub(curdate(), interval 45 day) and e.personal_email like 'employee%%@swisscorner.demo'
                group by e.branch, a.status
                order by e.branch, a.status
            """,
        },
        "Swiss Corner - Payroll Summary": {
            "ref_doctype": "Salary Slip",
            "query": """
                select
                    e.branch as "Branch:Data:220",
                    count(ss.name) as "Salary Slips:Int:120",
                    round(sum(coalesce(ss.gross_pay, 0)), 2) as "Gross Pay:Currency:150",
                    round(sum(coalesce(ss.total_deduction, 0)), 2) as "Deductions:Currency:150",
                    round(sum(coalesce(ss.net_pay, 0)), 2) as "Net Pay:Currency:150"
                from `tabSalary Slip` ss
                inner join `tabEmployee` e on e.name = ss.employee
                where ss.docstatus < 2 and e.personal_email like 'employee%%@swisscorner.demo'
                group by e.branch
                order by e.branch
            """,
        },
        "Swiss Corner - HR Expense Claims": {
            "ref_doctype": "Expense Claim",
            "query": """
                select
                    ec.employee as "Employee:Link/Employee:150",
                    ec.employee_name as "Employee Name:Data:180",
                    ec.posting_date as "Posting Date:Date:120",
                    ec.total_claimed_amount as "Claimed:Currency:130",
                    ec.total_sanctioned_amount as "Sanctioned:Currency:130",
                    ec.status as "Status:Data:120"
                from `tabExpense Claim` ec
                inner join `tabEmployee` e on e.name = ec.employee
                where e.personal_email like 'employee%%@swisscorner.demo'
                order by ec.posting_date desc
            """,
        },
        "Swiss Corner - Recruitment Pipeline": {
            "ref_doctype": "Job Applicant",
            "query": """
                select
                    applicant_name as "Applicant:Data:220",
                    email_id as "Email:Data:240",
                    job_title as "Job Opening:Data:260",
                    status as "Status:Data:140"
                from `tabJob Applicant`
                where applicant_name like 'Swiss Corner Applicant%%'
                order by modified desc
            """,
        },
    }
    created = []
    for name, definition in reports.items():
        ensure_query_report(name, {"ref_doctype": definition["ref_doctype"], "query": definition["query"], "filters": [], "columns": []})
        created.append(name)
    return created


def add_hr_to_swiss_corner_workspace():
    if not frappe.db.exists("Workspace", "Swiss Corner Demo"):
        return
    doc = frappe.get_doc("Workspace", "Swiss Corner Demo")
    link_labels = {row.label for row in doc.get("links", []) if row.get("label")}
    if "الموارد البشرية والرواتب" not in link_labels:
        doc.append("links", {"type": "Card Break", "label": "الموارد البشرية والرواتب"})
        for report in [
            "Swiss Corner - HR Headcount by Branch",
            "Swiss Corner - Attendance Summary",
            "Swiss Corner - Payroll Summary",
            "Swiss Corner - HR Expense Claims",
            "Swiss Corner - Recruitment Pipeline",
        ]:
            doc.append("links", report_link(report, report.replace("Swiss Corner - ", "")))
        for doctype in ["Employee", "Attendance", "Salary Slip", "Expense Claim", "Leave Application", "Job Applicant"]:
            doc.append("links", doc_link(doctype))
    shortcuts = {row.label for row in doc.get("shortcuts", []) if row.get("label")}
    for label, doctype in [("الموظفون", "Employee"), ("الحضور", "Attendance"), ("مسيرات الرواتب", "Salary Slip"), ("مطالبات المصروفات", "Expense Claim")]:
        if label not in shortcuts:
            doc.append("shortcuts", doc_shortcut(doctype, label))
    save_doc(doc)


def add_hr_to_demo_guide():
    if not frappe.db.exists("Workspace", GUIDE_WORKSPACE):
        return
    doc = frappe.get_doc("Workspace", GUIDE_WORKSPACE)
    content = doc.content or "[]"
    marker = "الموارد البشرية والرواتب"
    if marker in content:
        return
    extra = """
<div class="sc-demo-section">
  <div class="sc-demo-section-title">مرحلة الموارد البشرية والرواتب</div>
  <div class="sc-demo-band">
    بعد عرض الحسابات والفواتير، انتقل إلى الموارد البشرية: اعرض الموظفين حسب الفرع، الحضور، الإجازات، مسيرات الرواتب، مطالبات المصروفات، وقيد استحقاق الرواتب في الحسابات.
  </div>
</div>
"""
    data = json.loads(content)
    if data and data[0].get("data", {}).get("text"):
        data[0]["data"]["text"] = data[0]["data"]["text"].replace("</div>\n", extra + "</div>\n", 1)
        doc.content = json.dumps(data, ensure_ascii=False)
        save_doc(doc)


def verify_swiss_corner_hr_demo():
    reports = {}
    for report in [
        "Swiss Corner - HR Headcount by Branch",
        "Swiss Corner - Attendance Summary",
        "Swiss Corner - Payroll Summary",
        "Swiss Corner - HR Expense Claims",
        "Swiss Corner - Recruitment Pipeline",
    ]:
        try:
            rows = frappe.get_attr("frappe.desk.query_report.run")(report_name=report, filters={}).get("result") or []
            reports[report] = {"ok": True, "rows": len(rows)}
        except Exception as exc:
            reports[report] = {"ok": False, "error": str(exc)}
    return {
        "employees": frappe.db.count("Employee", {"personal_email": ["like", "employee%@swisscorner.demo"]}),
        "attendance": frappe.db.sql("select count(*) from `tabAttendance` a inner join `tabEmployee` e on e.name=a.employee where e.personal_email like 'employee%%@swisscorner.demo'")[0][0],
        "salary_slips": frappe.db.sql("select count(*) from `tabSalary Slip` ss inner join `tabEmployee` e on e.name=ss.employee where e.personal_email like 'employee%%@swisscorner.demo'")[0][0],
        "expense_claims": frappe.db.sql("select count(*) from `tabExpense Claim` ec inner join `tabEmployee` e on e.name=ec.employee where e.personal_email like 'employee%%@swisscorner.demo'")[0][0],
        "job_applicants": frappe.db.count("Job Applicant", {"applicant_name": ["like", "Swiss Corner Applicant%"]}),
        "reports": reports,
    }


def try_submit_doc(doc):
    try:
        frappe.db.commit()
        doc.submit()
        frappe.db.commit()
        return True
    except Exception:
        frappe.db.rollback()
        try:
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
        return False


# ---------------------------------------------------------------------------
# Generic demo branding cleanup.


GENERIC_REPORT_RENAMES = {
    "Swiss Corner - Store Sales Report": "تقرير مبيعات الفروع",
    "Swiss Corner - POS Sales Summary": "ملخص مبيعات نقطة البيع",
    "Swiss Corner - Inventory Movement by Store": "حركة المخزون حسب المتجر",
    "Swiss Corner - Serial Number Register": "سجل الأرقام التسلسلية",
    "Swiss Corner - Warranty Report": "تقرير الضمان",
    "Swiss Corner - Gross Profit by Store and Brand": "الربحية حسب الفرع والعلامة",
    "Swiss Corner - Fast and Slow Moving Watches": "الساعات السريعة والبطيئة الحركة",
    "Swiss Corner - Branch Transfer Summary": "ملخص تحويلات الفروع",
    "Swiss Corner - WhatsApp Invoice Delivery Log": "سجل تسليم فواتير واتساب",
    "Swiss Corner - HR Headcount by Branch": "عدد الموظفين حسب الفرع",
    "Swiss Corner - Attendance Summary": "ملخص الحضور",
    "Swiss Corner - Payroll Summary": "ملخص الرواتب",
    "Swiss Corner - HR Expense Claims": "مطالبات مصروفات الموظفين",
    "Swiss Corner - Recruitment Pipeline": "مسار التوظيف",
}

GENERIC_CHART_RENAMES = {
    "Swiss Corner - Sales by Branch": "المبيعات حسب شرائح العملاء",
    "Swiss Corner - POS Profiles": "مبيعات نقاط البيع",
    "Swiss Corner - Invoice Trend": "اتجاه الفواتير",
}

GENERIC_CARD_RENAMES = {
    "Swiss Corner - Invoice Count": "عدد الفواتير",
    "Swiss Corner - Sales Total": "إجمالي المبيعات",
    "Swiss Corner - POS Invoice Count": "عدد فواتير نقطة البيع",
    "Swiss Corner - POS Sales Total": "إجمالي مبيعات نقطة البيع",
    "Swiss Corner - Serial Watches": "الساعات المسلسلة",
    "Swiss Corner - WhatsApp Logs": "سجلات واتساب",
}

GENERIC_MASTER_RENAMES = {
    "Employment Type": {
        "Swiss Corner Full Time": "دوام كامل",
        "Swiss Corner Part Time": "دوام جزئي",
        "Swiss Corner Contract": "تعاقد",
    },
    "Designation": {
        "Swiss Corner Store Manager": "مدير متجر",
        "Swiss Corner Cashier": "كاشير",
        "Swiss Corner Sales Consultant": "مستشار مبيعات",
        "Swiss Corner Watch Technician": "فني صيانة ساعات",
        "Swiss Corner Inventory Officer": "مسؤول مخزون",
        "Swiss Corner Accountant": "محاسب",
        "Swiss Corner HR Officer": "مسؤول موارد بشرية",
        "Swiss Corner E-Commerce Specialist": "أخصائي متجر إلكتروني",
        "Swiss Corner Buyer": "مسؤول مشتريات",
    },
    "Department": {
        "Swiss Corner - Retail Operations - M": "عمليات التجزئة - M",
        "Swiss Corner - Finance and Accounting - M": "المالية والمحاسبة - M",
        "Swiss Corner - Inventory and Logistics - M": "المخزون واللوجستيات - M",
        "Swiss Corner - HR and Admin - M": "الموارد البشرية والإدارة - M",
        "Swiss Corner - After Sales and Warranty - M": "خدمة ما بعد البيع والضمان - M",
        "Swiss Corner - E-Commerce - M": "المتجر الإلكتروني - M",
        "Swiss Corner - Procurement - M": "المشتريات - M",
    },
    "Leave Type": {
        "Swiss Corner Annual Leave": "إجازة سنوية",
        "Swiss Corner Sick Leave": "إجازة مرضية",
        "Swiss Corner Unpaid Leave": "إجازة بدون راتب",
    },
    "Salary Component": {
        "Swiss Corner Basic Salary": "الراتب الأساسي",
        "Swiss Corner Housing Allowance": "بدل السكن",
        "Swiss Corner Transport Allowance": "بدل النقل",
        "Swiss Corner Sales Commission": "عمولة المبيعات",
        "Swiss Corner GOSI Deduction": "استقطاع التأمينات",
        "Swiss Corner Advance Deduction": "استقطاع السلفة",
    },
    "Salary Structure": {
        "Swiss Corner Monthly Payroll": "مسير الرواتب الشهري",
    },
    "Expense Claim Type": {
        "Swiss Corner Travel": "تنقلات عمل",
        "Swiss Corner Staff Meal": "وجبات موظفين",
        "Swiss Corner Customer Hospitality": "ضيافة عملاء",
    },
    "Shift Type": {
        "Swiss Corner Morning Shift": "وردية صباحية",
        "Swiss Corner Evening Shift": "وردية مسائية",
        "Swiss Corner Office Shift": "وردية إدارية",
    },
    "Campaign": {
        "Swiss Corner POSNext Demo Campaign": "حملة عروض نقاط البيع",
    },
}


def apply_generic_demo_branding():
    """Remove customer-specific prefixes from reusable demo labels and HR masters."""
    renamed = {"reports": {}, "charts": {}, "cards": {}, "masters": {}, "workspaces": []}
    for old, new in GENERIC_REPORT_RENAMES.items():
        renamed["reports"][old] = rename_doc_if_needed("Report", old, new)
        if frappe.db.exists("Report", new):
            frappe.db.set_value("Report", new, {"report_name": new}, update_modified=False)

    for old, new in GENERIC_CHART_RENAMES.items():
        renamed["charts"][old] = rename_doc_if_needed("Dashboard Chart", old, new)
        if frappe.db.exists("Dashboard Chart", new):
            frappe.db.set_value("Dashboard Chart", new, {"chart_name": new}, update_modified=False)

    for old, new in GENERIC_CARD_RENAMES.items():
        renamed["cards"][old] = rename_doc_if_needed("Number Card", old, new)
        if frappe.db.exists("Number Card", new):
            frappe.db.set_value("Number Card", new, {"label": new}, update_modified=False)

    for doctype, mapping in GENERIC_MASTER_RENAMES.items():
        renamed["masters"][doctype] = {}
        if not frappe.db.exists("DocType", doctype):
            continue
        for old, new in mapping.items():
            renamed["masters"][doctype][old] = rename_doc_if_needed(doctype, old, new)
            update_generic_master_display_fields(doctype, new)

    remove_custom_report_links_from_workspaces()
    update_generic_demo_workspace_links()
    rename_visible_swiss_corner_labels()
    frappe.db.commit()
    frappe.clear_cache()
    return renamed


def rename_doc_if_needed(doctype, old, new):
    if old == new:
        return new if frappe.db.exists(doctype, new) else None
    if not frappe.db.exists(doctype, old):
        return new if frappe.db.exists(doctype, new) else None
    if frappe.db.exists(doctype, new):
        frappe.rename_doc(doctype, old, new, force=True, merge=True)
        return new
    frappe.rename_doc(doctype, old, new, force=True)
    return new


def update_generic_master_display_fields(doctype, name):
    if not frappe.db.exists(doctype, name):
        return
    field_map = {
        "Employment Type": "employee_type_name",
        "Designation": "designation_name",
        "Department": "department_name",
        "Leave Type": "leave_type_name",
        "Salary Component": "salary_component",
        "Salary Structure": "salary_structure_name",
        "Expense Claim Type": "expense_type",
        "Shift Type": "shift_type_name",
        "Campaign": "campaign_name",
    }
    fieldname = field_map.get(doctype)
    if fieldname and has_field(doctype, fieldname):
        frappe.db.set_value(doctype, name, fieldname, name, update_modified=False)


def remove_custom_report_links_from_workspaces():
    frappe.db.sql(
        """
        delete from `tabWorkspace Link`
        where parenttype = 'Workspace'
          and (
              link_type = 'Report'
              or coalesce(is_query_report, 0) = 1
              or label like '%%Swiss Corner%%'
              or label like '%%الركن السويسري%%'
          )
        """
    )
    frappe.db.sql(
        """
        delete from `tabWorkspace Link`
        where parenttype = 'Workspace'
          and type = 'Card Break'
          and (
              label like '%%تقارير%%'
              or label like '%%Reports%%'
              or label like '%%تقرير%%'
          )
        """
    )


def update_generic_demo_workspace_links():
    if not frappe.db.exists("Workspace", "Swiss Corner Demo"):
        return
    doc = frappe.get_doc("Workspace", "Swiss Corner Demo")
    doc.label = "لوحة العرض"
    doc.title = "لوحة العرض"
    doc.set(
        "links",
        build_workspace_links(
            [
                {
                    "label": "العمليات اليومية",
                    "links": [
                        doc_link("Sales Invoice", "فواتير المبيعات"),
                        doc_link("POS Invoice", "فواتير نقطة البيع"),
                        doc_link("Customer", "العملاء"),
                        doc_link("Item", "الأصناف"),
                        doc_link("Serial No", "الأرقام التسلسلية"),
                        doc_link("Stock Entry", "حركة المخزون"),
                    ],
                },
                {
                    "label": "الموارد البشرية والرواتب",
                    "links": [
                        doc_link("Employee", "الموظفون"),
                        doc_link("Attendance", "الحضور"),
                        doc_link("Salary Slip", "مسيرات الرواتب"),
                        doc_link("Expense Claim", "مطالبات المصروفات"),
                        doc_link("Leave Application", "طلبات الإجازة"),
                        doc_link("Job Applicant", "متقدمو الوظائف"),
                    ],
                },
            ]
        ),
    )
    doc.set(
        "shortcuts",
        [
            doc_shortcut("Sales Invoice", "فاتورة مبيعات"),
            doc_shortcut("POS Invoice", "فاتورة نقطة بيع"),
            doc_shortcut("Item", "الصنف"),
            doc_shortcut("Serial No", "رقم تسلسلي"),
            doc_shortcut("Employee", "الموظفون"),
            doc_shortcut("Salary Slip", "مسيرات الرواتب"),
        ],
    )
    doc.save(ignore_permissions=True)
    frappe.db.sql(
        "update `tabWorkspace` set label=%s, title=%s where name=%s",
        ("لوحة العرض", "لوحة العرض", "Swiss Corner Demo"),
    )


def rename_visible_swiss_corner_labels():
    replacements = [
        ("Swiss Corner - ", ""),
        ("الركن السويسري - ", ""),
        ("Swiss Corner ", ""),
        ("الركن السويسري ", ""),
    ]
    doctypes = ["Dashboard", "POS Profile", "POS Settings"]
    for doctype in doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue
        for name in frappe.get_all(doctype, pluck="name", limit_page_length=500):
            updates = {}
            for fieldname in ("label", "title", "name", "pos_profile"):
                if not has_field(doctype, fieldname):
                    continue
                value = frappe.db.get_value(doctype, name, fieldname)
                if isinstance(value, str):
                    new_value = value
                    for old, new in replacements:
                        new_value = new_value.replace(old, new)
                    if new_value != value and fieldname != "name":
                        updates[fieldname] = new_value
            if updates:
                frappe.db.set_value(doctype, name, updates, update_modified=False)
