/**
 * leads.js - Leads Management, Stages, Activity Timeline & Notes
 */

let leadsDataTable = null;
let currentStageFilter = "All";
let activeLeadForTimeline = null;
let allUsersList = [];

document.addEventListener("DOMContentLoaded", async () => {
  if (!CRM.requireAuth()) return;
  await loadUsers();
  initLeadsTable();
  setupStagePills();
});

async function loadUsers() {
  try {
    const res = await CRM.api("/api/users/");
    if (res.status === "success") {
      allUsersList = res.data;
      const select = document.getElementById("selectAssignedTo");
      if (!select) return;
      select.innerHTML = '<option value="">-- Unassigned --</option>';
      allUsersList.forEach(u => {
        if (u.isActive) {
          select.innerHTML += `<option value="${u.id}">${u.name} (${u.role})</option>`;
        }
      });
    }
  } catch (e) {
    console.warn("Could not load users for assignment dropdown", e);
  }
}

function setupStagePills() {
  const pills = document.querySelectorAll(".stage-pill");
  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => {
        p.classList.remove("btn-primary");
        p.classList.add("btn-outline-secondary");
      });
      pill.classList.remove("btn-outline-secondary");
      pill.classList.add("btn-primary");

      currentStageFilter = pill.getAttribute("data-stage");
      reloadLeadsTable();
    });
  });
}

function initLeadsTable() {
  leadsDataTable = CRM.initDataTable("#leadsTable", {
    ajax: {
      url: "/api/leads/",
      data: function(d) {
        if (currentStageFilter !== "All") {
          d.stage = currentStageFilter;
        }
      },
      dataSrc: "data"
    },
    columns: [
      {
        data: "customerName",
        render: function(data, type, row) {
          const city = row.city ? `<span class="text-muted small"><i class="fas fa-map-marker-alt me-1"></i>${row.city}</span>` : "";
          return `
            <div>
              <a href="javascript:void(0)" class="fw-bold text-primary text-decoration-none" onclick="openLeadTimeline('${row.id}')">${data}</a>
              <div>${city}</div>
            </div>
          `;
        }
      },
      {
        data: "phoneNumber",
        render: function(data, type, row) {
          return `
            <div><i class="fas fa-phone me-1 text-muted small"></i>${data}</div>
            <div class="small text-muted"><i class="far fa-envelope me-1 text-muted"></i>${row.email}</div>
          `;
        }
      },
      {
        data: "stage",
        render: function(data) {
          return CRM.getStageBadge(data);
        }
      },
      {
        data: "budgetMin",
        defaultContent: "",
        render: function(data, type, row) {
          if (!data && !row.budgetMax) return "-";
          const minStr = data ? CRM.formatCurrency(data) : "$0";
          const maxStr = row.budgetMax ? ` - ${CRM.formatCurrency(row.budgetMax)}` : "+";
          return `<span class="fw-medium">${minStr}${maxStr}</span>`;
        }
      },
      {
        data: "preferredUnitType",
        defaultContent: "",
        render: function(data) {
          return data ? `<span class="badge bg-light text-dark border">${data}</span>` : "-";
        }
      },
      {
        data: "assignedToName",
        defaultContent: "",
        render: function(data) {
          return data ? `<span class="fw-medium text-secondary">${data}</span>` : `<span class="text-muted fst-italic">Unassigned</span>`;
        }
      },
      {
        data: "nextFollowUpDate",
        defaultContent: "",
        render: function(data) {
          if (!data) return '<span class="text-muted">-</span>';
          const isOverdue = new Date(data) < new Date();
          const dateStr = CRM.formatDate(data);
          if (isOverdue) {
            return `<span class="text-danger fw-semibold"><i class="fas fa-exclamation-triangle me-1"></i>${dateStr}</span>`;
          }
          return `<span class="text-secondary">${dateStr}</span>`;
        }
      },
      {
        data: null,
        orderable: false,
        className: "text-end",
        render: function(data, type, row) {
          const user = CRM.getUser();
          const isAdmin = user && (user.role === "Super Admin" || user.role === "Admin");
          const deleteBtn = isAdmin
            ? `<button class="btn btn-outline-danger" onclick="deleteLead('${row.id}', '${row.customerName}')" title="Delete Lead"><i class="fas fa-trash"></i></button>`
            : "";
          return `
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-primary" onclick="openLeadTimeline('${row.id}')" title="Activity & Notes">
                <i class="fas fa-comments"></i>
              </button>
              <button class="btn btn-outline-secondary" onclick="openEditLeadModal('${row.id}')" title="Edit Lead">
                <i class="fas fa-edit"></i>
              </button>
              ${deleteBtn}
            </div>
          `;
        }
      }
    ]
  });
}

function reloadLeadsTable() {
  if (leadsDataTable) {
    leadsDataTable.ajax.reload();
  }
}

// Add / Edit Modal
function openAddLeadModal() {
  const form = document.getElementById("leadForm");
  form.reset();
  document.getElementById("leadId").value = "";
  document.getElementById("leadModalTitle").innerHTML = '<i class="fas fa-user-plus text-primary me-2"></i>Add New Lead';

  const currentUser = CRM.getUser();
  if (currentUser && currentUser.role === "Sales Employee") {
    const select = document.getElementById("selectAssignedTo");
    if (select) select.value = currentUser.id;
  }

  const modal = new bootstrap.Modal(document.getElementById("leadFormModal"));
  modal.show();
}

