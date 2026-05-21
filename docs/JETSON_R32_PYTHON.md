# Jetson Nano R32 + Python 3.6

Your board ships **Python 3.6.9** with JetPack **R32.x**. That affects FabrIQ like this:

## What works on Python 3.6

- **Flask API only**: use `backend/requirements-py36-jetson-r32.txt` (older Flask/Werkzeug pins).

## What does **not** work on Python 3.6

- **Ultralytics YOLOv8** requires **Python ≥ 3.8**. It will not install under 3.6.
- **Flask 3.x** requires **Python ≥ 3.8**.

So you have two paths:

---

### Path A — Recommended: Python 3.8+ on the Jetson

Then use normal `backend/requirements.txt` and full detection:

1. **Miniforge / Mambaforge** (aarch64): `conda create -n fabriq python=3.10 -y` then `conda activate fabriq` — see **[JETSON_INSTALL.md](JETSON_INSTALL.md)** if `pip install -r requirements.txt` still errors (split install, OpenCV headless, PyTorch wheel order).
2. **Build Python 3.10 from source** on the Nano (slow but common), or  
3. Use **Docker** with an ARM image that has Python 3.10+ and CUDA/L4T stack (`dustynv` containers are popular), or  
4. Move to hardware/OS that ships newer Python (some newer Jetsons / JetPack 5).

After `python --version` in your **conda or venv** shows **3.8 or newer**:

```bash
cd FabrIQ/backend
conda activate fabriq   # if using Miniforge
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

If that fails with the **same** error as on 3.6, you are likely still on **system** `python3` (3.6) or hitting **OpenCV** wheels — use **`requirements-jetson-core.txt`** then **`requirements-jetson-ml.txt`** as in [JETSON_INSTALL.md](JETSON_INSTALL.md).

Install **PyTorch for your L4T version** from NVIDIA / Jetson Zoo **behttps://github.com/kashifmayarfore** ultralytics if pip fails.

---

### Path B — Stay on Python 3.6 temporarily

```bash
pip install -r requirements-py36-jetson-r32.txt
```

You can **start Flask**, but **`python app.py` will fail** when importing **ultralytics / YOLO** until you upgrade Python or change the backend to a non-Ultralytics runtime (not included in this repo).

---

## Quick check

```bash
python3 --version
```

- **3.6.x** → Path A or B as above.  
- **3.8+** → use `requirements.txt` and install Jetson PyTorch if needed.
