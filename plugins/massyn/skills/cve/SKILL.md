---
name: cve
description: Look up a CVE and write its remediation document in Markdown - fetch the record from NVD (falling back to the massyn/nvd-cve GitHub mirror), then explain the vulnerability, what it affects (including copies bundled inside other software), a CVSS severity heatmap, how to check whether a machine is exposed, and how to remediate it. Use whenever the user mentions a CVE identifier (CVE-YYYY-NNNN) or asks to check, look up, explain, assess or document a vulnerability or its fix - even if they just say "check CVE-2026-0006" or paste the number on its own.
---

# CVE remediation documents

The user names a CVE; you fetch its record and write one Markdown document that tells a reader what the
vulnerability is, how bad it is, whether their machine is exposed and how to fix it. The document is
reusable: it names no one's machine, environments or tools, only the affected product and the places it
can live.

## 1. Fetch the record

Normalise the identifier to upper case (`CVE-2026-0006`). The year is the second part of the ID.

1. **NVD first** - the NVD API serves the same record as the detail page
   (`https://nvd.nist.gov/vuln/detail/<CVE-ID>`), as JSON:

   ```bash
   curl -sf -m 30 "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=<CVE-ID>"
   ```

   The record is `vulnerabilities[0].cve`. An empty `vulnerabilities` list means NVD doesn't know the ID.
2. **Fallback: the massyn/nvd-cve mirror** - when NVD fails (timeout, 403, 503, rate limit):

   ```bash
   curl -sf -m 30 "https://raw.githubusercontent.com/massyn/nvd-cve/refs/heads/main/database/<YEAR>/<CVE-ID>.json"
   ```

   The record is the top-level `cve` object, in the same schema as the NVD API. The mirror can lag
   behind NVD, so note in the document which source was used and its `lastModified`.
3. If neither has it, tell the user and stop. Don't write a document from memory.

If `vulnStatus` is `Rejected`, or the ID is reserved with no description, tell the user and stop.

## 2. Read the fields that matter

| Field | Use it for |
|---|---|
| `descriptions[lang=en].value` | What the vulnerability is |
| `metrics` | Severity - prefer `cvssMetricV40`, then `cvssMetricV31`, `cvssMetricV30`, `cvssMetricV2`; within one, prefer `type: Primary` |
| `weaknesses[].description[].value` | The CWE (e.g. `CWE-122`) - name it in plain words (heap-based buffer overflow) |
| `configurations[].nodes[].cpeMatch[]` | Affected products: `criteria` (CPE) plus `versionStartIncluding`/`versionEndExcluding` etc. |
| `affected[].affectedData[]` | Vendor/product/versions as the CNA states them, when present |
| `cisaExploitAdd`, `cisaActionDue`, `cisaRequiredAction` | Listed in CISA KEV - known exploited |
| `metrics.ssvcV203[].ssvcData.options` | Exploitation, automatable, technical impact |
| `references[]` | Vendor advisories, patches, release notes - tags `Vendor Advisory`, `Patch`, `Mitigation` |

## 3. Work out how it is exposed

The CPE list says which product is vulnerable; it does not say where the vulnerable code runs. Before
writing, classify the exposure:

| Model | Meaning | Typical signs |
|---|---|---|
| Direct | The affected product is installed as itself | An application, server or OS component |
| Bundled | Other software ships its own copy (vendored, statically linked, shaded, wheel-bundled, in a container layer) | A library, codec, parser, TLS or runtime component; references mention "bundled", "vendored", "embedded" or downstream advisories |
| Transitive | Pulled in as a dependency of a dependency | A package-registry library with many dependants |
| Service or configuration | Exposure depends on a running service or a setting | Network vector, a non-default feature, a config option |

A CVE can be several at once. When it is **bundled** or **transitive**, patching the named product is the
easy part and not the fix: every copy must be found and fixed through its owner. Read
`references/bundled-copies.md` before writing, and apply its sweep, remediation order and gotchas.

- Name a downstream product that carries a copy only when the record, a vendor advisory or the downstream
  project's own advisory says so; cite it. Otherwise describe the ecosystem pattern and label it generic.
- A fixed release of the named product may not exist for every branch, or the downstream owners may not
  have shipped a rebuild yet. Say which, from the sources.

## 4. Get the fix right

The record rarely spells out the fix. Read the references tagged `Vendor Advisory`, `Patch` or
`Mitigation` (fetch them) to find the fixed version, the update to install and any workaround. Record the
fixed version **per affected branch**: a product with 1.0.x, 1.1.x and 1.2.x lines usually has a fix on
each, and a reader on 1.1.0 needs 1.1.1, not 1.2.1.

