# AutoForensic AI: Project State & Agent Context
**Target Audience:** AI Coding Agent / Development Assistant
**Project:** AutoForensic AI - Automated Vehicle Damage Assessment & Cyber Forensics Pipeline

## 1. Project Overview
AutoForensic AI is a full-stack InsurTech platform designed to automate vehicle damage preliminary assessment using Computer Vision (Instance Segmentation) while combating insurance fraud through rigorous digital forensics (image manipulation detection). 

## 2. Core Architecture & Tech Stack
* **Computer Vision:** PyTorch, Ultralytics YOLOv8-Seg (Damage Segmentation), MiDaS (Depth/Indentation Estimation).
* **Cyber Forensics Pipeline:** Magic-byte validation, Image re-encoding, Error Level Analysis (ELA), Perceptual Hashing (pHash).
* **Backend API:** FastAPI (Python), Celery, Redis.
* **Database & Storage:** PostgreSQL (Relational), MinIO/S3 (Object Storage), SQLAlchemy.
* **Frontend:** Next.js, Three.js (for 3D visualization).

## 3. End-to-End Pipeline (Step-by-Step Flow)
1. **Intake & Cryptographic Forensics (Pre-processing):**
   * Receive `multipart/form-data` image via FastAPI.
   * Run magic-byte checks to prevent polyglot malware.
   * Re-encode image to strip hidden web-shells.
   * Perform Error Level Analysis (ELA) and EXIF extraction to verify image authenticity. Reject if tampered.
2. **Damage Detection (Vision Step 1):**
   * Pass verified image to YOLOv8-Seg.
   * Generate exact polygon masks for specific damage classes (dent, scratch, crack, glass_shatter, lamp_broken, tire_flat).
3. **Severity & Depth Analysis (Vision Step 2):**
   * Isolate masked damage areas and pass to MiDaS.
   * Calculate physical indentation depth ($\Delta z$). 
   * Trigger safety threshold rules (e.g., if $\Delta z > 3.5$ cm, flag for manual review).
4. **Cost Estimation & Ledger:**
   * Calculate repair cost based on class-specific formulas (e.g., area of scratch vs. flat replacement of lamp).
   * Package dimensions, class, and cost into JSON payload.
   * Generate SHA-256 hash of the transaction and store immutably in PostgreSQL.

## 4. Completed Progress (State as of Current)
* **Architecture & Scoping:** Complete. The system requirements, full-stack pipeline, and security thresholds are fully mapped out.
* **Local Environment Setup:** Working directory initialized at `D:\EDAI 07\`. 
* **Dataset Acquisition & Conversion:**
   * **Source Dataset:** CarDD (Car Damage Detection).
   * **Transformation:** Successfully converted annotations from standard COCO JSON format into YOLOv8 Segmentation format (normalized polygon coordinates).
* **New Dataset Structure (Completed):**
   * Organized into strict YOLO format inside `CarDD_YOLO_Format/`.
   * Parallel folder structure achieved:
     * `images/train2017/`, `images/val2017/`, `images/test2017/`
     * `labels/train2017/`, `labels/val2017/`, `labels/test2017/`
* **Configuration Validation:** 
   * `data.yaml` successfully created, correctly mapping the 6 target classes.
   * Absolute pathing configured correctly (pointing to `D:/EDAI 07/CarDD_YOLO_Format`).
   * **Sanity Check Passed:** A 1-epoch dry-run on CPU was executed. The dataset loaded correctly without missing path errors, and loss functions successfully initialized.

## 5. Excluded Phase (To Be Done Later)
* **Model Training:** The full 60-100 epoch YOLOv8-Seg training phase is currently paused. It will be executed later on a CUDA-enabled GPU (e.g., Google Colab) to avoid extensive CPU training times.

## 6. Next Immediate Tasks for AI Agent
1. Scaffold the **FastAPI** backend structure (routes, schemas, models).
2. Implement the **Cyber Forensics module** (Magic-byte checker, Image re-encoding using Pillow, OpenCV script for ELA).
3. Set up the database models using **SQLAlchemy** for storing the cryptographic audit ledger (SHA-256).
4. Create the downstream **Cost Estimation logic** that will eventually ingest the output from the (future) trained YOLO model.
