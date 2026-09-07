/**
 * dashboard.js - Real Estate CRM Dashboard Metrics & Charts Logic
 */

let pipelineChartInstance = null;
let inventoryChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  if (!CRM.requireAuth()) return;
  loadDashboardData();
});

async function loadDashboardData() {
  try {
    const res = await CRM.api("/api/dashboard/stats");
    if (res.status === "success" && res.data) {
      renderKPIs(res.data.counts);
      renderPipelineChart(res.data.leadsByStage);
      renderInventoryChart(res.data.unitsByStatus);
      renderFollowups(res.data.followups);
      renderRecentBookings(res.data.recentBookings);
    }
  } catch (err) {
    CRM.error("Could not load dashboard statistics. Please refresh.");
  }
}

function renderKPIs(c) {
  document.getElementById("kpiTotalLeads").textContent = c.totalLeads;
  const totalPending = c.todayFollowupsCount + c.overdueFollowupsCount;
  document.getElementById("kpiFollowupsCount").textContent = totalPending;
  document.getElementById("kpiFollowupSubtitle").textContent = `${c.todayFollowupsCount} today, ${c.overdueFollowupsCount} overdue`;
  document.getElementById("badgePendingCount").textContent = `${totalPending} Urgent`;

  document.getElementById("kpiAvailableUnits").textContent = c.availableUnits;
  document.getElementById("kpiTotalUnitsSubtitle").textContent = `out of ${c.totalUnits} total units`;

  document.getElementById("kpiTotalRevenue").textContent = CRM.formatCurrency(c.totalRevenue);
  document.getElementById("kpiBookingsCount").textContent = `${c.totalBookings} confirmed bookings`;
}

function renderPipelineChart(stages) {
  const canvas = document.getElementById("leadsPipelineChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const labels = ["New", "Contacted", "Site Visit", "Interested", "Negotiation", "Booked", "Lost"];
  const data = labels.map(stage => stages[stage] || 0);

  if (pipelineChartInstance) pipelineChartInstance.destroy();

  pipelineChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Leads",
        data: data,
        backgroundColor: [
          "#38bdf8", // New
          "#c084fc", // Contacted
          "#22d3ee", // Site Visit
          "#fbbf24", // Interested
          "#fb923c", // Negotiation
          "#4ade80", // Booked
          "#94a3b8"  // Lost
        ],
        borderRadius: 6,
        maxBarThickness: 45
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0 },
          grid: { color: "#f1f5f9" }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function renderInventoryChart(units) {
  const canvas = document.getElementById("inventoryChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const labels = ["Available", "Blocked", "Booked", "Sold"];
  const data = labels.map(s => units[s] || 0);

  if (inventoryChartInstance) inventoryChartInstance.destroy();

  inventoryChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: ["#10b981", "#f59e0b", "#ef4444", "#64748b"],
        borderWidth: 2,
        borderColor: "#ffffff"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 12, font: { size: 11 } }
        }
      },
      cutout: "68%"
    }
  });
}

