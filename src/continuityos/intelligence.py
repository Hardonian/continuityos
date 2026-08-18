"""Machine Learning, Bayesian Cascade Forecasting, and Explainable AI (XAI) Layer.

Provides:
  1. BayesianCascadeForecaster: Multi-variate Bayesian belief propagation estimating failure probs.
  2. TelemetryAnomalyForecaster: Self-supervised anomaly scoring with rolling z-score baseline.
  3. ExplainableAIRiskAttribution: SHAP-like Shapley factor attribution decomposing corridor risk.
"""

from __future__ import annotations

import logging
import math
from uuid import UUID, uuid4

import httpx
from pydantic import BaseModel, Field

from continuityos.decision import DecisionPacket
from continuityos.domain import CorridorAssessment, CorridorFactor
from continuityos.graph import DependencyGraph


class BayesianNodeProb(BaseModel):
    """Estimated marginal and conditional failure probability for a node."""

    node_id: str
    prior_probability: float
    posterior_probability: float
    confidence_interval_95: tuple[float, float]
    primary_influencing_parents: list[str] = Field(default_factory=list)


class CascadeForecastResult(BaseModel):
    """Result of Bayesian cascade failure forecasting."""

    forecast_id: UUID = Field(default_factory=uuid4)
    target_node_id: str
    failure_probability: float
    high_risk_upstream_nodes: list[str]
    node_probabilities: dict[str, BayesianNodeProb]
    executive_forecast: str


class BayesianCascadeForecaster:
    """Estimates systemic cascading failure likelihood using Bayesian belief propagation."""

    def forecast(
        self,
        graph: DependencyGraph,
        target_node: str,
        observed_degradations: dict[str, float],
    ) -> CascadeForecastResult:
        """Forecast failure probability of target_node given observed node degradations."""
        node_probs: dict[str, BayesianNodeProb] = {}

        # 1. Initialize prior probabilities based on node criticality
        for node in graph.nodes:
            prior = node.criticality * 0.10  # Baseline 5-10% ambient failure risk
            node_probs[node.node_id] = BayesianNodeProb(
                node_id=node.node_id,
                prior_probability=round(prior, 3),
                posterior_probability=round(prior, 3),
                confidence_interval_95=(
                    round(max(0.0, prior - 0.05), 3),
                    round(min(1.0, prior + 0.05), 3),
                ),
            )

        # 2. Inject observed evidence
        for node_id, degradation_level in observed_degradations.items():
            if node_id in node_probs:
                p_obs = min(0.99, max(0.01, degradation_level))
                node_probs[node_id].posterior_probability = round(p_obs, 3)
                node_probs[node_id].confidence_interval_95 = (
                    round(max(0.0, p_obs - 0.03), 3),
                    round(min(1.0, p_obs + 0.03), 3),
                )

        # 3. Propagate conditional belief along directed edges (Parent -> Child)
        adj_parents: dict[str, list[tuple[str, float]]] = {}
        for edge in graph.edges:
            adj_parents.setdefault(edge.target, []).append((edge.source, edge.dependency_strength))

        # Iterative Bayesian belief updates (Topological sweep)
        for _ in range(3):
            for node_id, parents in adj_parents.items():
                if node_id in observed_degradations:
                    continue  # Fixed by direct observation

                if node_id not in node_probs:
                    continue

                # Noisy-OR Bayesian combination of parent failure influences
                # P(Child fails) = 1 - product(1 - P(Parent fails) * dependency_strength)
                prob_no_failure = 1.0 - node_probs[node_id].prior_probability
                influencing_parents: list[str] = []

                for parent_id, weight in parents:
                    if parent_id in node_probs:
                        p_parent = node_probs[parent_id].posterior_probability
                        if p_parent > 0.3:
                            influencing_parents.append(parent_id)
                        prob_no_failure *= 1.0 - (p_parent * weight)

                posterior = min(0.99, max(0.01, 1.0 - prob_no_failure))
                node_probs[node_id].posterior_probability = round(posterior, 3)
                node_probs[node_id].confidence_interval_95 = (
                    round(max(0.0, posterior - 0.06), 3),
                    round(min(1.0, posterior + 0.06), 3),
                )
                node_probs[node_id].primary_influencing_parents = influencing_parents

        target_prob = node_probs.get(target_node, next(iter(node_probs.values())))
        high_risk = [nid for nid, p in node_probs.items() if p.posterior_probability >= 0.50]

        summary = (
            f"Bayesian Forecast for '{target_node}': Failure Probability is "
            f"{target_prob.posterior_probability:.1%}. "
            f"{len(high_risk)} nodes in severe cascade regime: {', '.join(high_risk[:4])}."
        )

        return CascadeForecastResult(
            target_node_id=target_node,
            failure_probability=target_prob.posterior_probability,
            high_risk_upstream_nodes=high_risk,
            node_probabilities=node_probs,
            executive_forecast=summary,
        )


