---
name: cve
description: Look up a CVE and write its remediation document in Markdown - fetch the record from NVD (falling back to the massyn/nvd-cve GitHub mirror), then explain the vulnerability, what it affects, a CVSS severity heatmap, how to check whether a machine is exposed, and how to remediate it. Use whenever the user mentions a CVE identifier (CVE-YYYY-NNNN) or asks to check, look up, explain, assess or document a vulnerability or its fix - even if they just say "check CVE-2026-0006" or paste the number on its own.
---

# CVE remediation documents

The user names a CVE; you fetch its record and write one Markdown document that tells a reader what the
vulnerability is, how bad it is, whether their machine is exposed and how to fix it.

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

## 3. Get the fix right

The record rarely spells out the fix. Read the references tagged `Vendor Advisory`, `Patch` or
`Mitigation` (fetch them) to find the fixed version, the update to install and any workaround.

- Never invent a fixed version, package name, KB number or command. Every one comes from the record or a
  reference you read; cite it.
- If no fix is published, say so plainly, then give the mitigations the advisory offers, or the generic
  ones the attack vector suggests (e.g. block the port for a network-vector flaw), labelled as generic.
- Check commands are **read-only**: they report a version or setting and change nothing. Give them only
  for the platforms the affected product actually runs on, and say what output means "affected".

## 4. Write the document

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
## How serious it is
## Am I affected?
## How to fix it
## References
```

- **What it is** - two or three short paragraphs in plain English: the flaw, how an attacker reaches it,
  and what they gain. No pasted description; explain it.
- **What it affects** - a table of vendor, product and affected versions (from the CPE ranges, written
  as "from 2.0 up to but not including 2.4.1"), plus who is typically running it.
- **How serious it is** - the severity visual (section 5), then one paragraph on what the combination
  means in practice, plus KEV and SSVC status when present.
- **Am I affected?** - per platform, the read-only check command in a fenced block and how to read its
  output.
- **How to fix it** - the fixed version and how to install it, per platform; then workarounds if
  patching has to wait; then how to confirm the fix (rerun the check).
- **References** - the advisories and patches used, as `[title](url)` links.

## 5. The severity visual

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