async function openEditLeadModal(leadId) {
  try {
    const res = await CRM.api(`/api/leads/${leadId}`);
    if (res.status === "success" && res.data) {
      const lead = res.data;
      const form = document.getElementById("leadForm");
      form.reset();
      CRM.fillForm(form, lead);
      document.getElementById("leadId").value = lead.id;
      document.getElementById("leadModalTitle").innerHTML = '<i class="fas fa-user-edit text-primary me-2"></i>Edit Lead Details';
      if (lead.assignedTo) {
        document.getElementById("selectAssignedTo").value = lead.assignedTo;
      }

      const modal = new bootstrap.Modal(document.getElementById("leadFormModal"));
      modal.show();
    }
  } catch (e) {
    CRM.error("Could not fetch lead details.");
  }
}

async function saveLead(e) {
  e.preventDefault();
  const form = document.getElementById("leadForm");
  const data = CRM.serializeForm(form);
  const leadId = document.getElementById("leadId").value;
  delete data.leadId;
  const isEdit = Boolean(leadId);

  try {
    let res;
    if (isEdit) {
      res = await CRM.api(`/api/leads/${leadId}`, "PUT", data);
    } else {
      res = await CRM.api("/api/leads/", "POST", data);
    }

    if (res.status === "success") {
      bootstrap.Modal.getInstance(document.getElementById("leadFormModal")).hide();
      CRM.success(isEdit ? "Lead updated successfully!" : "Lead created successfully!");
      reloadLeadsTable();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to save lead");
  }
}

async function deleteLead(leadId, name) {
  const ok = await CRM.confirm(
    "Delete Lead?",
    `Are you sure you want to delete lead "${name}"? This action cannot be undone.`,
    "Yes, Delete"
  );
  if (!ok) return;

  try {
    const res = await CRM.api(`/api/leads/${leadId}`, "DELETE");
    if (res.status === "success") {
      CRM.success("Lead removed successfully.");
      reloadLeadsTable();
    }
  } catch (e) {
    CRM.error(e.message || "Failed to delete lead");
  }
}

// Lead Timeline & Notes
async function openLeadTimeline(leadId) {
  try {
    const res = await CRM.api(`/api/leads/${leadId}`);
    if (res.status === "success" && res.data) {
      activeLeadForTimeline = res.data;
      document.getElementById("timelineLeadId").value = activeLeadForTimeline.id;
      document.getElementById("timelineLeadName").textContent = activeLeadForTimeline.customerName;
      document.getElementById("timelineLeadContact").textContent = `${activeLeadForTimeline.phoneNumber} • ${activeLeadForTimeline.email} • Stage: ${activeLeadForTimeline.stage}`;
      
      document.getElementById("newNoteContent").value = "";
      document.getElementById("newNoteStage").value = "";
      document.getElementById("newNoteNextDate").value = "";

      document.getElementById("btnConvertToBooking").onclick = () => {
        bootstrap.Modal.getInstance(document.getElementById("leadNotesModal")).hide();
        window.location.href = `/bookings?lead_id=${activeLeadForTimeline.id}`;
      };

      renderTimelineNotes(activeLeadForTimeline.notes || []);

      const modal = new bootstrap.Modal(document.getElementById("leadNotesModal"));
      modal.show();
    }
  } catch (e) {
    CRM.error("Could not load lead timeline.");
  }
}

function renderTimelineNotes(notes) {
  const container = document.getElementById("notesTimelineContainer");
  if (!notes || notes.length === 0) {
    container.innerHTML = `<div class="text-center py-4 text-muted"><i class="far fa-clipboard me-2"></i>No notes or activity logged yet. Add your first note above!</div>`;
    return;
  }

  const sorted = [...notes].reverse();

  container.innerHTML = `
    <ul class="timeline-list">
      ${sorted.map(n => `
        <li class="timeline-item">
          <div class="timeline-bullet"></div>
          <div class="timeline-card">
            <div class="d-flex align-items-center justify-content-between mb-1">
              <span class="fw-semibold text-primary small">${n.authorName || "Agent"}</span>
              <span class="text-muted" style="font-size: 0.75rem;">${CRM.formatDateTime(n.addedTime)}</span>
            </div>
            <p class="mb-0 text-dark small" style="white-space: pre-wrap;">${n.content}</p>
          </div>
        </li>
      `).join("")}
    </ul>
  `;
}

async function submitNote(e) {
  e.preventDefault();
  const leadId = document.getElementById("timelineLeadId").value;
  const content = document.getElementById("newNoteContent").value.trim();
  const stage = document.getElementById("newNoteStage").value;
  const nextFollowUpDate = document.getElementById("newNoteNextDate").value;
  const currentUser = CRM.getUser();

  const payload = {
    authorId: currentUser ? currentUser.id : "system",
    authorName: currentUser ? currentUser.name : "Sales Agent",
    content: content
  };
  if (stage) payload.stage = stage;
  if (nextFollowUpDate) payload.nextFollowUpDate = nextFollowUpDate;

  try {
    const res = await CRM.api(`/api/leads/${leadId}/notes`, "POST", payload);
    if (res.status === "success") {
      CRM.toast("Note added successfully");
      document.getElementById("newNoteContent").value = "";
      document.getElementById("newNoteStage").value = "";
      document.getElementById("newNoteNextDate").value = "";
      
      openLeadTimeline(leadId);
      reloadLeadsTable();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to add note");
  }
}
