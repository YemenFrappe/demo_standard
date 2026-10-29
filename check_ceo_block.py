import frappe
import json

frappe.init(site="demo.yemenfrappe.com")
frappe.connect()

block = frappe.get_doc("Custom HTML Block", "CEO Executive View")
result = {
    "html_len": len(block.html),
    "style_len": len(block.style),
    "script_len": len(block.script),
    "html_sample": block.html[:1500]
}
print(json.dumps(result, ensure_ascii=False))