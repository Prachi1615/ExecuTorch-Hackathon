"""Export DINOv2-small *features* (384-number fingerprint, no classifier) for the
Qualcomm HTP NPU with ExecuTorch, calibrated on your own camera images.

Copy into an ExecuTorch checkout at examples/qualcomm/oss_scripts/ and run:

  python -m examples.qualcomm.oss_scripts.dino_features \
    --soc_model QCS8275 --build_folder build-x86 --compile_only \
    --calib <folder of .jpg> -a <output folder> --quant 16a8w

Adapted from examples/qualcomm/oss_scripts/dino_v2.py.
"""
import glob
import os

import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from transformers import Dinov2Model

from executorch.backends.qualcomm._passes.qnn_pass_manager import get_qnn_pass_manager_cls
from executorch.backends.qualcomm.export_utils import (
    build_executorch_binary,
    QnnConfig,
    setup_common_args_and_variables,
)
from executorch.backends.qualcomm.quantizer.quantizer import QuantDtype

# Same preprocessing the robot uses at runtime (recognize.py also zooms to the
# center 60% of the frame before these steps)
PREPROCESS = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


class DinoFeatures(torch.nn.Module):
    """DINOv2-small backbone; returns one 384-number fingerprint per image."""

    def __init__(self):
        super().__init__()
        self.m = Dinov2Model.from_pretrained("facebook/dinov2-small")

    def forward(self, x):
        return self.m(pixel_values=x).pooler_output  # shape (1, 384)


def main(args):
    qnn_config = QnnConfig.load_config(args.config_file if args.config_file else args)
    os.makedirs(args.artifact, exist_ok=True)

    files = sorted(glob.glob(os.path.join(os.path.expanduser(args.calib), "*.jpg")))
    assert files, f"no .jpg files in {args.calib}"
    print(f"calibrating on {len(files)} images")
    inputs = [(PREPROCESS(Image.open(f).convert("RGB")).unsqueeze(0),) for f in files]

    model = DinoFeatures().eval()

    # Save a test input + CPU reference output, to check the NPU result later
    inputs[0][0].numpy().astype(np.float32).tofile(f"{args.artifact}/input_0_0.raw")
    with open(f"{args.artifact}/input_list.txt", "w") as fh:
        fh.write("input_0_0.raw\n")
    with torch.no_grad():
        np.save(f"{args.artifact}/cpu_reference.npy", model(inputs[0][0]).numpy())

    quant = {"8a8w": QuantDtype.use_8a8w, "16a8w": QuantDtype.use_16a8w}[args.quant]
    build_executorch_binary(
        model=model,
        qnn_config=qnn_config,
        file_name=f"{args.artifact}/dino_features",
        dataset=inputs,
        quant_dtype=quant,
        passes_job=get_qnn_pass_manager_cls().get_capture_program_passes(),
    )
    print(f"saved {args.artifact}/dino_features.pte")


if __name__ == "__main__":
    parser = setup_common_args_and_variables()
    parser.add_argument("-a", "--artifact", default="./dino_features", type=str)
    parser.add_argument("--calib", required=True, type=str, help="folder of .jpg calibration images")
    parser.add_argument("--quant", choices=["8a8w", "16a8w"], default="8a8w")
    main(parser.parse_args())
