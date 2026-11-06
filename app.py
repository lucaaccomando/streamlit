"""HIPAA Breach Explorer - Streamlit dashboard (Deliverable 3).

Data: HHS Office for Civil Rights Breach Portal, "Breaches Affecting 500 or More
Individuals" (Archive + Under Investigation lists), cleaned in Deliverable 2 and
saved as dashboard_data.csv.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Page setup and constants
# ---------------------------------------------------------------------------
st.set_page_config(page_title="HIPAA Breach Explorer", page_icon="🔒", layout="wide")

DATA_FILE = "dashboard_data.csv"

# One fixed colour per breach type, so a filter never repaints a category.
GROUP_ORDER = ["Hacking/IT Incident", "Unauthorized Access/Disclosure", "Theft",
               "Loss", "Improper Disposal", "Other/Unknown"]
GROUP_COLORS = dict(zip(GROUP_ORDER, ["#2a78d6", "#eb6834", "#1baf7a",
                                      "#eda100", "#e87ba4", "#6250d6"]))
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#a8a7a2"
INK, INK_MUTED, GRID = "#1f1f1e", "#6b6a66", "#e8e7e3"

LOCATIONS = {"loc_network_server": "Network Server", "loc_email": "Email",
             "loc_paper": "Paper/Films", "loc_laptop": "Laptop",
             "loc_emr": "Electronic Medical Record", "loc_desktop": "Desktop Computer",
             "loc_portable_device": "Other Portable Device", "loc_other": "Other"}

MIN_N = 30            # medians from fewer breaches than this are greyed out
DEFAULT_YEARS = (2010, 2025)   # complete years only
PARTIAL_YEARS = {2009, 2026}


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE, parse_dates=["submission_date", "year_month"])
    df["breach_type_group"] = pd.Categorical(df["breach_type_group"],
                                             categories=GROUP_ORDER, ordered=True)
    return df


def fmt_people(x: float) -> str:
    """Readable count: 1.2B, 45.3M, 12K, 800."""
    if pd.isna(x):
        return "n/a"
    if x >= 1e9:
        return f"{x / 1e9:,.2f}B"
    if x >= 1e6:
        return f"{x / 1e6:,.1f}M"
    if x >= 1e4:
        return f"{x / 1e3:,.0f}K"
    return f"{x:,.0f}"


def style_fig(fig: go.Figure, height: int = 420) -> go.Figure:
    """Shared chart styling: recessive grid, readable fonts, no chart junk."""
    fig.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=10, r=30, t=10, b=10),
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=13, color=INK),
        hoverlabel=dict(bgcolor="white", font_size=13, font_color=INK),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    title_text="", font=dict(size=12)),
        bargap=0.25,
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
                     title_font=dict(size=13, color=INK_MUTED), tickfont=dict(color=INK_MUTED))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
                     title_font=dict(size=13, color=INK_MUTED), tickfont=dict(color=INK_MUTED))
    return fig


df = load_data()
ALL_ENTITY_TYPES = sorted(df["entity_type"].unique())
ALL_STATES = sorted(s for s in df["state"].unique() if s != "Unknown") + ["Unknown"]
YEAR_MIN, YEAR_MAX = int(df["year"].min()), int(df["year"].max())

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
FILTER_DEFAULTS = {"f_years": DEFAULT_YEARS, "f_types": GROUP_ORDER,
                   "f_entities": ALL_ENTITY_TYPES, "f_states": [], "f_ba": "All breaches"}
for key, value in FILTER_DEFAULTS.items():
    st.session_state.setdefault(key, value)


def reset_filters():
    for k, v in FILTER_DEFAULTS.items():
        st.session_state[k] = v


with st.sidebar:
    st.header("Filters")
    st.caption("Every metric and chart on the page updates with these filters.")
    years = st.slider("Year reported", YEAR_MIN, YEAR_MAX, key="f_years",
                      help="2009 (from 21 Oct) and 2026 (to early Oct) are partial years, "
                           "so the default range leaves them out.")
    breach_types = st.multiselect("Breach type", GROUP_ORDER, key="f_types")
    entity_types = st.multiselect("Organization type", ALL_ENTITY_TYPES, key="f_entities",
                                  help="Covered Entity Type as reported to HHS. Business "
                                       "associates are outside vendors such as billing or IT firms.")
    states = st.multiselect("State", ALL_STATES, key="f_states", placeholder="All states",
                            help="Leave empty to include every state and territory.")
    ba_choice = st.radio("Business associate involved?", ["All breaches", "Yes", "No"],
                         key="f_ba", horizontal=True)
    st.button("Reset filters", on_click=reset_filters, width="stretch")


def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    out = data[data["year"].between(years[0], years[1])]
    out = out[out["breach_type_group"].isin(breach_types)]
    out = out[out["entity_type"].isin(entity_types)]
    if states:
        out = out[out["state"].isin(states)]
    if ba_choice != "All breaches":
        out = out[out["ba_involved"] == ba_choice]
    return out


fdf = apply_filters(df)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🔒 HIPAA Breach Explorer")
st.markdown(
    "**What is putting patient data at risk?** This dashboard explores every breach of "
    "protected health information affecting **500 or more people** that was reported to the "
    "U.S. Department of Health and Human Services (HHS) since October 2009. It shows how "
    "breaches have changed over time, which systems are exposed, and which organizations "
    "and states are hit hardest."
)
st.markdown(
    "**Who it is for:** hospital and health-system **security and compliance officers**, "
    "healthcare IT managers, and cybersecurity students or analysts deciding where to focus "
    "limited defensive resources. Use the **filters in the sidebar** (tap **>** at the top "
    "left on a phone) to narrow the data."
)

if not breach_types or not entity_types:
    st.warning("Select at least one breach type and one organization type in the sidebar.")
    st.stop()
if fdf.empty:
    st.warning("No data for the selected filters. Try widening the year range or "
               "clearing the state filter, or press **Reset filters**.")
    st.stop()

yr_label = f"{years[0]}" if years[0] == years[1] else f"{years[0]}–{years[1]}"
partial_in_range = sorted(PARTIAL_YEARS & set(range(years[0], years[1] + 1)))

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
n_breaches = len(fdf)
total_people = fdf["individuals_affected"].sum()
median_size = fdf["individuals_affected"].median()
hack_share = (fdf["breach_type_group"] == "Hacking/IT Incident").mean() * 100
ba_people_share = (fdf.loc[fdf["ba_involved"] == "Yes", "individuals_affected"].sum()
                   / total_people * 100) if total_people else 0

st.subheader(f"At a glance · {yr_label}")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Breaches reported", f"{n_breaches:,}",
          help="Number of breach reports matching the filters.")
k2.metric("Individuals affected", fmt_people(total_people),
          help="Sum of individuals affected. A person is counted once per breach, so this "
               "measures exposure events, not unique people.")
k3.metric("Median breach size", f"{median_size:,.0f}" if pd.notna(median_size) else "n/a",
          help="Half of the selected breaches affected fewer people than this. The median is "
               "used because a few mega-breaches make the average misleading.")
k4.metric("Caused by hacking/IT", f"{hack_share:.0f}%",
          help="Share of selected breaches classified as Hacking/IT Incident.")
k5.metric("People affected via a vendor", f"{ba_people_share:.0f}%",
          help="Share of individuals affected in breaches where a business associate "
               "(outside vendor) was involved.")

if partial_in_range:
    st.caption(f"Note: {' and '.join(map(str, partial_in_range))} "
               f"{'is a partial year' if len(partial_in_range) == 1 else 'are partial years'} "
               "in the HHS list, so those years look smaller than a full year would.")

st.divider()

# ---------------------------------------------------------------------------
# Chart 1 - Trends (Q1)
# ---------------------------------------------------------------------------
st.header("1. Is hacking driving the growth in breaches?")
c1_mode = st.radio("Show", ["Number of breaches", "Share of breaches (%)"],
                   horizontal=True, key="c1_mode", label_visibility="collapsed")

by_year = (fdf.groupby(["year", "breach_type_group"], observed=False)
              .size().unstack(fill_value=0)
              .reindex(range(years[0], years[1] + 1), fill_value=0))
present_types = [g for g in GROUP_ORDER if g in breach_types and by_year[g].sum() > 0]

fig1 = go.Figure()
for g in present_types:
    fig1.add_bar(x=by_year.index, y=by_year[g], name=g, marker_color=GROUP_COLORS[g],
                 marker_line=dict(color="white", width=1),
                 hovertemplate="%{y:,}" + ("%" if c1_mode.startswith("Share") else "")
                               + f"<extra>{g}</extra>")
fig1.update_layout(barmode="stack", legend_traceorder="normal", hovermode="x unified",
                   barnorm="percent" if c1_mode.startswith("Share") else None)
if c1_mode.startswith("Share"):
    fig1.update_traces(hovertemplate="%{y:.0f}%<extra>%{fullData.name}</extra>")
fig1.update_xaxes(title_text="Year reported to HHS", dtick=1 if years[1] - years[0] <= 17 else 2)
fig1.update_yaxes(tickformat=",", title_text="Share of breaches (%)" if c1_mode.startswith("Share")
                  else "Number of breaches")
st.plotly_chart(style_fig(fig1, 440), width="stretch", theme=None, config={"displayModeBar": False})

# Dynamic finding for the current selection
full_years = [y for y in by_year.index if y not in PARTIAL_YEARS and by_year.loc[y].sum() > 0]
if len(full_years) >= 2:
    y0, y1 = full_years[0], full_years[-1]
    n0, n1 = int(by_year.loc[y0].sum()), int(by_year.loc[y1].sum())
    h0 = by_year.loc[y0].get("Hacking/IT Incident", 0) / n0 * 100 if n0 else 0
    h1 = by_year.loc[y1].get("Hacking/IT Incident", 0) / n1 * 100 if n1 else 0
    change = f"{n1 / n0:.1f}×" if n0 else "n/a"
    st.info(f"**In your selection:** reported breaches went from **{n0:,} in {y0}** to "
            f"**{n1:,} in {y1}** ({change}), and hacking's share moved from "
            f"**{h0:.0f}%** to **{h1:.0f}%**.")
st.markdown(
    "**What it shows.** Across all data, reported breaches rose about **4×** from 2010 (199) to "
    "2025 (807), and **hacking accounts for all of that growth**: hacking/IT incidents went from "
    "about 4% of breaches in 2010 to about 81% in 2025, while theft collapsed (135 reports in "
    "2010, 9 in 2025), likely thanks to encrypted laptops and devices. "
    "**Why it matters:** the threat has shifted from lost or stolen equipment to network "
    "attacks, so defenses such as monitoring, patching and phishing training now cover most "
    "of the risk."
)

st.divider()

# ---------------------------------------------------------------------------
# Chart 2 - Exposure by location (Q2)
# ---------------------------------------------------------------------------
st.header("2. Where is the breached data stored?")
metric = st.radio("Measure", ["Number of breaches", "Total individuals affected",
                              "Median individuals per breach"],
                  horizontal=True, key="c2_metric",
                  help="Frequent is not the same as large: switch measures to compare.")

rows = []
for col, name in LOCATIONS.items():
    sub = fdf.loc[fdf[col] == 1, "individuals_affected"]
    rows.append({"location": name, "n": len(sub),
                 "Number of breaches": len(sub),
                 "Total individuals affected": sub.sum(),
                 "Median individuals per breach": sub.median() if len(sub) else 0})
loc = pd.DataFrame(rows).sort_values(metric, ascending=True)
is_median = metric.startswith("Median")
low_n = (loc["n"] < MIN_N) & is_median

if metric == "Number of breaches":
    labels = [f"{v:,}" for v in loc[metric]]
else:
    labels = [f"{fmt_people(v)}  (n={n:,})" for v, n in zip(loc[metric], loc["n"])]

fig2 = go.Figure(go.Bar(
    x=loc[metric], y=loc["location"], orientation="h",
    marker_color=[GRAY if s else BLUE for s in low_n],
    text=labels, textposition="outside", cliponaxis=False,
    textfont=dict(color=INK, size=12),
    customdata=loc[["n"]],
    hovertemplate="<b>%{y}</b><br>" + metric + ": %{x:,.0f}<br>Breaches: %{customdata[0]:,}"
                  "<extra></extra>",
))
fig2.update_xaxes(title_text=metric, exponentformat="B", separatethousands=True, range=[0, max(loc[metric].max(), 1) * 1.3])
fig2.update_yaxes(title_text="")
st.plotly_chart(style_fig(fig2, 400), width="stretch", theme=None, config={"displayModeBar": False})
st.caption("A breach can list several locations, so it is counted once in each location it "
           "lists and the bars can add up to more than the total."
           + (f" Grey bars are based on fewer than {MIN_N} breaches, too few to trust the "
              "median." if low_n.any() else ""))

top_count = loc.sort_values("Number of breaches").iloc[-1]
reliable = loc[loc["n"] >= MIN_N]
if not reliable.empty and top_count["n"] > 0:
    top_med = reliable.sort_values("Median individuals per breach").iloc[-1]
    share_people = (top_count["Total individuals affected"] / total_people * 100
                    if total_people else 0)
    st.info(f"**In your selection:** **{top_count['location']}** is involved in the most "
            f"breaches ({int(top_count['n']):,}, {share_people:.0f}% of people affected), and "
            f"**{top_med['location']}** has the largest typical breach "
            f"(median {top_med['Median individuals per breach']:,.0f} people).")
st.markdown(
    "**What it shows (all years).** Network servers are both the **most frequent** location (46% of all "
    "breaches) and the **most damaging** (median about 10,000 people, about 91% of everyone "
    "affected). Email is second by count but its breaches are small; paper is 13% of breaches "
    "but well under 1% of people affected. **Why it matters:** email and paper incidents call "
    "for training and process, while protecting the network servers that hold bulk records "
    "(segmentation, backups, monitoring) protects the most people."
)

st.divider()

# ---------------------------------------------------------------------------
# Chart 3 - Who is hit (Q3)
# ---------------------------------------------------------------------------
st.header("3. Which states and organizations are hit hardest?")
tab_states, tab_entities = st.tabs(["Top states", "Organization types"])

with tab_states:
    sc1, sc2 = st.columns([2, 1])
    state_measure = sc1.radio("Rank states by", ["Number of breaches", "Individuals affected"],
                              horizontal=True, key="c3_measure")
    top_n = sc2.slider("Number of states", 5, 25, 10, key="c3_topn")

    st_agg = (fdf.groupby("state")
                 .agg(breaches=("breach_id", "size"), people=("individuals_affected", "sum"))
                 .reset_index())
    sort_col = "breaches" if state_measure == "Number of breaches" else "people"
    top_states = st_agg.sort_values(sort_col, ascending=False).head(top_n)
    plot_states = top_states.iloc[::-1]

    st_labels = ([f"{v:,}" for v in plot_states["breaches"]] if sort_col == "breaches"
                 else [fmt_people(v) for v in plot_states["people"]])
    fig3 = go.Figure(go.Bar(
        x=plot_states[sort_col], y=plot_states["state"], orientation="h",
        marker_color=BLUE, text=st_labels, textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=12),
        customdata=plot_states[["breaches", "people"]],
        hovertemplate="<b>%{y}</b><br>Breaches: %{customdata[0]:,}<br>"
                      "Individuals affected: %{customdata[1]:,.0f}<extra></extra>",
    ))
    fig3.update_xaxes(title_text=state_measure, exponentformat="B", separatethousands=True,
                      range=[0, max(plot_states[sort_col].max(), 1) * 1.18])
    fig3.update_yaxes(title_text="", type="category")
    st.plotly_chart(style_fig(fig3, max(320, 28 * len(plot_states) + 80)),
                    width="stretch", theme=None, config={"displayModeBar": False})

    lead = st_agg.sort_values(sort_col, ascending=False).iloc[0]
    msg = (f"**In your selection:** **{lead['state']}** leads "
           f"({lead['breaches']:,} breaches, {fmt_people(lead['people'])} people)")
    if len(st_agg) > 5:
        top5_share = st_agg.nlargest(5, "breaches")["breaches"].sum() / n_breaches * 100
        msg += (f", and the top 5 states account for **{top5_share:.0f}%** of breaches "
                f"across {len(st_agg)} states/territories")
    st.info(msg + ".")
    st.markdown(
        "**What it shows.** By count, the most populous states lead (California, Texas, New "
        "York, Florida, Illinois). By people affected the ranking changes: Minnesota and Indiana "
        "jump to the top because of single mega-breaches (Change Healthcare, 192.7M; Anthem, "
        "78.8M). **Caution:** counts are not adjusted for population or number of providers, so "
        "a high rank mostly reflects having more organizations, not weaker security."
    )

with tab_entities:
    ent = (fdf.groupby("entity_type")
              .agg(breaches=("breach_id", "size"), people=("individuals_affected", "sum")))
    ent["Share of breaches"] = ent["breaches"] / ent["breaches"].sum() * 100
    ent["Share of individuals affected"] = (ent["people"] / ent["people"].sum() * 100
                                            if ent["people"].sum() else 0)
    ent = ent.sort_values("Share of breaches", ascending=True)

    fig4 = go.Figure()
    for col, color in [("Share of individuals affected", ORANGE), ("Share of breaches", BLUE)]:
        fig4.add_bar(x=ent[col], y=ent.index, orientation="h", name=col, marker_color=color,
                     text=[f"{v:.0f}%" for v in ent[col]], textposition="outside",
                     cliponaxis=False, textfont=dict(color=INK, size=12),
                     hovertemplate="<b>%{y}</b><br>" + col + ": %{x:.1f}%<extra></extra>")
    fig4.update_layout(barmode="group", bargroupgap=0.08, legend_traceorder="reversed")
    fig4.update_xaxes(title_text="Percent of selected breaches / people (%)", range=[0, 115])
    fig4.update_yaxes(title_text="")
    st.plotly_chart(style_fig(fig4, 380), width="stretch", theme=None, config={"displayModeBar": False})

    gap = (ent["Share of individuals affected"] - ent["Share of breaches"])
    if len(ent) > 1 and ent["people"].sum() > 0:
        over = gap.idxmax()
        st.info(f"**In your selection:** **{over}** organizations report "
                f"{ent.loc[over, 'Share of breaches']:.0f}% of breaches but "
                f"{ent.loc[over, 'Share of individuals affected']:.0f}% of the people affected.")
    st.markdown(
        "**What it shows.** Healthcare providers report about **72%** of breaches but only about "
        "**32%** of the people affected. Business associates (outside vendors) report just "
        "**15%** of breaches yet about **49%** of people affected, and none of the ten largest "
        "breaches was reported by a provider. **Why it matters:** vendors are not breached more "
        "often, but when they are, the breach can be enormous, so **vendor oversight** deserves "
        "real attention."
    )

st.divider()

# ---------------------------------------------------------------------------
# Data table and limitations
# ---------------------------------------------------------------------------
with st.expander(f"View the {n_breaches:,} breaches behind these charts"):
    show_cols = ["submission_date", "entity_name", "state", "entity_type", "breach_type_group",
                 "individuals_affected", "ba_involved", "report_list"]
    table = (fdf[show_cols].sort_values("individuals_affected", ascending=False)
             .rename(columns={"submission_date": "Date reported", "entity_name": "Organization",
                              "state": "State", "entity_type": "Organization type",
                              "breach_type_group": "Breach type",
                              "individuals_affected": "Individuals affected",
                              "ba_involved": "Business associate", "report_list": "HHS list"}))
    st.dataframe(table, width="stretch", hide_index=True,
                 column_config={"Date reported": st.column_config.DateColumn(format="YYYY-MM-DD"),
                                "Individuals affected": st.column_config.NumberColumn(format="%d")})
    st.download_button("Download filtered data (CSV)", table.to_csv(index=False).encode("utf-8"),
                       file_name="hipaa_breaches_filtered.csv", mime="text/csv")

st.markdown("#### About the data and its limitations")
st.markdown(
    "- **Source:** U.S. Department of Health and Human Services, Office for Civil Rights, "
    "[Breach Portal: Breaches Affecting 500 or More Individuals]"
    "(https://ocrportal.hhs.gov/ocr/breach/breach_report_hip.jsf), Archive and Under "
    "Investigation lists, downloaded 30 Oct 2026 (public U.S. government data).\n"
    "- Only breaches affecting **500 or more people** are listed; smaller breaches are not.\n"
    "- The **same person can be counted in several breaches**, so totals measure exposure "
    "events, not unique people (the all-time total exceeds the U.S. population).\n"
    "- Dates are when a breach was **reported to HHS**, not when it happened. **2009 and 2026 "
    "are partial years**, and recent cases are still under investigation and may change.\n"
    "- Breaches listing several types are grouped under the most serious one "
    "(Hacking > Unauthorized Access > Theft > Loss > Improper Disposal > Other).\n"
    "- State counts are **not adjusted for population**. Results show associations in "
    "reported data, not causes."
)
st.caption("HIPAA Breach Explorer · Luca Accomando · CIS 3400 Deliverable 3")