- Never invent a fixed version, package name, KB number or command. Every one comes from the record or a
  reference you read; cite it.
- If no fix is published, say so plainly, then give the mitigations the advisory offers, or the generic
  ones the attack vector suggests (e.g. block the port for a network-vector flaw), labelled as generic.
- Check commands are **read-only**: they report a version or setting and change nothing. Give them only
  for the platforms the affected product actually runs on, and say what output means "affected".
- Fix commands that remove, uninstall or delete are **destructive**: label them, put them after the
  non-destructive options, and put the dependency check before them.

## 5. Write the document

Save it as `<CVE-ID>.md` in the current directory, unless the project `CLAUDE.md` names another location.
Use plain Markdown that renders on GitHub and in mddoco: pipe tables, fenced code with a language, a blank
line before every table, list and fence; no GitHub alerts (`> [!NOTE]`) or task lists.

Structure, in this order:

```markdown
# CVE-2026-0006: <short plain-English title>

| | |
|---|---|
| **Severity** | 🟥 9.8 CRITICAL (CVSS 3.1) |
| **Vector** | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| **Weakness** | CWE-122 Heap-based buffer overflow |
| **Known exploited** | No (not in CISA KEV) |
| **Published / modified** | 2026-03-02 / 2026-06-17 |
| **Source** | NVD (or: massyn/nvd-cve mirror, record dated ...) |

## What it is
## What it affects
## Where it hides
## How serious it is
## Am I affected?
## How to fix it
## References
```

- **What it is** - two or three short paragraphs in plain English: the flaw, how an attacker reaches it,
  and what they gain. No pasted description; explain it.
- **What it affects** - a table of vendor, product, affected versions (from the CPE ranges, written as
  "from 2.0 up to but not including 2.4.1") and **fixed in**, one row per branch, plus who is typically
  running it.
- **Where it hides** - only when the exposure is bundled or transitive; leave the heading out otherwise.
  Say plainly that patching the named product does not fix other software's own copy, then a table of
  where copies live (ecosystem, location, how to tell), taken from `references/bundled-copies.md` and cut
  to the rows that fit. Name downstream products only as step 3 allows.
- **How serious it is** - the severity visual (section 6), then one paragraph on what the combination
  means in practice, plus KEV and SSVC status when present.
- **Am I affected?** - per platform, the read-only check in a fenced block and how to read its output.
  For a direct install, that is one version command. For a bundled or transitive exposure it is the sweep
  from `references/bundled-copies.md`, written out in full for this CVE (file patterns and version ranges
  filled in), covering every platform the product runs on, with version-aware `[VULN]`, `[PATCHED]` and
  `[UNKNOWN]` output and what a clean result looks like. The sweep lives in the document; do not point at
  an external script.
- **How to fix it** - the fixed version per branch and how to install it, per platform. For a bundled or
  transitive exposure, follow the remediation order in `references/bundled-copies.md` (remove if unused,
  check dependants, upgrade each owner, confirm the upgrade contains the fix, last resort) and include the
  gotchas that apply. Then workarounds if patching has to wait, then how to confirm the fix (rerun the
  check or sweep).
- **References** - the advisories and patches used, as `[title](url)` links.

## 6. The severity visual

Two parts, both built from the vector string. Mappings for every CVSS version are in
`references/cvss-heatmap.md`; read it before drawing.

**Score bar** - ten squares, filled to the rounded score, in the severity colour, then the score:

```markdown
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 **9.8 / 10 - CRITICAL**
```

**Heatmap** - one row per base metric, columns from worst (left, red) to best (right, green). The CVE's
value in each row is bold with its column's square; the other options are plain text. A column of red
down the left edge reads at a glance as "remote, easy, no login, full impact":

```markdown
| Metric | 🟥 Worst | 🟧 | 🟨 | 🟩 Best |
|---|---|---|---|---|
| Attack vector | **🟥 Network** | Adjacent | Local | Physical |
| Attack complexity | **🟥 Low** | | | High |
| Privileges required | **🟥 None** | Low | | High |
| User interaction | **🟥 None** | | | Required |
| Scope | Changed | | | **🟩 Unchanged** |
| Confidentiality | **🟥 High** | | Low | None |
| Integrity | **🟥 High** | | Low | None |
| Availability | **🟥 High** | | Low | None |
```

Follow it with one line naming the worst combination present, e.g. "Reachable over the network with no
login and no user interaction - the most exposed combination CVSS can describe."
