(() => {
  const TOTAL_STEPS = 8;
  let currentStep = 1;

  const panels = () => document.querySelectorAll(".step-panel");
  const progressBar = document.getElementById("progress-bar");
  const stepLabel = document.getElementById("step-label");
  const stepPct = document.getElementById("step-pct");
  const btnPrev = document.getElementById("btn-prev");
  const btnNext = document.getElementById("btn-next");
  const btnSubmit = document.getElementById("btn-submit");
  const errBox = document.getElementById("form-errors");

  function showStep(n) {
    panels().forEach((p) => {
      p.classList.toggle("hidden", parseInt(p.dataset.step) !== n);
    });
    const pct = Math.round((n / TOTAL_STEPS) * 100);
    progressBar.style.width = pct + "%";
    stepLabel.textContent = `Step ${n} of ${TOTAL_STEPS}`;
    stepPct.textContent = pct + "%";

    btnPrev.classList.toggle("hidden", n === 1);
    btnNext.classList.toggle("hidden", n === TOTAL_STEPS);
    btnSubmit.classList.toggle("hidden", n !== TOTAL_STEPS);

    if (n === TOTAL_STEPS) buildReview();
    errBox.classList.add("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function validateCurrentStep() {
    const panel = document.querySelector(`.step-panel[data-step="${currentStep}"]`);
    const required = panel.querySelectorAll("[required]");
    let valid = true;
    required.forEach((el) => {
      el.classList.remove("border-red-500");
      const empty =
        el.tagName === "SELECT"
          ? !el.value
          : !el.value.trim();
      if (empty) {
        el.classList.add("border-red-500");
        valid = false;
      }
    });

    // At least one checkbox checked for lead_receive_method (step 4)
    if (currentStep === 4) {
      const boxes = panel.querySelectorAll('input[name="lead_receive_method"]');
      if (boxes.length > 0 && !Array.from(boxes).some((b) => b.checked)) {
        valid = false;
        boxes.forEach((b) => b.closest("label")?.classList.add("text-red-500"));
      }
    }

    return valid;
  }

  function buildReview() {
    const form = document.getElementById("onboarding-form");
    const data = new FormData(form);
    const summary = document.getElementById("review-summary");
    const sections = [
      ["Business", ["company_name","owner_name","phone","best_email","website","city_state"]],
      ["Services", ["services_offered","top_revenue_service","more_leads_service","avg_project_size","service_area"]],
      ["Goals", ["primary_goal","success_90_days","leads_per_month","grow_or_steady"]],
      ["Budget", ["monthly_ad_budget","ran_ads_before","ads_live_when","approve_ad_copy"]],
    ];

    const labelMap = {
      company_name: "Company", owner_name: "Contact", phone: "Phone",
      best_email: "Email", website: "Website", city_state: "Location",
      services_offered: "Services", top_revenue_service: "Top Revenue Service",
      more_leads_service: "Want More Leads For", avg_project_size: "Avg Project Size",
      service_area: "Service Area", primary_goal: "Primary Goal",
      success_90_days: "90-Day Success", leads_per_month: "Leads/Month",
      grow_or_steady: "Growth Plan", monthly_ad_budget: "Monthly Budget",
      ran_ads_before: "Run Ads Before", ads_live_when: "Ads Live",
      approve_ad_copy: "Ad Copy Approval",
    };

    summary.innerHTML = sections.map(([title, fields]) => `
      <div class="border-t border-gray-100 pt-4">
        <h3 class="font-semibold text-gray-700 mb-2">${title}</h3>
        <dl class="space-y-1">
          ${fields.map(f => {
            const v = data.getAll(f).filter(Boolean).join(", ") || "—";
            return `<div class="flex gap-2"><dt class="text-gray-400 min-w-[140px]">${labelMap[f] || f}:</dt><dd>${v}</dd></div>`;
          }).join("")}
        </dl>
      </div>
    `).join("");
  }

  btnNext.addEventListener("click", () => {
    if (!validateCurrentStep()) {
      showError("Please fill in all required fields before continuing.");
      return;
    }
    currentStep++;
    showStep(currentStep);
  });

  btnPrev.addEventListener("click", () => {
    currentStep--;
    showStep(currentStep);
  });

  // Handle AJAX submit with error feedback
  document.getElementById("onboarding-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    btnSubmit.disabled = true;
    btnSubmit.textContent = "Submitting…";

    try {
      const form = e.target;
      const resp = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
      });

      if (resp.redirected) {
        window.location.href = resp.url;
        return;
      }
      if (resp.status === 422) {
        const { errors } = await resp.json();
        const msgs = Object.values(errors).join(" ");
        showError(msgs);
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Submit →";
        return;
      }
      // Fallback — follow redirect manually
      window.location.href = "/form/success";
    } catch (err) {
      showError("Something went wrong. Please try again.");
      btnSubmit.disabled = false;
      btnSubmit.textContent = "Submit →";
    }
  });

  function showError(msg) {
    errBox.textContent = msg;
    errBox.classList.remove("hidden");
  }

  showStep(1);
})();
