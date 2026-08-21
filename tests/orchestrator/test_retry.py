# tests/orchestrator/test_retry.py — FR-25 retry-mechanism recovery (Member 3)
from src.schemas.state import PipelineState
from src.orchestrator.graph import _AGENTS, _route


def test_fr25_route_retries_then_advances():
    """FR-25: a failing validate() routes back to the same node (retry) until
    max_retries, then advances. Tests the decision logic directly, without
    re-running destructive pipeline steps."""
    name = "verifier"
    agent = _AGENTS[name]
    original = agent.validate

    counter = {"n": 0}
    def flaky(s):                      # fail once, then pass
        counter["n"] += 1
        return counter["n"] > 1
    agent.validate = flaky
    try:
        state = PipelineState(input_path="x", tissue="PBMC")
        decide = _route(name)

        first = decide(state)          # fails -> should loop back to same node
        assert first == name
        assert state.retry_count.get(name) == 1

        second = decide(state)         # now passes -> should advance
        assert second != name
    finally:
        agent.validate = original


def test_fr25_gives_up_after_max_retries():
    """FR-25: after max_retries the pipeline continues (does not loop forever)."""
    name = "verifier"
    agent = _AGENTS[name]
    original = agent.validate
    agent.validate = lambda s: False   # always fail
    try:
        state = PipelineState(input_path="x", tissue="PBMC")
        state.max_retries = 2
        decide = _route(name)
        decide(state); decide(state)             # exhaust the 2 retries
        final = decide(state)                    # must advance, not loop
        assert final != name                     # gave up gracefully
    finally:
        agent.validate = original


def test_fr25_recovery_rate():
    """FR-25 acceptance: recovers from a transient failure in >=90% of agents."""
    recovered, agents = 0, ["parameter", "verifier", "analysis", "annotation"]
    for name in agents:
        agent = _AGENTS[name]
        original = agent.validate
        counter = {"n": 0}
        agent.validate = lambda s, c=counter: (c.__setitem__("n", c["n"] + 1) or c["n"] > 1)
        try:
            state = PipelineState(input_path="x", tissue="PBMC")
            r1 = _route(name)(state)             # fail -> retry
            r2 = _route(name)(state)             # pass -> advance
            if r1 == name and r2 != name:        # retried then recovered
                recovered += 1
        finally:
            agent.validate = original
    rate = recovered / len(agents)
    print(f"\nFR-25 recovery rate: {recovered}/{len(agents)} = {rate:.0%}")
    assert rate >= 0.90