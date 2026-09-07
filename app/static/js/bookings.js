/**
 * bookings.js - Bookings Management & Concurrency Guard
 */

let bookingsTable = null;
let currentStatusFilter = "All";
let cachedLeads = [];
let cachedProjects = [];
let cachedBuildings = [];

document.addEventListener("DOMContentLoaded", async () => {
  if (!CRM.requireAuth()) return;
  await Promise.all([loadLeads(), loadProjects(), loadBuildings()]);
  initBookingsTable();
  setupStatusFilter();
  checkUrlParams();
});

async function checkUrlParams() {
  const urlParams = new URLSearchParams(window.location.search);
  const leadId = urlParams.get("lead_id");
  const unitId = urlParams.get("unit_id");

  if (leadId || unitId) {
    openNewBookingModal();
    if (leadId) {
      document.getElementById("bookingLeadSelect").value = leadId;
    }
    if (unitId) {
      try {
        const uRes = await CRM.api(`/api/units/${unitId}`);
        if (uRes.status === "success" && uRes.data) {
          const u = uRes.data;
          document.getElementById("bookingProjectSelect").value = u.project;
          await onBookingProjectChange(u.project, u.building);
          await onBookingBuildingChange(u.building, u.id);
        }
      } catch (e) {
        console.warn("Could not pre-select unit from URL param", e);
      }
    }
  }
}

async function loadLeads() {
  try {
    const res = await CRM.api("/api/leads/");
    if (res.status === "success") {
      cachedLeads = res.data;
      const select = document.getElementById("bookingLeadSelect");
      if (!select) return;
      select.innerHTML = '<option value="">-- Choose Lead --</option>';
      cachedLeads.forEach(l => {
        if (l.stage !== "Booked" && l.stage !== "Lost") {
          select.innerHTML += `<option value="${l.id}">${l.customerName} (${l.phoneNumber}) - Stage: ${l.stage}</option>`;
        }
      });
    }
  } catch (e) {
    console.warn("Could not load leads", e);
  }
}

async function loadProjects() {
  try {
    const res = await CRM.api("/api/projects/");
    if (res.status === "success") {
      cachedProjects = res.data;
      const select = document.getElementById("bookingProjectSelect");
      if (!select) return;
      select.innerHTML = '<option value="">-- Choose Project --</option>';
      cachedProjects.forEach(p => {
        select.innerHTML += `<option value="${p.id}">${p.name} (${p.city})</option>`;
      });
    }
  } catch (e) {
    console.warn("Could not load projects", e);
  }
}

async function loadBuildings() {
  try {
    const res = await CRM.api("/api/buildings/");
    if (res.status === "success") {
      cachedBuildings = res.data;
    }
  } catch (e) {
    console.warn("Could not load buildings", e);
  }
}

function setupStatusFilter() {
  const btns = document.querySelectorAll(".booking-filter-btn");
  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      btns.forEach(b => {
        b.classList.remove("btn-primary");
        b.classList.add("btn-outline-secondary");
      });
      btn.classList.remove("btn-outline-secondary");
      btn.classList.add("btn-primary");

      currentStatusFilter = btn.getAttribute("data-status");
      if (bookingsTable) bookingsTable.ajax.reload();
    });
  });
}

function initBookingsTable() {
  bookingsTable = CRM.initDataTable("#bookingsTable", {
    ajax: {
      url: "/api/bookings/",
      data: function(d) {
        if (currentStatusFilter !== "All") {
          d.status = currentStatusFilter;
        }
      },
      dataSrc: "data"
    },
    columns: [
      {
        data: "bookingNumber",
        render: function(data) {
          return `<span class="fw-bold text-primary font-monospace small">${data}</span>`;
        }
      },
      {
        data: "leadName",
        render: function(data, type, row) {
          return `
            <div>
              <span class="fw-bold text-dark">${data || "Customer"}</span>
              <div class="small text-muted">${row.leadPhone || ""}</div>
            </div>
          `;
        }
      },
      {
        data: "unitNumber",
        render: function(data, type, row) {
          return `
            <div>
              <span class="fw-semibold text-dark">${data || "Unit"} (${row.unitType || ""})</span>
              <div class="small text-muted">${row.projectName || ""} - ${row.buildingName || ""}</div>
            </div>
          `;
        }
      },
      {
        data: "agreementValue",
        render: function(data) {
          return `<span class="fw-bold text-dark">${CRM.formatCurrency(data)}</span>`;
        }
      },
      {
        data: "bookingAmount",
        render: function(data) {
          return `<span class="fw-medium text-success">${CRM.formatCurrency(data)}</span>`;
        }
      },
      { data: "paymentMethod", defaultContent: "Wire Transfer" },
      {
        data: "status",
        render: function(data) {
          return CRM.getStatusBadge(data);
        }
      },
      {
        data: "bookingDate",
        render: function(data) {
          return `<span class="text-secondary small">${CRM.formatDate(data)}</span>`;
        }
      },
      {
        data: null,
        orderable: false,
        className: "text-end",
        render: function(data, type, row) {
          const isConfirmed = row.status === "Confirmed";
          const cancelBtn = isConfirmed
            ? `<button class="btn btn-sm btn-outline-danger" onclick="cancelBooking('${row.id}', '${row.bookingNumber}')" title="Cancel Booking"><i class="fas fa-times me-1"></i>Cancel</button>`
            : "";

          return `
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-primary" onclick="viewBookingDetails('${row.id}')" title="View Agreement"><i class="fas fa-eye"></i></button>
              ${cancelBtn}
            </div>
          `;
        }
      }
    ]
  });
}

