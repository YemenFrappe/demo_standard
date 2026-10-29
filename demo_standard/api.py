import frappe

from demo_standard.swiss_corner_demo import (
    DEMO_PRESENTATION_BLOCK,
    GUIDE_WORKSPACE,
    ensure_demo_presentation_custom_block,
    repair_swiss_corner_workspace_presentation,
    setup_demo_presentation_workspace,
)


@frappe.whitelist()
def set_language(language: str):
    if language not in {"ar", "en"}:
        frappe.throw("Unsupported language")

    if frappe.session.user == "Guest":
        frappe.throw("Login required")

    frappe.db.set_value("User", frappe.session.user, "language", language, update_modified=False)
    frappe.defaults.set_user_default("lang", language, user=frappe.session.user)
    frappe.defaults.set_user_default("language", language, user=frappe.session.user)
    frappe.clear_cache(user=frappe.session.user)

    return {"language": language}


@frappe.whitelist()
def repair_presentation_workspace():
    """Repair all demo workspaces: ensure Demo (presentation) is visible and properly configured."""

    # 1. Ensure the Custom HTML Block for the presentation exists
    ensure_demo_presentation_custom_block()

    # 2. Ensure the Demo workspace uses the presentation block and is visible
    if frappe.db.exists("Workspace", GUIDE_WORKSPACE):
        doc = frappe.get_doc("Workspace", GUIDE_WORKSPACE)
        doc.icon = "rocket"
        doc.indicator_color = "orange"
        doc.is_hidden = 0
        doc.public = 1
        doc.sequence_id = 1
        # Update content to use the presentation block
        import json

        content = [
            {
                "id": "demo_presentation_deck",
                "type": "custom_block",
                "data": {"custom_block_name": DEMO_PRESENTATION_BLOCK, "col": 12},
            }
        ]
        doc.content = json.dumps(content, ensure_ascii=False)
        # Set custom blocks
        doc.set(
            "custom_blocks",
            [{"custom_block_name": DEMO_PRESENTATION_BLOCK, "label": DEMO_PRESENTATION_BLOCK}],
        )
        doc.save(ignore_permissions=True)
    else:
        setup_demo_presentation_workspace()

    # 3. Fix Demo Start workspace to use presentation block too
    if frappe.db.exists("Workspace", "Demo Start"):
        import json

        doc = frappe.get_doc("Workspace", "Demo Start")
        content = [
            {
                "id": "demo_presentation_deck",
                "type": "custom_block",
                "data": {"custom_block_name": DEMO_PRESENTATION_BLOCK, "col": 12},
            }
        ]
        doc.content = json.dumps(content, ensure_ascii=False)
        doc.set(
            "custom_blocks",
            [{"custom_block_name": DEMO_PRESENTATION_BLOCK, "label": DEMO_PRESENTATION_BLOCK}],
        )
        doc.icon = "tool"
        doc.indicator_color = "orange"
        doc.public = 1
        doc.is_hidden = 0
        doc.sequence_id = 2
        doc.save(ignore_permissions=True)

    # 4. Fix CEO Executive View workspace - use presentation deck if it has no content
    if frappe.db.exists("Workspace", "CEO Executive View"):
        doc = frappe.get_doc("Workspace", "CEO Executive View")
        if not doc.content or doc.content == "[]":
            import json

            content = [
                {
                    "id": "ceo_presentation_deck",
                    "type": "custom_block",
                    "data": {"custom_block_name": DEMO_PRESENTATION_BLOCK, "col": 12},
                }
            ]
            doc.content = json.dumps(content, ensure_ascii=False)
            doc.set(
                "custom_blocks",
                [{"custom_block_name": DEMO_PRESENTATION_BLOCK, "label": DEMO_PRESENTATION_BLOCK}],
            )
        doc.icon = "dashboard"
        doc.indicator_color = "orange"
        doc.public = 1
        doc.is_hidden = 0
        doc.sequence_id = 3
        doc.save(ignore_permissions=True)

    # 5. Run the full repair function for workspace dashboards
    # (skip if it fails due to missing reports - those are non-critical)
    try:
        repair_result = repair_swiss_corner_workspace_presentation()
    except Exception as e:
        repair_result = {"skipped": True, "error": str(e)}

    frappe.db.commit()
    frappe.clear_cache()

    return {
        "message": "Workspaces repaired successfully",
        "demo_workspace": GUIDE_WORKSPACE,
        "route": "/app/demo",
        "repair_result": repair_result,
    }


