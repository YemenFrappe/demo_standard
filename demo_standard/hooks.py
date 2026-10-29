app_name = "demo_standard"
app_title = "Demo Standard"
app_publisher = "Yemen Frappe"
app_description = "Reusable demo polish app for Arabic ERPNext sites"
app_email = "support@yemenfrappe.com"
app_license = "mit"

ASSET_VERSION = "20260430_5"


def _v(path: str) -> str:
	return f"{path}?v={ASSET_VERSION}"


app_include_css = [_v("/assets/demo_standard/css/demo_standard.css")]
app_include_js = [_v("/assets/demo_standard/js/demo_standard.js")]
web_include_css = [_v("/assets/demo_standard/css/demo_standard.css")]
boot_session = "demo_standard.swiss_corner_demo.boot_session"

after_install = "demo_standard.setup.after_install"
after_migrate = ["demo_standard.setup.after_migrate"]

doc_events = {
	"Sales Invoice": {
		"before_submit": "demo_standard.swiss_corner_demo.before_swiss_corner_invoice_submit",
		"on_submit": "demo_standard.swiss_corner_demo.on_sales_invoice_submit",
	},
	"POS Invoice": {
		"before_submit": "demo_standard.swiss_corner_demo.before_swiss_corner_invoice_submit",
	},
}