// Cascading Dropdowns for Booking
async function onBookingProjectChange(projectId, selectedBuildingId = null) {
  const bldSelect = document.getElementById("bookingBuildingSelect");
  bldSelect.innerHTML = '<option value="">-- Choose Building --</option>';
  document.getElementById("bookingUnitSelect").innerHTML = '<option value="">-- Choose Available Unit --</option>';
  document.getElementById("bookingAgreementValue").value = "";

  if (!projectId) return;

  const filtered = cachedBuildings.filter(b => b.project === projectId || (b.project && b.project.id === projectId));
  filtered.forEach(b => {
    const isSel = selectedBuildingId && (b.id === selectedBuildingId) ? "selected" : "";
    bldSelect.innerHTML += `<option value="${b.id}" ${isSel}>${b.name}</option>`;
  });
}

async function onBookingBuildingChange(buildingId, selectedUnitId = null) {
  const unitSelect = document.getElementById("bookingUnitSelect");
  unitSelect.innerHTML = '<option value="">-- Choose Available Unit --</option>';
  document.getElementById("bookingAgreementValue").value = "";

  if (!buildingId) return;

  try {
    // Fetch live available units directly from DB
    const res = await CRM.api(`/api/units/?building_id=${buildingId}&status=Available`);
    let availableUnits = (res.status === "success") ? res.data : [];

    // If a specific unit was pre-selected from URL (even if already booked), fetch and include it
    if (selectedUnitId && !availableUnits.some(u => u.id === selectedUnitId)) {
      const singleRes = await CRM.api(`/api/units/${selectedUnitId}`);
      if (singleRes.status === "success" && singleRes.data) {
        availableUnits.unshift(singleRes.data);
      }
    }

    if (availableUnits.length === 0) {
      unitSelect.innerHTML = '<option value="">No Available Units in this Building</option>';
      return;
    }

    availableUnits.forEach(u => {
      const isSel = selectedUnitId && (u.id === selectedUnitId) ? "selected" : "";
      unitSelect.innerHTML += `<option value="${u.id}" ${isSel} data-price="${u.price}">${u.unitNumber} (${u.unitType}) - ${CRM.formatCurrency(u.price)}</option>`;
    });

    if (selectedUnitId) {
      onBookingUnitChange(selectedUnitId, availableUnits);
    }
  } catch (e) {
    console.warn("Could not fetch building units", e);
  }
}

function onBookingUnitChange(unitId, unitList = null) {
  const select = document.getElementById("bookingUnitSelect");
  const selectedOption = select.options[select.selectedIndex];
  if (selectedOption && selectedOption.dataset.price) {
    document.getElementById("bookingAgreementValue").value = selectedOption.dataset.price;
  }
}

function openNewBookingModal() {
  const form = document.getElementById("newBookingForm");
  form.reset();
  document.getElementById("bookingBuildingSelect").innerHTML = '<option value="">-- Choose Building --</option>';
  document.getElementById("bookingUnitSelect").innerHTML = '<option value="">-- Choose Available Unit --</option>';
  new bootstrap.Modal(document.getElementById("newBookingModal")).show();
}

