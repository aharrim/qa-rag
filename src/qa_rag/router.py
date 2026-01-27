import re

CLOSED_SYNONYMS   = ["closed", "resolved", "solved", "fixed", "done"]
OPEN_SYNONYMS     = ["open", "pending", "active"]
CRITICAL_SYNONYMS = ["critical", "p0", "blocker", "sev0"]
LIST_WORDS        = ["list", "show", "display"]
COUNT_WORDS       = ["how many", "count", "number", "total"]


def extract_metric(q: str) -> str | None:
    ql = (q or "").lower()
    if "median" in ql:
        return "median_days"
    if any(x in ql for x in ["average", "avg", "mean"]):
        return "avg_days"
    if "p75" in ql or "75th" in ql:
        return "p75_days"
    if "p90" in ql or "90th" in ql:
        return "p90_days"
    return None


def extract_component(q: str, known_components: list[str]) -> str | None:
    ql = (q or "").lower()

    norm = [(c, str(c).strip().lower()) for c in known_components if str(c).strip()]
    norm.sort(key=lambda x: len(x[1]), reverse=True)

    for original, lc in norm:
        if lc and lc in ql:
            return str(original).strip()
    return None


def filter_df_by_component(view_df, component: str | None):
    if not component:
        return view_df
    return view_df[view_df["component"].astype(str).str.strip().str.lower() == component.strip().lower()]


def known_components_from_df(df):
    return sorted(df["component"].dropna().astype(str).unique().tolist())


def has_any(ql: str, words: list[str]) -> bool:
    return any(w in ql for w in words)


# -----------------------------
# Analytics handlers
# -----------------------------
def show_resolution_metric(question: str, resolution_by_component, df):
    metric = extract_metric(question) or "median_days"
    component = extract_component(question, known_components_from_df(df))

    view = resolution_by_component[["component", metric]].copy()
    view = filter_df_by_component(view, component)

    if not component:
        view = view.sort_values(by=metric, ascending=False)

    print(f"\n--- Resolution metric: {metric}" + (f" | Component: {component}" if component else "") + " ---")
    if view.empty:
        print("No data found for that component/metric (maybe no closed bugs for it yet).")
    else:
        print(view.to_string(index=False))


def show_open_bugs_list(df, question: str):
    component = extract_component(question, known_components_from_df(df))
    view = df[df["is_open"]].copy()
    view = filter_df_by_component(view, component)

    cols = ["id", "title", "component", "severity", "created_date"]
    cols = [c for c in cols if c in view.columns]

    print("\n--- Open bugs (detailed)" + (f" | Component: {component}" if component else "") + " ---")
    if view.empty:
        print("No open bugs found." if not component else "No open bugs found for that component.")
    else:
        print(view[cols].sort_values(by="created_date", ascending=True).to_string(index=False))


def show_closed_bugs_list(df, question: str):
    component = extract_component(question, known_components_from_df(df))
    view = df[~df["is_open"]].copy()
    view = filter_df_by_component(view, component)

    cols = ["id", "title", "component", "severity", "created_date", "closed_date", "resolution_days"]
    cols = [c for c in cols if c in view.columns]

    print("\n--- Closed bugs (detailed)" + (f" | Component: {component}" if component else "") + " ---")
    if view.empty:
        print("No closed bugs found." if not component else "No closed bugs found for that component.")
    else:
        sort_col = "closed_date" if "closed_date" in view.columns else "created_date"
        print(view[cols].sort_values(by=sort_col, ascending=True).to_string(index=False))


def show_open_bugs_count(open_by_component, df, question: str):
    component = extract_component(question, known_components_from_df(df))
    view = open_by_component.copy()
    view = filter_df_by_component(view, component)

    print("\n--- Open bugs count" + (f" | Component: {component}" if component else "") + " ---")
    if component and view.empty:
        print(f"{component}  0")
    else:
        print(view.to_string(index=False))


def show_closed_bugs_count(df, question: str):
    component = extract_component(question, known_components_from_df(df))
    view = df[~df["is_open"]].copy()
    view = filter_df_by_component(view, component)

    n = int(view.shape[0])
    if component:
        print(f"\nClosed bugs for {component}: {n}")
    else:
        print(f"\nClosed bugs (total): {n}")


