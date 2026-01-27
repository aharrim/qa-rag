import pandas as pd

def bugs_to_df(bugs):
    df = pd.DataFrame(bugs).copy()

    # Parse dates safely
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    df["closed_date"]  = pd.to_datetime(df["closed_date"], errors="coerce")

    # Derived fields
    df["is_open"] = df["closed_date"].isna()
    df["resolution_days"] = (df["closed_date"] - df["created_date"]).dt.total_seconds() / 86400

    return df


def analytics_reports(df):
    # 1) Open bugs by component
    open_by_component = (
        df[df["is_open"]]
        .groupby("component")["id"]
        .count()
        .sort_values(ascending=False)
        .rename("open_bugs")
        .reset_index()
    )

    # 2) Resolution time by component (closed only)
    closed = df[~df["is_open"]].dropna(subset=["resolution_days"])
    resolution_by_component = (
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

    # 3) Critical bugs (open) - global + by component
    # (handles severity safely even if some are missing)
    sev = df["severity"].fillna("").astype(str).str.strip().str.lower()
    open_critical = df[df["is_open"] & (sev == "p0")].copy()
    open_critical = open_critical.sort_values(by="created_date", ascending=True)

    open_critical_by_component = (
        open_critical.groupby("component")["id"]
        .count()
        .sort_values(ascending=False)
        .rename("open_critical_bugs")
        .reset_index()
    )

    return open_by_component, resolution_by_component, open_critical, open_critical_by_component
