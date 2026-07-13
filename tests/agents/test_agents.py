# tests/agents/test_agents.py — per-agent unit tests (Member 3)
import numpy as np
import pytest
from anndata import AnnData
from src.schemas.state import PipelineState
from src.agents.base import BaseAgent
from src.agents.data_agent import DataAgent
from src.agents.parameter_agent import ParameterAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.annotation_agent import AnnotationAgent


def test_all_agents_inherit_base():
    for A in (DataAgent, ParameterAgent, AnalysisAgent, AnnotationAgent):
        assert issubclass(A, BaseAgent)
        assert hasattr(A, "run") and hasattr(A, "validate")


def test_agents_have_unique_ids():
    ids = [DataAgent().agent_id, ParameterAgent().agent_id,
           AnalysisAgent().agent_id, AnnotationAgent().agent_id]
    assert len(ids) == len(set(ids))          # no duplicate agent_ids


def test_data_agent_validate_rejects_empty():
    s = PipelineState(input_path="x")
    s.adata = None
    assert DataAgent().validate(s) is False   # no data -> invalid


def test_analysis_validate_requires_leiden():
    s = PipelineState(input_path="x")
    s.adata = AnnData(np.ones((10, 5), dtype="float32"))   # no leiden/umap
    assert AnalysisAgent().validate(s) is False


def test_data_agent_loads_real_file():
    """Integration-lite: DataAgent actually loads PBMC3k."""
    s = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad")
    s = DataAgent().run(s)
    assert DataAgent().validate(s) and s.adata.n_obs > 1000

# add to tests/agents/test_agents.py or a new test_cell_state.py
def test_fr18_states_only_on_high():
    from src.schemas.state import PipelineState
    from src.agents.data_agent import DataAgent
    from src.agents.analysis_agent import AnalysisAgent
    from src.agents.annotation_agent import AnnotationAgent
    s = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
    s = AnnotationAgent().run(AnalysisAgent().run(DataAgent().run(s)))
    # no LOW cluster may carry a cell_state (FR-18: HIGH-only)
    assert all(a.cell_state is None for a in s.annotations if a.confidence != "HIGH")

def test_fr19_annotations_carry_provenance():
    from src.schemas.state import PipelineState
    from src.agents.data_agent import DataAgent
    from src.agents.analysis_agent import AnalysisAgent
    from src.agents.annotation_agent import AnnotationAgent
    s = PipelineState(input_path="data/raw/pbmc3k/pbmc3k_raw.h5ad", tissue="PBMC")
    s = AnnotationAgent().run(AnalysisAgent().run(DataAgent().run(s)))
    a = s.annotations[0]
    assert a.confidence in ("HIGH", "MED", "LOW")
    assert len(a.marker_genes) > 0
    assert len(a.sources) > 0  