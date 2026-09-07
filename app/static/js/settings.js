/**
 * settings.js - Platform Settings & Dynamic Content CMS Manager
 * Exclusively accessible by Super Admin and Admin to dynamically manage all headings
 */

let groupedContentData = {};

document.addEventListener("DOMContentLoaded", () => {
  // Enforce access control: Exclusively accessible by Super Admin
  if (!CRM.requireAuth(["Super Admin"])) return;
  loadGroupedContent();
});

async function loadGroupedContent() {
  const container = document.getElementById("cmsAccordionContainer");
  if (!container) return;

  container.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-primary mb-2"></div>
      <p class="text-muted small">Loading platform content settings...</p>
    </div>
  `;

  try {
    const res = await CRM.api("/api/cms/content/grouped");
    if (res.status === "success" && res.data) {
      groupedContentData = res.data;
      renderGroupedContentUI(groupedContentData);
    }
  } catch (err) {
    container.innerHTML = `
      <div class="alert alert-danger">
        Failed to load content settings. Please refresh or check connection.
      </div>
    `;
  }
}

function renderGroupedContentUI(grouped) {
  const container = document.getElementById("cmsAccordionContainer");
  if (!container) return;

  const pageNames = {
    navigation: { title: "Global Navigation & Sidebar", icon: "fa-compass", color: "text-primary" },
    dashboard: { title: "Dashboard Page", icon: "fa-chart-pie", color: "text-primary" },
    leads: { title: "Leads Pipeline Page", icon: "fa-user-tag", color: "text-info" },
    properties: { title: "Properties & Inventory Page", icon: "fa-city", color: "text-success" },
    bookings: { title: "Bookings Page", icon: "fa-file-signature", color: "text-warning" },
    login: { title: "Login Page", icon: "fa-sign-in-alt", color: "text-secondary" },
    register: { title: "Register Page", icon: "fa-user-plus", color: "text-secondary" },
    users: { title: "Team / Users Page", icon: "fa-users-cog", color: "text-danger" },
    settings: { title: "Platform Settings Page", icon: "fa-sliders-h", color: "text-dark" },
  };

  let html = `<div class="accordion" id="cmsAccordion">`;
  let index = 0;

  for (const [pageKey, items] of Object.entries(grouped)) {
    const meta = pageNames[pageKey] || { title: pageKey.toUpperCase(), icon: "fa-file-alt", color: "text-primary" };
    const collapseId = `collapse_${pageKey}`;
    const headingId = `heading_${pageKey}`;
    const isFirst = index === 0;

    html += `
      <div class="accordion-item border mb-3 rounded overflow-hidden shadow-sm">
        <h2 class="accordion-header" id="${headingId}">
          <button class="accordion-button ${isFirst ? '' : 'collapsed'} fw-semibold" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}">
            <i class="fas ${meta.icon} ${meta.color} me-2 fs-5"></i>
            ${meta.title}
            <span class="badge bg-light text-secondary border ms-2">${items.length} items</span>
          </button>
        </h2>
        <div id="${collapseId}" class="accordion-collapse collapse ${isFirst ? 'show' : ''}" data-bs-parent="#cmsAccordion">
          <div class="accordion-body bg-light p-3">
            <div class="row g-3">
              ${items.map(item => `
                <div class="col-12">
                  <div class="card border p-3 bg-white">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                      <label class="form-label fw-bold text-dark mb-0 small">
                        ${item.label}
                      </label>
                      <span class="badge bg-secondary-subtle text-secondary small font-monospace" style="font-size:0.7rem;">
                        ${item.sectionKey}
                      </span>
                    </div>
                    <div class="small text-muted mb-2">Type: <span class="badge bg-light text-muted border text-uppercase" style="font-size:0.65rem;">${item.contentType}</span></div>
                    ${item.contentType === 'paragraph' || item.contentType === 'notice' || item.content.length > 80
                      ? `<textarea class="form-control cms-input" data-key="${item.sectionKey}" rows="2">${item.content}</textarea>`
                      : `<input type="text" class="form-control cms-input" data-key="${item.sectionKey}" value="${escapeHtml(item.content)}">`
                    }
                  </div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      </div>
    `;
    index++;
  }

  html += `</div>`;
  container.innerHTML = html;
}

function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

async function saveAllCmsChanges() {
  const inputs = document.querySelectorAll(".cms-input");
  const updates = {};

  inputs.forEach(input => {
    const key = input.getAttribute("data-key");
    const val = input.value.trim();
    if (key) {
      updates[key] = val;
    }
  });

  const saveBtn = document.getElementById("btnSaveCms");
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving Settings...';
  }

  try {
    const res = await CRM.api("/api/cms/content/batch", "PUT", { updates });
    if (res.status === "success") {
      CRM.success(
        `Successfully updated ${res.updatedCount} text elements across the platform.`,
        "Content Updated!"
      );
      // Refresh local CRM content cache
      await CRM.loadDynamicContent();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to update content");
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save All Headings';
    }
  }
}

async function resetCmsToDefaults() {
  const ok = await CRM.confirm(
    "Reset All Headings?",
    "Are you sure you want to revert all headings, titles, and paragraphs to system canonical defaults? Your custom changes will be overwritten.",
    "Yes, Reset",
    "warning"
  );
  if (!ok) return;

  try {
    const res = await CRM.api("/api/cms/reset", "POST");
    if (res.status === "success") {
      CRM.success("All headings and paragraphs have been restored to defaults.");
      await loadGroupedContent();
      await CRM.loadDynamicContent();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to reset content");
  }
}
