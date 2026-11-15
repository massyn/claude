# CVSS heatmap mappings

Each table places every value of a base metric in a column, from 1 (worst, 🟥) to 4 (best, 🟩). Columns
2 and 3 are 🟧 and 🟨. Empty columns stay empty in the heatmap. Use the vector string's abbreviations
to find the value.

## Score bar colours

Fill `round(score)` squares out of ten (at least one for any score above 0); pad the rest with ⬜.

| Score | Severity | Square |
|---|---|---|
| 0.0 | None | ⬜ |
| 0.1 - 3.9 | Low | 🟩 |
| 4.0 - 6.9 | Medium | 🟨 |
| 7.0 - 8.9 | High | 🟧 |
| 9.0 - 10.0 | Critical | 🟥 |

Example: 6.5 → `🟨🟨🟨🟨🟨🟨🟨⬜⬜⬜ **6.5 / 10 - MEDIUM**`

## CVSS 4.0

| Metric | Row label | 1 🟥 | 2 🟧 | 3 🟨 | 4 🟩 |
|---|---|---|---|---|---|
| AV | Attack vector | N Network | A Adjacent | L Local | P Physical |
| AC | Attack complexity | L Low | | | H High |
| AT | Attack requirements | N None | | | P Present |
| PR | Privileges required | N None | L Low | | H High |
| UI | User interaction | N None | P Passive | | A Active |
| VC | Confidentiality (vulnerable system) | H High | | L Low | N None |
| VI | Integrity (vulnerable system) | H High | | L Low | N None |
| VA | Availability (vulnerable system) | H High | | L Low | N None |
| SC | Confidentiality (other systems) | H High | | L Low | N None |
| SI | Integrity (other systems) | H High | | L Low | N None |
| SA | Availability (other systems) | H High | | L Low | N None |

Use the base metrics only. Supplemental, threat and environmental metrics (`E`, `S`, `AU`, `CR` ...) are
left out of the heatmap; mention `E:A` (attacked) in the text if present.

## CVSS 3.1 and 3.0

| Metric | Row label | 1 🟥 | 2 🟧 | 3 🟨 | 4 🟩 |
|---|---|---|---|---|---|
| AV | Attack vector | N Network | A Adjacent | L Local | P Physical |
| AC | Attack complexity | L Low | | | H High |
| PR | Privileges required | N None | L Low | | H High |
| UI | User interaction | N None | | | R Required |
| S | Scope | C Changed | | | U Unchanged |
| C | Confidentiality | H High | | L Low | N None |
| I | Integrity | H High | | L Low | N None |
| A | Availability | H High | | L Low | N None |

## CVSS 2.0

| Metric | Row label | 1 🟥 | 2 🟧 | 3 🟨 | 4 🟩 |
|---|---|---|---|---|---|
| AV | Access vector | N Network | A Adjacent | | L Local |
| AC | Access complexity | L Low | M Medium | | H High |
| Au | Authentication | N None | S Single | | M Multiple |
| C | Confidentiality | C Complete | | P Partial | N None |
| I | Integrity | C Complete | | P Partial | N None |
| A | Availability | C Complete | | P Partial | N None |

CVSS 2.0 severity bands differ: Low 0.0 - 3.9, Medium 4.0 - 6.9, High 7.0 - 10.0 (no Critical). Note
the version in the summary table, as a 2.0 score is not comparable with a 3.x or 4.0 one.
