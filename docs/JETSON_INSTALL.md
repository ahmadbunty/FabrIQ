# FabrIQ on Jetson Nano (same-day setup)

## Why “Option A” still failed

Usually one of these:

1. **Conda was not active** — `python` was still **3.6.9** from the system. Pip then fails on modern packages.
2. **`opencv-python`** has no matching wheel for your combo — use **`opencv-python-headless`** first (see below).

## Step 0 — Confirm Python is NOT 3.6

After Miniforge install and **every new terminal**:

```bash
source ~/miniforge3/etc/profile.d/conda.sh
# If you installed Mambaforge instead:
# source ~/mambaforge3/etc/profile.d/conda.sh

conda activate fabriq
which python
python -V
```

You must see **Python 3.10.x** (or 3.9+) and a path under `miniforge3` / `mambaforge3`.

If you still see **3.6.9**, conda is not active — fix that before any `pip install`.

---

## Step 1 — Core API (no OpenCV / no Ultralytics)

Always use **`python -m pip`** (never bare `pip`):

```bash
conda activate fabriq
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-jetson-core.txt
```

If this fails, paste the **full error** (first 30 lines).

---

## Step 2 — PyTorch on Jetson (required before Ultralytics)

Ultralytics needs **PyTorch** built for **Jetson / L4T**.

1. Open: [PyTorch for Jetson (platform wheel)](https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048)  
   or NVIDIA docs for your **JetPack** version.

2. Install the **`.whl`** they give for your **JetPack + Python version** (must match `python -V` from conda).

Example pattern (your URL/filename will differ):

```bash
conda activate fabriq
python -m pip install /path/to/torch-*.whl
# torchvision wheel if provided, same way
```

3. Quick check:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

---

## Step 3 — OpenCV + Ultralytics

```bash
conda activate fabriq
python -m pip install -r requirements-jetson-ml.txt
```

We use **`opencv-python-headless`** because full **`opencv-python`** often breaks on Jetson pip.

If Ultralytics fails, try:

```bash
python -m pip install ultralytics --no-deps
python -m pip install matplotlib pyyaml tqdm requests scipy psutil py-cpuinfo pandas seaborn
```

---

## Step 4 — Run FabrIQ

```bash
export FABRIQ_MODEL_PATH=/path/to/better.pt
cd ~/FabrIQ/backend
conda activate fabriq
python app.py
```

---

## One-page checklist

| Check | Command |
|--------|---------|
| Not system 3.6 | `python -V` → 3.9+ |
| Correct pip | `python -m pip -V` |
| Core deps | `pip install -r requirements-jetson-core.txt` |
| Torch | NVIDIA wheel for your JetPack |
| ML deps | `pip install -r requirements-jetson-ml.txt` |

---

## If you have no time for PyTorch wheels today

Run **only** the API shell (no YOLO) is not enough for `app.py` (it imports ultralytics). Minimum for “today” is: **conda Python 3.10 + core txt + torch wheel + ml txt**.
