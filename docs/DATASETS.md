# Dataset Registry and Licensing Review

Last verified: **2026-07-14**

OpenInspect OS treats **downloadable**, **openly licensed**, and **safe to redistribute in this repository** as separate questions. The default demo uses only project-owned generated media. External archives are never downloaded implicitly by `make demo`.

## Selection summary

| Dataset | Role | Licence status | Included in repository |
|---|---|---|---|
| OpenInspect OS Project-Owned Demo v0.1.0 | Default structural, sequential pipeline, sonar and navigation validation | CC BY 4.0 | Yes |
| SDNET2018 | Optional concrete crack classification corpus | CC BY 4.0, verified on official Utah State University record | No; adapter only |
| SubPipe v3.0.0 | Optional real RGB, side-scan sonar and navigation inspection corpus | Dataset record is CC BY 4.0; repository code is GPL-3.0; required OceanScan-MST attribution applies | No; adapter only |
| SUIM | Underwater segmentation research reference | Terms must be rechecked at use time | No |
| CADDY Underwater Stereo Dataset | Underwater stereo/navigation research reference | Host terms must be accepted and rechecked | No |

---

## 1. OpenInspect OS Project-Owned Demo v0.1.0

- **Official site:** this repository, `datasets/project-owned/`
- **Download URL:** generated locally with `python scripts/generate_demo_data.py`
- **Repository URL:** the OpenInspect OS repository containing this file
- **Paper URL:** not applicable
- **Sensor types:** generated structural RGB, sequential underwater-style RGB, simulated one-dimensional sonar returns, timestamped latitude/longitude/depth/heading navigation
- **Number of images:** 20 source RGB images (8 structural, 12 pipeline)
- **Number of frames:** 12 ordered pipeline frames
- **Number of sequences:** one underwater pipeline sequence plus one structural still-image set
- **Other records:** 24 sonar timestamp records and 24 navigation records
- **Annotation format:** binary PNG masks; JSON manifest; timestamped CSV for sonar and navigation
- **Classes:** background, simulated crack/surface discontinuity, pipeline-visible region; sonar rows contain simulated candidate returns rather than corrosion labels
- **Licence:** Creative Commons Attribution 4.0 International for generated data; Apache-2.0 for generator code
- **Commercial restrictions:** none beyond CC BY 4.0 attribution
- **Redistribution rules:** redistribution and adaptation are allowed with attribution and an indication of changes
- **Attribution:** “OpenInspect OS Project-Owned Demo Dataset v0.1.0”
- **Download size:** generated output is approximately 17 MB before reports and database artifacts; exact size depends on codec versions
- **Preparation steps:** `make demo`, or run `scripts/generate_demo_data.py` followed by `ml/evaluation/evaluate_demo.py`
- **How it is used:** default CI/demo input; mask evaluation; measurement tests; timeline, trajectory and coverage processing; evidence/report generation
- **May appear in screenshots or GIFs:** yes, with attribution
- **May derived data be redistributed:** yes, under compatible attribution terms
- **Known limitations:** deliberately small, synthetic and visually controlled; not representative of field prevalence, substrate diversity, marine growth, turbidity, sensor noise or operator behavior
- **Data-quality concerns:** synthetic masks are exact by construction, which makes software regression measurable but can overstate algorithm behavior compared with uncontrolled inspections

The dataset card is at [`datasets/project-owned/DATASET_CARD.md`](../datasets/project-owned/DATASET_CARD.md).

---

## 2. SDNET2018

- **Dataset name:** SDNET2018: A concrete crack image dataset for machine learning applications
- **Official site:** https://digitalcommons.usu.edu/all_datasets/48/
- **Download URL:** https://digitalcommons.usu.edu/cgi/viewcontent.cgi?article=1047&context=all_datasets&filename=2&type=additional
- **Repository URL:** no official code repository is required for the archive
- **Paper URL:** https://doi.org/10.1016/j.conbuildmat.2018.08.011
- **Dataset DOI:** https://doi.org/10.15142/T3TD19
- **Publisher:** Utah State University
- **Sensor types:** RGB images from a 16 MP Nikon camera
- **Number of source photographs:** 230 concrete-surface photographs
- **Number of images:** more than 56,000 cropped 256 x 256 JPEG images
- **Number of frames/sequences:** not a temporal dataset; no ordered inspection sequences are claimed
- **Annotation format:** folder/file-level image classification (`C` cracked, `U` uncracked)
- **Classes:** cracked and uncracked, covering bridge decks, walls and pavements
- **Licence:** Creative Commons Attribution 4.0 International, stated on the official record
- **Commercial restrictions:** CC BY 4.0 permits commercial reuse with attribution
- **Redistribution rules:** allowed under CC BY 4.0; preserve citation, licence and change notices
- **Attribution:** Maguire, Dorafshan and Thomas (2018), Utah State University, DOI 10.15142/T3TD19
- **Download size:** 515,903 kB on the official record
- **Published checksum:** `677411e784f194422c90f52d9ed0d7c6` (32-character checksum as published by the host; verify the host documentation before assuming an algorithm)
- **Preparation steps:** user downloads the archive, verifies it, extracts it outside Git, then runs `datasets/adapters/sdnet2018.py`
- **How it is used:** optional crack/non-crack classification experiments and failure-case analysis; it is **not** treated as pixel-level crack segmentation ground truth
- **May appear in screenshots or GIFs:** yes under CC BY 4.0 with attribution, but OpenInspect OS does not bundle such screenshots by default
- **May derived data be redistributed:** yes under the licence, with attribution and change notices
- **Known limitations:** image-level labels only; no mission timestamps, calibration, GPS, asset hierarchy or segmentation masks
- **Data-quality concerns:** patch-level labels can include complex background artifacts and do not prove physical crack width; class balance and source-scene leakage must be controlled when splitting data

