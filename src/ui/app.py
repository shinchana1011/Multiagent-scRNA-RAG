# src/ui/app.py — polished Streamlit dashboard (Member 4, Task 3 + Task 5)  FR-24/FR-17
from __future__ import annotations
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # make 'src' importable

import requests
import streamlit as st
from src.ui import api_client as api
from src.config.settings import settings

st.set_page_config(page_title=settings.app_name, page_icon="🧬", layout="wide")

# ---- styling (HCI: clear hierarchy, consistent confidence colour) ----
st.markdown("""
<style>
.main-header{background:linear-gradient(90deg,#2E6E6A,#1F3A5F);padding:18px 24px;
  border-radius:12px;color:white;margin-bottom:18px}
.main-header h1{margin:0;font-size:24px}
.main-header p{margin:4px 0 0;opacity:.85;font-size:14px}
.conf-HIGH{color:#2E6E6A;font-weight:600}
.conf-MED{color:#E8A33D;font-weight:600}
.conf-LOW{color:#C0504D;font-weight:600}
.ev-card{background:#f7faf9;border-left:3px solid #2E6E6A;padding:8px 12px;margin:6px 0;
  border-radius:4px;font-size:13px}
.ev-genes{color:#2E6E6A;font-family:monospace}
.ev-src{color:#888;font-size:12px}
.stTabs [data-baseweb="tab-list"]{gap:6px}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""<div class="main-header">
<h1>🧬 {settings.app_name}</h1>
<p>Evidence-based, verified, confidence-scored single-cell RNA-seq annotation</p></div>""",
            unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("job_id", None)
ss.setdefault("file_id", None)

# ---- sidebar: navigation + live job status ----
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["① Upload", "② Monitor", "③ Results", "④ Review", "⑤ Report"])

if ss.job_id:
    s = api.status(ss.job_id)
    badge = {"done": "✅ done", "running": "⏳ running", "queued": "🕒 queued",
             "failed": "❌ failed"}.get(s.get("status", ""), s.get("status", ""))
    st.sidebar.markdown(f"**Job:** `{ss.job_id}`")
    st.sidebar.markdown(f"**Status:** {badge}")
    st.sidebar.progress(s.get("progress", 0) / 100.0)
else:
    st.sidebar.info("No active job. Start on the Upload page.")

_CONF = lambda c: f'<span class="conf-{c}">{c}</span>'


def _guard_done() -> dict | None:
    """Ensure a job exists and finished; return status or None (with a UI message)."""
    if not ss.job_id:
        st.info("👈 Upload and run a file first."); return None
    s = api.status(ss.job_id)
    if s["status"] == "failed":
        st.error(f"Pipeline failed: {s.get('error') or s.get('message')}"); return None
    if s["status"] != "done":
        st.warning(f"Not ready — status **{s['status']}** ({s['progress']}%). See Monitor."); return None
    return s


def _fetch_report_json() -> dict:
    try:
        return requests.get(api.report_url(ss.job_id, "json"), timeout=30).json()
    except Exception:
        return {}


# ---------- ① Upload ----------
if page == "① Upload":
    st.subheader("Upload scRNA-seq data")
    col1, col2 = st.columns([2, 1])
    with col1:
        up = st.file_uploader("Data file", type=["h5", "h5ad", "loom"],
                              help="10x .h5, Scanpy .h5ad, or Seurat .loom")
    with col2:
        tissue = st.selectbox("Tissue context", ["PBMC", "lung", "tumor", "general"],
                              help="Drives RAG parameter retrieval")
        disease = st.text_input("Disease (optional)", "")
    if up:
        st.caption(f"Selected: **{up.name}** ({up.size/1e6:.1f} MB)")
    if st.button("🚀 Upload & Run pipeline", type="primary", disabled=up is None,
                 use_container_width=True):
        with st.spinner("Uploading…"):
            r = api.upload(up.getvalue(), up.name); ss.file_id = r["file_id"]
        with st.spinner("Starting multi-agent pipeline…"):
            j = api.run(ss.file_id, tissue, disease); ss.job_id = j["job_id"]
        st.success(f"Started job `{ss.job_id}` — switch to **Monitor** to watch progress.")

# ---------- ② Monitor ----------
elif page == "② Monitor":
    st.subheader("Pipeline progress")
    if not ss.job_id:
        st.info("👈 No job running. Start on Upload."); st.stop()
    s = api.status(ss.job_id)
    st.progress(s["progress"] / 100.0, text=f"**{s['status']}** — {s['message']}")
    stages = ["Load", "RAG params", "Verify", "Analysis", "Annotate", "Report"]
    done_n = int(s["progress"] / 100 * len(stages))
    st.write(" → ".join(f"**{x}**" if i < done_n else x for i, x in enumerate(stages)))
    if s["status"] == "failed":
        st.error(s.get("error") or "failed")
        with st.expander("Error detail"): st.code(s.get("error", ""))
    elif s["status"] == "done":
        st.success("✅ Complete — view Results."); st.balloons()
    else:
        time.sleep(3); st.rerun()

