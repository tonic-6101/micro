import { defineComponent as b, ref as u, onMounted as w, openBlock as c, createElementBlock as g, toDisplayString as e, unref as r, createElementVNode as t, normalizeStyle as k, normalizeClass as f, createCommentVNode as p } from "/assets/dock/js/vendor/vue.esm.js";
function s(m, _) {
  const l = window;
  if (typeof l.__ == "function")
    return l.__(
      m,
      _
    );
  if (_) {
    let n = m;
    for (const [x, a] of Object.entries(_))
      n = n.replace(`{${x}}`, a);
    return n;
  }
  return m;
}
const C = {
  key: 0,
  class: "py-12 text-center text-sm text-gray-500"
}, S = {
  key: 1,
  class: "py-12 text-center text-sm text-red-500 dark:text-red-400"
}, E = {
  key: 2,
  class: "space-y-6"
}, M = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, N = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, R = { class: "grid grid-cols-2 gap-4" }, T = { class: "text-xs text-gray-400 dark:text-gray-500" }, A = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, D = { class: "text-xs text-gray-400 dark:text-gray-500" }, F = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, j = { class: "text-xs text-gray-400 dark:text-gray-500" }, B = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, L = { class: "text-xs text-gray-400 dark:text-gray-500" }, O = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, P = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, z = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, U = { class: "grid grid-cols-2 gap-4" }, V = { class: "text-xs text-gray-400 dark:text-gray-500" }, W = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, q = { class: "text-xs text-gray-400 dark:text-gray-500" }, H = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, I = { class: "text-xs text-gray-400 dark:text-gray-500" }, J = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, X = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, Z = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, $ = { class: "grid grid-cols-2 gap-4" }, G = { class: "text-xs text-gray-400 dark:text-gray-500" }, K = { class: "mt-1 flex items-baseline gap-1" }, Q = { class: "text-lg font-bold text-gray-900 dark:text-white" }, Y = { class: "text-sm text-gray-500 dark:text-gray-400" }, tt = {
  key: 0,
  class: "mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700"
}, et = { class: "text-xs text-gray-400 dark:text-gray-500" }, st = { class: "mt-1 flex items-baseline gap-1" }, at = { class: "text-lg font-bold text-gray-900 dark:text-white" }, rt = { class: "text-sm text-gray-500 dark:text-gray-400" }, dt = {
  key: 0,
  class: "mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700"
}, it = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, ot = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, lt = { class: "grid grid-cols-2 gap-4" }, nt = { class: "text-xs text-gray-400 dark:text-gray-500" }, ct = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, gt = { class: "text-xs text-gray-400 dark:text-gray-500" }, _t = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, xt = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, ut = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, mt = { class: "grid grid-cols-2 gap-4" }, yt = { class: "text-xs text-gray-400 dark:text-gray-500" }, vt = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, ht = { class: "text-xs text-gray-400 dark:text-gray-500" }, pt = { class: "mt-1 text-sm text-gray-500 dark:text-gray-400" }, kt = { class: "flex justify-end" }, ft = {
  href: "/app/micro-settings",
  class: "text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
}, wt = /* @__PURE__ */ b({
  __name: "Settings",
  setup(m) {
    function _() {
      var d, i, o;
      return ((d = window.frappe) == null ? void 0 : d.csrf_token) ?? window.csrf_token ?? ((o = (i = window.dockBoot) == null ? void 0 : i.session) == null ? void 0 : o.csrf_token) ?? "";
    }
    async function l(d, i = {}) {
      const o = await fetch("/api/method/" + d, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": _()
        },
        body: JSON.stringify(i)
      }), h = await o.json();
      if (!o.ok)
        throw new Error((h == null ? void 0 : h.exc_type) ?? "Request failed");
      return { message: h.message };
    }
    const n = u(!0), x = u(null), a = u(null), y = u(null), v = u(null);
    return w(async () => {
      try {
        const [d, i, o] = await Promise.all([
          l("frappe.client.get", { doctype: "Micro Settings" }),
          l("frappe.client.get_count", { doctype: "Contact", filters: { micro_status: ["is", "set"] } }),
          l("frappe.client.get_count", { doctype: "Micro Article" })
        ]);
        a.value = d.message, y.value = i.message, v.value = o.message;
      } catch (d) {
        x.value = (d == null ? void 0 : d.message) ?? s("Failed to load settings");
      } finally {
        n.value = !1;
      }
    }), (d, i) => (c(), g("div", null, [
      n.value ? (c(), g("div", C, e(r(s)("Loading...")), 1)) : x.value ? (c(), g("div", S, e(x.value), 1)) : a.value ? (c(), g("div", E, [
        t("div", M, [
          t("h2", N, e(r(s)("Company Information")), 1),
          t("div", R, [
            t("div", null, [
              t("div", T, e(r(s)("Company Name")), 1),
              t("div", A, e(a.value.company_name || "—"), 1)
            ]),
            t("div", null, [
              t("div", D, e(r(s)("Email")), 1),
              t("div", F, e(a.value.company_email || "—"), 1)
            ]),
            t("div", null, [
              t("div", j, e(r(s)("Phone")), 1),
              t("div", B, e(a.value.company_phone || "—"), 1)
            ]),
            t("div", null, [
              t("div", L, e(r(s)("Address")), 1),
              t("div", O, e(a.value.company_address || "—"), 1)
            ])
          ])
        ]),
        t("div", P, [
          t("h2", z, e(r(s)("Defaults")), 1),
          t("div", U, [
            t("div", null, [
              t("div", V, e(r(s)("Currency")), 1),
              t("div", W, e(a.value.default_currency), 1)
            ]),
            t("div", null, [
              t("div", q, e(r(s)("Language")), 1),
              t("div", H, e(a.value.default_language), 1)
            ]),
            t("div", null, [
              t("div", I, e(r(s)("Monthly Capacity Hours")), 1),
              t("div", J, e(a.value.monthly_capacity_hours || 100) + e(r(s)("h / month")), 1)
            ])
          ])
        ]),
        t("div", X, [
          t("h2", Z, e(r(s)("Usage & Limits")), 1),
          t("div", $, [
            t("div", null, [
              t("div", G, e(r(s)("Customers")), 1),
              t("div", K, [
                t("span", Q, e(y.value ?? "—"), 1),
                t("span", Y, " / " + e(a.value.customer_limit || r(s)("unlimited")), 1)
              ]),
              a.value.customer_limit ? (c(), g("div", tt, [
                t("div", {
                  class: f(["h-full rounded-full transition-all", (y.value || 0) >= a.value.customer_limit ? "bg-red-500" : "bg-accent-600"]),
                  style: k({ width: Math.min(100, (y.value || 0) / a.value.customer_limit * 100) + "%" })
                }, null, 6)
              ])) : p("", !0)
            ]),
            t("div", null, [
              t("div", et, e(r(s)("Articles")), 1),
              t("div", st, [
                t("span", at, e(v.value ?? "—"), 1),
                t("span", rt, " / " + e(a.value.article_limit || r(s)("unlimited")), 1)
              ]),
              a.value.article_limit ? (c(), g("div", dt, [
                t("div", {
                  class: f(["h-full rounded-full transition-all", (v.value || 0) >= a.value.article_limit ? "bg-red-500" : "bg-accent-600"]),
                  style: k({ width: Math.min(100, (v.value || 0) / a.value.article_limit * 100) + "%" })
                }, null, 6)
              ])) : p("", !0)
            ])
          ])
        ]),
        t("div", it, [
          t("h2", ot, e(r(s)("Tax Advisor")), 1),
          t("div", lt, [
            t("div", null, [
              t("div", nt, e(r(s)("Name")), 1),
              t("div", ct, e(a.value.tax_advisor_name || "—"), 1)
            ]),
            t("div", null, [
              t("div", gt, e(r(s)("Email")), 1),
              t("div", _t, e(a.value.tax_advisor_email || "—"), 1)
            ])
          ])
        ]),
        t("div", xt, [
          t("h2", ut, e(r(s)("Compliance (Zone 2)")), 1),
          t("div", mt, [
            t("div", null, [
              t("div", yt, e(r(s)("Watermark Text")), 1),
              t("div", vt, e(a.value.draft_watermark_text || "ENTWURF"), 1)
            ]),
            t("div", null, [
              t("div", ht, e(r(s)("Disclaimer")), 1),
              t("div", pt, e(a.value.draft_disclaimer || "—"), 1)
            ])
          ])
        ]),
        t("div", kt, [
          t("a", ft, e(r(s)("Edit in Desk")) + " → ", 1)
        ])
      ])) : p("", !0)
    ]));
  }
});
export {
  wt as MicroSettings
};
