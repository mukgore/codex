"""Render a compact reproducibility report from preserved JSON run artifacts."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


MODEL_LABELS = {
    "local:2d": "C offline 2D",
    "local:3d": "C offline 3D-projection",
    "realtime:2d_A_current": "A current-only 2D",
    "realtime:2d_B_past_current": "B past+current 2D",
    "realtime:3d_A_current": "A current-only 3D-projection",
    "realtime:3d_B_past_current": "B past+current 3D-projection",
    "hamer:hamer": "HaMeR",
    "mediapipe:mediapipe": "MediaPipe Hands",
}
ORDER = list(MODEL_LABELS)


def number(value, digits=3):
    return "n/a" if value is None else f"{value:.{digits}f}"


def key_ordered(data, suffix):
    return [f"{name}:{suffix}" for name in ORDER if f"{name}:{suffix}" in data]


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(resolved)


def pair(report, left, right, metric):
    results = report["paired_video_comparisons"]["results"]
    direct = f"{left}__minus__{right}"
    reverse = f"{right}__minus__{left}"
    if direct in results and metric in results[direct]:
        return results[direct][metric]
    if reverse in results and metric in results[reverse]:
        row = results[reverse][metric]
        lo, hi = row["ci95_video_bootstrap"]
        return {**row, "left_minus_right_mean": -row["left_minus_right_mean"],
                "ci95_video_bootstrap": [-hi, -lo]}
    return None


def duration_summary(videos, key):
    bins = ("<0.1s", "0.1-0.5s", "0.5-1s", ">=1s")
    out = []
    for label in bins:
        rows = [v["results"][key]["by_occlusion_duration"].get(label, {}) for v in videos]
        usable = [r for r in rows if r.get("mean_position_error_palm_normalized") is not None]
        n = sum(r.get("hidden_joint_frames", 0) for r in usable)
        mean = (sum(r["mean_position_error_palm_normalized"] * r.get("hidden_joint_frames", 0)
                    for r in usable) / n) if n else None
        out.append((label, n, mean))
    return out


def runtime_samples(result):
    runtime = result["runtime"]
    if "frame_seconds" in runtime:
        return [x * 1000 for x in runtime["frame_seconds"]], "per-frame"
    if "chunk_seconds" in runtime:
        chunk = runtime["chunk_size"]
        frames = result["frames"]
        values = []
        for index, elapsed in enumerate(runtime["chunk_seconds"]):
            n = min(chunk, frames - index * chunk)
            if n > 0:
                values.extend([elapsed / n * 1000] * n)
        return values, "per-chunk divided by frames"
    return [], "per-video mean only"


def render(results_path: Path, training_path: Path, output_path: Path,
           resource_dir: Path | None = None):
    report = json.loads(results_path.read_text(encoding="utf-8"))
    training = json.loads(training_path.read_text(encoding="utf-8"))
    videos = report["videos"]
    models = key_ordered(report["accuracy_summary"], "circle")
    lines = [
        "# 독립 손 관절 추정 검증 보고서", "",
        f"평가 원자료: `{display_path(results_path)}`",
        f"A/B 학습 원자료: `{display_path(training_path)}`",
        "평가 코드: `analysis/external_hand_verification.py`; 지표 근거와 공식은 "
        "`docs/reproducibility/hand_pose_metric_audit.md` 참고.",
        f"입력·소스·모델·결과 SHA-256 재현 명세: `{display_path(results_path.parent / 'provenance_github.json')}`.", "",
        "## 데이터와 조건", "",
        f"- 데이터: {report['dataset']}",
        f"- 선택: {report['selection']}",
        f"- 평가 영상 {len(videos)}개, 총 {sum(v['frames'] for v in videos):,}프레임. "
        "p41 세션 영상 2개가 포함된 4명 편의 표본이며 모집단 무작위 표본이 아니다.",
        f"- 참조 좌표: {report['reference']}. 독립 수작업 해부학 주석이 아닌 markerless 캡처 기반 좌표다.",
        f"- 가림 조건: 512×420, 중심 ({report['mask']['center_xy_px'][0]}, "
        f"{report['mask']['center_xy_px'][1]}), r={report['mask']['radius_px']}px, "
        f"RGB{tuple(report['mask']['fill_rgb'])}, 모든 프레임 적용; 경계 포함.",
        "- 프레임별 `circle`과 `unoccluded`는 동일한 원본 영상·정답 좌표를 사용한다. "
        "숨은 관절은 정답 좌표 중심이 원형 마스크 안에 있는 경우로 정의했다.",
        f"- 가림 적용 재생 영상 5개와 해시/프레임 인덱스: `{display_path(results_path.parent / 'occlusion_previews')}`.",
        "- HaMeR는 손 좌우 정보를 받았고, MediaPipe는 양손 검출 후 정답 손목에 가장 가까운 손을 "
        "선택했다. MediaPipe의 손 선택은 평가 정답을 참조한 사후 매칭이다.", "",
        "## 가림 조건 결과", "",
        "MPJPE는 유효 좌표를 낸 프레임에 조건부로 계산했다. 실패 프레임은 이 오차에서 제외하되 "
        "검출 실패율에 남기고, PCK 분모에는 실패를 오답으로 포함했다. 각도·거리·가림 수준·연속 "
        "가림 시간·가속도·VERA-Hand 안정성은 원 JSON에 영상별로 보존돼 있다. A/B, C ridge, HaMeR는 "
        "손 검출기가 아니라 매 프레임 좌표를 내므로 이들의 1.0은 유효 좌표 출력률이다. MediaPipe만 실제 "
        "검출 성공률이며, HaMeR는 정답 손 방향을 사용한 고정 전체 프레임 crop이다.", "",
        "| 모델 | MPJPE px | MPJPE palm | 가린 관절 palm | 보이는 관절 palm | PCK@0.2 | 유효 출력/MP 검출률 | 실패 | PCK AUC |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key in models:
        a = report["accuracy_summary"][key]
        lines.append(
            f"| {MODEL_LABELS[key.rsplit(':', 1)[0]]} | "
            f"{number(a['mpjpe_2d_px_valid_predictions_micro'], 2)} | "
            f"{number(a['mpjpe_2d_palm_normalized_valid_predictions_micro'], 4)} | "
            f"{number(a['occluded_mpjpe_2d_palm_normalized_valid_predictions_micro'], 4)} | "
            f"{number(a['visible_mpjpe_2d_palm_normalized_valid_predictions_micro'], 4)} | "
            f"{number(a['pck20_all_labeled_joint_frames_micro'], 4)} | "
            f"{number(a['detection_success_rate_micro'], 4)} | "
            f"{number(1-a['detection_success_rate_micro'], 4)} | "
            f"{number(a['pck_auc_0_to_0_5_palm_micro'], 4)} |"
        )
    lines += ["", "### 영상별 가린 관절 오차", "",
              "| 영상 | " + " | ".join(MODEL_LABELS[k.rsplit(":", 1)[0]] for k in models) + " |",
              "|---|" + "---:|" * len(models)]
    for video in videos:
        cells = []
        for key in models:
            value = video["results"][key]["occluded_joints"]["mean_position_error_palm_normalized"]
            cells.append(number(value, 3))
        lines.append(f"| {video['video']} | " + " | ".join(cells) + " |")

    a_key, b_key = "realtime:2d_A_current:circle", "realtime:2d_B_past_current:circle"
    ab = pair(report, a_key, b_key, "mean_position_error_palm_normalized_valid_frames")
    lines += ["", "## 시간 정보 효과와 대응 비교", "",
              "왼쪽 모델 − 오른쪽 모델의 차이다. 음수 MPJPE는 왼쪽 오차가 낮음을 뜻한다. "
              "95% 구간은 프레임이 아니라 영상 단위 10,000회 대응 부트스트랩이다. 영상 5개라 "
              "구간은 탐색적이다.", "",
              "| 비교 (왼쪽−오른쪽) | Δ MPJPE palm | 95% 영상 bootstrap CI | Δ PCK@0.2 | 95% CI |",
              "|---|---:|---:|---:|---:|"]
    comparisons = [
        (a_key, b_key),
        ("hamer:hamer:circle", a_key), ("hamer:hamer:circle", b_key),
        ("mediapipe:mediapipe:circle", a_key), ("mediapipe:mediapipe:circle", b_key),
        ("local:3d:circle", a_key), ("local:3d:circle", b_key),
    ]
    for left, right in comparisons:
        err = pair(report, left, right, "mean_position_error_palm_normalized_valid_frames")
        pck = pair(report, left, right, "pck20_all_reference_joints")
        if not err or not pck:
            continue
        left_label = MODEL_LABELS[left.rsplit(":", 1)[0]]
        right_label = MODEL_LABELS[right.rsplit(":", 1)[0]]
        lines.append(f"| {left_label} − {right_label} | {number(err['left_minus_right_mean'],4)} | "
                     f"[{number(err['ci95_video_bootstrap'][0],4)}, {number(err['ci95_video_bootstrap'][1],4)}] | "
                     f"{number(pck['left_minus_right_mean'],4)} | "
                     f"[{number(pck['ci95_video_bootstrap'][0],4)}, {number(pck['ci95_video_bootstrap'][1],4)}] |")

    lines += ["", "### 가림 지속 시간별 숨은 관절 오차", "",
              "영상별 joint-frame 수로 가중한 요약이며, 긴 구간은 서로 독립 표본으로 간주하지 않는다.", "",
              "| 모델 | 연속 가림 | 관절 프레임 수 | 오차 palm |", "|---|---:|---:|---:|"]
    duration_keys = ["realtime:2d_A_current:circle", "realtime:2d_B_past_current:circle",
                     "hamer:hamer:circle", "mediapipe:mediapipe:circle"]
    for key in duration_keys:
        for label, count, value in duration_summary(videos, key):
            lines.append(f"| {MODEL_LABELS[key.rsplit(':',1)[0]]} | {label} | {count:,} | {number(value,4)} |")

    lines += ["", "## 실행 시간", "",
              "모델 시간은 영상 디코드·공통 가림 변환 시간과 분리했다. A/B의 프레임 시간에는 입력 크기 "
              "변환이 포함된다. HaMeR 시간은 8프레임 배치 추론 시간의 합이며, MP와 A/B는 프레임 호출 "
              "시간의 합이다. C 오프라인 ridge는 전체 영상 벡터화 실행이라 프레임별 분포가 없다.", "",
              "| 모델/조건 | 전체 5영상 초 | 평균 초/영상 | 평균 ms/프레임 | 관측 p50 ms | 관측 p95 ms | p95 영상평균 ms | 지연 표본 단위 | 1.5× 평균 초과 영상 |",
              "|---|---:|---:|---:|---:|---:|---:|---|---:|"]
    for suffix in ("unoccluded", "circle"):
        for base in ORDER:
            key = f"{base}:{suffix}"
            if key not in report["timing"]["summary"]:
                continue
            t = report["timing"]["summary"][key]
            outliers = [x["video"] for x in t["per_video_latency"] if x["at_least_1_5x_mean"]]
            samples, basis = [], ""
            for video in videos:
                vals, unit = runtime_samples(video["results"][key])
                if vals:
                    samples.extend(vals)
                    basis = unit
            if not samples:
                samples = [x["ms_per_frame"] for x in t["per_video_latency"]]
                basis = "per-video average"
            p50, p95 = statistics.median(samples), sorted(samples)[int(.95 * (len(samples)-1))]
            lines.append(f"| {MODEL_LABELS[base]} / {suffix} | {number(t['total_model_seconds'],2)} | "
                         f"{number(t['mean_video_seconds'],3)} | {number(t['mean_ms_per_frame'],3)} | "
                         f"{number(p50,3)} | {number(p95,3)} | "
                         f"{number(t['p95_ms_per_frame_across_video_averages'],3)} | {basis} | "
                         f"{', '.join(outliers) if outliers else '없음'} |")
    lines += ["", "### 모델별·영상별 시간 (원본초/가림초)", "",
              "| 모델 | " + " | ".join(v["video"] for v in videos) + " |",
              "|---|" + "---:|" * len(videos)]
    for base in ORDER:
        raw = f"{base}:unoccluded"; circle = f"{base}:circle"
        if raw not in report["timing"]["summary"]:
            continue
        vals = []
        for video in videos:
            raw_s = video["results"][raw]["runtime"]["total_seconds"]
            mask_s = video["results"][circle]["runtime"]["total_seconds"]
            vals.append(f"{raw_s:.2f}/{mask_s:.2f}")
        lines.append(f"| {MODEL_LABELS[base]} | " + " | ".join(vals) + " |")

    lines += ["", "### 초기화·warm-up을 포함한 모델 실행 총계", "",
              "모델별 추론 시간에 한 번의 backend 모델 초기화와 모든 영상·조건별 초기화/warm-up을 더했다. "
              "공통 영상 디코드·좌표 변환은 별도라 이 표에 없다.", "",
              "| 모델 | backend 초기화 초 | 영상별 모델 초기화 합계 초 | warm-up 합계 초 | 추론 합계 초 | 위 항목 합계 초 |",
              "|---|---:|---:|---:|---:|---:|"]
    prediction_data = {}
    for backend in ("local", "realtime", "hamer", "mediapipe"):
        pred_path = results_path.parent / f"{backend}_predictions.json"
        if pred_path.exists():
            prediction_data[backend] = json.loads(pred_path.read_text(encoding="utf-8"))
    for base in ORDER:
        backend, model_name = base.split(":", 1)
        run = prediction_data.get(backend)
        if not run:
            continue
        init_each = warmups = inference = 0.0
        for video in videos:
            for condition in ("unoccluded", "circle"):
                result = video["results"].get(f"{base}:{condition}")
                if result is None:
                    continue
                runtime = result["runtime"]
                init_each += runtime.get("initialization_seconds", 0.0)
                warmups += runtime.get("warmup_seconds", 0.0)
                inference += runtime.get("total_seconds", 0.0)
        setup = run.get("setup_seconds", 0.0)
        lines.append(f"| {MODEL_LABELS[base]} | {number(setup,3)} | {number(init_each,3)} | "
                     f"{number(warmups,3)} | {number(inference,3)} | "
                     f"{number(setup+init_each+warmups+inference,3)} |")

    lines += ["", "### 학습 held-out 결과", "",
              "| 도메인 | 모델 | 검증 NME | held-out NME | held-out 가림 관절 NME | PCK@0.2 | 클립/프레임 |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for domain, row in training["results"].items():
        for mode, model in row["models"].items():
            h, v = model["held_out"], model["validation"]
            lines.append(f"| {domain} | {mode} | {number(v['nme'],6)} | {number(h['nme'],6)} | "
                         f"{number(h['hidden_nme'],6)} | {number(h['pck_20'],4)} | "
                         f"{h['scored_clips']}/{h['reference_frames']:,} |")

    lines += ["", "### 기존 CAPTCHA 점수 계산과의 관계", "",
              "아래 값은 각 모델의 전체 영상 관절 시퀀스를 production 방식에 대입한 **점수 유사값**이다. "
              "실제 CAPTCHA 시도나 통과율이 아니다. MediaPipe는 유효 검출 영상이 1개뿐이라 그 영상만 요약한다.", "",
              "| 모델 / 가림 | 점수 유사값 평균 | 범위 | 임계값 통과 영상 | 유효 영상 |", "|---|---:|---:|---:|---:|"]
    for key in models:
        scores = [v["results"][key]["production_score_analog"]["challenge_score_analog"]
                  for v in videos if v["results"][key]["production_score_analog"] is not None]
        if scores:
            threshold = videos[0]["results"][key]["production_score_analog"]["challenge_threshold"]
            label = MODEL_LABELS[key.rsplit(":", 1)[0]]
            lines.append(f"| {label} / circle | {statistics.mean(scores):.4f} | "
                         f"{min(scores):.4f}–{max(scores):.4f} | "
                         f"{sum(s >= threshold for s in scores)}/{len(scores)} | {len(scores)} |")

    base_dir = results_path.parent
    lines += ["", "## 실행 환경", "",
              "- 하드웨어: Windows 10 Pro 26H2, build 26300; Intel Core i5-1135G7 @ 2.40 GHz; "
              "8 logical processors; 15.8 GiB RAM; CPU-only inference.",
              "- HaMeR 전 모델 초기화는 29.972초였고 전체 추론 파일은 11:47에 저장됐다. 개별 모델의 "
              "준비·warm-up·프레임/배치 시간은 backend JSON에 분리 기록했다.",
              "", "## 소프트웨어·모델 버전", ""]
    for backend in ("local", "realtime", "hamer", "mediapipe"):
        path = base_dir / f"{backend}_predictions.json"
        if not path.exists():
            continue
        run = json.loads(path.read_text(encoding="utf-8"))
        lines.append(f"- **{backend}:** {json.dumps(run.get('environment', {}), ensure_ascii=False, sort_keys=True)}; "
                     f"초기화 {number(run.get('setup_seconds'),3)}초.")
    probe_dir = resource_dir or (results_path.parent / "resource-probe")
    lines += ["", "### 프로세스 메모리 고수위", "",
              "Windows PROCESS_MEMORY_COUNTERS_EX의 process peak working set이다. C/A/B/MediaPipe는 한 backend "
              "프로세스가 전체 영상·조건을 처리할 때의 값으로, 모델별 단독 RAM 사용량은 아니다.", "",
              "| backend | peak working set GiB | 측정 방식 |", "|---|---:|---|"]
    for backend in ("local", "realtime", "mediapipe"):
        probe_path = probe_dir / f"{backend}_predictions.json"
        if not probe_path.exists():
            continue
        run = json.loads(probe_path.read_text(encoding="utf-8"))
        memory = run.get("environment", {}).get("process_memory", {})
        peak = memory.get("peak_working_set_bytes")
        lines.append(f"| {backend} | {number(peak / (1024**3),3) if peak else 'n/a'} | "
                     f"{memory.get('measurement', memory.get('state','n/a'))} |")
    lines.append("| HaMeR | 약 3.39 | 실행 중 Get-Process 표본에서 관측된 최대 working set; OS high-water 계측은 아님 |")
    lines += ["", "## 결론과 한계", "",
              "- 이 5개 가림 영상에서 HaMeR가 A/B보다 pooled 위치 오차가 낮았다. A current-only는 B past+current보다 "
              "2D 모델의 가린 관절 평균 오차가 낮았다. A−B 정규화 MPJPE CI는 0을 포함하지 않았지만, "
              "HaMeR−A/B MPJPE CI는 0을 포함해 HaMeR 우위를 통계적으로 확정할 수 없다.",
              "- A/B의 합성 held-out 이점은 외부 실제 영상에 그대로 전이되지 않았다. 현재 표본에서는 두 실시간 모델 모두 "
              "가림 관절 오차가 크고, PCK@0.2가 매우 낮아 정확한 추정 성능을 입증하지 못했다.",
              "- MediaPipe는 보이는 관절에는 낮은 오차를 보였지만 가림 조건 검출 성공률이 낮았다. 조건부 MPJPE와 전체 PCK를 "
              "함께 봐야 한다.",
              "- 표본 5개, 참여자 4명, p41 영상 2개, convenience selection 및 자동 참조 라벨 때문에 일반화 주장은 불가하다. "
              "bootstrap은 영상 단위이며 모집단 근거가 아닌 기술 통계다.",
              "- A/B는 hand-present 자료로 학습됐다. 좌표를 매 프레임 반환하지만 손 부재를 판별하지 않으므로, 독립 hand-presence "
              "검출/실패 정책이 필요한 배포 기능으로 남아 있다. 브라우저 직접 실행은 아직 검증하지 않았다.",
              "- 세부 관절별/가림 수준/연속 가림 시간/실패 프레임/production 점수 구성요소/모든 영상별 결과는 연결된 JSON에 보존했다.",
              ""]
    output_path.open("x", encoding="utf-8").write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-json", type=Path, required=True)
    parser.add_argument("--training-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resource-dir", type=Path)
    args = parser.parse_args()
    render(args.results_json, args.training_json, args.output, args.resource_dir)


if __name__ == "__main__":
    main()