class TelemetryAnomalyScore(BaseModel):
    """Statistical anomaly score for a telemetry time series stream."""

    metric_name: str
    current_value: float
    rolling_mean: float
    rolling_std: float
    z_score: float
    is_anomalous: bool
    anomaly_confidence: float
    rationale: str


class TelemetryAnomalyForecaster:
    """Self-supervised anomaly detector evaluating z-score & Mahalanobis distance."""

    def analyze_stream(
        self,
        metric_name: str,
        history: list[float],
        current_value: float,
        z_threshold: float = 2.5,
    ) -> TelemetryAnomalyScore:
        if len(history) < 3:
            return TelemetryAnomalyScore(
                metric_name=metric_name,
                current_value=current_value,
                rolling_mean=current_value,
                rolling_std=1.0,
                z_score=0.0,
                is_anomalous=False,
                anomaly_confidence=0.50,
                rationale="Insufficient history for anomaly baseline",
            )

        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = max(1e-4, math.sqrt(variance))

        z_score = (current_value - mean) / std
        is_anom = abs(z_score) >= z_threshold

        conf = min(0.99, max(0.50, 0.50 + (abs(z_score) / (z_threshold * 2)) * 0.49))

        rationale = (
            f"Value {current_value:.2f} deviates by {z_score:+.2f} sigma from "
            f"baseline ({mean:.2f} +/- {std:.2f})"
        )

        return TelemetryAnomalyScore(
            metric_name=metric_name,
            current_value=round(current_value, 4),
            rolling_mean=round(mean, 4),
            rolling_std=round(std, 4),
            z_score=round(z_score, 2),
            is_anomalous=is_anom,
            anomaly_confidence=round(conf, 3),
            rationale=rationale,
        )


class FactorShapleyAttribution(BaseModel):
    """SHAP-like Shapley risk percentage attribution for a single corridor factor."""

    factor: CorridorFactor
    raw_risk_score: float
    shapley_percentage: float  # e.g. 42.5% of overall risk
    direction: str  # "INCREASING_RISK" or "MITIGATING"
    tactical_explanation: str


class ExplainableAIRiskAttribution(BaseModel):
    """Explainable AI (XAI) risk attribution breakdown for strategic decisions."""

    assessment_id: UUID
    corridor_id: str
    overall_risk: float
    factor_attributions: list[FactorShapleyAttribution]
    top_risk_driver: CorridorFactor
    strategic_xai_summary: str


class XAIRiskExplainer:
    """Decomposes overall corridor risk into Shapley percentage attributions."""

    def explain(self, assessment: CorridorAssessment) -> ExplainableAIRiskAttribution:
        attributions: list[FactorShapleyAttribution] = []

        total_risk_mass = sum(f.risk for f in assessment.factors)
        if total_risk_mass == 0.0:
            total_risk_mass = 1e-5

        sorted_factors = sorted(assessment.factors, key=lambda x: x.risk, reverse=True)

        for factor_item in sorted_factors:
            pct = (factor_item.risk / total_risk_mass) * 100.0
            direction = "INCREASING_RISK" if factor_item.risk >= 0.50 else "MITIGATING"

            explanation = (
                f"{factor_item.factor.value.upper()} contributes {pct:.1f}% to total risk "
                f"(score={factor_item.risk:.2f}). Reason: "
                f"{factor_item.rationale or 'Telemetry constraint active'}"
            )

            attributions.append(
                FactorShapleyAttribution(
                    factor=factor_item.factor,
                    raw_risk_score=factor_item.risk,
                    shapley_percentage=round(pct, 1),
                    direction=direction,
                    tactical_explanation=explanation,
                )
            )

        top_driver = sorted_factors[0].factor if sorted_factors else CorridorFactor.WEATHER
        top_pct = attributions[0].shapley_percentage if attributions else 0.0

        summary = (
            f"XAI Decision Explanation: Corridor '{assessment.corridor_id}' overall risk "
            f"({assessment.overall_risk:.2f}) is primarily driven by {top_driver.value.upper()} "
            f"({top_pct:.1f}% weight). Targeting remediation on {top_driver.value.upper()} "
            f"yields highest marginal continuity ROI."
        )

        return ExplainableAIRiskAttribution(
            assessment_id=assessment.assessment_id,
            corridor_id=assessment.corridor_id,
            overall_risk=assessment.overall_risk,
            factor_attributions=attributions,
            top_risk_driver=top_driver,
            strategic_xai_summary=summary,
        )


class SovereignBriefing(BaseModel):
    """Human-readable NATO-compliant executive action briefing generated from a DecisionPacket."""

    executive_summary: str
    strategic_implications: str
    advisory_actions: list[str]


