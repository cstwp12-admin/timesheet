# Roadmap

**Now: v0.9.7 beta.** A trial within the project team. The app is feature-complete for what it is meant to do:

1. Key in the month on the phone.
2. Print the official form for hand signature.
3. Keep a scan of the signed copy.
4. Compile the team's signed copies into one PDF for HQ.

No new features are planned. The work from here is trial, fixes and upkeep.

## Trial plan

| When | What | Who |
|---|---|---|
| **Week of 19 Oct 2026** | Publish on GitHub. Announce in the team group. Everyone installs the app, completes the Welcome and tries **Fill month** on October. | All |
| **26–30 Oct** | Key in October as the days go. Send feedback with **Setup → Send feedback**. | All |
| **End Oct – 6 Nov** | **October month-end with the app.** Print from the app, sign by hand as usual. The compiler collects QRs, prints all, scans the signed stack and makes the HQ PDF. Keep the Excel sheet in parallel this month and compare the totals. | All, compiler |
| **9–13 Nov** | Review the feedback. Fix what's needed in v0.9.x beta releases. | WPN |
| **End Nov 2026** | If November month-end runs without problems: **v1.0.0**. The beta label comes off and the app becomes the normal way to prepare the timesheet. | WPN |

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