def show_open_critical(df, open_critical, open_critical_by_component, question: str):
    component = extract_component(question, known_components_from_df(df))

    view_crit = open_critical.copy()
    view_crit = filter_df_by_component(view_crit, component)

    cols = ["id", "title", "component", "severity", "created_date"]
    cols = [c for c in cols if c in view_crit.columns]

    print("\n--- Open P0 (critical) bugs (oldest first)" + (f" | Component: {component}" if component else "") + " ---")
    if view_crit.empty and component:
        print("No open P0 bugs found for that component.")
    else:
        if not view_crit.empty:
            print(view_crit[cols].sort_values(by="created_date", ascending=True).to_string(index=False))
        else:
            print("No open P0 bugs found.")

    print("\n--- Open P0 (critical) bugs by component" + (f" | Component: {component}" if component else "") + " ---")
    view_crit_comp = open_critical_by_component.copy()
    view_crit_comp = filter_df_by_component(view_crit_comp, component)

    if view_crit_comp.empty and component:
        print(f"{component}  0")
    else:
        print(view_crit_comp.to_string(index=False))


def analytics_dispatch(user_question: str, df, open_by_component, resolution_by_component, open_critical, open_critical_by_component):
    ql = user_question.lower()
    print("=== Analytics (computed by Python, not guessed) ===")

    wants_list  = has_any(ql, LIST_WORDS)
    wants_count = has_any(ql, COUNT_WORDS)

    mentions_open     = has_any(ql, OPEN_SYNONYMS) or "open bugs" in ql
    mentions_closed   = has_any(ql, CLOSED_SYNONYMS) or "closed bugs" in ql
    mentions_critical = has_any(ql, CRITICAL_SYNONYMS)

    if has_any(ql, ["median", "average", "avg", "mean", "p75", "p90", "percentile", "resolution", "time to close", "sla"]):
        show_resolution_metric(user_question, resolution_by_component, df)
        return

    if mentions_open and (("not only" in ql) or ("not just" in ql)):
        if wants_list or ("all open" in ql):
            show_open_bugs_list(df, user_question)
        else:
            show_open_bugs_count(open_by_component, df, user_question)
        return

    if mentions_critical:
        show_open_critical(df, open_critical, open_critical_by_component, user_question)
        return

    if mentions_closed:
        if wants_list:
            show_closed_bugs_list(df, user_question)
        else:
            show_closed_bugs_count(df, user_question)
        return

    if mentions_open:
        if wants_list:
            show_open_bugs_list(df, user_question)
        else:
            show_open_bugs_count(open_by_component, df, user_question)
        return

    show_open_bugs_count(open_by_component, df, user_question)


# -----------------------------
# Routing (Hybrid)
# -----------------------------
def rule_route(q: str) -> str | None:
    ql = (q or "").strip().lower()

    analytics_patterns = [
        r"\bmedian\b", r"\baverage\b", r"\bavg\b", r"\bmean\b",
        r"\bp\d{2}\b",
        r"\bpercentile\b",
        r"\bhow many\b", r"\bcount\b", r"\bnumber of\b", r"\btotal\b",
        r"\bby component\b", r"\bbreakdown\b",
        r"\bresolution time\b", r"\btime to close\b", r"\bsla\b",
        r"\btrend\b", r"\bover (last|past)\b", r"\bper week\b", r"\bper month\b",
        r"\bopen\b", r"\bclosed\b", r"\bresolved\b", r"\bfixed\b", r"\bsolved\b",
    ]
    if any(re.search(p, ql) for p in analytics_patterns):
        return "ANALYTICS"

    rag_patterns = [
        r"\bis there (a|any) (known )?bug\b",
        r"\bknown issue\b",
        r"\bsimilar bug\b",
        r"\brelated to\b",
        r"\bwhy does\b",
        r"\bwhat causes\b",
        r"\bwhich bug\b",
    ]
    if any(re.search(p, ql) for p in rag_patterns):
        return "RAG"

    return None
