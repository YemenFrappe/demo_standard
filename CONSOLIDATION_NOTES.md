# Consolidation Notes

## Source Review

- `ar_translations`: best Arabic translation base. It fully covers `translations_ar_eg` and adds more entries.
- `translations_ar_eg`: useful only for Arabic font and RTL CSS. Its translation file is smaller than `ar_translations`.
- `pro_standard`: contains some workspace ideas, but also old client branding and non-generic website settings.
- `pro_plan`: restaurant-specific. Keep only if restaurant demos are still required.
- `basic_paln`: legacy customizations bundle, not suitable as a reusable demo polish app.

## Recommended Status

- Replace `ar_translations` and `translations_ar_eg` with `demo_standard` for future demos.
- Do not install `pro_standard` on generic demos. Reuse selected ideas manually if needed.
- Keep `pro_plan` only for restaurant/POS vertical demos.
- Archive `basic_paln` unless there is a current customer depending on its custom fields.

## Current Bench Status

- `demo_standard` is now installed on:
  - `dreamwear.yemenfrappe.com`
  - `demo.yemenfrappe.com`
  - `pos.yemenfrappe.com`
  - `pos2.yemenfrappe.com`
  - `xair.yemenfrappe.com`
- `translations_ar_eg` has been removed from all currently detected sites.
- `pro_standard` is not installed on any currently detected site.
- `ar_translations` is not installed on any currently detected site.
- `basic_paln` is still installed on `xair.yemenfrappe.com`.
- `pro_plan` is still installed on `level2.yemenfrappe.com`.

## Safe To Delete Now

- `translations_ar_eg`
- `ar_translations`
- `pro_standard`

## Keep Until Migrated

- `basic_paln`
- `pro_plan`

## What Demo Standard Owns

- Arabic translation file
- Arabic font bundle
- desk and web CSS polish
- curated demo workspace
- workspace ordering rules
