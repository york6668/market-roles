"""A one-time, evidence-audited codec for the four immutable revision-2 files.

This is not a market inference engine and accepts no current decision bundle.
Every call rechecks the historical bytes before recovering comparison semantics.
The audit envelope is internal and never part of a report or its fingerprint.
"""
from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

import decision_report


FIXTURE_DIRECTORY = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
ARTIFACTS = {
    "state": ("revision2_state_1346.md", "sha256:9e5a8acb5813e0243022c56333560a968d2b1ad0096be524a811866097aeb8fb"),
    "plan": ("revision2_plan_1346.md", "sha256:2e286e7cdde6c0b780d077a84b2b64af5e38c00b2238b9fef7465b0136415601"),
    "report": ("revision2_report_1346.md", "sha256:b308fe9c1363364df32265b5aa4695e81d5c20d18a609600c5bf2f311716a3f4"),
    "report_projection": ("revision2_report_1346_semantics.json", "sha256:e2434d36fa3c3fad7d71ad386f3776ca51b31aaaee20ee33e000a9d9a09800a5"),
}
CODEC = "BTC_REVISION2_1346_REPORT_COMPARISON_V1"
UNRESOLVED_DIMENSIONS = (
    "cross_exchange_acceptance", "spot_flow", "derivatives_flow", "oi_timeline",
    "funding_basis", "capital_source", "macro", "relative_strength",
)
# This mask is fixed by the historical audit, never by the current report.
# Changes to it require reviewing this one-time codec's source witnesses.
HISTORICAL_UNKNOWN_PATHS = tuple(sorted(
    [f"portfolio_action_by_module.{module}.portfolio_role" for module in (
        "existing_digital_beta", "existing_alpha_short", "new_short", "optionality",
    )]
    + [f"portfolio_action_by_module.{module}.{field}" for module in decision_report.MODULES
       for field in ("zero_amount_reason_class", "invalidation_conditions")]
))
CODEC_COMPARISON_LIMITATIONS = (
    "旧反证与缺失证据使用聚合codec，不能机械判定任意新语义键与其同义。",
    "旧下一鉴别条件使用跨所现货和持仓量时序codec；仅改成另一命名也会报告差异，须由主任务审阅而非自动忽略。",
    "比较只覆盖旧已知语义；历史缺失字段的补齐不是已证实相同，也不得用其当前值反填历史指纹。",
)


class BridgeError(ValueError):
    """The historical evidence no longer matches this one-time codec."""


def _read_checked() -> dict[str, str]:
    texts = {}
    for artifact, (filename, expected) in ARTIFACTS.items():
        raw = (FIXTURE_DIRECTORY / filename).read_bytes()
        actual = "sha256:" + hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise BridgeError("immutable revision2 artifact changed: " + artifact)
        texts[artifact] = raw.decode("utf-8")
    return texts


def _source(texts: dict[str, str], artifact: str, quote: str) -> dict[str, Any]:
    text = texts[artifact]
    start = text.find(quote)
    if start < 0:
        raise BridgeError("audit quote is absent from immutable " + artifact)
    return {
        "artifact": ARTIFACTS[artifact][0],
        "line_start": text[:start].count("\n") + 1,
        "line_end": text[:start + len(quote)].count("\n") + 1,
        "quote": quote,
    }


def _witness(texts: dict[str, str], sources: list[tuple[str, str]], interpretation: str, *, inference_kind: str = "HISTORICAL_SEMANTIC_CODEC") -> dict[str, Any]:
    return {
        "sources": [_source(texts, artifact, quote) for artifact, quote in sources],
        "inference_kind": inference_kind,
        "interpretation": interpretation,
    }


