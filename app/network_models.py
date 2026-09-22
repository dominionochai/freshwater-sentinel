from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SafetyState = Literal['SAFE', 'UNSAFE', 'FIELD SAMPLE REQUIRED']
SAFE = 'SAFE'


@dataclass(frozen=True)
class NetworkNode:
    node_id: str
    name: str
    latitude: float
    longitude: float
    source: str
    safety_state: str = 'FIELD SAMPLE REQUIRED'
    community: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NetworkEdge:
    upstream: str
    downstream: str
    distance_km: float
    relation: str = 'proximity'


@dataclass(frozen=True)
class WaterNetwork:
    network_id: str
    nodes: tuple[NetworkNode, ...]
    edges: tuple[NetworkEdge, ...]
    provenance: tuple[dict[str, Any], ...] = ()

    def to_dict(self):
        return {'network_id': self.network_id, 'nodes': [asdict(x) for x in self.nodes], 'edges': [asdict(x) for x in self.edges], 'provenance': list(self.provenance)}


@dataclass(frozen=True)
class PropagationEvent:
    node_id: str
    source_node_id: str | None
    hops: int
    risk_score: float
    state: str
    uncertainty_state: str
    rationale: str


@dataclass(frozen=True)
class AlternativeWaterPoint:
    node_id: str
    name: str
    distance_km: float | None
    safety_state: str
    rationale: str


@dataclass(frozen=True)
class NetworkAnalysis:
    network_id: str
    alert_node_ids: tuple[str, ...]
    propagation: tuple[PropagationEvent, ...]
    alternatives: tuple[AlternativeWaterPoint, ...]
    uncertainty_state: str
    dashboard: dict[str, Any]

    @property
    def decision(self) -> dict[str, Any]:
        """Return the deterministic act-here recommendation for this analysis."""
        ranked = sorted(
            self.propagation,
            key=lambda event: (-event.risk_score, event.hops, event.node_id),
        )
        if ranked:
            top = ranked[0]
            rationale = (
                f'Prioritize {top.node_id}: {top.rationale}. '
                f'It has the highest propagated risk score '
                f'({top.risk_score:.6f}) at {top.hops} hop(s).'
            )
            act_here = top.node_id
        else:
            nodes = sorted(
                self.dashboard.get('nodes', []),
                key=lambda node: str(node.get('node_id', '')),
            )
            act_here = str(nodes[0].get('node_id', '')) if nodes else ''
            rationale = (
                'No propagated risk event was identified; use the first '
                'deterministically ordered network node as the review point.'
            )
        return {
            'act_here': act_here,
            'rationale': rationale,
            'alternatives': [asdict(item) for item in self.alternatives],
        }

    def to_dict(self):
        return {
            'network_id': self.network_id,
            'alert_node_ids': list(self.alert_node_ids),
            'propagation': [asdict(x) for x in self.propagation],
            'alternatives': [asdict(x) for x in self.alternatives],
            'uncertainty_state': self.uncertainty_state,
            'dashboard': self.dashboard,
            'decision': self.decision,
        }


class NetworkBuildRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')

    records: list[dict[str, Any]] = Field(default_factory=list)
    max_distance_km: float = Field(10, gt=0, le=500)
    source: str = 'inline'


class NetworkAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')

    network_id: str | None = None
    records: list[dict[str, Any]] = Field(default_factory=list)
    alert_node_ids: list[str] = Field(default_factory=list)
    max_distance_km: float = Field(10, gt=0, le=500)
    max_hops: int = Field(3, ge=0, le=20)
    decay: float = Field(.75, gt=0, le=1)
    alternatives_limit: int = Field(5, ge=0, le=100)