// Handle Booking Creation with SweetAlert Concurrency Alert
async function handleCreateBooking(e) {
  e.preventDefault();
  const form = document.getElementById("newBookingForm");
  const data = CRM.serializeForm(form);
  const currentUser = CRM.getUser();

  if (currentUser) {
    data.bookedBy = currentUser.id;
  }

  const submitBtn = document.getElementById("btnSubmitBooking");
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Securing Unit...';

  try {
    const res = await CRM.api("/api/bookings/", "POST", data);
    if (res.status === "success") {
      bootstrap.Modal.getInstance(document.getElementById("newBookingModal")).hide();

      // SweetAlert2 Success Celebration
      Swal.fire({
        icon: "success",
        title: "Booking Confirmed!",
        html: `Agreement Number: <strong>${res.data.bookingNumber}</strong><br>Unit has been reserved successfully!`,
        confirmButtonColor: "#059669",
        confirmButtonText: "Done"
      });

      if (bookingsTable) bookingsTable.ajax.reload();
      loadLeads();
    }
  } catch (err) {
    // Handle Concurrency Double Booking Error
    if (err.status === 409) {
      Swal.fire({
        icon: "error",
        title: "Double Booking Prevented!",
        text: err.message || "This property unit was just reserved by another agent. Please select another available unit.",
        confirmButtonColor: "#dc2626",
        confirmButtonText: "Select Another Unit"
      });
    } else {
      CRM.error(err.message || "Failed to complete booking");
    }
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-check-circle me-1"></i> Confirm & Reserve Unit';
  }
}

async function cancelBooking(bookingId, number) {
  const { value: reason } = await Swal.fire({
    title: "Cancel Booking?",
    text: `Are you sure you want to cancel booking ${number}? The unit will be released back to "Available".`,
    icon: "warning",
    input: "text",
    showCancelButton: true,
    confirmButtonColor: "#dc2626",
    cancelButtonColor: "#64748b",
    confirmButtonText: "Yes, Cancel Booking",
    inputValidator: (val) => {
      if (!val) return "Please enter a cancellation reason!";
    }
  });

  if (!reason) return;

  try {
    const res = await CRM.api(`/api/bookings/${bookingId}/cancel`, "POST", { cancellationReason: reason });
    if (res.status === "success") {
      CRM.success("Booking cancelled and unit returned to Available pool.");
      if (bookingsTable) bookingsTable.ajax.reload();
    }
  } catch (e) {
    CRM.error(e.message || "Failed to cancel booking");
  }
}

async function viewBookingDetails(bookingId) {
  const modal = new bootstrap.Modal(document.getElementById("bookingDetailsModal"));
  modal.show();

  const container = document.getElementById("bookingDetailsContent");
  container.innerHTML = '<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary"></div></div>';

  try {
    const res = await CRM.api(`/api/bookings/${bookingId}`);
    if (res.status === "success" && res.data) {
      const b = res.data;
      container.innerHTML = `
        <div class="border rounded-3 p-3 bg-light mb-3">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="small text-muted font-monospace">${b.bookingNumber}</span>
            ${CRM.getStatusBadge(b.status)}
          </div>
          <h5 class="fw-bold text-dark mb-1">${CRM.formatCurrency(b.agreementValue)}</h5>
          <span class="text-muted small">Advance Deposit: <strong class="text-success">${CRM.formatCurrency(b.bookingAmount)}</strong></span>
        </div>

        <div class="row g-2 mb-3 small">
          <div class="col-6">
            <div class="text-muted">Customer Name:</div>
            <div class="fw-bold text-dark">${b.leadName || "-"}</div>
          </div>
          <div class="col-6">
            <div class="text-muted">Customer Contact:</div>
            <div class="fw-bold text-dark">${b.leadPhone || "-"}</div>
          </div>
          <div class="col-6">
            <div class="text-muted">Unit Number:</div>
            <div class="fw-bold text-dark">${b.unitNumber || "-"} (${b.unitType || ""})</div>
          </div>
          <div class="col-6">
            <div class="text-muted">Project / Building:</div>
            <div class="fw-bold text-dark">${b.projectName || ""} - ${b.buildingName || ""}</div>
          </div>
          <div class="col-6">
            <div class="text-muted">Payment Method:</div>
            <div class="fw-bold text-dark">${b.paymentMethod || "Wire Transfer"}</div>
          </div>
          <div class="col-6">
            <div class="text-muted">Transaction Ref:</div>
            <div class="fw-bold text-dark font-monospace">${b.transactionReference || "N/A"}</div>
          </div>
          <div class="col-6">
            <div class="text-muted">Booked By:</div>
            <div class="fw-bold text-dark">${b.bookedByName || "Sales Rep"}</div>
          </div>
          <div class="col-6">
            <div class="text-muted">Date:</div>
            <div class="fw-bold text-dark">${CRM.formatDate(b.bookingDate)}</div>
          </div>
        </div>

        ${b.status === "Cancelled" ? `
          <div class="alert alert-danger py-2 px-3 small">
            <strong>Cancellation Reason:</strong> ${b.cancellationReason || "No reason specified"}
          </div>
        ` : ""}
      `;
    }
  } catch (e) {
    container.innerHTML = '<div class="alert alert-danger py-2">Could not fetch booking details.</div>';
  }
}