def bridge_artifact() -> dict[str, Any]:
    """Return pure eight-dimensional semantics plus byte-bound audit witnesses.

    Zero is *suggested incremental adjustment*, never actual position, cash,
    available budget or account delta. The old public comparison projection
    selects V0, although the old prose also contained other conditional levels.
    Missing purpose/conditions stay explicit legacy unknowns, not fabricated
    agreements with a new bundle. A caller must review a real change in such
    information rather than silently declaring it equivalent.
    """
    texts = _read_checked()
    legacy = json.loads(texts["report_projection"])["report_semantics"]
    modules = decision_report.MODULES
    if legacy["portfolio_action_by_module"] != {module: "MAINTAIN" for module in modules}:
        raise BridgeError("legacy maintain interpretation is not supported")
    # These are historical codec keys, not declarations of newly verified data.
    roles = {
        "existing_digital_beta": "LEGACY_MODULE_ROLE_NOT_STATED",
        "existing_alpha_short": "LEGACY_MODULE_ROLE_NOT_STATED",
        "new_spot": "INCREMENTAL_SPOT",
        "new_short": "LEGACY_SHORT_PURPOSE_NOT_STATED",
        "optionality": "LEGACY_OPTIONALITY_ROLE_NOT_STATED",
    }
    actions = {
        module: {
            "decision": "MAINTAIN", "amount_u": "0", "portfolio_role": roles[module],
            "net_exposure_impact": "UNCHANGED", "capital_pool_impact": "NONE",
            "reason_class": "WAIT_FOR_DECISIONAL_EVIDENCE",
            "zero_amount_reason_class": "LEGACY_OPTIONALITY_COMPARISON_NOT_STATED",
            "formation_conditions": ["DECISION_EVIDENCE_CHANGES"],
            "invalidation_conditions": ["LEGACY_MODULE_INVALIDATION_NOT_STATED"],
        }
        for module in modules
    }
    rejected = [
        {"hypothesis_id": identity, "counter_evidence": ["NO_STRUCTURAL_CONFIRMATION"], "missing_evidence": ["SPOT_FLOW_AND_OI_SEQUENCE"]}
        for identity in ("H_SPOT", "H_LEVERAGE", "H_MACRO")
    ]
    semantics = {
        "overall_user_decision": {"path_decision": "MAINTAIN", "module_decisions": {module: "MAINTAIN" for module in modules}},
        "primary_causal_explanation": {
            "hypothesis_id": "H_UNRESOLVED", "driver_regime": "UNRESOLVED", "driver_components": [],
            "decision_evidence_status": "EVIDENCE_LIMITED", "mechanism": [],
        },
        "rejected_competing_explanations": rejected,
        "portfolio_action_by_module": actions,
        "material_uncertainties": [{"dimension": dimension, "status": "UNRESOLVED"} for dimension in UNRESOLVED_DIMENSIONS],
        "next_decision_changing_evidence": {
            "hypothesis_id": "H_UNRESOLVED", "conditions": ["CROSS_VENUE_SPOT_AND_OI_TIMELINE"],
            "falsification_conditions": ["OPPOSING_DRIVER_SEQUENCE_VERIFIED"],
        },
        "user_visible_major_risk": {"active": False, "kinds": ["NONE"], "portfolio_effect": "NONE"},
        "decision_relevant_levels_and_sizes": [{
            "level_id": "V0", "kind": "VALUE_ZONE", "value_role": "PERSISTENT_VALUE_DISPUTE_ZONE",
            "lifecycle": "RETEST_PENDING", "price_band_u": {"lower_u": "77000", "upper_u": "77500"}, "amount_u": "0",
        }],
    }
    witness = {
        "overall_user_decision": _witness(texts, [
            ("state", "**path_decision**：MAINTAIN。下方接受未成立，收回后的结构留存也尚未成立"),
            ("report", "当前应继续等待结构留存，不把这次回升视为现货加仓、平空或新增空单的信号。"),
            ("report_projection", '"existing_digital_beta": "MAINTAIN",\n      "existing_alpha_short": "MAINTAIN",\n      "new_spot": "MAINTAIN",\n      "new_short": "MAINTAIN",\n      "optionality": "MAINTAIN"'),
        ], "保持既有路径与五模块的建议，不从旧CURRENT_DERIVATION或FACT_SYNC标法推导用户决定变化。"),
        "primary_causal_explanation": _witness(texts, [
            ("state", "没有独立的现货主动买卖、ETF或完整OI时序能把这次收回归因为原生买盘主导；贴水和资金费继续仅作杠杆成本覆盖层。"),
            ("state", "正资金费与轻微贴水没有获得结构解释权。"),
            ("report_projection", '"primary_causal_explanation": "CAUSE_UNRESOLVED_KEEP_LAST_VALID_ANCHOR"'),
        ], "旧driver名称含MIXED，但正文明确无结构解释权，因此仅恢复未解决主因及空typed机制，不虚构cause。"),
        "rejected_competing_explanations": _witness(texts, [
            ("report_projection", '{"hypothesis_id": "H_SPOT", "reason_class": "NO_ACCEPTANCE_SEQUENCE"},\n      {"hypothesis_id": "H_LEVERAGE", "reason_class": "NO_OI_SEQUENCE"},\n      {"hypothesis_id": "H_MACRO", "reason_class": "NO_MACRO_TIMELINE"}'),
            ("plan", "没有独立、跨窗口的原生现货主动买卖、宏观冲击或完整OI时序，不能把这次收回解释为结构性价值上移。"),
        ], "三个旧假设都未形成结构确认。SPOT_FLOW_AND_OI_SEQUENCE是本次旧证据链缺口的聚合codec，不表示已观察反向驱动，也不表示宏观解释仅需OI。逐假设原拒绝原因保留在见证中。"),
        "portfolio_action_by_module": _witness(texts, [
            ("report", "当前应继续等待结构留存，不把这次回升视为现货加仓、平空或新增空单的信号。"),
            ("plan", "当前价格不在P1，且没有“杠杆反弹而现货不能建立价值”的完整证据，**当前建议为0U**。"),
            ("plan", "当前尚未进入D0，且没有“V0下方流动性冲击后出现现货吸收”的完整条件，**当前建议为0U**。"),
            ("state", "实时权益、完整净Delta、现金、全部委托、累计资金费及强平距离未知；这不构成账户实时核验，也不阻断推导。"),
            ("report", "已确认的 Digital Beta 与 Alpha 空头事实没有变化；上述档位均未成交、仅供用户评估。"),
            ("state", "只有V0内留存/再次失守与独立现货、杠杆归因共同改变论点时再重定价。"),
        ], "五模块MAINTAIN及新增建议0来自旧决定；UNCHANGED/NONE只表示本轮建议不新增净敞口与资金占用，绝非账户Delta或现金。旧文件没有完整模块角色/失效/可选性优势论证，字段保留LEGACY_*_NOT_STATED。", inference_kind="DIRECT_PROPOSED_INCREMENT_NOT_ACCOUNT_FACT"),
        "material_uncertainties": _witness(texts, [
            ("state", "三家独立现货可用且价差有限，频道同步与SQLite健康。ETF、稳定币、ETH相对强弱及宏观缺少同口径即时独立验证，不拥有本轮路径迁移权。"),
            ("plan", "没有独立、跨窗口的原生现货主动买卖、宏观冲击或完整OI时序"),
            ("state", "账户输入只来自 `LOCAL_CONFIRMED_RECORDS`；`position_fact`未变化。"),
            ("state", "正资金费与轻微贴水没有获得结构解释权。"),
        ], "报价与本地记录作为历史输入可用；其余八个决策证据维度未达到新typed序列证明标准，统一为UNRESOLVED而非UNAVAILABLE或反证。funding点值可见不等于结构资金成本序列已验证；account可用不表示实时账户已查询。"),
        "next_decision_changing_evidence": _witness(texts, [
            ("report", "先观察欧洲现金开盘首小时是否在价值区内留存；随后以纽约现金开盘首小时作为本周期最后的结构复核窗口。"),
            ("state", "只有V0内留存/再次失守与独立现货、杠杆归因共同改变论点时再重定价。"),
            ("plan", "V0下方跨主要窗口持续接受、反弹不能收回，并由持续原生现货卖出而非单纯去杠杆解释"),
            ("plan", "合约主动买入/OI相对现货取得主导并伴随资金费或基差成本扩张"),
        ], "迁移codec表达跨所现货/持仓量时序鉴别及相反驱动证据可推翻当前等待论点；具体日期、窗口时刻和最终事件属于运行周期，不进入报告语义。"),
        "user_visible_major_risk": _witness(texts, [
            ("report_projection", '"user_visible_major_risk": "NONE"'),
            ("report", "完整净Delta、实时权益、可用现金、委托、累计资金费和强平距离仍未记录，因此不将建议金额表述为实时可执行额度。"),
        ], "只恢复旧报告未声明新增重大风险及相应无新增风险处理，不宣称账户安全已确认或未来无风险。"),
        "decision_relevant_levels_and_sizes": _witness(texts, [
            ("report_projection", '"level_id": "V0",\n        "price_band_u": {"lower_u": "77000", "upper_u": "77500"},\n        "amount_u": "0"'),
            ("state", "| V0_PERSISTENT_VALUE | 77,000–77,500U | RETEST_PENDING_REENTRY | 下层既有结构未删除；已重新进入，等待欧洲窗口确认留存或再次失守 |"),
            ("state", "| V1_CONFIRMED_VALUE | 78,300–80,000U | RETEST_PENDING_AFTER_EXIT | 保留待回测身份；未成熟、未确认、也未删除 |"),
            ("report", "| 78,300–80,000U | 等待回测的上层价值区 | 当前0U | 跨主要窗口接受并完成回测 | 上冲后不能留存，或驱动转为杠杆而非现货 |"),
        ], "比较集合沿用旧已批准JSON投影只含V0；V0角色和待回测映射由旧结构表支持。V1仍是状态锚，且旧报告正文确实包含V1及候选阶梯，不能将未纳入旧比较集合说成从未披露。"),
    }
    explicit_unknowns = [
        f"portfolio_action_by_module.{module}.{key}"
        for module, action in actions.items() for key, value in action.items()
        if (isinstance(value, str) and value.startswith("LEGACY_"))
        or (isinstance(value, list) and any(item.startswith("LEGACY_") for item in value))
    ]
    # Reuse the report's canonical serializer, but never a current bundle.
    wrappers = {field: {"semantic": semantics[field], "narrative": []} for field in decision_report.FIELDS}
    canonical = decision_report.semantic_projection(wrappers)
    return {
        "codec": CODEC, "semantic_projection": canonical, "audit_witness": witness,
        "artifact_fingerprints": {artifact: value[1] for artifact, value in ARTIFACTS.items()},
        "explicit_unknowns": sorted(explicit_unknowns),
    }


