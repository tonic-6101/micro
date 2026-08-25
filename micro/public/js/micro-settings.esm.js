import { defineComponent as w, computed as k, openBlock as c, createElementBlock as h, normalizeClass as f, renderSlot as T, createTextVNode as C, toDisplayString as e, createCommentVNode as _, ref as y, onMounted as S, unref as o, createElementVNode as t, createVNode as M, normalizeStyle as b } from "/assets/dock/js/vendor/vue.esm.js";
function s(r, i) {
  const n = window;
  if (typeof n.__ == "function")
    return n.__(
      r,
      i
    );
  if (i) {
    let l = r;
    for (const [u, a] of Object.entries(i))
      l = l.replace(`{${u}}`, a);
    return l;
  }
  return r;
}
const z = {
  // --- Micro Lead ---------------------------------------------------------
  lead_name: "The name of this deal. Imported leads take the name of the company or person they came from — click it to rename.",
  contact: "The person or organization this deal is about. One contact can run through several pipelines at once, which is why leads and contacts are kept apart.",
  stage: "Where the deal stands in its pipeline. Moving it to a won or lost stage closes the lead and sets its status.",
  status: 'Open, Won or Lost — this follows from the stage rather than being set by hand. Leads in the trash read "In trash".',
  priority: "How urgently this deal needs you. High and Low show as a badge on the board card; Medium stays quiet.",
  expected_value: "What the deal is worth in euros if it is won — never negative, and capped so a slipped zero cannot distort the board totals. Raise the ceiling under Micro Settings → Max Expected Value. A guess is better than nothing.",
  source: "Where the lead came from — an import, an ad, a referral. This is what tells you later which channels are worth the money.",
  next_follow_up: `The day you mean to get back in touch. Today or earlier puts the lead in the call list and in the board's "Due today" filter.`,
  lost_reason: "Why the deal fell through. Asked for when a lead lands in a lost stage, and worth writing plainly — it is the only record of why.",
  notes: "What was said, what was agreed, what comes next. Free text, kept on the lead rather than on the contact.",
  // --- Contact (Micro CRM fields) -----------------------------------------
  first_name: "The person's first name. For an organization, this holds the full company name.",
  last_name: "The person's surname. Left empty for organizations.",
  company_name: "The company this contact writes under. Shown on the board card when it differs from the lead name.",
  email_id: "The main address for this contact. Offers and invoices go here.",
  phone: "The landline. The call list dials whichever number is set.",
  mobile_no: "The mobile number. Preferred over the landline on board cards and in the call list.",
  micro_website: "The contact's website — handy before a first call.",
  micro_address: "Street and house number. Printed on offers and invoices.",
  micro_postal_code: "Postal code, printed on documents and used to group contacts by area.",
  micro_city: "City, printed on documents and used to group contacts by area.",
  micro_country: "Country, printed on documents. Matters for VAT on invoices.",
  micro_status: "Where the relationship stands overall: Potential, Active or Inactive. This describes the contact, not any single deal.",
  micro_source: "How this contact first reached you. The deal has its own source, which may differ.",
  micro_segment: "Durable target group — independent of the pipeline stage of any single deal.",
  micro_organization: "The organization this person belongs to. Documents are addressed to the organization; the conversation belongs to the person.",
  micro_contact_type: "Person or Organization. Organizations are addressed by company name; people carry a first and last name.",
  micro_pipeline_stage: "Mirror of the contact's most recent open lead. The pipeline board reads Micro Lead — edit the lead, not this field.",
  micro_notes: "Anything worth remembering about this contact that has no field of its own.",
  micro_client_loves: "What this client values — bring it up and the conversation goes easier.",
  micro_communication_style: "How this client likes to be approached: short and factual, or with time to talk.",
  // --- Board controls -----------------------------------------------------
  due_only: "Show only leads whose follow-up date is today or already past.",
  show_closed: "Also show the won and lost stages, which the board hides by default.",
  search_leads: "Finds a lead by its own name, or by the contact on the card — name, company, email or phone.",
  // --- Customer list controls ----------------------------------------------
  select_customer: "Select this customer for a bulk action, such as deleting several at once.",
  select_all_customers: "Select every customer currently shown on this page.",
  // --- Distance ------------------------------------------------------------
  distance_km: "Straight distance between your company postal code and this contact's — as the crow flies, so the drive is longer, usually by a fifth to a third. Set your postal code under Settings → Company Information; contacts without one show no distance.",
  company_postal_code: "Where you work from. Printed on documents, and the point every lead's distance is measured from — without it the cards show no distance at all.",
  // --- Call attempts (Micro Lead) ------------------------------------------
  log_call_attempt: "Log how this call went, with the current time. Logged against the contact, not this deal, so the pattern of when they answer builds up across every lead they are ever part of.",
  best_time_to_call: "Worked out from every logged call: the weekday and time of day this contact has answered most often. Needs a couple of reached calls in the same slot before a pattern shows."
};
function A(r) {
  const i = r ? z[r] : "";
  return i ? s(i) : "";
}
const W = ["tabindex", "aria-describedby"], L = /* @__PURE__ */ w({
  __name: "FieldLabel",
  props: {
    label: {},
    field: {},
    hint: {},
    uppercase: { type: Boolean, default: !0 },
    align: { default: "left" }
  },
  setup(r) {
    const i = r, n = k(() => i.hint || A(i.field)), l = `field-hint-${Math.random().toString(36).slice(2, 10)}`;
    return (u, a) => (c(), h("span", {
      class: f(["group relative inline-flex items-center text-xs text-gray-500", [r.uppercase ? "uppercase" : "font-medium", n.value ? "cursor-help" : ""]]),
      tabindex: n.value ? 0 : void 0,
      "aria-describedby": n.value ? l : void 0
    }, [
      T(u.$slots, "default", {}, () => [
        C(e(r.label), 1)
      ]),
      n.value ? (c(), h("span", {
        key: 0,
        id: l,
        role: "tooltip",
        class: f(["pointer-events-none absolute top-full z-30 mt-1 hidden w-64 max-w-[80vw] rounded-md bg-gray-900 px-2.5 py-2 text-xs font-normal normal-case leading-snug text-white shadow-lg group-hover:block group-focus-visible:block", r.align === "right" ? "right-0" : "left-0"])
      }, e(n.value), 3)) : _("", !0)
    ], 10, W));
  }
}), N = {
  key: 0,
  class: "py-12 text-center text-sm text-gray-500"
}, P = {
  key: 1,
  class: "py-12 text-center text-sm text-red-500 dark:text-red-400"
}, F = {
  key: 2,
  class: "space-y-6"
}, E = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, O = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, D = { class: "grid grid-cols-2 gap-4" }, I = { class: "text-xs text-gray-400 dark:text-gray-500" }, R = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, H = { class: "text-xs text-gray-400 dark:text-gray-500" }, V = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, B = { class: "text-xs text-gray-400 dark:text-gray-500" }, $ = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, j = { class: "text-xs text-gray-400 dark:text-gray-500" }, q = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, U = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, J = {
  key: 0,
  class: "mt-3 text-xs text-amber-700 dark:text-amber-500"
}, X = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, Z = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, G = { class: "grid grid-cols-2 gap-4" }, K = { class: "text-xs text-gray-400 dark:text-gray-500" }, Q = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, Y = { class: "text-xs text-gray-400 dark:text-gray-500" }, tt = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, et = { class: "text-xs text-gray-400 dark:text-gray-500" }, at = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, st = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, ot = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, rt = { class: "grid grid-cols-2 gap-4" }, nt = { class: "text-xs text-gray-400 dark:text-gray-500" }, it = { class: "mt-1 flex items-baseline gap-1" }, dt = { class: "text-lg font-bold text-gray-900 dark:text-white" }, lt = { class: "text-sm text-gray-500 dark:text-gray-400" }, ct = {
  key: 0,
  class: "mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700"
}, ht = { class: "text-xs text-gray-400 dark:text-gray-500" }, ut = { class: "mt-1 flex items-baseline gap-1" }, mt = { class: "text-lg font-bold text-gray-900 dark:text-white" }, gt = { class: "text-sm text-gray-500 dark:text-gray-400" }, yt = {
  key: 0,
  class: "mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700"
}, _t = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, pt = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, xt = { class: "grid grid-cols-2 gap-4" }, vt = { class: "text-xs text-gray-400 dark:text-gray-500" }, ft = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, bt = { class: "text-xs text-gray-400 dark:text-gray-500" }, wt = { class: "mt-1 text-sm text-gray-900 dark:text-gray-200" }, kt = { class: "rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5" }, Tt = { class: "mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400" }, Ct = { class: "grid grid-cols-2 gap-4" }, St = { class: "text-xs text-gray-400 dark:text-gray-500" }, Mt = { class: "mt-1 text-sm font-medium text-gray-900 dark:text-white" }, zt = { class: "text-xs text-gray-400 dark:text-gray-500" }, At = { class: "mt-1 text-sm text-gray-500 dark:text-gray-400" }, Wt = { class: "flex justify-end" }, Lt = {
  href: "/app/micro-settings",
  class: "text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
}, Pt = /* @__PURE__ */ w({
  __name: "Settings",
  setup(r) {
    function i() {
      var d, m, g;
      return ((d = window.frappe) == null ? void 0 : d.csrf_token) ?? window.csrf_token ?? ((g = (m = window.dockBoot) == null ? void 0 : m.session) == null ? void 0 : g.csrf_token) ?? "";
    }
    async function n(d, m = {}) {
      const g = await fetch("/api/method/" + d, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": i()
        },
        body: JSON.stringify(m)
      }), v = await g.json();
      if (!g.ok)
        throw new Error((v == null ? void 0 : v.exc_type) ?? "Request failed");
      return { message: v.message };
    }
    const l = y(!0), u = y(null), a = y(null), p = y(null), x = y(null);
    return S(async () => {
      try {
        const [d, m, g] = await Promise.all([
          n("frappe.client.get", { doctype: "Micro Settings" }),
          n("frappe.client.get_count", { doctype: "Contact", filters: { micro_status: ["is", "set"] } }),
          n("frappe.client.get_count", { doctype: "Micro Article" })
        ]);
        a.value = d.message, p.value = m.message, x.value = g.message;
      } catch (d) {
        u.value = (d == null ? void 0 : d.message) ?? s("Failed to load settings");
      } finally {
        l.value = !1;
      }
    }), (d, m) => (c(), h("div", null, [
      l.value ? (c(), h("div", N, e(o(s)("Loading...")), 1)) : u.value ? (c(), h("div", P, e(u.value), 1)) : a.value ? (c(), h("div", F, [
        t("div", E, [
          t("h2", O, e(o(s)("Company Information")), 1),
          t("div", D, [
            t("div", null, [
              t("div", I, e(o(s)("Company Name")), 1),
              t("div", R, e(a.value.company_name || "—"), 1)
            ]),
            t("div", null, [
              t("div", H, e(o(s)("Email")), 1),
              t("div", V, e(a.value.company_email || "—"), 1)
            ]),
            t("div", null, [
              t("div", B, e(o(s)("Phone")), 1),
              t("div", $, e(a.value.company_phone || "—"), 1)
            ]),
            t("div", null, [
              t("div", j, e(o(s)("Address")), 1),
              t("div", q, e(a.value.company_address || "—"), 1)
            ]),
            t("div", null, [
              M(L, {
                field: "company_postal_code",
                label: o(s)("Postal Code / City"),
                uppercase: !1,
                class: "!font-normal !text-gray-400 dark:!text-gray-500"
              }, null, 8, ["label"]),
              t("div", U, e([a.value.company_postal_code, a.value.company_city].filter(Boolean).join(" ") || "—"), 1)
            ])
          ]),
          a.value.company_postal_code ? _("", !0) : (c(), h("p", J, e(o(s)("Add your postal code to see how far away each lead is.")), 1))
        ]),
        t("div", X, [
          t("h2", Z, e(o(s)("Defaults")), 1),
          t("div", G, [
            t("div", null, [
              t("div", K, e(o(s)("Currency")), 1),
              t("div", Q, e(a.value.default_currency), 1)
            ]),
            t("div", null, [
              t("div", Y, e(o(s)("Language")), 1),
              t("div", tt, e(a.value.default_language), 1)
            ]),
            t("div", null, [
              t("div", et, e(o(s)("Monthly Capacity Hours")), 1),
              t("div", at, e(a.value.monthly_capacity_hours || 100) + e(o(s)("h / month")), 1)
            ])
          ])
        ]),
        t("div", st, [
          t("h2", ot, e(o(s)("Usage & Limits")), 1),
          t("div", rt, [
            t("div", null, [
              t("div", nt, e(o(s)("Customers")), 1),
              t("div", it, [
                t("span", dt, e(p.value ?? "—"), 1),
                t("span", lt, " / " + e(a.value.customer_limit || o(s)("unlimited")), 1)
              ]),
              a.value.customer_limit ? (c(), h("div", ct, [
                t("div", {
                  class: f(["h-full rounded-full transition-all", (p.value || 0) >= a.value.customer_limit ? "bg-red-500" : "bg-accent-600"]),
                  style: b({ width: Math.min(100, (p.value || 0) / a.value.customer_limit * 100) + "%" })
                }, null, 6)
              ])) : _("", !0)
            ]),
            t("div", null, [
              t("div", ht, e(o(s)("Articles")), 1),
              t("div", ut, [
                t("span", mt, e(x.value ?? "—"), 1),
                t("span", gt, " / " + e(a.value.article_limit || o(s)("unlimited")), 1)
              ]),
              a.value.article_limit ? (c(), h("div", yt, [
                t("div", {
                  class: f(["h-full rounded-full transition-all", (x.value || 0) >= a.value.article_limit ? "bg-red-500" : "bg-accent-600"]),
                  style: b({ width: Math.min(100, (x.value || 0) / a.value.article_limit * 100) + "%" })
                }, null, 6)
              ])) : _("", !0)
            ])
          ])
        ]),
        t("div", _t, [
          t("h2", pt, e(o(s)("Tax Advisor")), 1),
          t("div", xt, [
            t("div", null, [
              t("div", vt, e(o(s)("Name")), 1),
              t("div", ft, e(a.value.tax_advisor_name || "—"), 1)
            ]),
            t("div", null, [
              t("div", bt, e(o(s)("Email")), 1),
              t("div", wt, e(a.value.tax_advisor_email || "—"), 1)
            ])
          ])
        ]),
        t("div", kt, [
          t("h2", Tt, e(o(s)("Compliance (Zone 2)")), 1),
          t("div", Ct, [
            t("div", null, [
              t("div", St, e(o(s)("Watermark Text")), 1),
              t("div", Mt, e(a.value.draft_watermark_text || "ENTWURF"), 1)
            ]),
            t("div", null, [
              t("div", zt, e(o(s)("Disclaimer")), 1),
              t("div", At, e(a.value.draft_disclaimer || "—"), 1)
            ])
          ])
        ]),
        t("div", Wt, [
          t("a", Lt, e(o(s)("Edit in Desk")) + " → ", 1)
        ])
      ])) : _("", !0)
    ]));
  }
});
export {
  Pt as MicroSettings
};
