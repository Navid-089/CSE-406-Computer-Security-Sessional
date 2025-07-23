# CSE‑406 Computer Security Sessional (Offline Labs)

> **Course:** BUET CSE‑406 — Computer Security Sessional\

This repository contains my solutions, reports and source code for the two **assignments** of CSE‑406.  Every offline is fully self‑contained so you can reproduce the experiments, run the code and read the accompanying write‑ups.

---

## Table of Contents

1. [Repository layout](#repository-layout)
2. [Quick start](#quick-start)
3. [Offline 1 – Cryptography](#offline-1--cryptography)
4. [Offline 2 – Side‑Channel Attack](#offline-2--side-channel-attack)
5. [Global requirements](#global-requirements)
6. [License](#license)

---

## Repository layout

```text
.
├── Offline 1 Cryptography/
│   ├── CSE406 - Assignment 1.pdf         ⟶ problem specification
│   ├── code/                            ⟶ Python sources for AES, ECDH & utilities
│   │   ├── 2005089_aes_defs.py          ⟶ AES implementation (CBC & CTR mode helpers)
│   │   ├── 2005089_ctr.py               ⟶ CLI wrapper for AES‑CTR encrypt / decrypt
│   │   ├── 2005089_ecdh_defs.py         ⟶ Elliptic‑Curve primitives
│   │   ├── 2005089_task‑1.py            ⟶ Task 1 driver (CBC encryption)
│   │   ├── 2005089_task‑2.py            ⟶ Task 2 driver (ECDH timing study)
│   │   └── …                            ⟶ auxiliary demo / helper scripts
│   ├── 2005089_image‑min.jpg            ⟶ sample plaintext image
│   └── output_2005089_image‑min.jpg     ⟶ ciphertext image (CBC or CTR encrypted)
│
└── Offline 2 Side Channel Attack/
    ├── specification.pdf                ⟶ assignment brief
    ├── report.pdf                       ⟶ write‑up & results
    ├── dataset_normalised_2005089.json  ⟶ pre‑processed timing traces
    └── code/
        ├── app.py                       ⟶ Flask demo server (live attack)
        ├── train.py                     ⟶ PyTorch model training pipeline
        ├── collect.py                   ⟶ Trace collector (JS + Selenium)
        ├── prediction_tester.py         ⟶ End‑to‑end evaluation script
        ├── index.{html,js}              ⟶ Web front‑end
        └── …                            ⟶ helpers (DB, normaliser, utils)
```

---

## Quick start

```bash
# 1 – Clone the repo
$ git clone https://github.com/Navid-089/CSE-406-Computer-Security-Sessional.git
$ cd CSE-406-Computer-Security-Sessional

# 2 – (Recommended) create a virtual environment
$ python3 -m venv .venv && source .venv/bin/activate

# 3 – Install common Python dependencies
$ pip install -r requirements.txt        # provided below; copy/paste if you prefer

# 4 – Run the desired offline
$ cd "Offline 1 Cryptography/code" && python 2005089_task-1.py
$ cd "Offline 2 Side Channel Attack/code" && python app.py
```

---

## Offline 1 – Cryptography

### Goals

1. **AES Encryption** – implement AES in both CBC and CTR mode to encrypt / decrypt data-block losslessly.
2. **Elliptic‑Curve Diffie–Hellman (ECDH)** – code low‑level EC point arithmetic and benchmark shared‑secret generation for key sizes 128, 192 and 256 bits.

### How to run

```bash
# inside Offline 1 Cryptography/code
pip install BitVector pycryptodome prettytable
python 2005089_task-1.py # CBC mode
python 2005089_ctr.py    # CTR mode
python 2005089_task-2.py # ECDH timing table
```


### 📄 Files of interest

| File                       | Purpose                                                       |
| -------------------------- | ------------------------------------------------------------- |
| **2005089\_aes\_defs.py**  | Minimal AES S‑box, key schedule & GF(2⁸) helpers              |
| **2005089\_ctr.py**        | Counter‑mode driver (handles IV, padding)                     |
| **2005089\_ecdh\_defs.py** | Finite‑field EC arithmetic (point add / double / scalar‑mult) |
| **2005089\_task‑1.py**     | Batch image encryption demo                                   |
| **2005089\_task‑2.py**     | Generates timing statistics for ECDH                          |

---

## Offline 2 – Side‑Channel Attack

### Goal

Implement and evaluate a **website‑fingerprinting attack** using client‑side timing traces as the side channel.

### Components

| Component                 | Description                                                                                          |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| **collect.py**            | Launches Chromium via Selenium, visits target sites, records fine‑grained timers & stores raw traces |
| **normaliser.py**         | Cleans & zero‑pads traces to a fixed length                                                          |
| **train.py**              | Trains a fully‑connected PyTorch network (`ComplexFingerprintClassifier`) on the normalised dataset  |
| **app.py**                | Flask API & static front‑end for real‑time prediction                                                |
| **prediction\_tester.py** | Runs the trained model against held‑out traces                                                       |
| **database.py**           | SQLite ORM (SQLAlchemy) storing traces + stats                                                       |

### How to run a live demo

```bash
# inside Offline 2 Side Channel Attack/code
pip install flask torch numpy scikit-learn pillow matplotlib tqdm sqlalchemy selenium webdriver-manager



python train.py          # train model → saved_models/model.pt
python app.py            # start Flask server on localhost:5000
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser and allow the client script to send timing traces. The backend predicts the visited site in real time and returns a JSON response with confidence scores.

---

## Global requirements

Below is a *unified* requirements list covering both offlines. Copy it to **requirements.txt** if you want a one‑shot install.

```txt
BitVector==3.6.0
pycryptodome>=3.18
prettytable>=3.5
flask>=3.0
numpy>=1.26
torch>=2.2
scikit-learn>=1.5
pillow>=10.4
matplotlib>=3.9
tqdm>=4.66
sqlalchemy>=2.0
selenium>=4.21
webdriver-manager>=4.0
requests>=2.32
```

*(Versions are indicative; feel free to relax or pin as per your environment.)*

---

## License

Unless stated otherwise in individual lab folders, all code is released under the **MIT License**.  See `LICENSE` for full text.

---