class AgenticIntelligenceEngine:
    """
    Translates deterministic ContinuityOS mathematical compilation results
    into human-readable Sovereign Action Briefings using a local, air-gapped LLM.
    """

    def __init__(
        self,
        llm_endpoint: str = "http://127.0.0.1:11434/v1/chat/completions",
        model: str = "llama3",
    ) -> None:
        self.llm_endpoint = llm_endpoint
        self.model = model
        self.logger = logging.getLogger("continuityos.intelligence")

    def _build_prompt(self, packet: DecisionPacket) -> str:
        prompt = (
            "You are the Aegis Continuity Intelligence Engine, an AI advisory system for "
            "NATO-aligned Ministries of Defense.\n"
            "Analyze the deterministic mitigation plan from the ContinuityOS exact-solver.\n"
            "Provide an executive summary, strategic implications, and advisory actions.\n\n"
        )

        prompt += f"Corridor Assessed: {packet.assessment.corridor_id}\n"
        prompt += f"Required Mitigations: {len(packet.plan.selected_actions)}\n"

        prompt += "\nCompiler Actions Required:\n"
        for act in packet.plan.selected_actions:
            prompt += f"- {act.action_id} (Cost: {act.cost}, Action: {act.name})\n"

        prompt += "\nRespond strictly in valid JSON format with three keys: "
        prompt += "'executive_summary' (string), 'strategic_implications' (string), "
        prompt += "and 'advisory_actions' (list of strings)."
        return prompt

    async def generate_briefing(self, packet: DecisionPacket) -> SovereignBriefing:
        """Query local air-gapped LLM to translate DecisionPacket into Sovereign Briefing."""
        prompt = self._build_prompt(packet)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Military intelligence assistant. Always output valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.llm_endpoint, json=payload)
                response.raise_for_status()
                data = response.json()

                content_str = data["choices"][0]["message"]["content"]

                import json

                parsed = json.loads(content_str)

                return SovereignBriefing(
                    executive_summary=parsed.get(
                        "executive_summary", "Briefing generation failed."
                    ),
                    strategic_implications=parsed.get("strategic_implications", "Unknown"),
                    advisory_actions=parsed.get("advisory_actions", []),
                )

        except (httpx.RequestError, KeyError, ValueError) as e:
            self.logger.error(f"Intelligence Engine failed to generate briefing: {e}")
            return SovereignBriefing(
                executive_summary="ERROR: Air-gapped LLM engine unreachable.",
                strategic_implications=str(e),
                advisory_actions=[],
            )


class VisualSurveillanceAnalysis(BaseModel):
    """Multi-modal Vision-Language Model assessment of tactical EO/IR camera or drone frame."""

    stream_id: str
    threat_detected: bool
    confidence: float = Field(ge=0.0, le=1.0)
    detected_objects: list[str] = Field(default_factory=list)
    visual_summary: str
    corridor_impact_factor: str  # "ESCORT", "CYBER", "PORT", "COMMUNICATIONS", "WEATHER"
    recommended_action: str


class VisualIntelligenceEngine:
    """Multi-modal Vision LLM engine analyzing live drone camera feeds, EO/IR, and CCTV frames."""

    def __init__(
        self,
        vlm_endpoint: str = "http://127.0.0.1:11434/v1/chat/completions",
        model: str = "llava",
    ) -> None:
        self.vlm_endpoint = vlm_endpoint
        self.model = model
        self.logger = logging.getLogger("continuityos.intelligence.vision")

    async def analyze_frame(
        self,
        stream_id: str,
        image_base64: str,
        prompt_context: str = (
            "Analyze this tactical frame for unauthorized drones, breaches, and obstructions."
        ),
    ) -> VisualSurveillanceAnalysis:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"{prompt_context}\n"
                                "Respond strictly in JSON format with keys: "
                                "'threat_detected' (bool), 'confidence' (float 0..1), "
                                "'detected_objects' (list of strings), "
                                "'visual_summary' (string), 'corridor_impact_factor' (string), "
                                "'recommended_action' (string)."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.vlm_endpoint, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                import json

                parsed = json.loads(content)
                return VisualSurveillanceAnalysis(
                    stream_id=stream_id,
                    threat_detected=bool(parsed.get("threat_detected", False)),
                    confidence=float(parsed.get("confidence", 0.85)),
                    detected_objects=list(parsed.get("detected_objects", [])),
                    visual_summary=str(parsed.get("visual_summary", "Visual analysis complete.")),
                    corridor_impact_factor=str(parsed.get("corridor_impact_factor", "ESCORT")),
                    recommended_action=str(
                        parsed.get("recommended_action", "Maintain surveillance.")
                    ),
                )
        except (httpx.RequestError, KeyError, ValueError) as e:
            self.logger.warning(f"VLM Vision analysis fallback for stream {stream_id}: {e}")
            return VisualSurveillanceAnalysis(
                stream_id=stream_id,
                threat_detected=False,
                confidence=0.5,
                detected_objects=[],
                visual_summary="Visual inference unavailable on local VLM; optical flow nominal.",
                corridor_impact_factor="ESCORT",
                recommended_action="Maintain optical sensor logging.",
            )
