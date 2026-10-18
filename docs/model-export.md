# Exporting DINOv2 for the NPU

The checkout's `examples/qualcomm/oss_scripts/dino_v2.py` exports `facebook/dinov2-small-imagenet1k-1-layer`, which includes an ImageNet classifier (1,000 scores out) and needs an ImageNet dataset for calibration. For teaching new objects we want **features** instead, so [`export/dino_features.py`](../export/dino_features.py) is an adapted copy that:

- exports `facebook/dinov2-small` **without the classifier**, returning the 384-number pooled CLS feature
- **calibrates on images from your own webcam** (no ImageNet download, and quantization matched to your camera and room)
- saves one test input plus the CPU model's output for that input, so the NPU result can be checked

## 1. Capture calibration images

About 50 varied webcam frames: the desk, people, objects held up, different angles.

```bash
scripts/capture_calib.sh ~/robo/calib 50
```

## 2. Export

```bash
cp export/dino_features.py ~/git/executorch/examples/qualcomm/oss_scripts/
source scripts/qnn_env.sh
cd ~/git/executorch
python -m examples.qualcomm.oss_scripts.dino_features \
  --soc_model QCS8275 --build_folder build-x86 --compile_only \
  --calib ~/robo/calib -a <this repo>/dino16 --quant 16a8w
```

The first run downloads the model from Hugging Face (~88 MB). Calibration and the NPU compile take several minutes on the board. Output:

| File | What |
|---|---|
| `dino_features.pte` | the model for the NPU (~23 MB at 8a8w) |
| `input_0_0.raw`, `input_list.txt` | one preprocessed test image (588 KB = 3×224×224 float32) |
| `cpu_reference.npy` | the CPU model's output for that image |

`recognize.py` uses `dino16/` if it exists, otherwise `dino/`.

## 3. Check the NPU against the CPU

```bash
source scripts/qnn_env.sh
cd <this repo>/dino16
mkdir -p outputs
"$QNN_RUNNER" --model_path dino_features.pte --input_list_path input_list.txt --output_folder_path outputs
python ../export/check_npu.py
```

Expect `sizes 384 384`. Our results:

| Quantization | Cosine similarity to CPU | NPU time |
|---|---|---|
| `8a8w` (8-bit activations and weights) | 0.81 | ~5 ms |
| `16a8w` (16-bit activations, 8-bit weights) | used for the demo | ~5 ms |

8-bit activations hurt vision transformers like DINOv2 noticeably, so use `16a8w`.

## Notes

- The **preprocessing must match** between export and runtime: resize 256, center-crop 224, ImageNet mean/std. At runtime, `recognize.py` additionally zooms to the center 60% of the frame first. Calibration images go through the same resize and crop but not the zoom; it worked fine, and re-exporting with zoomed calibration images could tighten quantization further.
- Each export downloads from Hugging Face without a token; set `HF_TOKEN` to avoid rate limits.
- Exported models and calibration images are not in the repo (see `.gitignore`); re-export them on each board.