def bridge_semantics() -> dict[str, Any]:
    """Return only the eight canonical values; no metadata or audit in the hash."""
    return deepcopy(bridge_artifact()["semantic_projection"])


def _canonical_pure_semantics(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(decision_report.FIELDS):
        raise BridgeError("migration comparison requires exactly eight pure semantic fields")
    wrappers = {field: {"semantic": value[field], "narrative": []} for field in decision_report.FIELDS}
    try:
        canonical = decision_report.semantic_projection(wrappers)
        errors: list[str] = []
        # These checks inspect typed semantics, not the absent historical prose.
        decision_report._shape(canonical, errors)
        decision_report._semantic_atoms(canonical, errors)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise BridgeError("invalid migration comparison semantics: " + str(exc)) from exc
    if errors:
        raise BridgeError("invalid migration comparison semantics: " + "; ".join(errors))
    return canonical


def _without_historical_unknowns(value: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(value)
    for path in HISTORICAL_UNKNOWN_PATHS:
        parts = path.split(".")
        parent = result
        for part in parts[:-1]:
            parent = parent[part]
        # Delete on both sides; never copy the new value into the old side.
        del parent[parts[-1]]
    return result


def _known_differences(previous: Any, current: Any, path: str = "") -> list[dict[str, Any]]:
    if previous == current:
        return []
    if isinstance(previous, Mapping) and isinstance(current, Mapping):
        differences = []
        for key in sorted(set(previous) | set(current)):
            child_path = path + "." + key if path else key
            if key not in previous or key not in current:
                differences.append({"path": child_path, "previous": previous.get(key), "current": current.get(key)})
            else:
                differences.extend(_known_differences(previous[key], current[key], child_path))
        return differences
    # Lists are canonical unordered semantic sets; report their complete change
    # instead of suggesting that their sorted array indexes are stable identities.
    return [{"path": path, "previous": deepcopy(previous), "current": deepcopy(current)}]


def _comparison_fingerprint(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def migration_compare(current_pure_semantics: Mapping[str, Any]) -> dict[str, Any]:
    """Compare known historical decisions for this one migration only.

    Both returned fingerprints hash the same fixed *masked comparison view*.
    They are not the complete production report fingerprints and must not be
    persisted as such after migration. ``changed=False`` means no change in the
    recoverable old meaning, not proof of equivalence for its missing fields.

    Stable-key spelling changes in rejected/next evidence are deliberately not
    guessed to be synonyms. See CODEC_COMPARISON_LIMITATIONS and the raw witnesses
    in bridge_artifact(); differences in those fields require semantic review.
    """
    historical = bridge_artifact()  # reads/checks four immutable files first
    if tuple(historical["explicit_unknowns"]) != HISTORICAL_UNKNOWN_PATHS:
        raise BridgeError("historical unknown mask no longer matches the audited codec")
    previous = _canonical_pure_semantics(historical["semantic_projection"])
    current = _canonical_pure_semantics(current_pure_semantics)
    previous_masked = _without_historical_unknowns(previous)
    current_masked = _without_historical_unknowns(current)
    differences = _known_differences(previous_masked, current_masked)
    return {
        "changed": bool(differences),
        "known_differences": differences,
        "historical_unknown_paths": list(HISTORICAL_UNKNOWN_PATHS),
        "previous_report_fingerprint": _comparison_fingerprint(previous_masked),
        "current_report_fingerprint": _comparison_fingerprint(current_masked),
    }
