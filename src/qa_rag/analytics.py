# import pandas as pd

# def bugs_to_df(bugs):
#     df = pd.DataFrame(bugs).copy()

#     # Parse dates safely
#     df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
#     df["closed_date"]  = pd.to_datetime(df["closed_date"], errors="coerce")

#     # Derived fields
#     df["is_open"] = df["closed_date"].isna()
#     df["resolution_days"] = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 86400

#     return df


# def analytics_reports(df):
#     # 1) Open bugs by component
#     open_by_component = (
#         df[df["is_open"]]
#         .groupby("component")["id"]
#         .count()
#         .sort_values(ascending=False)
#         .rename("open_bugs")
#         .reset_index()
#     )

#     # 2) Resolution time by component (closed only)
#     closed = df[~df["is_open"]].dropna(subset=["resolution_days"])
#     resolution_by_component = (
#         closed.groupby("component")["resolution_days"]
#         .agg(
#             closed_bugs="count",
#             median_days="median",
#             avg_days="mean",
#             p75_days=lambda s: s.quantile(0.75),
#             p90_days=lambda s: s.quantile(0.90),
#         )
#         .sort_values(by="median_days", ascending=False)
#         .reset_index()
#     )

#     # 3) Critical bugs (open) - global + by component
#     # (handles severity safely even if some are missing)
#     sev = df["severity"].fillna("").astype(str).str.strip().str.lower()
#     open_critical = df[df["is_open"] & (sev == "p0")].copy()
#     open_critical = open_critical.sort_values(by="created_date", ascending=True)

#     open_critical_by_component = (
#         open_critical.groupby("component")["id"]
#         .count()
#         .sort_values(ascending=False)
#         .rename("open_critical_bugs")
#         .reset_index()
#     )

#     return open_by_component, resolution_by_component, open_critical, open_critical_by_component


import pandas as pd


# -------------------------
# Build DF from bugs
# -------------------------
def bugs_to_df(bugs):
    df = pd.DataFrame(bugs).copy()

    # Parse dates safely
    df["created_date"] = pd.to_datetime(df.get("created_date"), errors="coerce")
    df["closed_date"]  = pd.to_datetime(df.get("closed_date"), errors="coerce")

    # Derived fields
    df["is_open"] = df["closed_date"].isna()

    # resolution_days only makes sense for closed bugs
    df["resolution_days"] = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 86400

    return df


# -------------------------
# Normalization helpers
# -------------------------
def _norm_series(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.lower()


def apply_filters(
    df: pd.DataFrame,
    status: str | None = None,      # "open" | "closed" | None
    component: str | None = None,   # exact match, case-insensitive
    severity: str | None = None,    # exact match, case-insensitive (p0/p1/etc)
) -> pd.DataFrame:
    out = df.copy()

    # Status filter
    if status:
        st = status.strip().lower()
        if st == "open":
            out = out[out["is_open"]]
        elif st == "closed":
            out = out[~out["is_open"]]

    # Component filter (case-insensitive exact match)
    if component:
        comp = component.strip().lower()
        comp_norm = _norm_series(out["component"])
        out = out[comp_norm == comp]

    # Severity filter (case-insensitive exact match)
    if severity:
        sev = severity.strip().lower()
        sev_norm = _norm_series(out["severity"])
        out = out[sev_norm == sev]

    return out


# -------------------------
# Aggregations
# -------------------------
def bugs_count_by_component(df: pd.DataFrame, count_col_name: str = "bugs") -> pd.DataFrame:
    return (
        df.groupby("component", dropna=False)["id"]
        .count()
        .sort_values(ascending=False)
        .rename(count_col_name)
        .reset_index()
    )


def bugs_count_by_severity(df: pd.DataFrame, count_col_name: str = "bugs") -> pd.DataFrame:
    # keep severity normalized but show original value; simplest: use current column as-is
    return (
        df.groupby("severity", dropna=False)["id"]
        .count()
        .sort_values(ascending=False)
        .rename(count_col_name)
        .reset_index()
    )


def resolution_time_by_component(df: pd.DataFrame) -> pd.DataFrame:
    closed = df[~df["is_open"]].dropna(subset=["resolution_days"]).copy()
    if closed.empty:
        return pd.DataFrame(columns=["component", "closed_bugs", "median_days", "avg_days", "p75_days", "p90_days"])

    return (
        closed.groupby("component")["resolution_days"]
        .agg(
            closed_bugs="count",
            median_days="median",
            avg_days="mean",
            p75_days=lambda s: s.quantile(0.75),
            p90_days=lambda s: s.quantile(0.90),
        )
        .sort_values(by="median_days", ascending=False)
        .reset_index()
    )


def bugs_list_view(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["id", "title", "component", "severity", "created_date", "closed_date", "resolution_days", "is_open"]
    cols = [c for c in cols if c in df.columns]
    # prefer recent first
    if "created_date" in df.columns:
        return df.sort_values(by="created_date", ascending=False)[cols]
    return df[cols]


# -------------------------
# Backward-compatible "reports" (your original)
# -------------------------
def analytics_reports(df):
    # 1) Open bugs by component
    open_by_component = bugs_count_by_component(df[df["is_open"]], count_col_name="open_bugs")

    # 2) Resolution time by component (closed only)
    resolution_by_component = resolution_time_by_component(df)

    # 3) Critical bugs (open) - global + by component (P0)
    sev = _norm_series(df["severity"])
    open_critical = df[df["is_open"] & (sev == "p0")].copy()
    open_critical = open_critical.sort_values(by="created_date", ascending=True)

    open_critical_by_component = bugs_count_by_component(open_critical, count_col_name="open_critical_bugs")

    return open_by_component, resolution_by_component, open_critical, open_critical_by_component
