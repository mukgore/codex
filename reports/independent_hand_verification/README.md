# Independent occluded-hand verification artifacts

This bundle contains the final report, per-backend frame predictions, aggregate metrics, A/B training report and checkpoints, resource probes, provenance, and five circular-mask preview videos. The source archive and extracted GigaHands videos and labels are not included; see `../../docs/reproducibility/realtime_occluded_hand_models.md` for setup and replay commands.

## GigaHands attribution and license

The five source sequences and derived masked previews are from the GigaHands demo dataset, released under **CC BY-NC 4.0**. The previews apply the study's fixed circular mask to every frame and are shared with attribution under the same non-commercial terms.

Rao Fu, Dingxi Zhang, Alex Jiang, Wanjia Fu, Austin Funk, Daniel Ritchie, and Srinath Sridhar. “GigaHands: A Massive Annotated Dataset of Bimanual Hand Activities.” *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)*, 2025, pp. 17461–17474. [Official project and dataset license](https://github.com/brown-ivl/GigaHands).

## Preview clips

The five MP4 files in `occlusion_previews/` are the masked videos. `index.json` records source names, frame counts, and hashes.