---

## 3. SubPipe v3.0.0

- **Dataset name:** SubPipe: A Submarine Pipeline Inspection Dataset for Segmentation and Visual-inertial Localization
- **Official site:** https://zenodo.org/records/10808161
- **Full download URL:** https://zenodo.org/records/10808161/files/SubPipe.zip?download=1
- **Mini RGB/segmentation download URL:** https://zenodo.org/records/10808161/files/SubPipeMini.zip?download=1
- **Mini sonar download URL:** https://zenodo.org/records/10808161/files/SubPipeMini2.zip?download=1
- **Repository URL:** https://github.com/remaro-network/SubPipe-dataset
- **Paper URL:** https://arxiv.org/abs/2401.17907
- **Dataset DOI:** https://doi.org/10.5281/zenodo.10808161
- **Publisher:** Zenodo; data acquired by OceanScan-MST within the H2020 REMARO project
- **Sensor types:** two cameras, side-scan sonar, inertial/navigation state, depth, altitude, pressure, angular velocity, acceleration, RPM, temperature and water velocity
- **Number of sequences:** five chunks in the published structure
- **RGB frame count:** the official record describes full and mini archives but does not publish one consolidated RGB-frame total; adapters must calculate it locally rather than inventing a number
- **Sonar images:** 5,000 low-frequency plus 5,030 high-frequency images (10,030 total)
- **Sonar annotations:** 3,163 low-frequency plus 3,172 high-frequency object annotations (6,335 total)
- **Annotation format:** RGB semantic-segmentation label images; sonar COCO JSON and YOLO text bounding boxes; timestamped sensor/navigation CSV files
- **Classes:** pipeline segmentation/detection and background as defined by the supplied annotations; no general corrosion-label claim is made
- **Dataset licence:** Creative Commons Attribution 4.0 International on the Zenodo dataset record
- **Repository-code licence:** GPL-3.0 on the GitHub repository; this is distinct from the dataset record's CC BY 4.0 licence
- **Commercial restrictions:** CC BY 4.0 permits commercial reuse with attribution; downstream users must separately respect GPL-3.0 when copying repository code
- **Redistribution rules:** dataset redistribution is allowed by CC BY 4.0 with attribution; OpenInspect OS nevertheless keeps the 38.7 GB archive user-supplied to avoid repository bloat and accidental omission of source notices
- **Required attribution text:** preserve the official statement that SubPipe is a public submarine-outfall-pipeline dataset, property of OceanScan-MST, acquired with a Light Autonomous Underwater Vehicle within Challenge Camp 1 of H2020 REMARO
- **Archive sizes:** full 27.8 GB (`~80 GB` extracted); Mini 5.9 GB (`~12 GB` extracted); Mini2 4.9 GB (`~16 GB` extracted)
- **Published MD5 values:** full `abf70702276c69c04c8774c7832f8550`; Mini `8c63dac2e37dea0bbfda13fa6602b264`; Mini2 `7e0d925f93a89bc0e8715e4f6f7caecb`
- **Preparation steps:** user downloads one archive, validates the published MD5, extracts it outside Git, preserves attribution/licence files and runs `datasets/adapters/subpipe.py`
- **How it is used:** optional real pipeline RGB segmentation, sonar detection, timestamp association, trajectory and SLAM/localization research
- **May appear in screenshots or GIFs:** yes under CC BY 4.0 with the required attribution; no third-party frames are bundled in the default release
- **May derived data be redistributed:** yes under CC BY 4.0 with attribution and indication of changes
- **Known limitations:** one real submarine outfall context cannot establish broad offshore generalization; pipeline presence labels are not corrosion labels
- **Data-quality concerns:** cross-sensor clocks, annotation density, water visibility, sand occlusion and chunk-level train/test leakage require explicit handling

---

## 4. SUIM - candidate/reference only

- **Official/repository URL:** https://github.com/xahidbuffon/SUIM
- **Paper URL:** https://arxiv.org/abs/2004.01241
- **Sensor types:** underwater RGB
- **Published scale:** more than 1,500 images
- **Annotation format/classes:** semantic masks with eight underwater object classes
- **Licence and redistribution:** must be confirmed from the exact repository revision and downloaded package before use; OpenInspect OS does not treat availability as permission
- **How it is used:** research reference for underwater enhancement and semantic-segmentation failure modes, not as a pipeline-defect corpus
- **Screenshots/derived redistribution:** disabled by default until terms are recorded in a locked manifest
- **Known limitation:** classes are not tailored to pipeline integrity or corrosion severity

---

## 5. CADDY Underwater Stereo Dataset - candidate/reference only

- **Official site:** https://caddy-underwater-datasets.ge.issia.cnr.it/
- **Sensor types:** underwater stereo imagery with navigation/IMU-linked records depending on selected subset
- **Annotations:** diver gesture, pose and tracking tasks depending on package
- **Licence and redistribution:** host terms must be accepted and recorded before use; no files are redistributed by OpenInspect OS
- **How it is used:** localization, quality and synchronization research reference only
- **Screenshots/derived redistribution:** disabled by default until exact subset terms are verified
- **Known limitation:** not a pipeline-defect dataset

## Reproducible preparation policy

1. External downloads are opt-in and never part of `make demo`.
2. Each adapter receives a user-controlled source directory and emits a local manifest.
3. Original licence, citation and checksum files must be retained.
4. Train/validation/test splits must be stored in the manifest, not inferred dynamically.
5. Screenshot eligibility is a manifest field and defaults to `false` for unreviewed datasets.
6. Unclear terms mean no redistribution and no mandatory dependency.
