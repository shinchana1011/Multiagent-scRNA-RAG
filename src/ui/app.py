# src/ui/app.py — Streamlit dashboard (Member 4, Task 3)
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # repo root -> makes 'src' importable

import time
import streamlit as st
from src.ui import api_client as api
from src.config.settings import settings

st.set_page_config(page_title=settings.app_name, layout="wide")
ss = st.session_state
ss.setdefault("job_id", None)
ss.setdefault("file_id", None)
ss.setdefault("page", "Upload")

st.sidebar.title("scRNA-RAG")
ss.page = st.sidebar.radio("Navigate", ["Upload", "Monitor", "Results", "Review", "Report"])

# ---------- Upload ----------
if ss.page == "Upload":
    st.header("1 · Upload scRNA-seq data")
    up = st.file_uploader("File (.h5 / .h5ad / .loom)", type=["h5", "h5ad", "loom"])
    tissue = st.selectbox("Tissue", ["PBMC", "lung", "tumor", "general"])
    disease = st.text_input("Disease context (optional)", "")
    if st.button("Upload & Run", type="primary", disabled=up is None):
        with st.spinner("Uploading…"):
            r = api.upload(up.getvalue(), up.name); ss.file_id = r["file_id"]
        with st.spinner("Starting pipeline…"):
            j = api.run(ss.file_id, tissue, disease); ss.job_id = j["job_id"]
        ss.page = "Monitor"; st.rerun()

# ---------- Monitor ----------
elif ss.page == "Monitor":
    st.header("2 · Pipeline progress")
    if not ss.job_id:
        st.info("Upload a file first."); st.stop()
    s = api.status(ss.job_id)
    st.progress(s["progress"] / 100.0, text=f"{s['status']} — {s['message']}")
    if s["status"] == "failed":
        st.error(s.get("error") or "failed")
    elif s["status"] == "done":
        st.success("Complete."); st.balloons()
    else:
        time.sleep(3); st.rerun()          # poll

# ---------- Results ----------
elif ss.page == "Results":
    st.header("3 · Annotated results")
    if not ss.job_id:
        st.info("Upload and run a file first."); st.stop()

    # confirm the job actually finished before asking for results
    s = api.status(ss.job_id)
    if s["status"] == "failed":
        st.error(f"Pipeline failed: {s.get('error') or s.get('message')}")
        st.stop()
    if s["status"] != "done":
        st.warning(f"Not ready yet — status: {s['status']} ({s['progress']}%). "
                   "Check the Monitor page.")
        st.stop()

    d = api.results(ss.job_id)
    if "n_clusters" not in d:                       # API returned an error dict
        st.error(f"Could not load results: {d}")
        st.stop()
    
    # reliability scorecard (novelty headline)
    try:
        rep = requests.get(api.report_url(ss.job_id, "json")).json()
        scard = rep.get("scorecard", {})
    except Exception:
        scard = {}
    if scard:
        st.markdown("#### Run reliability")
        s1, s2, s3 = st.columns(3)
        s1.metric("Reliability score", f"{scard['reliability_score']}/100", scard.get("grade"))
        s2.metric("Params verified", f"{scard['pct_claims_verified']}%")
        s3.metric("HIGH clusters", f"{scard['pct_high_confidence']}%")
        st.caption(rep.get("scorecard_summary", ""))

    c1, c2, c3 = st.columns(3)
    c1.metric("Clusters", d["n_clusters"])
    c2.metric("HIGH conf.", sum(a["confidence"] == "HIGH" for a in d["annotations"]))
    c3.metric("Review queue", len(d["review_queue"]))
    st.caption("Full annotated UMAP is in the downloadable report (Report page).")
    st.dataframe([{"Cluster": a["cluster_id"], "Cell type": a["cell_type"],
                   "Confidence": a["confidence"], "State": a.get("cell_state") or "-",
                   "Top markers": ", ".join(a["marker_genes"][:5])} for a in d["annotations"]],
                 use_container_width=True)
    # composition profiling
    import requests
    comp = requests.get(api.report_url(ss.job_id, "json")).json().get("composition", [])
    if comp:
        st.subheader("Cell-type composition vs healthy reference")
        st.caption("Deviation flagging only — no disease is diagnosed.")
        st.dataframe([{"Cell type": c["cell_type"], "Fraction": f"{c['fraction']:.1%}",
                       "Status": c["status"]} for c in comp], use_container_width=True)

# ---------- Review (Task 5 / FR-17) ----------
elif ss.page == "Review":
    st.header("4 · Human review queue (LOW-confidence)")
    st.caption("AI-flagged uncertain clusters. Approve or override. "
               "Expert biological validation is documented as future work.")
    if not ss.job_id:
        st.info("Upload and run a file first."); st.stop()

    # ensure the job finished before requesting the queue
    s = api.status(ss.job_id)
    if s["status"] == "failed":
        st.error(f"Pipeline failed: {s.get('error') or s.get('message')}"); st.stop()
    if s["status"] != "done":
        st.warning(f"Not ready yet — status: {s['status']} ({s['progress']}%). "
                   "Check the Monitor page."); st.stop()

    queue = api.review_queue(ss.job_id)
    if not isinstance(queue, list):                 # API returned an error dict, not a list
        st.error(f"Could not load review queue: {queue}"); st.stop()
    if len(queue) == 0:
        st.success("No LOW-confidence clusters — nothing to review."); st.stop()

    for a in queue:
        with st.expander(f"Cluster {a['cluster_id']} — {a['cell_type']} [LOW]"):
            st.write("Method votes:", a.get("method_votes", {}))
            st.write("Top markers:", ", ".join(a.get("marker_genes", [])[:8]))
            override = st.text_input("Override label (optional)", key=f"ov_{a['cluster_id']}")
            col1, col2 = st.columns(2)
            if col1.button("Approve", key=f"ap_{a['cluster_id']}"):
                api.submit_review(ss.job_id, a["cluster_id"], True, override or None)
                st.success("Recorded.")
            if col2.button("Reject", key=f"rj_{a['cluster_id']}"):
                api.submit_review(ss.job_id, a["cluster_id"], False, override or None)
                st.warning("Recorded.")

# ---------- Report ----------
elif ss.page == "Report":
    st.header("5 · Download report")
    if not ss.job_id:
        st.stop()
    st.markdown(f"- [PDF]({api.report_url(ss.job_id,'pdf')})")
    st.markdown(f"- [HTML]({api.report_url(ss.job_id,'html')})")
    st.markdown(f"- [JSON]({api.report_url(ss.job_id,'json')})")