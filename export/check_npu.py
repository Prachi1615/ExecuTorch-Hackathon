"""Compare the NPU's DINOv2 output against the CPU reference saved at export time.

Run inside the export folder after running qnn_executor_runner there:
  python check_npu.py
"""
import numpy as np

npu = np.fromfile("outputs/output_0_0.raw", dtype=np.float32)
cpu = np.load("cpu_reference.npy").ravel()
print("sizes", npu.size, cpu.size)
print("similarity", float(npu @ cpu / (np.linalg.norm(npu) * np.linalg.norm(cpu))))
