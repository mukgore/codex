# ���޺� ���� �۾� �Ϸ� ���ο� �ڵ� ���� ��Ȳ ����

���� ����: 2026-11-04. ���: **deliverables�� �� ������� ������ �� ���� ���� ������ ���� �ƴϴ�.** ��ȹ ���ա����� ī�塤���� �ʾȰ� �� ������ �ڵ�(���� �� ��, Stage6/7 ���� ����, ���� �� ����/��ø �ÿ�)�� �߰��ƴ�. �����⡤���� ���/���� ���� �򰡡�prod ���ա�� ���ϴ� �Ϸ���� �ʾҴ�.

**�յ��� �ڵ� ������ ���� GitHub �䱸���׿� �־���.** main�� [3D �ա���ü ����][THREED]�� 2026-10-26 �ۼ��� PROPOSED / NOT_TESTED ������. [�ʾ� PR #2](https://github.com/mukgore/codex/pull/2)�� [�Կ� �� ���� ����][GEN]�� Text2HOI+GRAB/MANO ���� ���� R1�� ��ü skeleton/primitive ����� ���Ϸ� P1�� �����Ѵ�. ���� Ȯ�� �� PR #2�� open/draft���̺����̸� head�� b8c39d5��. ���� ��α� G01~G08���� ������ ������, �ش� ���� �ڵ塤���� �αס����� �ڻ��� �̹� ���޿� ����.

## ���� ������ ���� ����

- ���� G1~G4�� ����� ��������˻� ������ �����ߴ�. G3�� ���� ������ G4 ���� Ž��/���� ���/�˻� �ϷḦ �ļ� �̿Ϸ�� �ǵ����� �ʴ´�. �� ������ ���� ���� �� ���� ��ɡ����衤� Ȯ���̴�.
- main: codex 6cfe1b1, handcaptcha b4d96d1. ���� Ŀ��: [codex 916cc6f](https://github.com/mukgore/codex/commit/916cc6fd0febe7f94115c94ff16b8abc10c46e4a), [handcaptcha 6d92012](https://github.com/mukgore/handcaptcha/commit/6d9201296b3c4341b555845868ae15fd5f5ada8b). ���� �۾� �귣ġ head�� ���� �귣ġ ����� �ٽ� Ȯ���ߴ�. ���� ������ �۾� �귣ġ�� ������ main ���ա����� ����� �ƴϴ�.
- ���� ���� ��ü, ���� ������ ����, ���� ���� �ڵ�� �׽�Ʈ, ���� G3/G4 ���, PR #1/#2 �� ���� ���� �귣ġ�� ���� tree�� �����ߴ�. Git ��ü ���� �̷¡������ ���� ���ڷᡤ�ܺ� ��ȭ ��ü�� ���縦 �����ϴ� ����� �ƴϴ�.
- ǥ�� ������ �Ϸᡱ�� �ش� ��ȹ/���� �ۼ� �Ϸ��. ���ڵ塤�ռ� �˻硱�� �ڵ�� �ռ� ȸ�� �����̴�. ���κС��� �䱸�� �Ϻθ� �����Ѵ�. ���̽���/�Է� �ʿ�/���� �ĺ����� ���� ������ �ƴϴ�. ������ �Ϸ� �������� ���޺� ������ ����� �����.
- 62�� ���� ��� ���� ���� ����� ���� ��ġ�� ũ�⵵ �ٸ���. �Ʒ� **190�� ���� ��**�� ������ ���� ���� ���̸� 190���� ���� �۾��̳� �Ϸ��� �и� �ƴϴ�.
- ���� ���� ���뿡�� ����� 58��(����12+CSV7+���� �Լ�17+����9+Node13)�� [���� ���][REVIEW]�� ������. �̹� ���� ���翡�� ���� �����̳� �� �˻縦 �ٽ� �������� �ʾҴ�. �߰� ��Ű���� ��ġ���� �ʾҴ�.

## ���� ������ ������ ���

| ���� | Ȯ���� ���� | ������ ���� ���� |
|---|---|---|
| ���� �� | �� ������ �̹� �ִ� CSV�� ���� ������validation ���á�����/�ߴ� �и����� | ����ǥ��Ư¡/���� adapter, ���� ���� �ڷ�, B2/B3������ CI��JS �̽� |
| �� ����/��ø | ���� �ÿ��� ū ��ȿ �� ���á��������ҽ� �ߴܡ��и�/��ø | prod�� handedness/����/gate/timer/�α�, ���� ī�޶󡤻�� �� |
| ���� | Stage6/7�� 2D ���������� �źΡ���ü �и���decode ���� �˻� | run_batch ���ᡤPTS/�ð��������ٸ� bake/legacy������ release |
| �ڵ� ���� | �䱸�����塤R1/P1 ���� ����� ���� | ���� generator, ��/��ü/����, ���������䡤�򰡡����� �ڻ� |
| ����/�� | ���� G4 loopback���ݷʡ���ȸ �Һ� �˻��� ���� | ���� �Է� ��ó��� ��衤�� ���/�̻�� source����� |

## �ڵ� �������� ȥ���ϱ� ���� ���� �ڵ�

1. [Stage6 generate_occluded_video][H6]�� ���� �Կ� ���� ������ ���´�. [���� bake][BAKE]�� ����� ������ ó���Ѵ�. ���ο� �ൿ family�� �ռ��ϴ� �����Ⱑ �ƴϴ�.
2. [lab ���� issue][SERVER]�� ����� source ��Ͽ��� �����Ѵ�. �� �յ����� ����� �Լ��� �ƴϴ�.
3. g4_lab/attacks.py�� generate_attacks�� �˷��� ���� ������ ����/����/����/����/���� ���� �������� �����Ѵ�. ���� G4 ���� �ڵ��̸� ���� challenge ������� ���� �ʴ´�.
4. �׽�Ʈ�� �ռ� ��ǥ/3-frame MP4�� Canvas render�� ȸ�� fixture/ȭ�� �ռ��̴�. 3D �ա���ü generator�� ����/���� ����� ���� �ʴ´�.
5. ���� tree���� �ڵ塤��Ʈ�ϡ��� �ڻ� ���� ����� �˻��ߴ�. �Ʒ� scope JSON�� �˻��� ref/SHA�� ����� �����Ѵ�. ��� �����/���� ��ġ�� �����Ⱑ ���ٴ� ������ ���� �ʴ´�.

## ���� ���˿��� �߰��� �߿��� ����

1. [pipeline.run_batch][PIPE]�� ������ Stage6 renderer�� ȣ������ �ʰ� Stage7�� �ĺ� manifest�� ����. accepted�� �ϼ��� ���� MP4/release�� �ٸ���.
2. [Stage2][QUALITY]�� frame�� �����ϰ� [Stage4][STAGE4]�� forward+reverse�� �����. �� [Stage6][H6]�� �� ������ �������� �ʰ� consecutive source index�� ����Ѵ�. ��� FPS�� ���� info�� ����ϸ� ���� PTS/VFR ����� �������� �ʴ´�.
3. w3>1�̸� ���� �� �ȿ� P0 �ո��� ������ [Stage7][H7]�� �ո��� �ۿ� ���� ���� �䱸�Ѵ�. [�浹 ȸ��][HGATETEST]�� �����ư� �ؼҵ����� �ʾҴ�.
4. [dataset_expansion_bake_v1.py][BAKE]�� ���� ��η� ���� �ְ� last mask ���롤���� mask ������ ������ ������ Colab !pip ������ �����ȴ�. Stage6 ������ �� ���ϱ��� ��ģ ���� �ƴϴ�.
5. [legacy ingest][INGEST]�� ���� tree�� ���� export_pool�� import�ϸ� ���� ���� ������ �������� �ʴ� ������ ���� �ִ�.
6. [prod][PROD]�� maxNumHands:1�� �迭 ù ��, ���� ���� fetch, client ä�� ������ �����Ѵ�. ���� �ÿ��� �� �� ���⡤��ø ������ ���� prod�� �ݿ��ƴٰ� ǥ���ϸ� �� �ȴ�.
7. [�ÿ�][DEMO]���� ���� ������ ������ ī�� B�� trial/event logger�� ����. 8 callback ����ȭ�� ������ �ð� ������ �ƴϸ� �¿��/����/���� �ʱ�ȭ�� prod�� ������� �ʾҴ�.
8. [CSV CLI][COMPARE]�� caller�� ������ �躸 ID�� �ϼ��� �� ������ �˻��Ѵ�. attack-family/object/contact family ����, ���� ���� �ߺ�, �̻�� source�� �������� ������ �������� �ʴ´�. ��� split�� scored human/attack�� �䱸�ϹǷ� Ư�� split/������ ���� ������ �ڷḦ �״�� ó���ϴ� ���� ��ü�ý��� ����⵵ �ƴϴ�.
9. ��α� V03�� ��2��2���� [���� V3][VALIDATION]�� 2��3(��ȣ ���������� ����/������/����)�� ����ߴ�. P0/P1�� ��ȣ ���������� ���� ������ �� �����Ѵ�. ��� 2��2�� �����ϸ� �� ��� ������ ������ �Ѵ�.
10. POOL-03�� ���� ���´� INGESTED��RIGHTS_CLEARED��QUALITY_CHECKED��MASKED��ARTIFACT_VERIFIED��HUMAN_REVIEWED��SECURITY_EVALUATED��RELEASED�̸� ���� QUARANTINED/��� RETIRED��. ��α��� ª�� ���� ���� ������ ���� �ӽ��� ȥ������ �ʴ´�.
11. T03�� ù/�߰�/��, T05�� raster�� gate, T07/08�� RELEASED��PTS����� Ʈ�� �μ��� ���� �Ϻ� �ռ� �˻纸�� �д�. ���� ID ��ü ����� �°����� �ʾҴ�.
12. [���� ���� ����][SCORE]�� ��NumPy 2.2.6 ����� ������ �Ϻ� ���� ������ ���ε� ���д� ���� ���� ����̴�. �ļ� [���� �˻�][REVIEW]�� 2.2.6 ��������� Ŀ���� �Բ� �о�� �Ѵ�.

## ���� ��α� 62�� �׸�

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| NOW-01 | ���� �Ϸ� | ���� ��ϡ����� ������ ���޵ǰ� Ŀ�Ե� | ��Ͽ� �ִ� ��� �۾��� ���� �ϷḦ ������ ���� | [BACKLOG][BACKLOG], [INDEX][INDEX] |
| NOW-02 | �ڵ塤�ռ� �˻� | Stage6/7 ��ġ ���� �� ���� 9�������� �Լ� 17�� �˻� | PTS��release���ٸ� ���� ��Ρ����� �浹�� ���� | [H6][H6], [H7][H7], [HTEST][HTEST], [REVIEW][REVIEW], [HINTEGRITY][HINTEGRITY] |
| NOW-03 | �ڵ塤�ռ� �˻� | ���� �ÿ��� ���� ���, Node 13�� �˻� | prod ���ᡤ���� ī�޶󡤻�뼺 ���� | [SEL][SEL], [DEMO][DEMO], [NTEST][NTEST], [DEMOTEST][DEMOTEST] |
| NOW-04 | �ڵ塤�ռ� �˻� | ���� �� CSV �� CLI�� 7�� �˻� | ���ڷ� Ư¡/���� ����� ���� �� �ڷ� | [COMPARE][COMPARE], [CTEST][CTEST] |
| NOW-05 | ���� �Ϸ� | ī�� A/B/C�� ���ǡ��и𡤱�� ��� �ۼ� | ���� ���á���ġ ��ݡ����������ࡤ���� | [CARDS][CARDS] |
| NOW-06 | ���� �Ϸ� | ���� ���� ��������ǥ ���� �ʾ� �ۼ� | ��ǥ �ð������� ���� ���ð� ���� ��ǥ | [EXPLAIN][EXPLAIN] |
| R01 | �κ� | ���� �ʾ��� �ۼ��� | ���� ��ǥ �������з��������� ���� | [EXPLAIN][EXPLAIN], [ROADMAP][ROADMAP] |
| R02 | ���� �Ϸ� ���� | G3��A/B��FR1~4��DR3 ���� ���¸� ���� | ���� �м��� ������� �� �̿Ϸ�� ������� ���� | [G3][G3] |
| R03 | ���� �Ϸ� ���� | ���Ǻ� ���� ����� ���� build �躸 �Ѱ踦 ���� | �̷� ���࿡�� build/pool manifest ���; ���� �߰� ������ �� ���� �ҿ� | [G3][G3], [LINEAGE][LINEAGE] |
| R04 | ���� �Ϸ� ���� | ���� �ΰ� �ܰ� ��ü�� ���� ����, ���� 13�ó����� ���� ���� ���� | �� ���� �򰡸� ���� ������ �ұ����� ���� | [G3][G3] |
| R05 | �Է� �ʿ� | �ʱ� n=4��ǥ10��grid25���ð����� p�� �躸�� ���ȭ | Ư�� ���ڷ�/���� �̷� Ȯ�� �� ���� ����; �Ϸ�� A/B�� �ٽ� ���� ���� | [RECOVERY][RECOVERY], [G3][G3] |
| R06 | �κ� | ���� null�� �ؼ� �Ѱ�� �� �α� ��� �ۼ� | �� ������ ���� ����/���� ���� �� ��ü UI �ð� ���� | [CARDS][CARDS], [DICT][DICT] |
| R07 | ���� �Ϸ� ���� | ���� G4 ���� Ž�������� ���˻� ����� ���� | ���� source/���/�ŷ� �Է��� ���� �ļ� ���� | [G4STATE][G4STATE], [G4REPORT][G4REPORT] |
| R08 | ���� �Ϸ� | ��ȣ������� �� ���� ī�� A �ۼ� | ���� �� �ּ���ä�� ��Ģ ���� �� ���� | [CARDS][CARDS] |
| R09 | ���� �Ϸ� | ����/�/���� ���� ���ؿ� ���� ���ɼ� ��ȹ | ���� ���������ǡ��ڷ� �� ���� �� | [CARDS][CARDS], [FOLLOWUP][FOLLOWUP] |
| U01 | �ڵ塤�ռ� �˻� | ��ȿ 21����bbox������������ȭ ���� ���� | ���� ���� ��ȯ �����߸�/�ڼ�/FPS ���� Ȯ�� | [SEL][SEL], [NTEST][NTEST] |
| U02 | �κ� | ��ġ��ũ�⡤���� ���� ����, �ҽ�/��ȣ�� �� ��ü ����� | ª�� �翬�ᡤhandedness/����/gate/�α� ����; ������ �Ǳ� ���� | [SEL][SEL], [DEMO][DEMO], [UI][UI] |
| U03 | �ڵ塤�ռ� �˻� | �и�/��ø�������������� ���������� ī�޶� ���� | ���� �¿�ա����̾ƿ���ī�޶󡤻�뼺 | [DEMO][DEMO], [HTML][HTML], [NTEST][NTEST], [DEMOTEST][DEMOTEST] |
| U04 | �̽��� | prod�� ������ �ÿ������� ���� | ���� �ա��¿�ա�������Ÿ�̸ӡ���� ���� �� shadow �� | [PROD][PROD], [DEMO][DEMO] |
| U05 | �κ� | �ĺ� ��ϰ� �� ���� ���� �ȳ����� �׵θ� �Ϻ� ���� | ����/�ù�/���� ����ȭ��/���� ���á��������� | [UI][UI], [DEMO][DEMO], [CARDS][CARDS] |
| U06 | ���� �Ϸ� | �� ���ð� UI ȿ���� ������ ī�� B �ۼ� | �ൿ ���� ���ǡ��̺�Ʈ �����⡤������ �񱳡�ä�� ���� | [CARDS][CARDS], [UI][UI] |
| S01 | �̽��� | ��ǥ���ð������� ǥ�� adapter�� ������ ���� | ��Ⱦ�񡤹̷������� �ð���null/gap������ �躸 adapter ���� | [SCORE][SCORE], [COMPARE][COMPARE] |
| S02 | �κ� | ���� constrained_dtw�� �ռ� �˻� ���� | ���� 15���� Ư¡��band/grid ���á����� �񱳡�JS �̽� | [METRICS][METRICS], [SCORE][SCORE] |
| S03 | �κ� | ���� ����� timestamp �̺� �Լ� ���� | ������gap����Ȱȭ��FPS/������ ������ ���� trial ���� | [METRICS][METRICS], [SCORE][SCORE] |
| S04 | �κ� | �̹� ����� legacy/candidate ���� �� ���� �߰� | B0/B1 Ư¡/���� ����, B2 �н���B3 ablation��calibration | [COMPARE][COMPARE], [SCORE][SCORE] |
| S05 | �κ� | ���� threshold �Լ��� �� validation/test ���� | ROC/DET �׸������ݱ��� �־Ƿ������� CI������ �� | [COMPARE][COMPARE], [METRICS][METRICS] |
| S06 | �̽��� | legacy gate�� �����ϰ� �� �α� �׸� ���� | gap/hold/coverage ��Ģ, ���� ����, ���� �αס����� ��ε� | [SCORE][SCORE], [PROD][PROD], [CARDS][CARDS] |
| S07 | �κ� | �ռ� ����/CSV �˻�� ���� | adapter �˻����� ���� trial�浶�� �򰡡�JS parity��shadow | [SCORE][SCORE], [REVIEW][REVIEW] |
| V00 | �κ� | ���� lab�� L1/L2/L3 ���а� �� score-only �и� ó�� | �� ���� metadata validator����ü attempts �αס����� ��� | [SERVER][SERVER], [COMPARE][COMPARE], [VALIDATION][VALIDATION] |
| V01 | ���� �Ϸ� ���� | known-pool�� ����/����/����/���� Ž���� ���� G4���� ���� | �� ���ء��� �ڷ��� Ȯ�� �򰡰� �ʿ��ϸ� ���� ���� | [G4REPORT][G4REPORT], [G4STATE][G4STATE] |
| V02 | �κ� | CSV�� source/participant/capture ID ������ �˻� | ���� �躸������ �ߺ���attack-family holdout�� �̻�� �ڷ� | [COMPARE][COMPARE], [CARDS][CARDS], [VALIDATION][VALIDATION] |
| V03 | �̽��� | �Է� ��ȣ �߰� ȿ���� ���踸 ���� | ���� 2��3 ����(������ ���), ��ȣ ���� ���ռ� �� ���� ���� | [VALIDATION][VALIDATION], [CARDS][CARDS] |
| V04 | ���� �Ϸ� ���� | ���� loopback ����/����/��ȸ �Һ�ȸ�� �Ϸ� | ���� capture trust������ � ������������ ���� ���� | [SERVER][SERVER], [G4STATE][G4STATE] |
| V05 | �̽��� | lab�� in-process RLock�� ���� ���´� ���� | rate/query������ ������evaluator ���� ��ݡ����� worker/���� ���ڼ� | [SERVER][SERVER], [G4REVIEW][G4REVIEW] |
| V06 | �Է� �ʿ� | ���� human18/���� pool/legacy�� ���̸� ���� | ���� challenge�� �� ���� �ڷᡤ���� ī�޶�source �躸 | [OVERLAP][OVERLAP], [G4STATE][G4STATE] |
| N01 | �κ� | �̹� ���� ������ ���� ������Ű ������ �˻� | ����� ��ü Git �̷¡������ �ڷ��� ���� ���� | [REVIEW][REVIEW], [BACKLOG][BACKLOG] |
| N02 | �κ� | ���� ���ɡ����� ȯ��� ���޺� �ؽ� ��� | ������ ������ ��ݡ��� run manifest; ���� �躸�� ���� ���� ���� | [REVIEW][REVIEW], [REPRO][REPRO] |
| N03 | �κ� | ���� ���� �ٰš����� ���塤�űԼ� �Ѱ� ���� | ä���� ������ ���� ������ �ʿ�� �ֽ� 1�� ���� ���� | [CLAIM][CLAIM], [THREED][THREED] |
| P01 | �Է� �ʿ� | �Ǹ� ���� ��Ű���� ���� ������ ����� | source�� �㰡�����ǡ��Ļ�/���� �Ǹ� ���� �� validator | [POOL][POOL] |
| P02 | �Է� �ʿ� | �Կ���source/capture/performer���ߺ� ��ȹ ���� | �� �Կ�/���� �ڷᡤ���� family ���������ҡ��ּ� | [POOL][POOL], [CARDS][CARDS] |
| P03 | �̽��� | private source/artifact�� public ���䡤���� ���� ���� | ��� ���� schema�� �°�/�ݸ�/��� ���� �ӽ� | [POOL][POOL], [PIPE][PIPE] |
| M01 | �κ� | Stage6/7�� x/y ����, �񿬼� �ε��� �ź� | ��������� frame/PTS mapping���ð�������VFR ó�� | [H6][H6], [H7][H7], [STAGE4][STAGE4] |
| M02 | ���� �ĺ� | M0~M4������/����/�ð���ȭ �ĺ��� ���� | ����-�ո� �浹 �ذ�� ���/�ܼ�/�ռ� ���� ���� �� | [POOL][POOL], [HGATETEST][HGATETEST], [G4REPORT][G4REPORT] |
| M03 | �κ� | Stage6�� ���� �źΡ����� decode��ũ��/����/���� �ȼ� �˻� | �غ��� ROI��PTS����� rendition/track���Ǹ���release gate | [H6][H6], [HTEST][HTEST], [POOL][POOL] |
| P04 | �κ� | ���� closed-set lookup����/�Ǻ�/�̵�� �ܼ� �ݷʴ� ���� | ���� source���ݺ� ���ꡤ���� ���š����� ����ũ �ռ� ���� | [G4REPORT][G4REPORT], [POOL][POOL] |
| D01 | ���� �ĺ� | ��������/��û����/ĳ��/�ǽð� �� ��� | ���� source���� ������CPU��p95������/���ۡ�����/��� �� | [POOL][POOL] |
| D02 | �κ� | ���� loopback�� media session/expiry �˻� | � private origin��tenant��warm cache��Range/seek����� ��å | [SERVER][SERVER], [POOL][POOL] |
| D03 | �κ� | �� lab ���� ����� ���� ����, prod�� ���� ���� fetch ���� | ����� ���� ��� �ǽð� UX���Է� ��衤oracle/query ��å | [PROD][PROD], [SERVER][SERVER], [POOL][POOL] |
| T01 | �κ� | �μ� 24���� �Ϻ� ��� �˻�� ���� lab ȸ�͸� ���� | �Ʒ� T01~24 ������ �/���ڷ� ������ Ȯ�� | [POOL][POOL], [HTEST][HTEST] |
| W01 | �κ� | WP0 ���� ��ϰ� WP2 ���� ���� �Ϻ� | WP1 Ȯ��/schema��WP2 ����/PTS��WP3~5 ��/� ���� �۾� | [POOL][POOL] |
| G01 | ���� �Ϸ� | �Կ� �� ���� �� PR #2�� G01~08 ���� | R1/P1 ���� �ڵ塤�ڷᡤ���� ��� | [GEN][GEN], [THREED][THREED] |
| G02 | �̽��� | seed/��/��ü/ī�޶�/���� manifest ���� | 3D generator���⺻ ��/��ü������ ��ȹ������ manifest | [GEN][GEN], [THREED][THREED] |
| G03 | �̽��� | ���������ˡ�����롤���� ������������ ��� | ����/���� validator�� ���� ���� ���ɼ� �˻� | [THREED][THREED], [GEN][GEN] |
| G04 | �̽��� | ����� �� �����ӿ� ��ü �ܼ��� ���� �ٸ� ������ ���� | ���� scene ���������� ���ա����/���� ���� �� | [THREED][THREED] |
| G05 | �̽��� | ���� pass/mesh/seed ����������� ���� ���� ��� | ���������׸���/�ݻ�/�Ƿ翧��buffer/codec ���� �˻� | [THREED][THREED], [GEN][GEN] |
| G06 | ���� �ĺ� | G0/G1/G2 ���� �ǹ̿� SCORE3D ���� | G0 ���á����� Ư¡������ �䡤��ķ ��Ȯ�Ǽ� �� | [THREED][THREED] |
| G07 | �̽��� | B0~B3��A1~A4 ���� �� ���� | source/object/contact family ���ҡ����� ������ ���� ���� | [THREED][THREED], [GEN][GEN] |
| G08 | �Է� �ʿ� | �ܺ� �ڵ�/��/������ �Ǹ����ڿ� ���� ��� | ��� �ڻꡤcheckpoint��ȯ��/�ڿ� Ȯ�� �� ���� ���� | [GEN][GEN], [THREED][THREED] |
| B01 | ���� �Ϸ� | ��� �������ð����ߴܡ����ټ� ��ȹ�� ī�� A/B | �� ��� �ڷᡤ���ǡ��������ൿ/��ġ ���ء����� | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| B02 | �̽��� | ����/�������� ��� ������ ���� | ���� setup/attempt/CPU/���ۡ�p50/p95�������� �Է� | [VALIDATION][VALIDATION], [POOL][POOL] |
| B03 | ���� �ĺ� | ���������������ŷ� ���� ������ ���� ���� | ���ε� ���� ���硤���������/���� �ٰ� | [VALIDATION][VALIDATION] |
| B04 | �̽��� | CONTINUE/MODIFY/STOP/INCONCLUSIVE ���� ���� | ��������� ���ݡ���롤�Ǹ� ���Ÿ� ���� �� �ǻ���� | [VALIDATION][VALIDATION], [ROADMAP][ROADMAP] |

## ���� �ڵ� ���� AUD-01~20�� ��ġ ����

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| AUD-01 | ���ذ� | ���� 8 clip manifest ���� ���� | ���� ����� ����� ���� manifest �и� | [MANIFEST][MANIFEST], [PROD][PROD] |
| AUD-02 | ���ذ� | prod�� landmark fetch �״�� | ���� reference�� ���� ���� UX | [PROD][PROD], [SERVER][SERVER] |
| AUD-03 | �κ� | prod Math.random sort ����; lab�� secrets.choice | ���� �߱޿� ������ ������pool ���� ���� ���� | [PROD][PROD], [SERVER][SERVER] |
| AUD-04 | ���� | ���� 5-MCP ��� baseline ���� ���� | M0 ����/�躸�� ������ �� | [LEGACYMASK][LEGACYMASK], [POOL][POOL] |
| AUD-05 | �κ� | Stage6 ���� �� ���ġ�2D ��� | M0/M1 manifest �������� �Ķ���� ���� | [H6][H6], [POOL][POOL] |
| AUD-06 | ���ذ� | w3>1 �ո� �浹 ȸ�͸� ���� | ��ǥ ROI/����/�ܺ� �ܼ� ���� ���� | [H7][H7], [HGATETEST][HGATETEST] |
| AUD-07 | ������ | Stage6/7 ���� ������ x/y�� ��� | ��ü adapter����� ��η� �Ϲ�ȭ���� ���� | [H6][H6], [H7][H7] |
| AUD-08 | ������ | �̰����� Stage7 ��ü �и� ���� | � ���� gate �� �ٸ� ��� ���� | [H7][H7], [HTEST][HTEST] |
| AUD-09 | ������ | Stage6 ��� mask ���� Ȯ�Ρ����н� ��� �̰Խ� | ���� bake/legacy ��ε� ���� ��å ���� | [H6][H6], [HTEST][HTEST], [BAKE][BAKE] |
| AUD-10 | �κ� | Stage6�� �񿬼�/����� �ε����� �ź� | ���� filter/reverse ����mask�����䡤PTS ����� | [H6][H6], [STAGE4][STAGE4], [QUALITY][QUALITY] |
| AUD-11 | ���ذ� | run_batch�� Stage6 ȣ�� ���� | ���� renderer��������immutable manifest ���� | [PIPE][PIPE] |
| AUD-12 | ���ذ� | forward+reverse �� len/fps ��� | ���� PTS ���� gate����ǥ ���� ���� | [STAGE4][STAGE4], [CONFIG][CONFIG] |
| AUD-13 | ���ذ� | ��ü ��ġ�� open-hand median ���� ���� | train-only ����������/�Կ��� �������ߺ� ���� | [WEIGHTS][WEIGHTS], [PIPE][PIPE] |
| AUD-14 | ���ذ� | handedness �з� score�� confidence�� ��� | ���� �з� Ȯ�Ű� landmark ǰ�� �и� | [EXTRACT][EXTRACT], [QUALITY][QUALITY] |
| AUD-15 | ���ذ� | legacy ���� ���� ���� ���� | Stage2/3/7������ byte���Ǹ� ���� ���� ���� | [INGEST][INGEST] |
| AUD-16 | ���ذ� | ���� export_pool�� import ���� | ���/��� ���������� �� ������ Ȯ�� | [INGEST][INGEST] |
| AUD-17 | ���ذ� | ���� bake�� !pip Colab �� ���� | CLI ��Ű¡��adopted_clips/filter ��� | [BAKE][BAKE] |
| AUD-18 | ���ذ� | ���� bake�� last mask ���� ��� ���� | ��� frame mask���ӽ�/���� �Խá����� �ݸ� | [BAKE][BAKE] |
| AUD-19 | ���ذ� | ���� H264 �� 1:1 ������ ���� ���� | ���� H264 ��decode��PTS/����/���� �˻� | [BAKE][BAKE] |
| AUD-20 | ���ذ� | config�� �̰��� placeholder ǥ�� ���� | ���� dev �ڷ��� ���ప/�ٰ�/��� ��� | [CONFIG][CONFIG] |

## ���� �μ� T01~24�� ���� ���� ����

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| T01 | �̽��� | �Ǹ� UNKNOWN �źδ� ���� | �Ǹ� ���塤release validator������ fixture | [POOL][POOL] |
| T02 | �̽��� | prod�� ��ü manifest�� ������ fetch | ���� ���� client bundle������ allowlist �˻� | [PROD][PROD], [POOL][POOL] |
| T03 | �κ� | Stage6 ���� ���� �ź� �� �߰� ���� ������ �˻� | ù/�� ���� ���� ���ࡤ��� ����� �ݸ�/���� �˻� | [H6][H6], [HTEST][HTEST], [BAKE][BAKE] |
| T04 | �κ� | �̰����� �и� �����ϰ� renderer�� �ź� | ���� ���� �°� ������ ���� | [H7][H7], [HTEST][HTEST], [PIPE][PIPE] |
| T05 | �κ� | 2D ���� �ڵ�� ū z circle ȸ�� ���� | x/y ���� z������ raster��gate ���� ������ ��� �˻� | [H6][H6], [H7][H7], [HTEST][HTEST] |
| T06 | �κ� | �񿬼� ���� �ε��� �ź� �˻� | ����/�����/�ð������� ���� ����ȭ�ϴ� mapping | [H6][H6], [STAGE4][STAGE4] |
| T07 | �κ� | �ӽ� ��¡���decode�����н� �̰Խ� �� �������� ���� | encoder ���� ���� �� ������ RELEASED �°� ���� ���� | [H6][H6], [HTEST][HTEST], [PIPE][PIPE] |
| T08 | �κ� | �ռ� MP4 ��ü count/dimension/���� �ȼ� �˻� | PTS ��������duration����� ���� rendition/���ڷ� ��밪 | [H6][H6], [HTEST][HTEST] |
| T09 | �̽��� | Stage6 �ϳ��� MP4�� ���� | poster/thumbnail/���� track/�����/metadata ���� �˻� | [POOL][POOL], [H6][H6] |
| T10 | �̽��� | legacy ������ �ڵ� ��ȸ ���� ���� | ���� ���� ���ࡤ���� ���� | [INGEST][INGEST] |
| T11 | �κ� | lab�� ������ ��Ρ�media session �˻� | � private origin/��ϡ����� ���� �� ȸ�� �Ұ� ���� | [SERVER][SERVER], [PROD][PROD] |
| T12 | �κ� | ���� lab�� ����/�ٸ� session �˻� | tenant��REVOKED/release ��å ���� ���� ���� ���� | [SERVER][SERVER], [G4REVIEW][G4REVIEW] |
| T13 | �̽��� | � CDN/warm cache ��� ���� | ĳ�� ���� ���¿����� ������ ��ȯ ���� ���� | [POOL][POOL], [SERVER][SERVER] |
| T14 | �̽��� | lab media ������ ������ � Range �μ� �ƴ� | ���� ���� Range/seek/retry�� ���� ��ȸ ���� | [SERVER][SERVER], [POOL][POOL] |
| T15 | ���� ���� �Ϸ� | in-process ���ǡ���ȸ �Һ�/���� ȸ�� �ٰ� ���� | ���� worker��DB������ �Һ���� Ȯ���Ϸ��� ���� ���� | [SERVER][SERVER], [G4STATE][G4STATE], [G4TEST][G4TEST] |
| T16 | ���� ���� �Ϸ� | lab�� client passed�� �ŷ����� �ʰ� ���� �Լ� ���� | prod ������capture trust�� ȥ������ ���� | [SERVER][SERVER], [G4TEST][G4TEST], [PROD][PROD] |
| T17 | ���� �ݷ� Ȯ�� | ���� lookup�� ����/��� ��ȣ ��� | �� source/���� ���ѿ� ���� �� �ĺ� ����; ��� ����� ǥ�� �Ұ� | [G4REPORT][G4REPORT], [G4REVIEW][G4REVIEW] |
| T18 | �̽��� | ���� ����ũ�� ���� ������ ���� | ���� source mask ���ġ��ռ� ���ݰ� �Ѱ� ��� | [POOL][POOL] |
| T19 | �̽��� | ī�常 �ۼ� | ���� ���� ���/���� ���������� �߰�ȿ����UX ���� | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| T20 | �κ� | ������ source/participant/capture ID �ߺ� �˻� | ���� �躸��perceptual/trajectory �ߺ����Կ��� �Ļ��� ���� | [COMPARE][COMPARE], [POOL][POOL] |
| T21 | �̽��� | ���� �ÿ��� ä���� ���� ��ü ���� �ƴ� | ���� fetch ���� �� generic guide������ gate�� �Ϸ� | [PROD][PROD], [DEMO][DEMO], [POOL][POOL] |
| T22 | �̽��� | retired/revoked artifact ���� ���� | �ű� �߱� ������Ȱ�� challenge/ĳ�� ��ȿȭ | [POOL][POOL], [SERVER][SERVER] |
| T23 | �̽��� | �߱� ����/����� � ��ü �帧 �̿� | ���� �ڻ� ���������� ���� �� ���� ���� fallback ���� | [POOL][POOL], [SERVER][SERVER] |
| T24 | �κ� | �ڵ� Ŀ�ԡ����� manifest���˻� ��� ���� | �� release�� �Է�/�Ǹ�/�˻硤�ڻ� ���� ���� �ϼ� | [REVIEW][REVIEW], [PIPE][PIPE], [POOL][POOL] |

## �۾� ��Ű�� WP0~5

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| WP0 | ���� �Ϸ� | ���� ���� ���硤����/���� ����/���� ���� ��� | �ļ� ������ ���¸� �� ����� ���� | [POOL][POOL], [ARCH][ARCH] |
| WP1 | ��ȹ���Է� �ʿ� | �Ǹ�/�Կ�/schema �䱸�� ī�� ���� | ���� �Ǹ� ���塤capture_protocol��split_manifest��schema ���� | [POOL][POOL], [CARDS][CARDS] |
| WP2 | �κ� | Stage6/7 ���� �ߴܡ�2D������ ���� �˻�� ���� | frame/PTS mapping��recipe��run_batch ���ᡤimmutable manifest��T03~10 | [H6][H6], [H7][H7], [PIPE][PIPE], [POOL][POOL] |
| WP3 | ���� Ž��+�ļ� �̽��� | known-pool G4 ����� ���� | �Ǹ�/���� ��� �� �ڷ��� ��������ݡ���� �񱳿� release �ĺ� | [G4REPORT][G4REPORT], [POOL][POOL] |
| WP4 | ���� ����+�ļ� �̽��� | loopback ���������ǡ���ȣ counter ���� | � private store��API������ client UX��T11~16/T21~24 | [SERVER][SERVER], [POOL][POOL] |
| WP5 | �̽��� | � ���� ��Ģ�� ���� | ���� ���衤�ݺ� ���⡤��������ü UX���/��� ���� | [POOL][POOL], [VALIDATION][VALIDATION] |

## �ǿ뼺 V0~V6�� 26�� ���� �׸�

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| V0-01 | �κ� | �ڵ�/���� manifest �� ���� lab run ��� ���� | �� �ʼ� metadata validator������ code/config/split ��� | [REVIEW][REVIEW], [G4STATE][G4STATE], [VALIDATION][VALIDATION] |
| V0-02 | ���� �Ϸ� ���� | ���� lab�� L1/L2/���� L3 �и�; CLI�� score_only ǥ�� | ���� �Է� ��ȣ ������ L3�� ���� Ȯ�� | [SERVER][SERVER], [G4REPORT][G4REPORT], [COMPARE][COMPARE] |
| V0-03 | �κ� | ī�� B �̺�Ʈ ��ࡤlab events ���� | ������ attempts/global_frame/�ð�/����/��� ������ | [CARDS][CARDS], [SERVER][SERVER], [VALIDATION][VALIDATION] |
| V0-04 | �κ� | CLI ����/�ߴ��� attempted �и� ���� | ��ü ���ǡ���õ���timeout��missing ��� ��谪 ���� | [COMPARE][COMPARE], [VALIDATION][VALIDATION] |
| V1-01 | ���� �Ϸ� ���� | ���� G4���� ���� �Ǻ� ��� ������ Ž�� | �� ���� ������ ������ �� �ڷ�� ���� ���� | [G4REPORT][G4REPORT] |
| V1-02 | ���� �Ϸ� ���� | oracle/����/����/�ٸ� ����/invalid ȸ�� �ٰ� | ���� ��ǥ�� �� ���� ��� �ڷ� | [G4STATE][G4STATE], [G4TEST][G4TEST] |
| V1-03 | �κ� | ���� ��� ����, �� CLI validation threshold ���� | ���� trial �ĺ� Ư¡����� test��source�� confusion | [COMPARE][COMPARE], [G4REPORT][G4REPORT] |
| V1-04 | ���� Ž�� �Ϸ� | ���� ���� ����������/�������ݷ� ���� | �� ����/���� ���� ���ѡ������� Ȯ�� ���� | [G4REPORT][G4REPORT], [VALIDATION][VALIDATION] |
| V2-01 | �κ� | source ������ҡ������ڡ�capture ID �˻� ���� | �̻�� ���� ���� manifest�� ���� ������ ���� | [COMPARE][COMPARE], [CARDS][CARDS] |
| V2-02 | ���� Ž��+�ļ� �̽��� | ����/known-pool ���ݱ� ��� ���� | K0/K1 �� source�� ���ݱ�/���꺰 ���� | [G4REPORT][G4REPORT], [VALIDATION][VALIDATION] |
| V2-03 | ���� �Ϸ� | ���� source�����ꡤ���� ���� ���� | �ػ�/ũ��/�ڵ� �� ���� ���� ���� ���ۡ����� | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| V2-04 | ���� Ž�� �Ϸ� | known-pool �ݷʡ��Ѱ� ���� ���� | held-out��adaptive �� �򰡸� ���� ���� | [G4REPORT][G4REPORT], [VALIDATION][VALIDATION] |
| V3-01 | ���� �Ϸ� | ������ ��ȣ��������������/������/���� 2��3 | P���� ���ɼ� Ȯ��; ��� 2��2�� �����ϸ� ��� ���� ���� | [VALIDATION][VALIDATION] |
| V3-02 | �̽��� | �Է� ��ȣ ���ռ��� ���� �׸� ���� | �� �Է¡����� ���ᡤ����ȯ�桤����/�����ȣ������ �� | [VALIDATION][VALIDATION] |
| V3-03 | �κ� | ���� ��ǥ ���⡤client ����������/���� �˻� | ���� ���� ī�޶�/���� ī�޶�/��ȣ ���� ���� ���� | [SERVER][SERVER], [G4STATE][G4STATE], [VALIDATION][VALIDATION] |
| V3-04 | �̽��� | ���� protected counter�� �̹� �˻�� | O1-U1/P1 �߰�ȿ�������� �񿭵�� �� ���� | [G4REPORT][G4REPORT], [VALIDATION][VALIDATION] |
| V4-01 | ���� �Ϸ� | ����/����/�н������� ��ȹ ī�� | �� �����ڡ�source ���������ټ� ������ ���� | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| V4-02 | ���� �Ϸ� | ù �õ����Ϸᡤ�ߴܡ���ü �ð������� ��ǥ ���� | ���� �̺�Ʈ ���������� ���� �ð�/��� ���� | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| V4-03 | �̽��� | �Ϸ������δ� ���� ��Ģ ���� | ���� ��ġ ������ �� ��� ��� ���� | [VALIDATION][VALIDATION] |
| V5-01 | �̽��� | setup/attempt �󰢡�p=0 ���� ���� ���� | cold/warm��CPU/�޸�/���ۡ��ݺ� ��� ���� | [VALIDATION][VALIDATION] |
| V5-02 | �̽��� | ����/����/ä��/����/SDK �и� ���� ���� | ��ġ�� ��롤���������� ��õ� ���� | [VALIDATION][VALIDATION], [POOL][POOL] |
| V5-03 | �̽��� | ���� ����ġ ���� ���� | ����/���� ���� �Է¡��ΰ��� �м� | [VALIDATION][VALIDATION] |
| V6-01 | ���� �Ϸ� | ������������ �ʵ塤���� �ܰ� ���� ���� | ���ε� ����� ��ȿ ���� ��ȭ ��� | [VALIDATION][VALIDATION] |
| V6-02 | ���� �Ϸ� | ���� ���ͺ� ������ ���� | ���� ���ͺ� ���ࡤ�߾�/�ؼ� ���� | [VALIDATION][VALIDATION] |
| V6-03 | �̽��� | ���/����/���� ���� ���� | �� ���������ꡤ��ࡤ������ ���� �ٰ� | [VALIDATION][VALIDATION] |
| V6-04 | �̽��� | ����/�ǻ�/���ޡ����/�ߴ� ���� ���� | ���� ���� ��� �ǻ���� | [VALIDATION][VALIDATION] |

## ǥ�� ä�� S1~S8 ���� �׸�

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| S1 | �̱��� | ǥ�� ��ǥ/time/missing adapter ���� | S1-01/02�� ���� �Է� �ļ���fixture | [SCORE][SCORE], [COMPARE][COMPARE] |
| S1-01 | �̱��� | ��/���̡��ѹ��� mirror����ȭ scale ��� | ��Ⱦ�� ����������/�̷� ���� adapter�� �˻� | [SCORE][SCORE] |
| S1-02 | �κ� | �̺� primitive�� ������/�ߺ�/gap �ź� | segment �ð����ʡ����� frame/PTS��null ������resample adapter | [METRICS][METRICS], [SCORE][SCORE] |
| S2 | ���� primitive | ���� DP DTW��band�����/cell budget ���� | ���� ������������ grid/radius������/�ð����� �� | [METRICS][METRICS], [SCORE][SCORE] |
| S3 | ���� primitive | ����� �ð� gradient������ ��� ���� | ���ڷ� noise/FPS����Ȱȭ��gap ���� �� ablation | [METRICS][METRICS], [SCORE][SCORE] |
| S4 | �κ� | �̹� ����� �� ������ �� | Ư¡ ���⡤B0/B1/B2/B3 �н�/�� �� ���� | [COMPARE][COMPARE], [SCORE][SCORE] |
| S4-01 | �κ� | CSV human/attack label �䱸 | wrong-human/attack-family/knowledge budget�� ���� �躸 | [COMPARE][COMPARE], [SCORE][SCORE] |
| S4-02 | �̱��� | B0/B1/B2/B3 �ĺ� ���� | B1 Ư¡ ���⡤StandardScaler/LogisticRegression��ablation | [SCORE][SCORE] |
| S4-03 | �̱��� | ID ������ �˻�� validation-only ������ ���� | �׷� �н���fit ���� ������calibration������ test | [COMPARE][COMPARE], [SCORE][SCORE] |
| S5 | �κ� | threshold_table�������validation ����/���� | ������� CI�����ݱ��� �־ǰ������ڷ� �� | [METRICS][METRICS], [COMPARE][COMPARE] |
| S6 | �̱��� | prod legacy gate�� ī�� �α� ��� ���� | �ð� gap/coverage������ ���衤���� round-trip | [PROD][PROD], [CARDS][CARDS], [SCORE][SCORE] |
| S7 | �κ� | ���� legacy�� �� �ռ� ���� �˻� ���� | adapter����� trial�浶�� �򰡡�JS parity��shadow | [SCORE][SCORE], [REVIEW][REVIEW] |
| S8 | �κ� | ����12��CSV7 �˻�� ���� ���� ���� | ���ڷ� �μ���JS/� ��ü ��� ���� | [REVIEW][REVIEW], [SCORE][SCORE] |

## �� ���á���ø UI�� ���� ���

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| A-01 | �ڵ塤�ռ� �˻� | ���� ���� ��ȿ bbox������ ū �ĺ������� ó�� | ���� detector/�κ� �߸����� ũ�� ���� ���� | [SEL][SEL], [NTEST][NTEST] |
| A-02 | �κ� | ����ȭ�������������ҽ� latch�������� ��ü ����� | ª�� �翬�ᡤhandedness/����/gate/timer/log ���� | [SEL][SEL], [DEMO][DEMO], [UI][UI] |
| A-03 | �ڵ塤�ռ� �˻� | ����/����ȭ/����/�ҽ� �ȳ��� �ٽü��� ��ư | ���� ����� ���ص������� ���� | [DEMO][DEMO], [HTML][HTML] |
| A-04 | �κ� | ������ũ�⡤�������ҽǡ��迭���� �ռ� �˻� | ���� ���6�� �¿�ա�������gate����� �ʱ�ȭ �� �Ǳ�7�� | [NTEST][NTEST], [PROD][PROD] |
| B-01 | �ڵ塤�ռ� �˻� | ī�޶� �� ���� ������ ��ġ�� �ÿ� | �ü�/���� �δ� ������ ���� ���� | [DEMO][DEMO], [HTML][HTML], [UI][UI] |
| B-02 | �κ� | �и�/��ø������������������Ⱦ�񡤿��� ���� | ���� �¿��/��ġ������ ä��/time ���� ���� | [DEMO][DEMO], [HTML][HTML], [PROD][PROD] |
| B-03 | �������κ� ���� | �� �׵θ������������ȳ��� �Ϻ� ȥ�� ���� | ��桤���������� ȥ���� ���� ���� ���� | [UI][UI], [DEMO][DEMO] |
| B2 | ��ȹ���κ� ���� | AI �ȳ� �ĺ�6���� ���¾ȳ� �Ϻ� | ������ �Ҽ� �ĺ� ���� ��ϡ��߰� UI���� | [UI][UI], [CARDS][CARDS] |
| E1 | ���� �Ϸ� | ����/�ൿ/�̺�Ʈ ���� ��� ī�� B | �ǵ��� �� ���䡤first-correct ���� ��ݡ����� logger | [CARDS][CARDS] |
| E2 | �̽��� | ä��/����/���� ���� ���� | ��ĺ� �� ��������� ���� | [CARDS][CARDS], [UI][UI] |

## �� ���� ���� ��� 7��

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| CASE-1 | �ռ� �˻� | ���� �� ������� �����ϰ� ū ��ȿ �� ���� | ���� ī�޶��� ���� �� ��ȯ ���� | [NTEST][NTEST] |
| CASE-2 | �ռ� �˻� | ���� �迭 �����Ŀ��� ���� ���� | ���� �� ������/���� ǰ�� | [NTEST][NTEST] |
| CASE-3 | �ռ� �˻� | �� ū �� distractor ���忡�� ���� | ����� ���� ���� ������ �� | [NTEST][NTEST], [SEL][SEL] |
| CASE-4 | �ռ� �˻� | ����� ũ��/���� ��ȣ������ ���� ���� �ź� | ���� ���������� �ڷ��� �ΰ��� | [NTEST][NTEST] |
| CASE-5 | �ռ� �˻� | ���� �� �ҽǽ� ���� ������ ���� �� �� | ���� timeout��gate������ ó�� ���� | [NTEST][NTEST], [PROD][PROD] |
| CASE-6 | �κ� | ������ reload�� �ÿ� ��ü �ʱ�ȭ | ���� �� handedness������ ���⡤��������� �ϰ��� | [DEMO][DEMO], [PROD][PROD] |
| CASE-7 | �κ� | ���� ���� ���� �̵� ���� ���� �ռ� �˻� | ���� prod ���� �帧�� ���� �� ȸ�� | [NTEST][NTEST], [PROD][PROD] |

## AI �ȳ� �ĺ� 6��

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| OPT-1 | �ĺ� | ª�� ���� �ù� ��� | ������ �ٸ� ������ �ù� �������н�ȿ�� ���� | [UI][UI] |
| OPT-2 | �κ� ���� | ���º� �� ���� �ȳ� ���� | ����/���� �ܰ� �ȳ� ���հ� �� | [DEMO][DEMO], [UI][UI] |
| OPT-3 | �ĺ� | ū ��ȭ��+���� ����ȭ�� ���� | ���� ����â UI����ø�� ���� �� | [UI][UI] |
| OPT-4 | �κ� ���� | ���� �� �׵θ� ���� | ���� ���/���� ���� ������ ���� ���� ���� | [DEMO][DEMO], [UI][UI] |
| OPT-5 | �ĺ� | ���� ���� ��� ��� | ä�� ���� ���� ��������ü �δ� ���� | [UI][UI] |
| OPT-6 | �ĺ� | ������ ���� ��� | ��û�� ����/�ù� ���������� ���� ���� | [UI][UI] |

## �յ��� �ڵ� ���� ���� ���� �׸�

| ID | ���� ���� | Ȯ���� �� / ���޺��� �⿩ | ���� ��Ȯ�� �۾����Ѱ� | �ٰ� |
|---|---|---|---|---|
| GEN3D-01 | ���踸 | ��� ������seed��generator_version������ ����� ���� | ��/��ü/ī�޶�/trajectory/contact ������ manifest | [THREED][THREED], [GEN][GEN] |
| GEN3D-02 | ���踸 | ����/�ӵ������ˡ�����롤��� ������ ��� | ����/���� �ڵ� �˻�� ��� ���� �˻� | [THREED][THREED], [GEN][GEN] |
| GEN3D-03 | ���踸 | ��ü �ܼ��� ���� �ٲٴ� ������ ���� | scene ��������� �䡤���/���� �ΰ� �� | [THREED][THREED] |
| GEN3D-04 | ���踸 | ���� ������ ���⡤buffer/seed ���� ���� | renderer���������׸���/�ݻ�/�ڵ� �˻硤���� | [THREED][THREED] |
| SCORE3D | ���踸 | G0�� 2D ���, ���� ������ �������� ä������ ���� | ���� ��������ķ ��Ȯ�Ǽ������� �� ���ա����� �� | [THREED][THREED] |
| EVAL3D | ���踸 | B0~B3�� A1~A4��family holdout �� | ���� scene/���/���� ���ݡ���� ���� | [THREED][THREED] |
| R1-1 | �̽��� | Text2HOI ���� ���� ���� ��� | ���� code/checkpoint/data/model �Ǹ���ȯ�� manifest | [GEN][GEN] |
| R1-2 | �̽��� | ���� ��ó�� ���� ���� | ��� GRAB/H2O/ARCTIC �� ���� �غ���ó�� �α� | [GEN][GEN] |
| R1-3 | �̽��� | VAE contact��diffusion��refiner ���� ���� | ���� demo/checkpoint ���ࡤ�� ��� ���� | [GEN][GEN] |
| R1-4 | �̽��� | �� ���� ����/���� �� ��� | �پ缺���ڿ��������ˡ����� ���� �� | [GEN][GEN] |
| R1-5 | �̽��� | ���� ���� �� CAPTCHA ���� �ܰ� ���� | G0 ���͡�����/������byte�˻硤�߱� adaptation | [GEN][GEN] |
| P1-1 | �̽��� | �Կ� 2~3 family ��� ��ü ���Ϸ� ���� | ���� ���� �ڼ����ð������� ���� �ڷ� | [GEN][GEN] |
| P1-2 | �̽��� | ��ü skeleton+primitive������ ���� ���� | �⺻ �ա���ü��grasp/contact ��ȹ��trajectory ���� | [GEN][GEN] |
| P1-3 | �̽��� | ����/����/���� ��ȿ�� ���� ��ǥ | �ĺ� ��������ϰ˻�添��/������Ż������/CPU ���� | [GEN][GEN] |
| P1-4 | �̽��� | �Կ� V0�����Ѻ��� V1����ü V2������ V3 �� | ���� source/family�����/���ݡ������ ���� �� | [GEN][GEN] |
| GEN-RELEASE | �̽��� | ǰ�����Ǹ������������ ���ݡ���� ���� ���� | ������ ���� �ڻ�� ��ü ����/����� ���� ��� | [GEN][GEN], [THREED][THREED], [POOL][POOL] |

## ���� ���� ����

���� ����� �������� ������ ������ ���� �������� ������. �� ����� �Ʒ� �۾��� ���� ����� ���� ���� ���� �ƴϴ�.

1. ���� G1~G4 �ٰſ� ������ baseline�� �����Ѵ�. �̹� ����� ����/�м��� �ٽ� �Ϸ� �������� ������ �ʴ´�.
2. ���� ��δ� ����/ROI �浹 ���������/��� PTS mapping�溰�� bake/legacy �����run_batch/immutable artifact ���� ������ ���´�.
3. �� ������ �ÿ��� ���� ī�޶� Ȯ�Ρ�handedness/����/gate/timer/�α� ���ա浿�� UI���� ���� ��å �񱳡氰�� ���� ��å�� UI �� ������ �����Ѵ�.
4. ���� �񱳴� ǥ�� adapter�浿�� trial�� B0/B1 ������躸�� ��� validation/test�決�� ��Ȯ�Ǽ�/���ݱ��� ������ʿ��� B2/B3��Python/JS parity/shadow ������ �����Ѵ�.
5. �ڵ� ������ G0 ����/���� family�� ����/��� �ڻ��� ���� �� P1 ��ü skeleton/primitive ���Ϸ��� R1 ���� ������ ���� �����Ѵ�. ���� ������ ���� �ʰ� �Կ� ���ؼ��� ���Ѵ�. �Ǹ�/�ڷ�/�ڿ��� �ʿ��� �׸��� �ʿ��� �Է��� �����Ѵ�.
6. �� ������̻�� source������ ���ݡ��Է� ��ȣ������� ���� �ڷᰡ Ȯ���� �� �/��� ���θ� �����Ѵ�. ���� seed ���� ���� ���� �������� ���� ���� ��/���� ����� ������� �ʴ´�.

## ���� ��� ���� ���� ����

���� ������ `2026-11-04_completion_matrix.json`�� �� 190�� ��� ���� tree �˻� ������ref/SHA���ٰ� URL�� �����Ѵ�. ���� �˻�� ���� ��α� 62��, AUD20��, �μ�24��, V����26���� ���� ID ������ �����ߴ�. �ٸ� ������ ������ ID �ߺ��� Ȯ���ߴ�. �� ���Ἲ ������ �䱸������ ���� �Ϸ� �˻簡 �ƴϴ�.

[BACKLOG]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/backlog_2026-11-03.md
[INDEX]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/backlog_source_index_2026-11-03.md
[REVIEW]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/deliveries/2026-11-03_review.md
[CARDS]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/experiment_cards_2026-11-03.md
[EXPLAIN]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/research_explanation_2026-11-03.md
[G3]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/reproducibility/g3_dr3_fr5_researcher_update_2026-10-28.md
[LINEAGE]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/reproducibility/prod_v2_source_lineage_correction_2026-10-26.md
[RECOVERY]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/RECOVERY_TARGETS.md
[DICT]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/data_dictionary.md
[G4STATE]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/g4_actual/g4_progress_state.md
[G4REPORT]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/g4_actual/g4_final_report.md
[G4REVIEW]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/g4_actual/g4_independent_review.md
[G4TEST]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/g4_actual/g4_test_results.md
[ROADMAP]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/research_roadmap_2026-11-02.md
[UI]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/hand_selection_and_overlay_ui_proposal_v0.1_2026-11-02.md
[FOLLOWUP]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/followup_experiments.md
[SCORE]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/scoring_standardization_v0.3.md
[VALIDATION]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/practical_validation_requirements_v0.3.md
[POOL]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/video_pool_occlusion_delivery_requirements_v0.4.md
[THREED]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/3d_hand_object_challenge_requirements_v0.1.md
[CLAIM]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/claim_evidence_matrix.md
[REPRO]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/reproduction.md
[OVERLAP]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/reproducibility/g4_human_attack_pool_overlap_2026-10-26.md
[COMPARE]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/validation_v03/compare_scores.py
[METRICS]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/validation_v03/standard_metrics.py
[CTEST]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/tests/test_compare_scores.py
[SERVER]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/g4_lab/server.py
[SEL]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/selection.js
[DEMO]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/demo.js
[HTML]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/index.html
[NTEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/selection.test.cjs
[DEMOTEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/demo.test.cjs
[H6]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage6_occlusion.py
[H7]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage7_gate.py
[HTEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/tests/test_mask_delivery.py
[HINTEGRITY]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/tests/test_mask_integrity.py
[HGATETEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/tests/test_stage7_gate.py
[PIPE]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/pipeline.py
[PROD]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/hand_captcha_prod.html
[MANIFEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/pool_manifest.json
[LEGACYMASK]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/handtest1.py
[CONFIG]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/config.py
[WEIGHTS]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage5_weights.py
[EXTRACT]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage1_extract.py
[QUALITY]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage2_quality.py
[STAGE4]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage4_length_norm.py
[INGEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/ingest_experiment_folders.py
[BAKE]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_expansion_bake_v1.py
[GEN]: https://github.com/mukgore/codex/blob/b8c39d5b4453865e1eca1106976406447b588a3a/docs/hand_motion_source_and_generation_research_v0.1.md
[ARCH]: https://github.com/mukgore/codex/blob/e4e918b606f3b0626a54cae96c78743924062ab7/docs/captcha_architecture_and_repo_audit_2026-10-26.md