@frappe.whitelist()
def update_ceo_executive_view():
    """Create a proper CEO Executive View dashboard with professional layout."""
    # Check if presentation block exists
    if not frappe.db.exists("Custom HTML Block", DEMO_PRESENTATION_BLOCK):
        ensure_demo_presentation_custom_block()

    import json

    # Create CEO Executive View HTML content
    ceo_html = """
<style>
.ceo-dashboard{font-family:"Inter","Noto Sans Arabic",Arial,sans-serif;direction:rtl;max-width:1200px;margin:0 auto;padding:24px 16px}
.ceo-hero{background:linear-gradient(135deg,#1a2332 0%,#2d3a4f 100%);border-radius:20px;padding:40px 36px;color:#fff;margin-bottom:24px;position:relative;overflow:hidden}
.ceo-hero::before{content:"";position:absolute;top:-60px;inset-inline-end:-60px;width:200px;height:200px;background:radial-gradient(circle,rgba(201,151,63,0.3) 0%,transparent 70%);border-radius:50%}
.ceo-hero h1{font-size:32px;font-weight:900;margin:0 0 8px;color:#fff}
.ceo-hero p{font-size:17px;opacity:0.9;margin:0;max-width:700px;line-height:1.7}
.ceo-kicker{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border-radius:999px;background:rgba(201,151,63,0.2);border:1px solid rgba(201,151,63,0.4);color:#f0c97a;font-size:12px;font-weight:800;margin-bottom:14px}
.ceo-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.ceo-card{border:1px solid #e8d6ba;border-radius:14px;background:#fff;padding:20px;transition:all 0.2s}
.ceo-card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.08)}
.ceo-card-icon{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:12px;margin-bottom:12px;font-size:20px}
.ceo-card-icon.navy{background:#f0f2f6;color:#1a2332}
.ceo-card-icon.gold{background:#fff4df;color:#9b672e}
.ceo-card-icon.green{background:#ecfdf5;color:#059669}
.ceo-card-icon.blue{background:#eff6ff;color:#2563eb}
.ceo-card h3{font-size:15px;font-weight:800;color:#1a2332;margin:0 0 6px}
.ceo-card p{font-size:13px;color:#6b7280;margin:0;line-height:1.6}
.ceo-card .stat{font-size:26px;font-weight:900;color:#1a2332;margin:8px 0 4px}
.ceo-card .stat-label{font-size:12px;color:#9ca3af}
.ceo-section-title{font-size:18px;font-weight:900;color:#1a2332;margin:0 0 14px;display:flex;align-items:center;gap:8px}
.ceo-section-title::before{content:"";width:4px;height:20px;background:#c9973f;border-radius:2px}
.ceo-features{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:20px}
.ceo-feature{border:1px solid #e8d6ba;border-radius:14px;background:#fff;padding:22px}
.ceo-feature h4{font-size:15px;font-weight:800;color:#1a2332;margin:0 0 8px}
.ceo-feature p{font-size:13px;color:#6b7280;margin:0;line-height:1.7}
.ceo-feature ul{margin:8px 0 0;padding:0;list-style:none}
.ceo-feature li{font-size:13px;color:#374151;padding:4px 0;display:flex;align-items:center;gap:8px}
.ceo-feature li::before{content:"→";color:#c9973f;font-weight:900}
.ceo-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}
.ceo-actions a{display:inline-flex;align-items:center;gap:8px;padding:12px 18px;border-radius:10px;text-decoration:none;font-weight:700;font-size:14px;transition:all 0.2s}
.ceo-actions a.primary{background:#1a2332;color:#fff}
.ceo-actions a.primary:hover{background:#2d3a4f}
.ceo-actions a.secondary{background:#fff;color:#1a2332;border:1px solid #e8d6ba}
.ceo-actions a.secondary:hover{background:#faf8f5}
@media(max-width:900px){.ceo-grid{grid-template-columns:repeat(2,1fr)}.ceo-features{grid-template-columns:1fr}}
@media(max-width:600px){.ceo-grid{grid-template-columns:1fr}}
</style>

<div class="ceo-dashboard">
  <div class="ceo-hero">
    <div class="ceo-kicker">🏢 Swiss Corner Watches</div>
    <h1>لوحة الرئيس التنفيذي</h1>
    <p>نظرة شاملة على أداء الفروع والمبيعات والربحية والمخزون والفريق والتنبيهات التشغيلية للإدارة العليا.</p>
  </div>

  <div class="ceo-grid">
    <div class="ceo-card">
      <div class="ceo-card-icon navy">📊</div>
      <h3>أداء الفروع</h3>
      <p>مقارنة سريعة بين مبيعات واتجاهات كل فرع.</p>
    </div>
    <div class="ceo-card">
      <div class="ceo-card-icon gold">💰</div>
      <h3>الربحية</h3>
      <p>عرض الربحية حسب الفرع والعلامة التجارية.</p>
    </div>
    <div class="ceo-card">
      <div class="ceo-card-icon green">📦</div>
      <h3>المخزون</h3>
      <p>مراقبة قيمة المخزون ру حرکة والأصناف منخفضة الكمية.</p>
    </div>
    <div class="ceo-card">
      <div class="ceo-card-icon blue">👥</div>
      <h3>الفريق</h3>
      <p>ربط العمليات التشغيلية مع الموارد البشرية والحضور.</p>
    </div>
  </div>

  <div class="ceo-section-title">روابط سريعة</div>
  <div class="ceo-features">
    <div class="ceo-feature">
      <h4>📈 التقارير المالية</h4>
      <ul>
        <li>تقرير مبيعات الفروع</li>
        <li>ملخص نقطة البيع (POS)</li>
        <li>الربحية حسب الفرع والعلامة</li>
      </ul>
    </div>
    <div class="ceo-feature">
      <h4>🏪 إدارة الفروع</h4>
      <ul>
        <li>لوحة إدارة الفروع</li>
        <li>نقاط البيع (POS)</li>
        <li>تحويلات المخزون</li>
      </ul>
    </div>
    <div class="ceo-feature">
      <h4>📦 المخزون والضمان</h4>
      <ul>
        <li>حركة المخزون حسب المتجر</li>
        <li>سجل الأرقام التسلسلية</li>
        <li>تقرير الضمان</li>
      </ul>
    </div>
    <div class="ceo-feature">
      <h4>👔 الموارد البشرية</h4>
      <ul>
        <li>الموظفين</li>
        <li>الحضور والغياب</li>
        <li>سجل رسائل واتساب</li>
      </ul>
    </div>
  </div>

  <div class="ceo-actions">
    <a class="primary" href="/app/swiss-corner-demo">🏢 لوحة الركن السويسري</a>
    <a class="secondary" href="/app/point-of-sale">💳 نقطة البيع</a>
    <a class="secondary" href="/app/branch-operations">🏪 عمليات الفروع</a>
    <a class="secondary" href="/app/accounting">📊 المحاسبة</a>
  </div>
</div>
"""

    # Create or update the CEO Executive View custom block
    if frappe.db.exists("Custom HTML Block", "CEO Executive View"):
        block = frappe.get_doc("Custom HTML Block", "CEO Executive View")
        block.html = ceo_html
        block.style = ""
        block.script = ""
        block.private = 0
        block.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "Custom HTML Block",
            "name": "CEO Executive View",
            "html": ceo_html,
            "style": "",
            "script": "",
            "private": 0,
        }).insert(ignore_permissions=True)

    # Update workspace to use this block
    if frappe.db.exists("Workspace", "CEO Executive View"):
        doc = frappe.get_doc("Workspace", "CEO Executive View")
        doc.content = json.dumps([{
            "id": "ceo_executive_dashboard",
            "type": "custom_block",
            "data": {"custom_block_name": "CEO Executive View", "col": 12}
        }], ensure_ascii=False)
        doc.set("custom_blocks", [{"custom_block_name": "CEO Executive View", "label": "CEO Executive View"}])
        doc.icon = "dashboard"
        doc.indicator_color = "orange"
        doc.public = 1
        doc.is_hidden = 0
        doc.sequence_id = 4
        doc.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()

    return {"message": "CEO Executive View updated successfully", "route": "/app/ceo-executive-view"}
