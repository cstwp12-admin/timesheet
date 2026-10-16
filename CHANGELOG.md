# What changed

Versions before 1.0.0 are for testing. 1.0.0 will be the first public release.

## v0.9.6 beta – 16 October 2026

- **Digital signature is opt-in** (Setup → Digital signature, off by default): the timesheet is normally signed by hand. When on, *Sign & signed copy* has **Sign this month**, **Remove from this month** and **Change or delete my signature** in one place.
- **RE key removed**: RE signing is protected by the RE role and the signature PIN only, with no key to set up.
- **Summary QR** (about 13 mm) replaces the small ID mark: project, month, name, designation, normal hours and OT hours. A scan of the signed stack identifies each page and lists the hours on the cover page, even without the team list.
- **Mark under the form** is chosen on the **Print / PDF** screen and next to **Print all** (None · Summary QR · Full QR), not only in Setup.
- **HQ PDF preview** shows every scanned page, not only the first.
- **User guide** with screenshots, and **ROADMAP.md** (trial plan).

## v0.9.5 beta – 14 October 2026

- **Mark under the printed form**, three choices in Setup → Signature block: *None* (default, names are read from the scans), **Small ID mark** (about 10 mm, a 21 × 21 QR in the bottom corner outside the form, saying whose timesheet and which month; read first, name reading as fallback), or *Full data QR* (about 28 mm, also fills the team list).

## v0.9.4 beta – 14 October 2026

- **No QR on the printed form** by default. Scanned pages are now matched by **reading the printed name** on each page (offline text recognition, `lib/tesseract/`), matched to the team list; pages it cannot read follow the print order. **Check pages** shows each page with the name as read and a team-name picker to confirm or correct. The data QR under the form is still available in Setup, off by default.
- **RE key**: the RE's phone creates a key once (Setup → Your role); its public part goes in the project file (*Export project file*). Only the phone holding that key can take the RE role and sign under *Verified by PYKP*. Every RE signature carries a cryptographic signature over the name, month, hours and date; any phone shows it only if it checks out against the key in the project file. Needs the app opened from its web address (https).

## v0.9.3 beta – 14 October 2026

- **Roles** (Setup → Your role, also asked at first start): *Staff* (own timesheet), *Compiler* (also HQ submission), *RE* (also signs under *Verified by PYKP*). Only the RE role can sign as RE.
- **Signature PIN**: asked each time a saved signature is put on a timesheet; required for the RE role.
- **Signature check**: each digital signature keeps a fingerprint of the hours. If the hours change after signing, the signature is not printed until signed again (also for signatures received in a QR).
- **Adjust signature position**: drag each signature on the form and set its size (Print / PDF → *Adjust signature position*, or Setup). Saved per project and layout.
- **Timesheet data QR on the printout**: the QR under the form now carries the whole timesheet (same as *Show QR*, without signatures). A photocopier scan of the signed stack fills the team list by itself; *Scan team QR* also reads a printed sheet.
- **Welcome** on first start: name, status, code and role only; the details panel stays folded.
- **HQ submission** split into two screens: *1 · Team timesheets* and *2 · Signed copies for HQ*, with the monthly steps on the first screen. The HQ button shows only for the Compiler and RE roles.
- **Records** is now the history of months; actions stay on the month itself.

## v0.9.2 beta – 14 October 2026

- **Signature block** back to the **original form** by default (everyone signs and stamps the hardcopy). Side by side (PYKP beside SOR, more room for stamps) remains an option in Setup. With the original form, the RE's and SOR's names print under their lines when set.
- **Digital signature (optional)**: draw your signature on the screen or take a photo of it (Setup → My signature). **Sign** puts it on *Signature* (prepared by). A drawn signature travels in the QR to the RE; the RE taps **Sign** or **Sign all as RE** in HQ submission to sign under *Verified by PYKP*, with the RE's name and status. PDF and Excel both carry the signatures.
- **Photocopier scans**: each printed sheet has a small page ID (QR and text) under the form. Add the photocopier's scan PDF in HQ submission and the app reads the ID on every page (turned pages too), so the cover page lists whose timesheet is on which page. Pages without an ID can be matched to the team list order. Missing timesheets are flagged.
- **Cover page** no longer has signature boxes: it is generated digitally and says so.
- **Month-end steps** strip at the top: Fill → Print → Sign → Submit, each tappable.

## v0.9.1 beta – 14 October 2026

- **HQ submission** reordered: **1 · Team timesheets** (scan everyone's QR, print all for signature) then **2 · Signed copies for HQ**.
- **Preview** for the team timesheets and for the HQ PDF before making it.
- **Cover page** in a proper format: letterhead, submission details, list of timesheets with designation, hours, OT, pages and page numbers, totals, sign-off boxes (compiled by, checked by, received by HQ), and a footer with the app QR and "generated by". Every page of the HQ PDF is numbered.
- **Signature block**: *Verified by PYKP* (RE) now sits beside the SOR, each with signature line, name, title and date; the employee signs above. The original stacked layout is still available in Setup. RE and SOR names can be set in Setup (blank prints NAME : …… to write by hand).
- **Send feedback on WhatsApp** in Setup and at the bottom of the main screen, with the app version and phone type filled in.

## v0.9.0 beta – 14 October 2026

First test version.

- **Layout** in the same style as the site photo report app: one screen with *Timesheet details*, *Fill month* / *Select days*, the calendar, the summary and the signed copy; *Records* and *Setup* at the top; *Print / PDF* in the bottom bar.
- **Code no. and stage code pickers** (A–G, from the form's stage code legend). Day codes from the form's leave legend: AL, EL, MC, PKP, plus RD, PH, half day, any hours or another code.
- **Fill month**: normal hours on working days, RD on rest days, PH on public holidays (replacement days included). **Select days** to set several days at once.
- Overtime under time codes 2–5, private day notes, remarks column.
- **Checks** before printing: blank days, overtime under the wrong code, hours on RD/PH, over 24 hours, missing details.
- **PDF** drawn from the official spreadsheet form; **Excel** fills the form itself (formatting, header, totals and print setup kept).
- **Document scanner** for the signed copy: live camera finds the page edges, drag the corners, the page is straightened and cleaned up (B&W, grey or colour). Falls back to the phone's camera app when the live camera is not available.
- **Status** Printed → Signed → Sent to HQ, tap again to undo.
- **QR transfer**: each person shows a QR of their month; the compiler scans it (live camera or a photo of the QR). No internet needed. Data files remain as a second way.
- **HQ submission**: scan the team's signed sheets one after another or add files, then one PDF with a cover list for submission to HQ. Team timesheets: all in one PDF, one Excel workbook (a sheet per person), summary CSV.
- Projects in `packages/`, holiday lists in `holidays/`, opens straight from a folder (`app-data.js`), works offline, backup and restore.
- Top bar stays dark in dark mode.
