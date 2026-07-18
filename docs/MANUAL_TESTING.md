# Manual Test Protocol — UI & R-dependent paths

Run before every demo / submission. Requires API + Streamlit + Ollama running.

## UI walkthrough (FR-24)
- [ ] Upload page: select `data/raw/pbmc3k/pbmc3k_raw.h5ad`, tissue=PBMC, click Run → job starts
- [ ] Monitor page: progress bar advances; stage tracker moves Load→…→Report; balloons on done
- [ ] Results page: shows cluster count, reliability scorecard, annotation table with
      confidence colours, marker-evidence expander, composition table
- [ ] Review page: LOW-confidence clusters listed; Approve/Reject records a decision
- [ ] Report page: PDF, HTML, JSON each download and open correctly

## Error handling
- [ ] Upload `pbmc68k_reduced.h5ad` (pre-processed) → clean "not raw counts" message, NOT "process died"
- [ ] Upload a .txt file → rejected with format error

## R-dependent path
- [ ] After a run, `runs/<job_id>/run.log` contains "SingleR annotated N clusters"

Tester: __________  Date: __________  Result: PASS / FAIL