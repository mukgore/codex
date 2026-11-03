# ������ �յ��� CAPTCHA ���� ����

**���޺� �ļ� ����:** [�۾� �Ϸ� ���Ρ��յ��� �ڵ� ���� ����](docs/deliveries/2026-11-04_completion_audit.md)�� ���� ��� 62���� ���� �䱸�� �����մϴ�. �ڵ� ������ ���� ���迡 ���Ե� ������ ������������� �ʾҰ�, �� ���� �ÿ������� ���������� �� ������ ���� ���� �۾��� ������ ����߽��ϴ�.

**�ֽ� �۾� ��Ȳ(2026-11-03 ���޺�):** [�� ����� ���� �� ��](docs/backlog_2026-11-03.md), [���� ī��](docs/experiment_cards_2026-11-03.md), [��������ǥ �ʾ�](docs/research_explanation_2026-11-03.md), [handcaptcha ���� ��ġ�� ���� �ȳ�](patches/README.md). ū �� ���á���ø ȭ��� ���� ������ [handcaptcha �۾� �귣ġ](https://github.com/mukgore/handcaptcha/tree/work/todo-consolidation-20261103)�� Ŀ���߰� ����/�ĺ� ���� �� CLI�� �߰��߽��ϴ�. �̹� ���롤�˻� ������ [���޺� �ݿ� ���](docs/deliveries/2026-11-03_review.md)�� �ֽ��ϴ�.

�� ����Ҵ� ���� ������ ����� �����ϰ� �Ѱ踦 �����ϴ� ���� �м� ������Դϴ�. ���� �������������� ���䡤���κ� ��ǥ�����󡤸� ���⹰�� ���� ����ҿ� �������� �ʽ��ϴ�. ���� ������ ���� ����� �м� �ڵ常 �����մϴ�.

G3�� [������ ���� ������ ���� ���� �Ѱ�](docs/reproducibility/g3_dr3_fr5_researcher_update_2026-10-28.md)�� ����� �ܰ��Դϴ�. ���� ���ε� ���� G4 ���ݡ���� Ž���� �����߽��ϴ�. �ֽ� ����� [G4 ���� �ڵ� ������](docs/g4_actual/g4_final_report.md), ���� 1�� ���¿� ����� [PROJECT_STATUS.md](PROJECT_STATUS.md) �� [phase1_review.md](docs/phase1_review.md)���� Ȯ���� �� �ֽ��ϴ�. � �������ű� ������ ���������� holdout ������ �������� �ʾҽ��ϴ�.

## ���� ������ �м�

Windows PowerShell���� ����� ��Ʈ�� �̵��ϰ�, Python 3.10 �̻����� ���� ����ȯ���� ���� ����:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe analysis\audit.py
```

`analysis/audit.py`�� ���� `data/raw/`�� ���ڷ� �������� ���� �� ���� �ڷḦ �о� �����մϴ�. `data/`�� Git���� ���ܵǾ� �����Ƿ�, ������ ���� Ȯ���� ���� ������ ����ڰ� ���ÿ� ��ġ�ؾ� �մϴ�. �Է� �����ʹ� �������� �ʽ��ϴ�. ���� �������� `reports/phase1_aggregates.json`�� ���ϴ�. ���� ��, ���� �и�, ������ ���� �ؽ� �� ���� ȯ�� ������ ���� ���� `data/derived/`�� ��ϵ˴ϴ�.

���� �� ������ ��� ������ `analysis/replay_existing.py`�� ����� ���� ������� ����� �� �ֽ��ϴ�. �� ����� ���� �������� �ٽ� ó������ ������, �ȼ� ���⡤ī�޶� �Է¡����� ���� ��θ� �������� �ʽ��ϴ�. �ʿ��� �ڵ�� ���ڷ� �������� ����� ���� �������� �ֽ��ϴ�.

## �ڷ� ó��

- ������ ������ �������� �ʽ��ϴ�.
- ������ ���� �ڷ�, ���� ������, ��ǥ, ������, ���� ���� ��ϰ� �ؽ�, �ӽ� �۾� ���⹰�� �������� �ʽ��ϴ�.
- ����� ������ �� ���� ���� ������ ����� ��ó�� ǥ������ �ʽ��ϴ�.
- �ٽ� ���� ����� ���� �ڷ� ������ [docs/phase1_review.md](docs/phase1_review.md)�� �ֽ��ϴ�.


## Reproducibility follow-up (2026-10)

Independent, conditional replay of the archived A/B and prod_v2_pool records and the paired A/B summary are organized under [analysis/reproducibility](analysis/reproducibility), [docs/reproducibility](docs/reproducibility), and [reports/reproducibility](reports/reproducibility). See the [artifact map](docs/reproducibility/README.md). Raw records, participant-level rows, per-session errors, and input hashes remain local and are excluded from Git. Historical executed-build provenance remains unresolved.

## �ǿ뼺 ���� �� ǥ�� ä�� ��ȯ v0.3

- [�ǿ뼺������� ���� �䱸����](docs/practical_validation_requirements_v0.3.md): ���� �ź�, �̰��� ����, �Է� ��ȣ�� ������ �߰� ȿ��, ����� �δ�, ���, ���� ���Ÿ� �и��մϴ�.
- [prod �м� �� ǥ�� ���� ��� ä�� ��ȯ](docs/scoring_standardization_v0.3.md): handcaptcha prod�� ���� ������ �м��ϰ� DTW���ð� �̺С������� ����Ӱ谪 ������ ���� �䱸������ �����մϴ�.
- [����� ���� ���](validation_v03/standard_metrics.py)�� [�ռ� �׽�Ʈ](tests/test_standard_metrics.py)�� �߰��߽��ϴ�. ���� ���/���� ���� �����̳� prod ��ü�������� �ǹ����� �ʽ��ϴ�.

```bash
python -m unittest discover -s tests -p test_standard_metrics.py -v
```

## ���� Ǯ������ ���������� ���� v0.4

[���� ���� Ǯ Ȯ�������� ���������� ���� �䱸����](docs/video_pool_occlusion_delivery_requirements_v0.4.md)�� ���� handcaptcha ������ ���� ����, ���� Ȯ�������ǡ��ߺ� ����, �� ������ ���� �� ����ڵ� �˻�, ���� ����������� ��� ����, �ݺ����� ���ݰ� � �μ� ������ �����մϴ�. ���� �����̸� �ű� ���� ���������� ���衤������ �����ߴٴ� �ǹ̰� �ƴմϴ�.

## G4 ���� �ڵ� Ž�� �� ���� ��� (2026-10-28)

[���� �ڵ�� ���� �ȳ�](g4_lab/README.md)�� ���� HTML ä�������� �Լ�, ���� MP4 �� �� localhost ������ �����մϴ�. [���� ���](docs/g4_actual/g4_attack_matrix.md), [��� ��](docs/g4_actual/g4_defense_matrix.md), [ȸ�͡������˻�](docs/g4_actual/g4_test_results.md), [���� ����](docs/g4_actual/g4_independent_review.md), [��ĺ� ����](reports/g4_actual)�� �����߽��ϴ�. ���� ī�޶��ΰ� ���ɡ��̻�� source �Ϲ�ȭ������ �ý��� L3�� ������ ����� �ƴմϴ�. ���ڷ�� ���� replay �Է��� �������� �ʽ��ϴ�.

## �ļ� ���������� ��ȹ (2026-11-02)

[�ļ� �ε��](docs/research_roadmap_2026-11-02.md)�� ���� ��������ǥ ������, ���� ��ȣ���� ��� ���� ���ɼ�, ä�����Է� ��ȣ ����, ���� Ǯ �� 3D �ա���ü ���� �ĺ��� �켱������ �ܰ� ��ȯ ������ �����߽��ϴ�. ��ȹ ����̸� �ű� ���衤���� �ϷḦ �ǹ����� �ʽ��ϴ�.
