# scripts/visualize_graph.py — render the actual LangGraph agent DAG
from src.orchestrator.graph import build_graph
graph = build_graph()
# LangGraph can export its structure as Mermaid
try:
    png = graph.get_graph().draw_mermaid_png()
    with open("docs/agent_dag.png", "wb") as f:
        f.write(png)
    print("Wrote docs/agent_dag.png")
except Exception as e:
    # fallback: Mermaid text (paste into mermaid.live or a markdown file)
    print("PNG failed ({}); Mermaid source below:".format(e))
    print(graph.get_graph().draw_mermaid())