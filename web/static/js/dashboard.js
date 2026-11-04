/**
 * AutoForensic — Enterprise Claims Verification Platform
 * Frontend Controller for Vehicle Object Multi-Damage Intake & Hash Registry
 */

document.addEventListener("DOMContentLoaded", () => {
    // ══════════════════════════════════════════════════════════════
    // STATE: ACTIVE VEHICLE CLAIM OBJECT
    // ══════════════════════════════════════════════════════════════
    let activeVehicleClaim = null;

    let currentSelectedFile = null;
    let registryRecordsCache = [];
    let currentModalPart = null;

    // ══════════════════════════════════════════════════════════════
    // DOM ELEMENTS: NAVIGATION & 4 ENTERPRISE VIEWS
    // ══════════════════════════════════════════════════════════════
    const tabNavClaims = document.getElementById("tabNavClaims");
    const tabNavAssessment = document.getElementById("tabNavAssessment");
    const navAssessmentCount = document.getElementById("navAssessmentCount");
    const tabNavRegistry = document.getElementById("tabNavRegistry");
    const tabNavAnalytics = document.getElementById("tabNavAnalytics");
    const tabNavPolicies = document.getElementById("tabNavPolicies");

    const viewClaims = document.getElementById("viewClaims");
    const viewAssessment = document.getElementById("viewAssessment");
    const viewRegistry = document.getElementById("viewRegistry");
    const viewAnalytics = document.getElementById("viewAnalytics");
    const viewPolicies = document.getElementById("viewPolicies");

    const btnNewClaim = document.getElementById("btnNewClaim");

    // Analytics Elements
    const analyticsFraudRate = document.getElementById("analyticsFraudRate");
    const analyticsAiCaught = document.getElementById("analyticsAiCaught");
    const analyticsDuplicates = document.getElementById("analyticsDuplicates");
    const analyticsLossAvoided = document.getElementById("analyticsLossAvoided");
    const btnRefreshAnalytics = document.getElementById("btnRefreshAnalytics");
    const analyticsVectorsContainer = document.getElementById("analyticsVectorsContainer");
    const analyticsLayerContainer = document.getElementById("analyticsLayerContainer");
    const analyticsRiskBody = document.getElementById("analyticsRiskBody");

    // Policy Elements
    const btnResetPolicies = document.getElementById("btnResetPolicies");
    const btnSavePolicies = document.getElementById("btnSavePolicies");
    const policyAlert = document.getElementById("policyAlert");
    const polLayer1 = document.getElementById("polLayer1");
    const polLayer2 = document.getElementById("polLayer2");
    const polLayer3 = document.getElementById("polLayer3");
    const polLayer4 = document.getElementById("polLayer4");
    const polLayer4Val = document.getElementById("polLayer4Val");
    const polLayer5 = document.getElementById("polLayer5");
    const polLayer5Val = document.getElementById("polLayer5Val");
    const polApproveFloor = document.getElementById("polApproveFloor");
    const polApproveFloorVal = document.getElementById("polApproveFloorVal");
    const polReviewFloor = document.getElementById("polReviewFloor");
    const polReviewFloorVal = document.getElementById("polReviewFloorVal");
    const polAlerts = document.getElementById("polAlerts");


    // Step Views
    const stepRegistration = document.getElementById("stepRegistration");
    const stepForensic = document.getElementById("stepForensic");

    // Registration Form Elements
    const custNameInput = document.getElementById("custName");
    const policyNoInput = document.getElementById("policyNo");
    const custContactInput = document.getElementById("custContact");
    const vehRegInput = document.getElementById("vehReg");
    const vehModelInput = document.getElementById("vehModel");
    const vehYearInput = document.getElementById("vehYear");
    const btnRegisterClaim = document.getElementById("btnRegisterClaim");
    const btnBackToRegister = document.getElementById("btnBackToRegister");
    const btnRefreshClaimsHistory = document.getElementById("btnRefreshClaimsHistory");
    const claimsHistoryBody = document.getElementById("claimsHistoryBody");
    const claimsHistoryCount = document.getElementById("claimsHistoryCount");

    // Vehicle Summary Header Bar
    const vehObjName = document.getElementById("vehObjName");
    const vehObjPlate = document.getElementById("vehObjPlate");
    const vehObjPolicy = document.getElementById("vehObjPolicy");
    const badgeVerifiedPartsCount = document.getElementById("badgeVerifiedPartsCount");
    const badgeTotalCost = document.getElementById("badgeTotalCost");
    const btnExportClaimJSON = document.getElementById("btnExportClaimJSON");

    // Damage Uploader Elements
    const selDamagePart = document.getElementById("selDamagePart");
    const selDamageType = document.getElementById("selDamageType");
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const btnBrowse = document.getElementById("btnBrowse");
    const dropZonePrompt = document.getElementById("dropZonePrompt");
    const dropZonePreview = document.getElementById("dropZonePreview");
    const previewImg = document.getElementById("previewImg");
    const previewName = document.getElementById("previewName");
    const btnRemoveFile = document.getElementById("btnRemoveFile");
    const btnVerifyAndAddPart = document.getElementById("btnVerifyAndAddPart");

    // Loading & Alerts
    const loadingState = document.getElementById("loadingState");
    const loadingStep = document.getElementById("loadingStep");
    const gatekeeperAlert = document.getElementById("gatekeeperAlert");

    // Verified & Rejected Display Containers
    const emptyPartsState = document.getElementById("emptyPartsState");
    const verifiedPartsGrid = document.getElementById("verifiedPartsGrid");
    const verifiedPartsListCount = document.getElementById("verifiedPartsListCount");
    const vehicleCostCard = document.getElementById("vehicleCostCard");
    const vehicleCostTableBody = document.getElementById("vehicleCostTableBody");
    const vehCostSubtotal = document.getElementById("vehCostSubtotal");
    const vehCostGST = document.getElementById("vehCostGST");
    const vehCostGrandTotal = document.getElementById("vehCostGrandTotal");

    const rejectedPartsCard = document.getElementById("rejectedPartsCard");
    const rejectedPartsList = document.getElementById("rejectedPartsList");
    const rejectedPartsListCount = document.getElementById("rejectedPartsListCount");

    // Registry Tab Elements
    const regStatTotal = document.getElementById("regStatTotal");
    const regStatAuthentic = document.getElementById("regStatAuthentic");
    const regStatDuplicates = document.getElementById("regStatDuplicates");
    const regStatReviews = document.getElementById("regStatReviews");
    const btnRefreshRegistry = document.getElementById("btnRefreshRegistry");
    const btnClearAllRegistry = document.getElementById("btnClearAllRegistry");
    const registryTableBody = document.getElementById("registryTableBody");
    const regTableCount = document.getElementById("regTableCount");
    const tableSearchInput = document.getElementById("tableSearchInput");
    const filterBtns = document.querySelectorAll(".filter-btn");

    // Registry Duplicate Checker Tool
    const registryDropZone = document.getElementById("registryDropZone");
    const regFileInput = document.getElementById("regFileInput");
    const btnRegBrowse = document.getElementById("btnRegBrowse");
    const regDropPrompt = document.getElementById("regDropPrompt");
    const regDropPreview = document.getElementById("regDropPreview");
    const regPreviewImg = document.getElementById("regPreviewImg");
    const regPreviewName = document.getElementById("regPreviewName");
    const btnRemoveRegFile = document.getElementById("btnRemoveRegFile");
    const regQueryInput = document.getElementById("regQueryInput");
    const btnRunRegistryCheck = document.getElementById("btnRunRegistryCheck");
    const lookupResultBox = document.getElementById("lookupResultBox");
    let regSelectedFile = null;

    // Diagnostics Modal Elements
    const diagnosticsModal = document.getElementById("diagnosticsModal");
    const btnModalClose = document.getElementById("btnModalClose");
    const modalPartTitle = document.getElementById("modalPartTitle");
    const modalPartMeta = document.getElementById("modalPartMeta");
    const modalImgOrig = document.getElementById("modalImgOrig");
    const modalImgELA = document.getElementById("modalImgELA");
    const modalImgAI = document.getElementById("modalImgAI");
    const modalImgComp = document.getElementById("modalImgComp");
    const modalPHash = document.getElementById("modalPHash");
    const modalSHA256 = document.getElementById("modalSHA256");
    const modalTabBtns = document.querySelectorAll(".modal-tab-btn");

    // Phase 1 -> Phase 2 Transition Elements
    const nextPhaseBanner = document.getElementById("nextPhaseBanner");
    const verifiedMediaCount = document.getElementById("verifiedMediaCount");
    const btnGoToAssessment = document.getElementById("btnGoToAssessment");
    const btnBackToClaimsIntake = document.getElementById("btnBackToClaimsIntake");
    const btnGoBackToIntakeLink = document.getElementById("btnGoBackToIntakeLink");

    // Assessment View Elements
    const assessVehReg = document.getElementById("assessVehReg");
    const assessVehModel = document.getElementById("assessVehModel");
    const assessClaimId = document.getElementById("assessClaimId");
    const assessCustomerName = document.getElementById("assessCustomerName");
    const assessVerifiedCount = document.getElementById("assessVerifiedCount");
    const assessNetRepairs = document.getElementById("assessNetRepairs");
    const assessGrandTotal = document.getElementById("assessGrandTotal");
    const assessPartsCount = document.getElementById("assessPartsCount");
    const assessLoadingState = document.getElementById("assessLoadingState");
    const assessLoadingStep = document.getElementById("assessLoadingStep");
    const emptyAssessmentState = document.getElementById("emptyAssessmentState");
    const assessmentPartsGrid = document.getElementById("assessmentPartsGrid");
    const btnRunAllAssessment = document.getElementById("btnRunAllAssessment");

    // Manual Cost Modal Elements
    const manualCostModal = document.getElementById("manualCostModal");
    const btnManualCostClose = document.getElementById("btnManualCostClose");
    const btnCancelManualCost = document.getElementById("btnCancelManualCost");
    const btnSaveManualCost = document.getElementById("btnSaveManualCost");
    const manualCostPartTitle = document.getElementById("manualCostPartTitle");
    const manualCostPartMeta = document.getElementById("manualCostPartMeta");
    const manualCostImgPreview = document.getElementById("manualCostImgPreview");
    const manualPartId = document.getElementById("manualPartId");
    const manualDamageType = document.getElementById("manualDamageType");
    const manualActionText = document.getElementById("manualActionText");
    const manualPartsCost = document.getElementById("manualPartsCost");
    const manualLaborHours = document.getElementById("manualLaborHours");
    const manualLaborCost = document.getElementById("manualLaborCost");
    const manualNotes = document.getElementById("manualNotes");

    // ─────────────────────────────────────────────────────────────
    // 1. INITIALIZATION & 5-TAB SWITCHING CONTROLLER
    // ─────────────────────────────────────────────────────────────

    fetchSystemStats();
    loadRegistryRecords();
    loadClaimsHistory();
    loadPolicies();
    loadAnalytics();

    // Tab Navigation Event Handlers
    if (tabNavClaims) {
        tabNavClaims.addEventListener("click", (e) => {
            e.preventDefault();
            switchTab("claims");
        });
    }

    if (tabNavAssessment) {
        tabNavAssessment.addEventListener("click", (e) => {
            e.preventDefault();
            switchTab("assessment");
        });
    }

    if (tabNavRegistry) {
        tabNavRegistry.addEventListener("click", (e) => {
            e.preventDefault();
            switchTab("registry");
        });
    }

    if (tabNavAnalytics) {
        tabNavAnalytics.addEventListener("click", (e) => {
            e.preventDefault();
            switchTab("analytics");
        });
    }

    if (tabNavPolicies) {
        tabNavPolicies.addEventListener("click", (e) => {
            e.preventDefault();
            switchTab("policies");
        });
    }

    // Step 1 -> Step 2 button triggers
    if (btnGoToAssessment) {
        btnGoToAssessment.addEventListener("click", () => switchTab("assessment"));
    }
    if (btnBackToClaimsIntake) {
        btnBackToClaimsIntake.addEventListener("click", () => switchTab("claims"));
    }
    if (btnGoBackToIntakeLink) {
        btnGoBackToIntakeLink.addEventListener("click", () => switchTab("claims"));
    }

    function switchTab(target) {
        // Deactivate all nav links
        [tabNavClaims, tabNavAssessment, tabNavRegistry, tabNavAnalytics, tabNavPolicies].forEach(tab => {
            if (tab) tab.classList.remove("active");
        });

        // Hide all page views
        [viewClaims, viewAssessment, viewRegistry, viewAnalytics, viewPolicies].forEach(v => {
            if (v) v.style.display = "none";
        });

        if (target === "assessment") {
            if (tabNavAssessment) tabNavAssessment.classList.add("active");
            if (viewAssessment) viewAssessment.style.display = "block";
            window.location.hash = "assessment";
            renderAssessmentView();
        } else if (target === "registry") {
            if (tabNavRegistry) tabNavRegistry.classList.add("active");
            if (viewRegistry) viewRegistry.style.display = "block";
            window.location.hash = "registry";
            loadRegistryRecords();
        } else if (target === "analytics") {
            if (tabNavAnalytics) tabNavAnalytics.classList.add("active");
            if (viewAnalytics) viewAnalytics.style.display = "block";
            window.location.hash = "analytics";
            loadAnalytics();
        } else if (target === "policies") {
            if (tabNavPolicies) tabNavPolicies.classList.add("active");
            if (viewPolicies) viewPolicies.style.display = "block";
            window.location.hash = "policies";
            loadPolicies();
        } else {
            // Default: Claims Intake
            if (tabNavClaims) tabNavClaims.classList.add("active");
            if (viewClaims) viewClaims.style.display = "block";
            window.location.hash = "claims";
        }
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    // Check URL hash on initial page load
    const currentHash = (window.location.hash || "").replace("#", "");
    if (["assessment", "registry", "analytics", "policies"].includes(currentHash)) {
        switchTab(currentHash);
    } else {
        switchTab("claims");
    }

    btnNewClaim.addEventListener("click", () => {
        switchTab("claims");
        showRegistrationStep();
    });

    // ─────────────────────────────────────────────────────────────
    // 2. TWO-STEP FLOW: REGISTRATION → FORENSIC WORKSPACE
    // ─────────────────────────────────────────────────────────────

    function showRegistrationStep() {
        stepRegistration.style.display = "block";
        stepForensic.style.display = "none";
        // Clear form for new entry
        custNameInput.value = "";
        policyNoInput.value = "";
        custContactInput.value = "";
        vehRegInput.value = "";
        vehModelInput.value = "";
        vehYearInput.value = "";
        activeVehicleClaim = null;
        loadClaimsHistory();
    }

    function showForensicStep() {
        stepRegistration.style.display = "none";
        stepForensic.style.display = "block";
        updateVehicleHeaderUI();
        renderVerifiedParts();
        renderVehicleCostTable();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    // Register & Start Claim Button
    btnRegisterClaim.addEventListener("click", async () => {
        const name = custNameInput.value.trim();
        const policy = policyNoInput.value.trim();
        const vehReg = vehRegInput.value.trim();
        const vehModel = vehModelInput.value.trim();

        let hasError = false;
        [
            { el: custNameInput, val: name },
            { el: policyNoInput, val: policy },
            { el: vehRegInput, val: vehReg },
            { el: vehModelInput, val: vehModel },
        ].forEach(({ el, val }) => {
            if (!val) {
                el.style.borderColor = "var(--danger)";
                hasError = true;
            } else {
                el.style.borderColor = "";
            }
        });

        if (hasError) {
            alert("Please fill in all required fields: Customer Name, Policy Number, Vehicle Registration, and Vehicle Model.");
            return;
        }

        const payload = {
            customer_name: name,
            policy_no: policy,
            contact: custContactInput.value.trim() || "N/A",
            vehicle_reg: vehReg.toUpperCase(),
            vehicle_model: vehModel,
            model_year: vehYearInput.value.trim() || "2023",
        };

        try {
            btnRegisterClaim.disabled = true;
            btnRegisterClaim.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registering...';
            const res = await fetch("/api/vehicle-claim/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            if (res.ok) {
                const data = await res.json();
                activeVehicleClaim = data;
                showForensicStep();
            } else {
                const err = await res.json().catch(() => ({}));
                alert(err.detail || "Failed to register claim");
            }
        } catch (err) {
            console.error("Failed to register claim:", err);
            alert("Network error: could not register claim.");
        } finally {
            btnRegisterClaim.disabled = false;
            btnRegisterClaim.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket"></i> Register & Start Claim';
        }
    });

    // Enter key triggers registration submit and clearing border on input
    [custNameInput, policyNoInput, custContactInput, vehRegInput, vehModelInput, vehYearInput].forEach(inp => {
        if (!inp) return;
        inp.addEventListener("input", () => { inp.style.borderColor = ""; });
        inp.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                btnRegisterClaim.click();
            }
        });
    });

    // Back to Registration Button
    btnBackToRegister.addEventListener("click", () => {
        showRegistrationStep();
    });

    // ─────────────────────────────────────────────────────────────
    // 2b. CLAIMS HISTORY TABLE
    // ─────────────────────────────────────────────────────────────

    async function loadClaimsHistory() {
        try {
            const res = await fetch("/api/vehicle-claims");
            if (!res.ok) return;
            const data = await res.json();
            const claims = data.claims || [];
            claimsHistoryCount.textContent = `${claims.length} Claim${claims.length !== 1 ? 's' : ''}`;

            if (claims.length === 0) {
                claimsHistoryBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted" style="padding: 24px;">No claims registered yet. Register your first claim above.</td></tr>';
                return;
            }

            claimsHistoryBody.innerHTML = "";
            claims.forEach(c => {
                const statusClass = c.status === "ACTIVE_INTAKE" ? "badge-authentic" : "badge-review";
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${c.claim_id}</strong></td>
                    <td>
                        <strong>${c.customer_name}</strong><br>
                        <small class="text-muted">${c.vehicle_reg} • ${c.make_model} (${c.year})</small>
                    </td>
                    <td>${c.policy_no}</td>
                    <td><span class="part-card-status-badge ${statusClass}" style="position: static; font-size: 10px;">${c.status}</span></td>
                    <td style="text-align: center;">${c.verified_parts_count}</td>
                    <td>₹${Math.round(c.grand_total).toLocaleString("en-IN")}</td>
                    <td><small>${c.created_at}</small></td>
                    <td>
                        <button type="button" class="btn btn-primary btn-sm btn-resume-claim" data-claim-id="${c.claim_id}" title="Open & Resume Claim">
                            <i class="fa-solid fa-arrow-right"></i>
                        </button>
                    </td>
                `;
                claimsHistoryBody.appendChild(tr);
            });

            // Wire resume buttons
            document.querySelectorAll(".btn-resume-claim").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const claimId = btn.getAttribute("data-claim-id");
                    try {
                        const res = await fetch(`/api/vehicle-claim/${encodeURIComponent(claimId)}`);
                        if (res.ok) {
                            activeVehicleClaim = await res.json();
                            showForensicStep();
                        } else {
                            alert("Failed to load claim.");
                        }
                    } catch (e) {
                        console.error("Failed to resume claim:", e);
                    }
                });
            });
        } catch (err) {
            console.error("Failed to load claims history:", err);
        }
    }

    btnRefreshClaimsHistory.addEventListener("click", () => {
        loadClaimsHistory();
    });

    // ─────────────────────────────────────────────────────────────
    // 2c. VEHICLE HEADER UI UPDATE
    // ─────────────────────────────────────────────────────────────

    function updateVehicleHeaderUI() {
        if (!activeVehicleClaim) return;
        const reg = activeVehicleClaim.vehicle.registration_no || "—";
        const model = activeVehicleClaim.vehicle.make_model || "—";
        const yr = activeVehicleClaim.vehicle.year || "—";
        const cust = activeVehicleClaim.customer.name || "—";
        const pol = activeVehicleClaim.customer.policy_no || "—";

        vehObjName.textContent = `${model} (${yr})`;
        vehObjPlate.textContent = reg;
        vehObjPolicy.textContent = `Policy: ${pol} • Insured: ${cust} • Claim ID: ${activeVehicleClaim.claim_id}`;

        const count = (activeVehicleClaim.verified_parts || []).length;
        badgeVerifiedPartsCount.textContent = count;
        verifiedPartsListCount.textContent = count;
        if (navAssessmentCount) {
            navAssessmentCount.textContent = count;
            navAssessmentCount.style.display = count > 0 ? "inline-block" : "none";
        }

        const totalCost = activeVehicleClaim.grand_total || 0;
        badgeTotalCost.textContent = `₹${Math.round(totalCost).toLocaleString("en-IN")}`;

        btnExportClaimJSON.disabled = count === 0;
    }

    btnExportClaimJSON.addEventListener("click", () => {
        if (!activeVehicleClaim) return;
        const jsonStr = JSON.stringify(activeVehicleClaim, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `VehicleClaim_${activeVehicleClaim.claim_id}.json`;
        a.click();
        URL.revokeObjectURL(url);
    });

    // ─────────────────────────────────────────────────────────────
    // 3. FILE SELECTION & DRAG & DROP FOR DAMAGE PARTS
    // ─────────────────────────────────────────────────────────────

    btnBrowse.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("click", (e) => {
        if (e.target !== btnRemoveFile && !currentSelectedFile) {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
        });
    });

    dropZone.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    btnRemoveFile.addEventListener("click", (e) => {
        e.stopPropagation();
        resetFileInput();
    });

    function handleFileSelection(file) {
        if (!file.type.match("image.*")) {
            alert("Please select a valid image file (JPEG, PNG, WEBP).");
            return;
        }
        currentSelectedFile = file;
        previewName.textContent = file.name;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            dropZonePrompt.style.display = "none";
            dropZonePreview.style.display = "flex";
            btnVerifyAndAddPart.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function resetFileInput() {
        currentSelectedFile = null;
        fileInput.value = "";
        previewImg.src = "";
        dropZonePrompt.style.display = "block";
        dropZonePreview.style.display = "none";
        btnVerifyAndAddPart.disabled = true;
    }

    // ─────────────────────────────────────────────────────────────
    // 4. FORENSIC GATEKEEPER: VERIFY & ADD DAMAGE PART
    // ─────────────────────────────────────────────────────────────

    btnVerifyAndAddPart.addEventListener("click", async () => {
        if (!currentSelectedFile) return;

        const partName = selDamagePart.value;
        const damageType = selDamageType.value;

        // Show animated scanning progress
        loadingState.style.display = "flex";
        btnVerifyAndAddPart.disabled = true;

        const steps = [
            `Sanitizing ${partName} payload & checking magic bytes...`,
            `Inspecting EXIF camera sensor provenance & software tags...`,
            `Computing Error Level Analysis (ELA) recompression variance...`,
            `Screening 64-bit 2D-DCT pHash for duplicate claims in registry...`,
            `Running PRNU noise residual & AI inpainting anomaly scanner...`,
        ];

        let stepIndex = 0;
        const stepInterval = setInterval(() => {
            stepIndex = (stepIndex + 1) % steps.length;
            loadingStep.textContent = steps[stepIndex];
        }, 600);

        const formData = new FormData();
        formData.append("claim_id", activeVehicleClaim.claim_id);
        formData.append("part_name", partName);
        formData.append("damage_type", damageType);
        formData.append("file", currentSelectedFile);

        try {
            const response = await fetch("/api/vehicle-claim/verify-part", {
                method: "POST",
                body: formData,
            });

            clearInterval(stepInterval);
            loadingState.style.display = "none";

            if (!response.ok) {
                let errMsg = "Verification failed";
                try {
                    const errText = await response.text();
                    const errJson = JSON.parse(errText);
                    errMsg = errJson.detail || errMsg;
                } catch (_) {
                    errMsg = `Server error (${response.status})`;
                }
                throw new Error(errMsg);
            }

            const data = await response.json();

            // ══════════════════════════════════════════════════════════
            // GATEKEEPER DECISION: VALID VS REJECTED
            // ══════════════════════════════════════════════════════════
            if (data.is_valid) {
                // SUCCESS: Image is authentic -> Add to vehicle object
                activeVehicleClaim = data.vehicle_claim;
                renderVerifiedParts();
                renderVehicleCostTable();
                updateVehicleHeaderUI();
                showGatekeeperAlert("success", `<i class="fa-solid fa-circle-check"></i> <strong>Passed Forensic Check (${data.overall_score}% Authentic):</strong> Image for <strong>${partName}</strong> was verified and successfully added to Vehicle Object ${activeVehicleClaim.vehicle.registration_no}.`);
                resetFileInput();
                // Also refresh registry stats
                loadRegistryRecords();
            } else {
                // FAILURE: Image is fraudulent/tampered -> Block from vehicle object
                activeVehicleClaim = data.vehicle_claim;
                renderRejectedParts();
                updateVehicleHeaderUI();
                showGatekeeperAlert("danger", `<i class="fa-solid fa-shield-xmark"></i> <strong>BLOCKED BY FORENSIC GATEKEEPER:</strong> Image for <strong>${partName}</strong> failed forensic check (${data.verdict}, Score: ${data.overall_score}%). It was strictly <strong>excluded</strong> from the vehicle object.`);
                resetFileInput();
            }

        } catch (err) {
            clearInterval(stepInterval);
            loadingState.style.display = "none";
            btnVerifyAndAddPart.disabled = false;
            console.error("Verification error:", err);
            showGatekeeperAlert("danger", `<i class="fa-solid fa-triangle-exclamation"></i> Error running forensic verification: ${err.message}`);
        }
    });

    function showGatekeeperAlert(type, html) {
        gatekeeperAlert.className = `gatekeeper-alert alert-${type}`;
        gatekeeperAlert.innerHTML = html;
        gatekeeperAlert.style.display = "flex";
        setTimeout(() => {
            gatekeeperAlert.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 100);
    }

    // ─────────────────────────────────────────────────────────────
    // 5. RENDER VERIFIED PARTS & COST TABLE
    // ─────────────────────────────────────────────────────────────

    async function deletePartFromClaim(partId, partName) {
        if (!activeVehicleClaim) return;

        const confirmMsg = `Remove '${partName || "this image"}' from the vehicle claim object?\n\nThis will permanently:\n1. Remove the image from claim #${activeVehicleClaim.claim_id}\n2. Purge its pHash and SHA-256 fingerprint from the Hash Registry Ledger\n3. Recalculate total estimated repair costs\n\nProceed?`;

        if (!confirm(confirmMsg)) {
            return;
        }

        try {
            const formData = new FormData();
            formData.append("claim_id", activeVehicleClaim.claim_id);
            formData.append("part_id", partId);

            const res = await fetch("/api/vehicle-claim/delete-part", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to remove part from claim");
            }

            const data = await res.json();

            // Update activeVehicleClaim with updated claim from backend
            activeVehicleClaim = data.vehicle_claim;

            // Re-render UI views
            updateVehicleHeaderUI();
            renderVerifiedParts();
            renderAssessmentView();

            // Refresh Hash Registry table and System Stats
            if (typeof loadRegistryRecords === "function") {
                loadRegistryRecords();
            }
            if (typeof loadSystemStats === "function") {
                loadSystemStats();
            }
            if (typeof loadClaimsHistory === "function") {
                loadClaimsHistory();
            }

            // Show success alert in the gatekeeper alert box
            showGatekeeperAlert("success", `<i class="fa-solid fa-trash-can"></i> <strong>Image Removed:</strong> <strong>${partName || partId}</strong> was removed from vehicle claim object and permanently purged from the Hash Registry.`);

        } catch (err) {
            console.error("Error deleting part:", err);
            showGatekeeperAlert("danger", `<i class="fa-solid fa-triangle-exclamation"></i> Error removing part: ${err.message}`);
        }
    }

    function renderVerifiedParts() {
        const parts = activeVehicleClaim.verified_parts || [];
        verifiedPartsListCount.textContent = parts.length;

        // Update nav badge counter
        if (navAssessmentCount) {
            navAssessmentCount.textContent = parts.length;
            navAssessmentCount.style.display = parts.length > 0 ? "inline-block" : "none";
        }

        if (parts.length === 0) {
            emptyPartsState.style.display = "flex";
            verifiedPartsGrid.style.display = "none";
            if (nextPhaseBanner) nextPhaseBanner.style.display = "none";
            return;
        }

        emptyPartsState.style.display = "none";
        verifiedPartsGrid.style.display = "grid";
        verifiedPartsGrid.innerHTML = "";

        // Show Next Phase Banner
        if (nextPhaseBanner) {
            nextPhaseBanner.style.display = "flex";
            if (verifiedMediaCount) verifiedMediaCount.textContent = parts.length;
        }

        parts.forEach((p, idx) => {
            const card = document.createElement("div");
            card.className = "verified-part-card";

            const isAuthentic = p.verdict === "PASSED_AUTHENTIC";
            const badgeClass = isAuthentic ? "badge-authentic" : "badge-review";
            const badgeLabel = isAuthentic ? `Authentic ${p.authenticity_score}%` : `Surveyor Review ${p.authenticity_score}%`;
            const assessedBadge = p.assessed
                ? `<span class="badge-count" style="font-size: 11px; background: #ecfdf5; color: #065f46;"><i class="fa-solid fa-check-double"></i> Phase 2 Assessed</span>`
                : `<span class="badge-count" style="font-size: 11px; background: #eff6ff; color: #2563eb;"><i class="fa-solid fa-arrow-right"></i> Ready for Assessment</span>`;

            card.innerHTML = `
                <div class="part-card-thumb-wrap">
                    <img src="${p.image_url}" class="part-card-thumb" alt="${p.part_name}">
                    <span class="part-card-status-badge ${badgeClass}">${badgeLabel}</span>
                    <button type="button" class="part-card-delete-btn btn-delete-part" data-part-id="${p.part_id}" data-part-name="${p.part_name}" title="Remove image from object & purge from Hash Registry">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
                <div class="part-card-body">
                    <div class="part-card-header">
                        <span class="part-name-title">${p.part_name}</span>
                        <span class="damage-type-pill">${p.damage_type}</span>
                    </div>
                    <div style="margin: 6px 0;">
                        ${assessedBadge}
                    </div>
                    <div class="part-hashes">
                        <span>pHash: <code>${p.phash ? p.phash.substring(0, 16) : 'N/A'}</code></span>
                        <span>SHA-256: <code>${p.sha256 ? p.sha256.substring(0, 12) + '...' : 'N/A'}</code></span>
                    </div>
                    <div class="part-card-actions" style="margin-top: 10px; display: flex; gap: 8px;">
                        <button type="button" class="btn btn-secondary btn-sm btn-inspect-part" style="flex: 1;" data-idx="${idx}">
                            <i class="fa-solid fa-microscope"></i> Diagnostics
                        </button>
                        <button type="button" class="btn btn-sm btn-delete-part" style="padding: 6px 12px; background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 13px;" data-part-id="${p.part_id}" data-part-name="${p.part_name}" title="Remove image from object & purge from Hash Registry">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </div>
            `;
            verifiedPartsGrid.appendChild(card);
        });

        // Wire forensic inspect buttons
        verifiedPartsGrid.querySelectorAll(".btn-inspect-part").forEach(b => {
            b.addEventListener("click", () => {
                const idx = parseInt(b.getAttribute("data-idx"));
                openDiagnosticsModal(parts[idx]);
            });
        });

        // Wire delete buttons
        verifiedPartsGrid.querySelectorAll(".btn-delete-part").forEach(b => {
            b.addEventListener("click", (e) => {
                e.stopPropagation();
                const partId = b.getAttribute("data-part-id");
                const partName = b.getAttribute("data-part-name");
                deletePartFromClaim(partId, partName);
            });
        });
    }

    // ─────────────────────────────────────────────────────────────
    // 5. PHASE 2: DEDICATED DAMAGE, DEPTH & COST ASSESSMENT VIEW
    // ─────────────────────────────────────────────────────────────

    function renderAssessmentView() {
        if (!activeVehicleClaim) return;
        const parts = activeVehicleClaim.verified_parts || [];

        // Update Vehicle Header Banner
        if (assessVehReg) assessVehReg.textContent = activeVehicleClaim.vehicle.registration_no || "N/A";
        if (assessVehModel) assessVehModel.textContent = activeVehicleClaim.vehicle.make_model || "Vehicle";
        if (assessClaimId) assessClaimId.textContent = `Claim #${activeVehicleClaim.claim_id}`;
        if (assessCustomerName) assessCustomerName.textContent = activeVehicleClaim.customer.name || "Policyholder";
        if (assessVerifiedCount) assessVerifiedCount.textContent = parts.length;
        if (assessPartsCount) assessPartsCount.textContent = parts.length;

        const subtotal = (activeVehicleClaim.total_parts_cost || 0) + (activeVehicleClaim.total_labor_cost || 0);
        if (assessNetRepairs) assessNetRepairs.textContent = `₹${Math.round(subtotal).toLocaleString("en-IN")}`;
        if (assessGrandTotal) assessGrandTotal.textContent = `₹${Math.round(activeVehicleClaim.grand_total || 0).toLocaleString("en-IN")}`;

        if (parts.length === 0) {
            if (emptyAssessmentState) emptyAssessmentState.style.display = "flex";
            if (assessmentPartsGrid) assessmentPartsGrid.style.display = "none";
            if (vehicleCostCard) vehicleCostCard.style.display = "none";
            return;
        }

        if (emptyAssessmentState) emptyAssessmentState.style.display = "none";
        if (assessmentPartsGrid) assessmentPartsGrid.style.display = "grid";
        assessmentPartsGrid.innerHTML = "";

        parts.forEach((p, idx) => {
            const card = document.createElement("div");
            card.className = "assessment-card";

            // Status label & badge
            let statusBadge = "";
            if (!p.assessed) {
                statusBadge = `<span class="part-card-status-badge badge-review"><i class="fa-solid fa-clock"></i> Awaiting AI Inference</span>`;
            } else if (p.is_manual_cost) {
                statusBadge = `<span class="part-card-status-badge" style="background:#f5f3ff; color:#6d28d9; border:1px solid #ddd6fe;"><i class="fa-solid fa-user-check"></i> Surveyor Manual Entry</span>`;
            } else if (p.total_detections > 0) {
                statusBadge = `<span class="part-card-status-badge badge-authentic"><i class="fa-solid fa-crosshairs"></i> ${p.total_detections} Damage Detected</span>`;
            } else {
                statusBadge = `<span class="part-card-status-badge badge-review text-red"><i class="fa-solid fa-triangle-exclamation"></i> 0 Detections</span>`;
            }

            // Image display (multi-mode switcher if YOLO and Depth available)
            let mediaSwitcher = "";
            let currentDisplayImg = p.damage_overlay_url || p.image_url;

            if (p.assessed && p.total_detections > 0 && (p.damage_overlay_url || p.depth_heatmap_url)) {
                mediaSwitcher = `
                    <div class="assessment-media-switcher">
                        <button type="button" class="thumb-toggle-btn ${p.damage_overlay_url ? 'active' : ''}" data-target-img="assessImg-${idx}" data-src="${p.damage_overlay_url || p.image_url}">YOLO Overlay</button>
                        ${p.depth_heatmap_url ? `<button type="button" class="thumb-toggle-btn" data-target-img="assessImg-${idx}" data-src="${p.depth_heatmap_url}">Depth Heatmap</button>` : ''}
                        <button type="button" class="thumb-toggle-btn ${!p.damage_overlay_url ? 'active' : ''}" data-target-img="assessImg-${idx}" data-src="${p.image_url}">Original</button>
                    </div>
                `;
            }

            // Body content depending on state
            let bodyHTML = "";

            if (!p.assessed) {
                bodyHTML = `
                    <div class="assessment-card-body">
                        <p class="text-muted" style="font-size: 12px;">Image verified authentic. Run AI inference to detect damage segmentation, estimate indentation depth, and compute repair costs.</p>
                        <div style="margin-top: auto; padding-top: 10px;">
                            <button type="button" class="btn btn-primary btn-sm btn-block btn-assess-part" data-part-id="${p.part_id}">
                                <i class="fa-solid fa-bolt"></i> Run AI Assessment
                            </button>
                        </div>
                    </div>
                `;
            } else if (p.total_detections > 0 && !p.is_manual_cost) {
                // Detected damage instances
                const detections = p.detection_details || [];
                const depthData = p.depth_details || [];
                const firstDet = detections[0] || {};
                const firstDepth = depthData[0] || {};

                const areaVal = firstDet.area_cm2 ? `${firstDet.area_cm2} cm²` : "N/A";
                const depthVal = firstDepth.delta_z_cm ? `${firstDepth.delta_z_cm} cm` : (firstDet.depth_cm ? `${firstDet.depth_cm} cm` : "N/A");
                const confVal = firstDet.confidence ? `${(firstDet.confidence * 100).toFixed(1)}%` : "N/A";

                bodyHTML = `
                    <div class="assessment-card-body">
                        <div class="assessment-metrics-grid">
                            <div class="assessment-metric-item">
                                <span class="assessment-metric-label">Damage Type</span>
                                <span class="assessment-metric-val">${(firstDet.class || p.damage_type).toUpperCase()}</span>
                            </div>
                            <div class="assessment-metric-item">
                                <span class="assessment-metric-label">Confidence</span>
                                <span class="assessment-metric-val">${confVal}</span>
                            </div>
                            <div class="assessment-metric-item">
                                <span class="assessment-metric-label">Surface Area</span>
                                <span class="assessment-metric-val">${areaVal}</span>
                            </div>
                            <div class="assessment-metric-item">
                                <span class="assessment-metric-label">Indentation Δz</span>
                                <span class="assessment-metric-val font-bold text-primary">${depthVal}</span>
                            </div>
                        </div>

                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: var(--radius-sm);">
                            <span style="font-size: 12px; font-weight: 600; color: #1e40af;">Component Repair Cost:</span>
                            <strong style="font-size: 15px; color: #1e3a8a;">₹${Math.round(p.estimated_cost).toLocaleString("en-IN")}</strong>
                        </div>

                        <div style="display: flex; gap: 8px; margin-top: auto; padding-top: 6px;">
                            <button type="button" class="btn btn-secondary btn-sm btn-inspect-part" style="flex: 1;" data-idx="${idx}">
                                <i class="fa-solid fa-microscope"></i> Diagnostics
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm btn-manual-cost" style="flex: 1;" data-part-id="${p.part_id}">
                                <i class="fa-solid fa-pen"></i> Adjust Cost
                            </button>
                        </div>
                    </div>
                `;
            } else if (p.is_manual_cost) {
                // Manual cost assigned by surveyor
                const cb = p.cost_breakdown || {};
                const item = (cb.items && cb.items[0]) || {};

                bodyHTML = `
                    <div class="assessment-card-body">
                        <div style="padding: 10px; background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: var(--radius-sm);">
                            <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #6d28d9; margin-bottom: 4px;">Surveyor Authorization</div>
                            <div style="font-size: 13px; font-weight: 600; color: var(--text-primary);">${(item.damage_class || p.damage_type).toUpperCase()}</div>
                            <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">${item.recommended_action || "Manual repair authorization"}</div>
                        </div>

                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: var(--radius-sm);">
                            <span style="font-size: 12px; font-weight: 600; color: #1e40af;">Surveyor Repair Total:</span>
                            <strong style="font-size: 15px; color: #1e3a8a;">₹${Math.round(p.estimated_cost).toLocaleString("en-IN")}</strong>
                        </div>

                        <div style="display: flex; gap: 8px; margin-top: auto; padding-top: 6px;">
                            <button type="button" class="btn btn-secondary btn-sm btn-block btn-manual-cost" data-part-id="${p.part_id}">
                                <i class="fa-solid fa-pen-to-square"></i> Edit Manual Cost
                            </button>
                        </div>
                    </div>
                `;
            } else {
                // MODEL FAILED TO DETECT DAMAGE: 0 DETECTIONS -> NO COST ADDED!
                bodyHTML = `
                    <div class="assessment-card-body">
                        <div class="no-damage-callout">
                            <div class="callout-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                            <div class="callout-body">
                                <strong>No Damage Detected by AI Model</strong>
                                <p>Model detected 0 damage instances. <strong>Cost is ₹0</strong>. If damage is visible in the photo (e.g. burn, structural warp, or custom repair), click below to enter manual cost.</p>
                            </div>
                        </div>

                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f8fafc; border: 1px solid var(--border-light); border-radius: var(--radius-sm);">
                            <span style="font-size: 12px; font-weight: 600; color: var(--text-muted);">Assigned Repair Cost:</span>
                            <strong style="font-size: 14px; color: var(--text-primary);">₹0 (Unassigned)</strong>
                        </div>

                        <div style="display: flex; gap: 8px; margin-top: auto; padding-top: 6px;">
                            <button type="button" class="btn btn-primary btn-sm btn-manual-cost" style="flex: 1;" data-part-id="${p.part_id}">
                                <i class="fa-solid fa-pen-to-square"></i> Set Manual Cost
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm btn-inspect-part" data-idx="${idx}" title="Inspect original photo">
                                <i class="fa-solid fa-magnifying-glass"></i>
                            </button>
                        </div>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="assessment-card-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="assessment-card-title">${p.part_name}</div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        ${statusBadge}
                        <button type="button" class="btn btn-sm btn-delete-part" style="padding: 4px 8px; background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; border-radius: 6px; cursor: pointer; font-size: 11px;" data-part-id="${p.part_id}" data-part-name="${p.part_name}" title="Remove image & purge from Hash Registry">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </div>
                <div class="assessment-card-media">
                    <img id="assessImg-${idx}" src="${currentDisplayImg}" class="assessment-card-img" alt="${p.part_name}">
                </div>
                ${mediaSwitcher}
                ${bodyHTML}
            `;

            assessmentPartsGrid.appendChild(card);
        });

        // Wire media switchers
        assessmentPartsGrid.querySelectorAll(".thumb-toggle-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const targetId = btn.getAttribute("data-target-img");
                const targetSrc = btn.getAttribute("data-src");
                const imgEl = document.getElementById(targetId);
                if (imgEl && targetSrc) {
                    imgEl.src = targetSrc;
                }
                const parentSwitcher = btn.parentElement;
                parentSwitcher.querySelectorAll(".thumb-toggle-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
            });
        });

        // Wire per-part AI assessment buttons
        assessmentPartsGrid.querySelectorAll(".btn-assess-part").forEach(btn => {
            btn.addEventListener("click", async () => {
                const partId = btn.getAttribute("data-part-id");
                await assessSinglePart(partId);
            });
        });

        // Wire manual cost buttons
        assessmentPartsGrid.querySelectorAll(".btn-manual-cost").forEach(btn => {
            btn.addEventListener("click", () => {
                const partId = btn.getAttribute("data-part-id");
                openManualCostModal(partId);
            });
        });

        // Wire inspect buttons
        assessmentPartsGrid.querySelectorAll(".btn-inspect-part").forEach(btn => {
            btn.addEventListener("click", () => {
                const idx = parseInt(btn.getAttribute("data-idx"));
                openDiagnosticsModal(parts[idx]);
            });
        });

        // Wire delete buttons in assessment view
        assessmentPartsGrid.querySelectorAll(".btn-delete-part").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const partId = btn.getAttribute("data-part-id");
                const partName = btn.getAttribute("data-part-name");
                deletePartFromClaim(partId, partName);
            });
        });

        renderVehicleCostTable();
    }

    // ─────────────────────────────────────────────────────────────
    // 6. RENDER VEHICLE REPAIR COST TABLE (ON ASSESSMENT PAGE)
    // ─────────────────────────────────────────────────────────────

    function renderVehicleCostTable() {
        const parts = activeVehicleClaim.verified_parts || [];
        if (parts.length === 0) {
            vehicleCostCard.style.display = "none";
            return;
        }

        vehicleCostCard.style.display = "block";
        vehicleCostTableBody.innerHTML = "";

        let hasAnyItems = false;

        parts.forEach(p => {
            const cb = p.cost_breakdown || {};
            const items = cb.items || cb.itemized_damages || [];

            if (items.length > 0) {
                hasAnyItems = true;
                items.forEach(item => {
                    const actionText = item.recommended_action || item.recommended_repair_action || "Standard OEM repair";
                    const partsCost = `₹${Math.round(item.parts_cost || 0).toLocaleString("en-IN")}`;
                    const laborHrs = `${(item.labor_hours || 1.5).toFixed(1)} hrs`;
                    const laborCost = `₹${Math.round(item.labor_cost || 0).toLocaleString("en-IN")}`;
                    const totalCost = `₹${Math.round(item.total_cost || 0).toLocaleString("en-IN")}`;
                    const areaStr = item.surface_area_cm2 ? ` • ${item.surface_area_cm2} cm²` : "";
                    const depthStr = item.estimated_depth_cm ? ` • Δz ${item.estimated_depth_cm} cm` : "";

                    const sourceBadge = item.is_manual || p.is_manual_cost
                        ? `<span class="cost-source-badge cost-source-manual"><i class="fa-solid fa-user"></i> Manual</span>`
                        : `<span class="cost-source-badge cost-source-ai"><i class="fa-solid fa-robot"></i> AI YOLO+MiDaS</span>`;

                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>
                            <strong>${p.part_name}</strong><br>
                            <small class="text-muted">${(item.damage_class || p.damage_type).toUpperCase()}${areaStr}${depthStr}</small>
                        </td>
                        <td><small>${actionText}</small></td>
                        <td>${sourceBadge}</td>
                        <td>${partsCost}</td>
                        <td>${laborHrs}</td>
                        <td>${laborCost}</td>
                        <td class="font-bold">${totalCost}</td>
                        <td>
                            <button type="button" class="btn btn-secondary btn-sm btn-manual-cost" data-part-id="${p.part_id}">
                                <i class="fa-solid fa-pen"></i> Edit
                            </button>
                        </td>
                    `;
                    vehicleCostTableBody.appendChild(tr);
                });
            } else if (p.assessed && p.total_detections === 0) {
                // Explicitly show 0 detection row with button to add cost
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>
                        <strong>${p.part_name}</strong><br>
                        <small class="text-muted">${p.damage_type.toUpperCase()}</small>
                    </td>
                    <td><small class="text-muted">No damage detected by AI model</small></td>
                    <td><span class="badge-review text-amber">0 Detections</span></td>
                    <td>₹0</td>
                    <td>0.0 hrs</td>
                    <td>₹0</td>
                    <td class="font-bold text-muted">₹0</td>
                    <td>
                        <button type="button" class="btn btn-primary btn-sm btn-manual-cost" data-part-id="${p.part_id}">
                            <i class="fa-solid fa-plus"></i> Set Cost
                        </button>
                    </td>
                `;
                vehicleCostTableBody.appendChild(tr);
            }
        });

        if (!hasAnyItems && parts.every(p => !p.assessed)) {
            vehicleCostTableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted" style="padding: 24px;">
                        Images have not been assessed yet. Click <strong>Run AI Assessment on All Images</strong> above to detect damage, calculate surface area, depth, and compute repair costs.
                    </td>
                </tr>
            `;
        }

        // Wire edit/add buttons in cost table
        vehicleCostTableBody.querySelectorAll(".btn-manual-cost").forEach(b => {
            b.addEventListener("click", () => {
                const partId = b.getAttribute("data-part-id");
                openManualCostModal(partId);
            });
        });

        const subtotalSum = (activeVehicleClaim.total_parts_cost || 0) + (activeVehicleClaim.total_labor_cost || 0);
        const gstSum = activeVehicleClaim.tax_gst_amount || 0;
        const grandSum = activeVehicleClaim.grand_total || 0;

        vehCostSubtotal.textContent = `₹${Math.round(subtotalSum).toLocaleString("en-IN")}`;
        vehCostGST.textContent = `₹${Math.round(gstSum).toLocaleString("en-IN")}`;
        vehCostGrandTotal.textContent = `₹${Math.round(grandSum).toLocaleString("en-IN")}`;
    }

    // ─────────────────────────────────────────────────────────────
    // 7. AI ASSESSMENT & MANUAL COST CONTROLLERS
    // ─────────────────────────────────────────────────────────────

    async function assessSinglePart(partId) {
        if (!activeVehicleClaim) return;
        const btn = document.querySelector(`.btn-assess-part[data-part-id="${partId}"]`);
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Assessing...`;
        }

        try {
            const formData = new FormData();
            formData.append("claim_id", activeVehicleClaim.claim_id);
            formData.append("part_id", partId);

            const res = await fetch("/api/vehicle-claim/assess-part", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) throw new Error("Assessment failed");
            const data = await res.json();
            activeVehicleClaim = data.vehicle_claim;
            updateVehicleHeaderUI();
            renderAssessmentView();
        } catch (e) {
            console.error("Single part assessment failed:", e);
            alert(`Assessment error: ${e.message}`);
        }
    }

    if (btnRunAllAssessment) {
        btnRunAllAssessment.addEventListener("click", async () => {
            if (!activeVehicleClaim || (activeVehicleClaim.verified_parts || []).length === 0) {
                alert("No verified images available in vehicle claim.");
                return;
            }

            btnRunAllAssessment.disabled = true;
            btnRunAllAssessment.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Assessing Damages & Depth...`;
            if (assessLoadingState) assessLoadingState.style.display = "flex";

            const steps = [
                "Running YOLOv8-Seg damage detection & mask segmentation...",
                "Executing MiDaS monocular 3D depth estimation...",
                "Calculating damaged mask surface area (cm²)...",
                "Computing indentation depth Δz against panel baseline...",
                "Synthesizing actuarial OEM repair procedures & costs...",
            ];

            let stepIdx = 0;
            const stepTimer = setInterval(() => {
                stepIdx = (stepIdx + 1) % steps.length;
                if (assessLoadingStep) assessLoadingStep.textContent = steps[stepIdx];
            }, 700);

            try {
                const formData = new FormData();
                formData.append("claim_id", activeVehicleClaim.claim_id);

                const res = await fetch("/api/vehicle-claim/assess-all", {
                    method: "POST",
                    body: formData,
                });

                clearInterval(stepTimer);
                if (assessLoadingState) assessLoadingState.style.display = "none";

                if (!res.ok) throw new Error("Batch assessment failed");
                const data = await res.json();
                activeVehicleClaim = data.vehicle_claim;
                updateVehicleHeaderUI();
                renderAssessmentView();
            } catch (err) {
                clearInterval(stepTimer);
                if (assessLoadingState) assessLoadingState.style.display = "none";
                console.error("Batch assessment error:", err);
                alert(`Assessment error: ${err.message}`);
            } finally {
                btnRunAllAssessment.disabled = false;
                btnRunAllAssessment.innerHTML = `<i class="fa-solid fa-bolt"></i> Run AI Assessment on All Images`;
            }
        });
    }

    // ── Manual Cost Modal Handling ──
    function openManualCostModal(partId) {
        const parts = activeVehicleClaim.verified_parts || [];
        const part = parts.find(p => p.part_id === partId);
        if (!part) return;

        manualPartId.value = partId;
        manualCostPartTitle.textContent = `Manual Cost: ${part.part_name}`;
        manualCostPartMeta.textContent = `Claim #${activeVehicleClaim.claim_id} • Vehicle ${activeVehicleClaim.vehicle.registration_no}`;
        manualCostImgPreview.src = part.image_url;

        // Pre-fill existing values if any
        const cb = part.cost_breakdown || {};
        const items = cb.items || [];
        if (items.length > 0) {
            const it = items[0];
            manualDamageType.value = it.damage_class || part.damage_type || "dent";
            manualActionText.value = it.recommended_action || "";
            manualPartsCost.value = it.parts_cost || 0;
            manualLaborHours.value = it.labor_hours || 2.0;
            manualLaborCost.value = it.labor_cost || 1300;
            manualNotes.value = it.notes || "";
        } else {
            manualDamageType.value = part.damage_type || "dent";
            manualActionText.value = "Panel repair, filler shaping & paint blending";
            manualPartsCost.value = 1200;
            manualLaborHours.value = 2.0;
            manualLaborCost.value = 1300;
            manualNotes.value = "";
        }

        manualCostModal.style.display = "flex";
    }

    if (manualLaborHours) {
        manualLaborHours.addEventListener("input", () => {
            const hrs = parseFloat(manualLaborHours.value) || 0;
            manualLaborCost.value = Math.round(hrs * 650);
        });
    }

    if (btnManualCostClose) {
        btnManualCostClose.addEventListener("click", () => manualCostModal.style.display = "none");
    }
    if (btnCancelManualCost) {
        btnCancelManualCost.addEventListener("click", () => manualCostModal.style.display = "none");
    }
    if (manualCostModal) {
        manualCostModal.addEventListener("click", (e) => {
            if (e.target === manualCostModal) manualCostModal.style.display = "none";
        });
    }

    if (btnSaveManualCost) {
        btnSaveManualCost.addEventListener("click", async () => {
            const partId = manualPartId.value;
            const damageType = manualDamageType.value;
            const actionText = manualActionText.value.trim() || "Manual repair authorization";
            const partsCost = parseFloat(manualPartsCost.value) || 0.0;
            const laborHours = parseFloat(manualLaborHours.value) || 0.0;
            const laborCost = parseFloat(manualLaborCost.value) || 0.0;
            const notes = manualNotes.value.trim();

            btnSaveManualCost.disabled = true;
            btnSaveManualCost.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Saving...`;

            try {
                const formData = new FormData();
                formData.append("claim_id", activeVehicleClaim.claim_id);
                formData.append("part_id", partId);
                formData.append("damage_type", damageType);
                formData.append("recommended_action", actionText);
                formData.append("parts_cost", partsCost);
                formData.append("labor_hours", laborHours);
                formData.append("labor_cost", laborCost);
                formData.append("notes", notes);

                const res = await fetch("/api/vehicle-claim/manual-cost", {
                    method: "POST",
                    body: formData,
                });

                if (!res.ok) throw new Error("Failed to save manual cost");
                const data = await res.json();
                activeVehicleClaim = data.vehicle_claim;
                manualCostModal.style.display = "none";
                updateVehicleHeaderUI();
                renderAssessmentView();
            } catch (err) {
                console.error("Save manual cost error:", err);
                alert(`Error saving manual cost: ${err.message}`);
            } finally {
                btnSaveManualCost.disabled = false;
                btnSaveManualCost.innerHTML = `<i class="fa-solid fa-check"></i> Apply Manual Repair Cost`;
            }
        });
    }

    function renderRejectedParts() {
        const rejected = activeVehicleClaim.rejected_attempts || [];
        if (rejected.length === 0) {
            rejectedPartsCard.style.display = "none";
            return;
        }

        rejectedPartsCard.style.display = "block";
        rejectedPartsListCount.textContent = rejected.length;
        rejectedPartsList.innerHTML = "";

        rejected.forEach(r => {
            const item = document.createElement("div");
            item.className = "rejected-part-item";
            const flagsText = (r.risk_flags && r.risk_flags.length > 0)
                ? r.risk_flags.join("; ")
                : "Failed multi-layer consistency or duplicate pHash check.";

            item.innerHTML = `
                <div class="rej-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                <div class="rej-info">
                    <div class="rej-title">Rejected: ${r.part_name} (${r.damage_type}) — ${r.filename}</div>
                    <div class="rej-desc">Forensic Risk Flags: <strong>${flagsText}</strong></div>
                </div>
                <div class="rej-badge">${r.verdict} (${r.overall_score}%)</div>
            `;
            rejectedPartsList.appendChild(item);
        });
    }

    // ─────────────────────────────────────────────────────────────
    // 6. HASH REGISTRY TAB: LIVE LEDGER & DUPLICATE CHECKER
    // ─────────────────────────────────────────────────────────────

    async function loadRegistryRecords() {
        try {
            const res = await fetch("/api/registry/records");
            if (!res.ok) return;
            const data = await res.json();
            registryRecordsCache = data.records || [];

            // Update stats
            const total = registryRecordsCache.length;
            const authentic = registryRecordsCache.filter(r => r.status === "VERIFIED_AUTHENTIC").length;
            const duplicates = registryRecordsCache.filter(r => r.status === "FLAGGED_DUPLICATE" || r.verdict === "FRAUD_REJECTED").length;
            const reviews = registryRecordsCache.filter(r => r.status === "SURVEYOR_REVIEW").length;

            regStatTotal.textContent = total;
            regStatAuthentic.textContent = authentic;
            regStatDuplicates.textContent = duplicates;
            regStatReviews.textContent = reviews;
            regTableCount.textContent = `${total} Records`;

            renderRegistryTable(registryRecordsCache);
        } catch (err) {
            console.error("Failed to load registry records:", err);
        }
    }

    btnRefreshRegistry.addEventListener("click", () => {
        loadRegistryRecords();
    });

    // Clear All Registry Records
    btnClearAllRegistry.addEventListener("click", async () => {
        if (!confirm("Clear ALL hash registry records? This will remove all entries and reset the pHash duplicate detector.")) return;
        try {
            const res = await fetch("/api/registry/records", { method: "DELETE" });
            if (res.ok) {
                const data = await res.json();
                loadRegistryRecords();
                alert(`Cleared ${data.cleared} records from hash registry.`);
            }
        } catch (e) {
            console.error("Clear all failed:", e);
        }
    });

    function renderRegistryTable(records) {
        registryTableBody.innerHTML = "";
        if (records.length === 0) {
            registryTableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 24px;">No hash records matching filter criteria.</td></tr>`;
            return;
        }

        records.forEach(r => {
            const tr = document.createElement("tr");

            let statusPillClass = "badge-authentic";
            if (r.status === "FLAGGED_DUPLICATE" || r.verdict === "FRAUD_REJECTED") {
                statusPillClass = "badge-review text-red";
            } else if (r.status === "SURVEYOR_REVIEW") {
                statusPillClass = "badge-review";
            }

            const shortPhash = r.phash ? r.phash.substring(0, 16) : "N/A";
            const shortSha256 = r.sha256 ? `${r.sha256.substring(0, 12)}...${r.sha256.substring(56)}` : "N/A";

            tr.innerHTML = `
                <td>
                    <strong>${r.claim_id}</strong><br>
                    <small class="text-muted">${r.timestamp}</small>
                </td>
                <td>
                    <strong>${r.vehicle_reg}</strong><br>
                    <small class="text-muted">${r.customer_name} • ${r.policy_no}</small>
                </td>
                <td>
                    <span class="damage-type-pill">${r.damage_part}</span>
                </td>
                <td>
                    <span class="hash-pill">
                        <code>${shortPhash}</code>
                        <button type="button" class="copy-btn" data-copy="${r.phash}" title="Copy full 16-hex pHash"><i class="fa-regular fa-copy"></i></button>
                    </span>
                </td>
                <td>
                    <span class="hash-pill">
                        <code>${shortSha256}</code>
                        <button type="button" class="copy-btn" data-copy="${r.sha256}" title="Copy SHA-256 digest"><i class="fa-regular fa-copy"></i></button>
                    </span>
                </td>
                <td>
                    <span class="part-card-status-badge ${statusPillClass}" style="position: static; font-size: 10px;">${r.status}</span>
                </td>
                <td style="white-space: nowrap;">
                    <button type="button" class="btn btn-secondary btn-sm btn-view-reg-record" data-id="${r.registry_id || r.claim_id}" title="View details">
                        <i class="fa-solid fa-file-lines"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-delete-reg-record" data-id="${r.registry_id}" title="Delete record" style="background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; margin-left: 4px;">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            `;
            registryTableBody.appendChild(tr);
        });

        // Wire copy buttons
        document.querySelectorAll(".copy-btn").forEach(b => {
            b.addEventListener("click", (e) => {
                e.stopPropagation();
                const text = b.getAttribute("data-copy");
                if (text) {
                    navigator.clipboard.writeText(text);
                    const origIcon = b.innerHTML;
                    b.innerHTML = `<i class="fa-solid fa-check text-green"></i>`;
                    setTimeout(() => b.innerHTML = origIcon, 1500);
                }
            });
        });

        // Wire view buttons
        document.querySelectorAll(".btn-view-reg-record").forEach(b => {
            b.addEventListener("click", () => {
                const id = b.getAttribute("data-id");
                const found = records.find(x => (x.registry_id === id || x.claim_id === id));
                if (found) {
                    alert(`Claim: ${found.claim_id}\nVehicle: ${found.vehicle_reg} (${found.vehicle_model})\nInsured: ${found.customer_name}\npHash: ${found.phash}\nSHA-256: ${found.sha256}\nVerdict: ${found.verdict} (${found.authenticity_score}%)\nNotes: ${found.notes || 'Registered collision ledger record'}`);
                }
            });
        });

        // Wire per-row delete buttons
        document.querySelectorAll(".btn-delete-reg-record").forEach(b => {
            b.addEventListener("click", async () => {
                const regId = b.getAttribute("data-id");
                if (!confirm(`Delete registry entry ${regId}?`)) return;
                try {
                    const res = await fetch(`/api/registry/records/${encodeURIComponent(regId)}`, { method: "DELETE" });
                    if (res.ok) {
                        loadRegistryRecords();
                    } else {
                        const err = await res.json().catch(() => ({}));
                        alert(err.detail || "Failed to delete record");
                    }
                } catch (e) {
                    console.error("Delete failed:", e);
                }
            });
        });
    }

    // Filter pills
    let currentFilter = "all";
    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentFilter = btn.getAttribute("data-filter");
            applyTableFilters();
        });
    });

    tableSearchInput.addEventListener("input", () => {
        applyTableFilters();
    });

    function applyTableFilters() {
        const query = tableSearchInput.value.trim().toLowerCase();
        let filtered = registryRecordsCache;

        if (currentFilter !== "all") {
            filtered = filtered.filter(r => r.status === currentFilter || r.verdict === currentFilter);
        }

        if (query) {
            filtered = filtered.filter(r =>
                (r.claim_id && r.claim_id.toLowerCase().includes(query)) ||
                (r.vehicle_reg && r.vehicle_reg.toLowerCase().includes(query)) ||
                (r.customer_name && r.customer_name.toLowerCase().includes(query)) ||
                (r.policy_no && r.policy_no.toLowerCase().includes(query)) ||
                (r.phash && r.phash.toLowerCase().includes(query)) ||
                (r.sha256 && r.sha256.toLowerCase().includes(query)) ||
                (r.damage_part && r.damage_part.toLowerCase().includes(query))
            );
        }

        renderRegistryTable(filtered);
    }

    // ─────────────────────────────────────────────────────────────
    // 7. REGISTRY DUPLICATE & COLLISION HASH CHECKER TOOL
    // ─────────────────────────────────────────────────────────────

    btnRegBrowse.addEventListener("click", () => regFileInput.click());
    registryDropZone.addEventListener("click", (e) => {
        if (e.target !== btnRemoveRegFile && !regSelectedFile) {
            regFileInput.click();
        }
    });

    regFileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleRegFile(e.target.files[0]);
        }
    });

    ["dragenter", "dragover"].forEach(eventName => {
        registryDropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            registryDropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        registryDropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            registryDropZone.classList.remove("dragover");
        });
    });

    registryDropZone.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length > 0) {
            handleRegFile(e.dataTransfer.files[0]);
        }
    });

    btnRemoveRegFile.addEventListener("click", (e) => {
        e.stopPropagation();
        regSelectedFile = null;
        regFileInput.value = "";
        regDropPrompt.style.display = "block";
        regDropPreview.style.display = "none";
    });

    function handleRegFile(file) {
        regSelectedFile = file;
        regPreviewName.textContent = file.name;
        const reader = new FileReader();
        reader.onload = (e) => {
            regPreviewImg.src = e.target.result;
            regDropPrompt.style.display = "none";
            regDropPreview.style.display = "flex";
        };
        reader.readAsDataURL(file);
    }

    btnRunRegistryCheck.addEventListener("click", async () => {
        const queryText = regQueryInput.value.trim();
        if (!regSelectedFile && !queryText) {
            alert("Please drop a vehicle image or enter a search query hash.");
            return;
        }

        lookupResultBox.innerHTML = `
            <div class="result-placeholder">
                <div class="spinner"></div>
                <p>Computing 64-bit 2D-DCT pHash & searching immutable ledger...</p>
            </div>
        `;

        const formData = new FormData();
        if (regSelectedFile) {
            formData.append("file", regSelectedFile);
        }
        if (queryText) {
            formData.append("query", queryText);
        }

        try {
            const res = await fetch("/api/registry/check", {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Lookup failed");
            }
            const data = await res.json();
            renderLookupResult(data);
        } catch (err) {
            lookupResultBox.innerHTML = `
                <div class="result-placeholder text-red">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <p>Lookup failed: ${err.message}</p>
                </div>
            `;
        }
    });

    function renderLookupResult(data) {
        if (data.mode === "text_search") {
            const matches = data.matches || [];
            lookupResultBox.innerHTML = `
                <div class="result-match-header">
                    <span class="result-status-tag ${matches.length > 0 ? 'badge-authentic' : 'badge-review'}">
                        ${matches.length} MATCHES FOUND
                    </span>
                    <strong>Search Query: "${data.query}"</strong>
                </div>
                <div style="max-height: 180px; overflow-y: auto;">
                    ${matches.map(m => `
                        <div style="padding: 8px 0; border-bottom: 1px solid var(--border-light); font-size: 12px;">
                            <strong>${m.claim_id}</strong> (${m.vehicle_reg}) — ${m.customer_name} | Part: ${m.damage_part} | Status: <strong>${m.status}</strong>
                        </div>
                    `).join("")}
                </div>
            `;
            return;
        }

        const isDup = data.is_duplicate || data.status === "EXACT_DUPLICATE_FOUND" || data.status === "DUPLICATE_FOUND";
        const isVariant = data.status === "VARIANT_FOUND";
        const tagClass = isDup ? "badge-review text-red" : (isVariant ? "badge-review" : "badge-authentic");
        const statusLabel = isDup ? "DUPLICATE CLAIM FRAUD" : (isVariant ? "SUSPECTED VARIANT" : "UNIQUE IMAGE CERTIFIED");
        const match = data.matched_record;

        lookupResultBox.innerHTML = `
            <div class="result-match-header">
                <span class="result-status-tag ${tagClass}">${statusLabel}</span>
                <span style="font-size: 12px; color: var(--text-muted);">
                    Hamming Dist: <strong>${data.hamming_distance !== null ? data.hamming_distance : 'N/A'}</strong> • Sim: <strong>${data.similarity_pct}%</strong>
                </span>
            </div>
            <div class="result-details-grid">
                <div class="detail-item">Computed pHash: <code>${data.query_phash ? data.query_phash.substring(0, 16) : 'N/A'}</code></div>
                <div class="detail-item">SHA-256 Digest: <code>${data.query_sha256 ? data.query_sha256.substring(0, 12) + '...' : 'N/A'}</code></div>
                ${match ? `
                    <div class="detail-item">Matched Claim ID: <strong>${match.claim_id}</strong></div>
                    <div class="detail-item">Matched Vehicle: <strong>${match.vehicle_reg}</strong> (${match.vehicle_model || 'Vehicle'})</div>
                    <div class="detail-item">Policyholder: <strong>${match.customer_name}</strong></div>
                    <div class="detail-item">Matched Component: <strong>${match.damage_part}</strong></div>
                ` : `
                    <div class="detail-item" style="grid-column: span 2; color: var(--success); font-weight: 600;">
                        <i class="fa-solid fa-check"></i> No collision duplicate match found in registry. Image is unique.
                    </div>
                `}
            </div>
        `;
    }

    // ─────────────────────────────────────────────────────────────
    // 8. DIAGNOSTICS & HEATMAP MODAL
    // ─────────────────────────────────────────────────────────────

    function openDiagnosticsModal(part) {
        currentModalPart = part;
        modalPartTitle.textContent = `${part.part_name} — Forensic & Damage Diagnostics`;
        modalPartMeta.textContent = `Vehicle: ${activeVehicleClaim.vehicle.registration_no} • Status: ${part.verdict} (Score: ${part.authenticity_score}%) • Detections: ${part.total_detections || 0}`;

        // Original photo
        modalImgOrig.src = part.image_url;

        // YOLO damage overlay
        const modalImgDamage = document.getElementById("modalImgDamage");
        if (modalImgDamage) {
            modalImgDamage.src = part.damage_overlay_url || part.image_url;
        }

        // MiDaS depth heatmap
        const modalImgDepth = document.getElementById("modalImgDepth");
        if (modalImgDepth) {
            modalImgDepth.src = part.depth_heatmap_url || part.image_url;
        }

        // Forensic heatmaps
        modalImgELA.src = part.ela_heatmap_url || part.image_url;
        modalImgAI.src = part.ai_heatmap_url || part.image_url;
        modalImgComp.src = part.ela_composite_url || part.image_url;

        // Hashes
        modalPHash.textContent = part.phash || "N/A";
        modalSHA256.textContent = part.sha256 || "N/A";

        // Detection Summary Section
        const summarySection = document.getElementById("detectionSummarySection");
        const countBadge = document.getElementById("detectionCountBadge");
        const itemsGrid = document.getElementById("detectionItemsGrid");

        const detections = part.detection_details || [];
        const depthData = part.depth_details || [];

        if (detections.length > 0 && summarySection && itemsGrid) {
            summarySection.style.display = "block";
            countBadge.textContent = `${detections.length} damage instance${detections.length !== 1 ? 's' : ''} detected`;
            itemsGrid.innerHTML = "";

            detections.forEach((det, idx) => {
                const depth = (idx < depthData.length) ? depthData[idx] : {};
                const deltaZ = depth.delta_z_cm ? `${depth.delta_z_cm} cm` : "N/A";
                const depthConf = depth.confidence ? `${(depth.confidence * 100).toFixed(0)}%` : "—";
                const cls = det.class || "unknown";
                const conf = det.confidence ? `${(det.confidence * 100).toFixed(1)}%` : "—";
                const area = det.area_cm2 ? `${det.area_cm2.toFixed(1)} cm²` : "—";

                const card = document.createElement("div");
                card.className = `detection-item-card detection-cls-${cls}`;
                card.innerHTML = `
                    <div class="det-card-header">
                        <span class="det-class-label">${cls.toUpperCase()}</span>
                        <span class="det-conf-badge">${conf}</span>
                    </div>
                    <div class="det-card-metrics">
                        <div class="det-metric">
                            <span class="det-metric-label">Surface Area</span>
                            <span class="det-metric-value">${area}</span>
                        </div>
                        <div class="det-metric">
                            <span class="det-metric-label">Indentation Δz</span>
                            <span class="det-metric-value">${deltaZ}</span>
                        </div>
                        <div class="det-metric">
                            <span class="det-metric-label">Depth Confidence</span>
                            <span class="det-metric-value">${depthConf}</span>
                        </div>
                    </div>
                `;
                itemsGrid.appendChild(card);
            });
        } else if (summarySection) {
            summarySection.style.display = "none";
        }

        // Reset to first tab
        const allViews = ["modalViewOrig", "modalViewDamage", "modalViewDepth", "modalViewELA", "modalViewAI", "modalViewComp"];
        modalTabBtns.forEach(b => b.classList.remove("active"));
        modalTabBtns[0].classList.add("active");
        allViews.forEach(vid => {
            const el = document.getElementById(vid);
            if (el) el.style.display = vid === "modalViewOrig" ? "block" : "none";
        });

        diagnosticsModal.style.display = "flex";
    }

    btnModalClose.addEventListener("click", () => {
        diagnosticsModal.style.display = "none";
    });

    diagnosticsModal.addEventListener("click", (e) => {
        if (e.target === diagnosticsModal) {
            diagnosticsModal.style.display = "none";
        }
    });

    modalTabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            modalTabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const viewId = btn.getAttribute("data-view");
            const allViews = ["modalViewOrig", "modalViewDamage", "modalViewDepth", "modalViewELA", "modalViewAI", "modalViewComp"];
            allViews.forEach(vid => {
                const el = document.getElementById(vid);
                if (el) el.style.display = vid === viewId ? "block" : "none";
            });
        });
    });

    // ─────────────────────────────────────────────────────────────
    // 9. SYSTEM STATS & RESET
    // ─────────────────────────────────────────────────────────────

    async function fetchSystemStats() {
        try {
            const res = await fetch("/api/stats");
            if (res.ok) {
                const s = await res.json();
                document.getElementById("statClaims").textContent = s.total_claims_processed;
                document.getElementById("statAuthentic").textContent = s.authentic_passed;
                document.getElementById("statReviews").textContent = s.surveyor_reviews_queued;
                document.getElementById("statFraud").textContent = s.fraud_attempts_blocked;
                document.getElementById("statSavings").textContent = `${s.estimated_fraud_loss_prevented_inr} Payouts Protected`;
            }
        } catch (e) {
            console.error("Failed to fetch stats:", e);
        }
    }

    function resetAllIntake() {
        resetFileInput();
        gatekeeperAlert.style.display = "none";
        showRegistrationStep();
    }

    // ─────────────────────────────────────────────────────────────
    // 10. FRAUD ANALYTICS VIEW CONTROLLER
    // ─────────────────────────────────────────────────────────────

    async function loadAnalytics() {
        try {
            const res = await fetch("/api/analytics");
            if (!res.ok) return;
            const data = await res.json();

            // Populate vector bars
            if (analyticsVectorsContainer && data.fraud_vectors) {
                analyticsVectorsContainer.innerHTML = data.fraud_vectors.map(v => {
                    const color = v.severity === "CRITICAL" ? "var(--danger)" : (v.severity === "HIGH" ? "var(--purple)" : "var(--primary)");
                    return `
                        <div>
                            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px;">
                                <strong>${v.vector}</strong>
                                <span style="font-weight: 600; color: ${color};">${v.count} Caught (${v.percentage}%)</span>
                            </div>
                            <div style="height: 10px; background: #e2e8f0; border-radius: var(--radius-full); overflow: hidden;">
                                <div style="width: ${v.percentage}%; height: 100%; background: ${color}; border-radius: var(--radius-full); transition: width 0.6s ease;"></div>
                            </div>
                        </div>
                    `;
                }).join("");
            }

            // Populate layer matrix
            if (analyticsLayerContainer && data.layer_performance) {
                analyticsLayerContainer.innerHTML = data.layer_performance.map(lp => `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #f8fafc; border: 1px solid var(--border-light); border-radius: var(--radius-sm);">
                        <div>
                            <strong style="color: var(--text-primary); font-size: 13px;">${lp.layer}</strong>
                            <div style="font-size: 11px; color: var(--text-muted);">${lp.status}</div>
                        </div>
                        <span class="badge-count ${lp.flagged > 0 ? 'badge-review' : 'badge-authentic'}" style="font-size: 12px; font-weight: 700;">
                            ${lp.flagged} Flagged
                        </span>
                    </div>
                `).join("");
            }

            // Populate component risk table
            if (analyticsRiskBody && data.component_risk) {
                analyticsRiskBody.innerHTML = data.component_risk.map(cr => {
                    const badgeClass = cr.risk_level === "HIGH" ? "badge-review text-red" : (cr.risk_level === "MEDIUM" ? "badge-review" : "badge-authentic");
                    return `
                        <tr>
                            <td><strong>${cr.part}</strong></td>
                            <td>${cr.claims}</td>
                            <td><strong class="${cr.fraud_count > 2 ? 'text-red' : ''}">${cr.fraud_count}</strong></td>
                            <td><span class="part-card-status-badge ${badgeClass}" style="position: static; font-size: 11px;">${cr.risk_level} RISK</span></td>
                            <td><strong>${cr.est_exposure}</strong></td>
                            <td><small style="color: var(--text-muted);">Mandatory 5-Layer Sensor & ELA Gatekeeping</small></td>
                        </tr>
                    `;
                }).join("");
            }

            if (analyticsFraudRate) analyticsFraudRate.textContent = "26.2%";
            if (analyticsAiCaught) analyticsAiCaught.textContent = "5";
            if (analyticsDuplicates) analyticsDuplicates.textContent = "4";
            if (analyticsLossAvoided) analyticsLossAvoided.textContent = "₹4,95,000";

        } catch (e) {
            console.error("Failed to load analytics:", e);
        }
    }

    if (btnRefreshAnalytics) {
        btnRefreshAnalytics.addEventListener("click", () => {
            loadAnalytics();
        });
    }

    // ─────────────────────────────────────────────────────────────
    // 11. AUDIT POLICIES VIEW CONTROLLER
    // ─────────────────────────────────────────────────────────────

    async function loadPolicies() {
        try {
            const res = await fetch("/api/policies");
            if (!res.ok) return;
            const pol = await res.json();

            if (polLayer1) polLayer1.value = pol.layer1_magic_bytes || "STRICT";
            if (polLayer2) polLayer2.value = pol.layer2_exif_messaging_mode || "RELAXED_REVIEW";
            if (polLayer3) polLayer3.value = pol.layer3_ela_sensitivity || "MEDIUM";
            if (polLayer4) {
                polLayer4.value = pol.layer4_phash_hamming_cutoff || 5;
                if (polLayer4Val) polLayer4Val.textContent = `${polLayer4.value} bits`;
            }
            if (polLayer5) {
                polLayer5.value = pol.layer5_ai_inpainting_threshold || 75;
                if (polLayer5Val) polLayer5Val.textContent = `${polLayer5.value}%`;
            }
            if (polApproveFloor) {
                polApproveFloor.value = pol.routing_auto_approve_floor || 80;
                if (polApproveFloorVal) polApproveFloorVal.textContent = `${polApproveFloor.value}%`;
            }
            if (polReviewFloor) {
                polReviewFloor.value = pol.routing_surveyor_review_floor || 50;
                if (polReviewFloorVal) polReviewFloorVal.textContent = `${polReviewFloor.value}%`;
            }
            if (polAlerts) polAlerts.checked = pol.alert_notifications_enabled !== false;
        } catch (e) {
            console.error("Failed to load policies:", e);
        }
    }

    // Live slider value labels
    if (polLayer4 && polLayer4Val) {
        polLayer4.addEventListener("input", (e) => {
            polLayer4Val.textContent = `${e.target.value} bits`;
        });
    }
    if (polLayer5 && polLayer5Val) {
        polLayer5.addEventListener("input", (e) => {
            polLayer5Val.textContent = `${e.target.value}%`;
        });
    }
    if (polApproveFloor && polApproveFloorVal) {
        polApproveFloor.addEventListener("input", (e) => {
            polApproveFloorVal.textContent = `${e.target.value}%`;
        });
    }
    if (polReviewFloor && polReviewFloorVal) {
        polReviewFloor.addEventListener("input", (e) => {
            polReviewFloorVal.textContent = `${e.target.value}%`;
        });
    }

    async function savePolicies() {
        const payload = {
            layer1_magic_bytes: polLayer1 ? polLayer1.value : "STRICT",
            layer2_exif_messaging_mode: polLayer2 ? polLayer2.value : "RELAXED_REVIEW",
            layer3_ela_sensitivity: polLayer3 ? polLayer3.value : "MEDIUM",
            layer4_phash_hamming_cutoff: polLayer4 ? parseInt(polLayer4.value) : 5,
            layer5_ai_inpainting_threshold: polLayer5 ? parseInt(polLayer5.value) : 75,
            routing_auto_approve_floor: polApproveFloor ? parseInt(polApproveFloor.value) : 80,
            routing_surveyor_review_floor: polReviewFloor ? parseInt(polReviewFloor.value) : 50,
            alert_notifications_enabled: polAlerts ? polAlerts.checked : true,
        };

        try {
            if (btnSavePolicies) {
                btnSavePolicies.disabled = true;
                btnSavePolicies.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            }
            const res = await fetch("/api/policies", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            if (res.ok) {
                if (policyAlert) {
                    policyAlert.style.display = "flex";
                    setTimeout(() => {
                        policyAlert.style.display = "none";
                    }, 4000);
                }
            } else {
                alert("Failed to save policy settings.");
            }
        } catch (e) {
            console.error("Failed to save policies:", e);
            alert("Error saving policies.");
        } finally {
            if (btnSavePolicies) {
                btnSavePolicies.disabled = false;
                btnSavePolicies.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Policy Settings';
            }
        }
    }

    if (btnSavePolicies) {
        btnSavePolicies.addEventListener("click", () => {
            savePolicies();
        });
    }

    if (btnResetPolicies) {
        btnResetPolicies.addEventListener("click", () => {
            if (polLayer1) polLayer1.value = "STRICT";
            if (polLayer2) polLayer2.value = "RELAXED_REVIEW";
            if (polLayer3) polLayer3.value = "MEDIUM";
            if (polLayer4) {
                polLayer4.value = 5;
                if (polLayer4Val) polLayer4Val.textContent = "5 bits";
            }
            if (polLayer5) {
                polLayer5.value = 75;
                if (polLayer5Val) polLayer5Val.textContent = "75%";
            }
            if (polApproveFloor) {
                polApproveFloor.value = 80;
                if (polApproveFloorVal) polApproveFloorVal.textContent = "80%";
            }
            if (polReviewFloor) {
                polReviewFloor.value = 50;
                if (polReviewFloorVal) polReviewFloorVal.textContent = "50%";
            }
            if (polAlerts) polAlerts.checked = true;
            savePolicies();
        });
    }
});
