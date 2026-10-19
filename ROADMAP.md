# Roadmap

**Now: v0.9.9 beta.** A trial within the project team. The app does what it is meant to do:

1. Key in the month on the phone.
2. Print the official form for hand signature.
3. Keep a scan of the signed copy.
4. Compile the team's signed copies into one PDF for HQ.

No new workflow is planned. The work from here is trial, polish, fixes and upkeep.

## Trial plan

| When | What | Who |
|---|---|---|
| **Week of 19 Oct 2026** | Publish on GitHub. Announce in the team group. Everyone installs the app, completes the Welcome and tries **Fill month** on October. | All |
| **26–30 Oct** | Key in October as the days go. Send feedback with **Help → Send feedback**. | All |
| **End Oct – 6 Nov** | **October month-end with the app.** Print from the app, sign by hand as usual. The compiler collects QRs, prints all, scans the signed stack and makes the HQ PDF. Keep the Excel sheet in parallel this month and compare the totals. | All, compiler |
| **9–13 Nov** | Review the feedback. Fix what's needed in the next beta. | WPN |
| **End Nov 2026** | If November month-end runs without problems: **v1.0.0**. The beta label comes off and the app becomes the normal way to prepare the timesheet. | WPN |

## Done in v0.9.9

- [x] Drag and drop on a computer (signed copy, photocopier scan, data files, backup)
- [x] HQ cover page in the house style of the WPN apps (as the ClaimPack cover)
- [x] Docs website with the shared "Site Tools" theme; Help opens it
- [x] Accessibility: stronger contrast for orange and green text, announced messages
- [x] Import checks for QR codes, data files and backups; content security policy
- [x] **Help → Share this app** (QR and link), as in ClaimPack
- [x] No company names in the app's wording, the docs or the screenshots
- [x] Third-party notices; licence clause for the official form

## Next beta (v0.9.10, during the trial): polish, no new workflow

Picked to bring the app level with ClaimPack and to close the points from the v0.9.9 audit. Each is small and can be dropped if the trial shows other priorities.

| | Change | Why |
|---|---|---|
| 1 | **Fonts kept in the app** (`fonts/`, Barlow and IBM Plex Mono, open font licence) instead of loading them from Google | Same look on the very first opening without signal; no outside request at all |
| 2 | **Name reading ready offline**: fetch the text-recognition files the first time the compiler opens HQ submission | Today they download the first time a scan is added, so the first HQ PDF needs signal |
| 3 | **Keyboard and screen reader**: focus moves into a sheet when it opens and back when it closes; Tab stays inside the sheet | Finishes the accessibility work started in v0.9.9 |
| 4 | **Try with a sample month** (Setup): loads a made-up month and team to practise on, removed with one tap | Training new staff and showing the app without using real data; ClaimPack has sample files |
| 5 | **Backup reminder** once a month, after *Signed* is marked | Everything lives only on the phone |
| 6 | **PDF properties** (title, author, subject) the same way as ClaimPack on every PDF the app makes | Consistent files from the same developer; easier to find in a folder |
| 7 | **Copy last month's pattern** (leave and codes on the same weekdays), optional | Saves taps for people with a fixed pattern |

**Later, only if the team asks for it:** Bahasa Melayu screens; next year's public holidays as soon as they are gazetted (upkeep).

## How feedback is handled

| Kind | Example | Action |
|---|---|---|
| **Wrong output** | Totals, the printed form, the Excel file or the HQ PDF differ from the official form | Fixed first, in the next beta |
| **Blocks someone** | Doesn't open on a phone model, camera or scan fails | Fixed in the next beta |
| **Wrong data** | A public holiday date, a project title | Corrected in the data file, live the same day |
| **Confusing** | A button or a word people misunderstand | Wording or layout change |
| **New feature** | Something the app doesn't do | Noted. Added only if it saves real time for most of the team and keeps the app simple. |

## After v1.0.0: upkeep only

- **Public holidays:** add next year's list in `holidays/` once it is gazetted, and declared replacement holidays during the year.
- **Projects:** confirm the placeholder project titles (`"toConfirm"` in `packages/`) and add a project when needed.
- **Form change:** if the official timesheet form changes, rebuild the template from the new spreadsheet (`tools/build_template.py`, see README). No change to the app is needed.
- **Library updates:** only if a phone or browser update breaks something.

## Out of scope

To keep the app simple, it will not have:

- user accounts
- a server or online storage of timesheets
- approval workflows
- payroll or claim calculation
- integration with other systems

The signed hardcopy stays the record.