# ---------- ③ Results ----------
elif page == "③ Results":
    st.subheader("Annotated results")
    if _guard_done() is None: st.stop()
    d = api.results(ss.job_id)
    if "n_clusters" not in d:
        st.error(f"Could not load results: {d}"); st.stop()

    high = sum(a["confidence"] == "HIGH" for a in d["annotations"])
    med = sum(a["confidence"] == "MED" for a in d["annotations"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clusters", d["n_clusters"])
    c2.metric("HIGH confidence", high)
    c3.metric("MED confidence", med)
    c4.metric("Review queue", len(d["review_queue"]))

    rep = _fetch_report_json()

    # --- reliability scorecard (novelty headline) ---
    scard = rep.get("scorecard", {})
    if scard:
        st.markdown("#### Run reliability")
        s1, s2, s3 = st.columns(3)
        s1.metric("Reliability score", f"{scard['reliability_score']}/100", scard.get("grade"))
        s2.metric("Params verified", f"{scard['pct_claims_verified']}%")
        s3.metric("HIGH clusters", f"{scard['pct_high_confidence']}%")
        st.caption(rep.get("scorecard_summary", ""))

    # --- annotations with confidence colour ---
    st.markdown("#### Cluster annotations")
    for a in d["annotations"]:
        cols = st.columns([1, 3, 2, 3])
        cols[0].markdown(f"**{a['cluster_id']}**")
        cols[1].markdown(a["cell_type"] + (f" · *{a['cell_state']}*" if a.get("cell_state") else ""))
        cols[2].markdown(_CONF(a["confidence"]), unsafe_allow_html=True)
        cols[3].caption(", ".join(a["marker_genes"][:5]))

    # --- marker-gene evidence panel (HIGH clusters, FR-19 deepened) ---
    high_anns = [a for a in d["annotations"] if a["confidence"] == "HIGH"]
    if high_anns:
        with st.expander(f"🔬 Marker-gene evidence — {len(high_anns)} HIGH-confidence clusters"):
            for a in high_anns:
                src = "; ".join(f"{k}: {v}" for k, v in a.get("sources", {}).items())
                st.markdown(
                    f"<div class='ev-card'><b>Cluster {a['cluster_id']} — {a['cell_type']}</b><br>"
                    f"<span class='ev-genes'>{', '.join(a['marker_genes'][:8])}</span><br>"
                    f"<span class='ev-src'>Evidence: {src}</span></div>",
                    unsafe_allow_html=True)

    # --- composition profiling (novelty, non-diagnostic) ---
    comp = rep.get("composition", [])
    if comp:
        st.markdown("#### Cell-type composition vs healthy reference")
        st.caption("Deviation flagging only — no disease is diagnosed (NFR-05).")
        st.dataframe([{"Cell type": c["cell_type"], "Fraction": f"{c['fraction']:.1%}",
                       "Status": c["status"]} for c in comp], use_container_width=True)
        if rep.get("composition_summary"):
            st.info(rep["composition_summary"])

# ---------- ④ Review ----------
elif page == "④ Review":
    st.subheader("Human review queue (LOW-confidence)")
    st.caption("AI-flagged uncertain clusters for inspection. Expert biological "
               "validation is documented as future work.")
    if _guard_done() is None: st.stop()
    queue = api.review_queue(ss.job_id)
    if not isinstance(queue, list):
        st.error(f"Could not load queue: {queue}"); st.stop()
    if not queue:
        st.success("🎉 No LOW-confidence clusters — nothing needs review."); st.stop()

    for a in queue:
        with st.expander(f"⚠️ Cluster {a['cluster_id']} — {a['cell_type']} (LOW confidence)"):
            st.write("**Method votes:**", a.get("method_votes", {}))
            st.write("**Top markers:**", ", ".join(a.get("marker_genes", [])[:8]))
            override = st.text_input("Corrected label (optional)", key=f"ov_{a['cluster_id']}")
            c1, c2 = st.columns(2)
            if c1.button("✅ Approve", key=f"ap_{a['cluster_id']}", use_container_width=True):
                api.submit_review(ss.job_id, a["cluster_id"], True, override or None)
                st.success("Recorded.")
            if c2.button("❌ Reject", key=f"rj_{a['cluster_id']}", use_container_width=True):
                api.submit_review(ss.job_id, a["cluster_id"], False, override or None)
                st.warning("Recorded.")

# ---------- ⑤ Report ----------
elif page == "⑤ Report":
    st.subheader("Download report")
    if _guard_done() is None: st.stop()
    st.write("Full report package — reliability scorecard, annotated UMAP, Methods "
             "(with citations), marker-gene evidence, and composition analysis.")
    c1, c2, c3 = st.columns(3)
    c1.link_button("📄 PDF", api.report_url(ss.job_id, "pdf"), use_container_width=True)
    c2.link_button("🌐 HTML", api.report_url(ss.job_id, "html"), use_container_width=True)
    c3.link_button("{ } JSON", api.report_url(ss.job_id, "json"), use_container_width=True)