function renderFollowups(followups) {
  const tbody = document.getElementById("followupsListBody");
  if (!tbody) return;
  const list = [...(followups.overdue || []), ...(followups.today || [])];

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted"><i class="fas fa-check-circle text-success me-2"></i>No urgent follow-ups pending today! Great job.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(item => {
    const isOverdue = new Date(item.nextFollowUpDate) < new Date().setHours(0,0,0,0);
    const dueBadge = isOverdue
      ? `<span class="badge bg-danger-subtle text-danger"><i class="fas fa-exclamation-circle"></i> Overdue</span>`
      : `<span class="badge bg-warning-subtle text-warning"><i class="fas fa-clock"></i> Today</span>`;

    return `
      <tr>
        <td>
          <div class="fw-semibold text-dark">${item.customerName}</div>
          <div class="small text-muted"><i class="fas fa-phone-alt me-1"></i>${item.phoneNumber}</div>
        </td>
        <td>${CRM.getStageBadge(item.stage)}</td>
        <td>${dueBadge}</td>
        <td><span class="small text-secondary">${item.assignedToName}</span></td>
        <td class="text-end">
          <button class="btn btn-sm btn-primary py-1 px-2" onclick="openQuickNoteModal('${item.id}', '${item.customerName}', '${item.stage}')" title="Log call / note">
            <i class="fas fa-pen me-1"></i> Log Note
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function renderRecentBookings(bookings) {
  const tbody = document.getElementById("recentBookingsBody");
  if (!tbody) return;

  if (!bookings || bookings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No bookings recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = bookings.map(b => `
    <tr>
      <td class="fw-medium font-monospace small text-primary">${b.bookingNumber}</td>
      <td>
        <div class="fw-semibold text-dark">${b.leadName || "Customer"}</div>
        <div class="small text-muted">${b.leadPhone || ""}</div>
      </td>
      <td>
        <span class="fw-medium">${b.unitNumber || "Unit"}</span>
        <div class="small text-muted">${b.projectName || ""}</div>
      </td>
      <td class="fw-semibold text-dark">${CRM.formatCurrency(b.agreementValue)}</td>
      <td>${CRM.getStatusBadge(b.status)}</td>
    </tr>
  `).join("");
}

// Quick Lead Modal Handlers
function openQuickLeadModal() {
  const form = document.getElementById("quickLeadForm");
  form.reset();
  const modal = new bootstrap.Modal(document.getElementById("quickLeadModal"));
  modal.show();
}

async function handleCreateLead(e) {
  e.preventDefault();
  const form = document.getElementById("quickLeadForm");
  const data = CRM.serializeForm(form);
  const currentUser = CRM.getUser();

  if (currentUser && currentUser.role === "Sales Employee") {
    data.assignedTo = currentUser.id;
  }

  const initialNote = data.initialNote;
  delete data.initialNote;

  try {
    const res = await CRM.api("/api/leads/", "POST", data);
    if (res.status === "success") {
      const leadId = res.data.id;
      if (initialNote) {
        await CRM.api(`/api/leads/${leadId}/notes`, "POST", {
          authorId: currentUser ? currentUser.id : "system",
          authorName: currentUser ? currentUser.name : "Sales Rep",
          content: initialNote
        });
      }

      bootstrap.Modal.getInstance(document.getElementById("quickLeadModal")).hide();
      CRM.success("Lead created successfully!", "Success");
      loadDashboardData();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to create lead");
  }
}

// Quick Note Modal Handlers
function openQuickNoteModal(leadId, name, stage) {
  document.getElementById("noteLeadId").value = leadId;
  document.getElementById("noteLeadNameDisplay").textContent = `${name} (${stage})`;
  document.getElementById("noteContent").value = "";
  document.getElementById("noteStage").value = "";
  document.getElementById("noteNextFollowup").value = "";
  const modal = new bootstrap.Modal(document.getElementById("quickNoteModal"));
  modal.show();
}

async function handleSaveFollowupNote(e) {
  e.preventDefault();
  const leadId = document.getElementById("noteLeadId").value;
  const content = document.getElementById("noteContent").value.trim();
  const stage = document.getElementById("noteStage").value;
  const nextFollowUpDate = document.getElementById("noteNextFollowup").value;
  const currentUser = CRM.getUser();

  const payload = {
    authorId: currentUser ? currentUser.id : "system",
    authorName: currentUser ? currentUser.name : "Sales Rep",
    content: content
  };
  if (stage) payload.stage = stage;
  if (nextFollowUpDate) payload.nextFollowUpDate = nextFollowUpDate;

  try {
    await CRM.api(`/api/leads/${leadId}/notes`, "POST", payload);
    bootstrap.Modal.getInstance(document.getElementById("quickNoteModal")).hide();
    CRM.success("Follow-up note logged successfully!");
    loadDashboardData();
  } catch (err) {
    CRM.error(err.message || "Failed to log note");
  }
}
