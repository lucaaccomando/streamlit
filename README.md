# HIPAA Breach Explorer

**A HIPAA breach dashboard for healthcare security teams**

**Live app:** https://YOUR-APP-NAME.streamlit.app <!-- replace with your Streamlit Community Cloud URL -->

Author: Luca Accomando · CIS 3400 Advanced Programming · Deliverable 3

## Project

Every breach of protected health information that affects 500 or more people must be reported
to the U.S. Department of Health and Human Services (HHS), and HHS publishes the list. This
project turns that public list into an interactive Streamlit dashboard. It shows how breaches
have changed over time, what causes them, which systems are exposed, and which kinds of
organizations and states are hit hardest.

## Intended audience

- Hospital and health-system **security and compliance officers**
- **Healthcare IT managers** deciding where to spend limited defensive resources
- **Cybersecurity students and analysts**, plus policy analysts and journalists who follow
  healthcare privacy

## Questions investigated

1. **Trends:** How have the number of breaches and the number of people affected changed since
   2010, and is hacking driving the recent growth compared with theft, loss, or unauthorized
   access?
2. **Exposure:** Which locations of breached information (network servers, email, paper,
   laptops, etc.) are involved in the most breaches, and which are involved in the largest ones?
3. **Who is hit:** Which types of organizations and which states report the most breaches, and
   are breaches that involve a business associate (outside vendor) larger?

## Dataset and source

- **Source:** U.S. Department of Health and Human Services, Office for Civil Rights (OCR),
  Breach Portal: *Breaches Affecting 500 or More Individuals*:
  <https://ocrportal.hhs.gov/ocr/breach/breach_report_hip.jsf>
- **Downloaded:** 30 October 2026 (CSV exports of the *Archive* and *Under Investigation* lists)
- **License:** public U.S. government data. Each row describes an organization, not a private
  individual, so the data raises no personal privacy concerns.
- **`dashboard_data.csv`:** 8,069 breaches (Oct 2009 to Oct 2026), 23 columns, about 1.3 MB.
  It was cleaned in the Deliverable 2 notebook: column names restored, duplicates removed,
  dates parsed, multi-valued breach types grouped under the most serious type, one 0/1 flag
  per breach location, and calculated year and size columns added. The long free-text
  description column was dropped. Only this cleaned file is uploaded; the raw exports are not
  needed for deployment.

## Dashboard features

- **Summary metrics:** breaches reported, individuals affected, median breach size, share
  caused by hacking/IT, and share of people affected in breaches involving a vendor
- **Interactive controls (sidebar):** year range, breach type, organization type, state, and
  business-associate involvement, plus a reset button
- **Charts:**
  1. Breaches per year by breach type (count or percent share)
  2. Breaches by location of the breached data (count, total people, or median size)
  3. Top states (by breaches or people affected) and organization types (share of breaches vs.
     share of people affected)
- A short "In your selection" finding that updates with the filters, an explanation under each
  chart, a filtered data table with CSV download, and a limitations section

## Key findings

- Reported breaches rose about **4×** from 2010 (199) to 2025 (807), and **hacking accounts
  for all of that growth**: from about 4% of breaches in 2010 to about 81% in 2025.
- **Network servers** are both the most frequent and the most damaging location: about 46% of
  breaches and about 91% of people affected.
- **Healthcare providers** report about 72% of breaches but only about 32% of people affected,
  while **business associates** report 15% of breaches but about 49% of people affected.

## Limitations

- Only breaches affecting 500 or more people are listed.
- The same person can be counted in several breaches, so totals measure exposure events, not
  unique people.
- Dates are when a breach was reported to HHS, not when it happened. 2009 and 2026 are partial
  years, and cases under investigation may still change.
- State counts are not adjusted for population.

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit dashboard |
| `dashboard_data.csv` | Cleaned dataset the app loads |
| `requirements.txt` | Python packages for Streamlit Community Cloud |
| `.streamlit/config.toml` | App theme |

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
