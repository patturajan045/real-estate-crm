/**
 * properties.js - Inventory Management (Units, Projects, Buildings)
 */

let unitsTable = null;
let projectsTable = null;
let buildingsTable = null;
let cachedProjects = [];
let cachedBuildings = [];

document.addEventListener("DOMContentLoaded", async () => {
  if (!CRM.requireAuth()) return;
  await loadProjectsAndBuildings();
  initUnitsTable();
  initProjectsTable();
  initBuildingsTable();
});

async function loadProjectsAndBuildings() {
  try {
    const [projRes, bldRes] = await Promise.all([
      CRM.api("/api/projects/"),
      CRM.api("/api/buildings/")
    ]);

    if (projRes.status === "success") {
      cachedProjects = projRes.data;
      populateProjectDropdowns();
    }
    if (bldRes.status === "success") {
      cachedBuildings = bldRes.data;
    }
  } catch (e) {
    console.warn("Error fetching projects or buildings", e);
  }
}

function populateProjectDropdowns() {
  const filterSelect = document.getElementById("unitFilterProject");
  const unitProjSelect = document.getElementById("unitProjectSelect");
  const bldProjSelect = document.getElementById("buildingProjectSelect");

  if (filterSelect) filterSelect.innerHTML = '<option value="">All Projects</option>';
  if (unitProjSelect) unitProjSelect.innerHTML = '<option value="">-- Choose Project --</option>';
  if (bldProjSelect) bldProjSelect.innerHTML = '<option value="">-- Choose Project --</option>';

  cachedProjects.forEach(p => {
    const opt = `<option value="${p.id}">${p.name} (${p.city})</option>`;
    if (filterSelect) filterSelect.innerHTML += opt;
    if (unitProjSelect) unitProjSelect.innerHTML += opt;
    if (bldProjSelect) bldProjSelect.innerHTML += opt;
  });
}

function populateBuildingSelectForUnit(projectId, selectedBuildingId = null) {
  const bldSelect = document.getElementById("unitBuildingSelect");
  if (!bldSelect) return;
  bldSelect.innerHTML = '<option value="">-- Choose Building --</option>';

  if (!projectId) return;

  const filtered = cachedBuildings.filter(b => b.project === projectId || (b.project && b.project.id === projectId));
  filtered.forEach(b => {
    const isSel = selectedBuildingId && (b.id === selectedBuildingId) ? "selected" : "";
    bldSelect.innerHTML += `<option value="${b.id}" ${isSel}>${b.name}</option>`;
  });
}

// UNITS TABLE
function initUnitsTable() {
  unitsTable = CRM.initDataTable("#unitsTable", {
    ajax: {
      url: "/api/units/",
      data: function(d) {
        const proj = document.getElementById("unitFilterProject") ? document.getElementById("unitFilterProject").value : "";
        const status = document.getElementById("unitFilterStatus") ? document.getElementById("unitFilterStatus").value : "All";
        const type = document.getElementById("unitFilterType") ? document.getElementById("unitFilterType").value : "All";
        if (proj) d.project_id = proj;
        if (status !== "All") d.status = status;
        if (type !== "All") d.unit_type = type;
      },
      dataSrc: "data"
    },
    columns: [
      {
        data: "unitNumber",
        render: function(data) {
          return `<span class="fw-bold text-dark font-monospace">${data}</span>`;
        }
      },
      { data: "buildingName", defaultContent: "-" },
      { data: "projectName", defaultContent: "-" },
      { data: "floor" },
      {
        data: "unitType",
        render: function(data) {
          return `<span class="badge bg-light text-dark border">${data}</span>`;
        }
      },
      {
        data: "carpetAreaSqFt",
        render: function(data) {
          return `${data} sq ft`;
        }
      },
      {
        data: "price",
        render: function(data) {
          return `<span class="fw-bold text-primary">${CRM.formatCurrency(data)}</span>`;
        }
      },
      {
        data: "status",
        render: function(data) {
          return CRM.getStatusBadge(data);
        }
      },
      {
        data: null,
        orderable: false,
        className: "text-end",
        render: function(data, type, row) {
          const user = CRM.getUser();
          const isAdmin = user && (user.role === "Super Admin" || user.role === "Admin");
          const canBook = row.status === "Available";

          const bookBtn = canBook
            ? `<a href="/bookings?unit_id=${row.id}" class="btn btn-sm btn-outline-success py-1 px-2" title="Book this unit"><i class="fas fa-check-circle me-1"></i>Book</a>`
            : `<button class="btn btn-sm btn-light py-1 px-2 text-muted" disabled title="Not available"><i class="fas fa-ban me-1"></i>Unavailable</button>`;

          const adminActions = isAdmin
            ? `
              <button class="btn btn-sm btn-outline-secondary py-1 px-2" onclick="openEditUnitModal('${row.id}')" title="Edit Unit"><i class="fas fa-edit"></i></button>
              <button class="btn btn-sm btn-outline-danger py-1 px-2" onclick="deleteUnit('${row.id}', '${row.unitNumber}')" title="Delete Unit"><i class="fas fa-trash"></i></button>
            `
            : "";

          return `<div class="btn-group btn-group-sm gap-1">${bookBtn}${adminActions}</div>`;
        }
      }
    ]
  });
}

function applyUnitFilters() {
  if (unitsTable) unitsTable.ajax.reload();
}

// PROJECTS TABLE
function initProjectsTable() {
  projectsTable = CRM.initDataTable("#projectsTable", {
    ajax: {
      url: "/api/projects/",
      dataSrc: "data"
    },
    columns: [
      {
        data: "name",
        render: function(data, type, row) {
          return `<div class="fw-bold text-dark">${data}</div><div class="small text-muted">${row.address || ""}</div>`;
        }
      },
      {
        data: "city",
        render: function(data, type, row) {
          return `${data}, ${row.state || ""}`;
        }
      },
      { data: "builder", defaultContent: "-" },
      {
        data: "status",
        render: function(data) {
          const cls = data === "Ready to Move" ? "bg-success-subtle text-success" : data === "Under Construction" ? "bg-primary-subtle text-primary" : "bg-warning-subtle text-warning";
          return `<span class="badge ${cls}">${data}</span>`;
        }
      },
      {
        data: null,
        orderable: false,
        className: "text-end",
        render: function(data, type, row) {
          const user = CRM.getUser();
          if (!user || (user.role !== "Super Admin" && user.role !== "Admin")) {
            return '<span class="text-muted small">View Only</span>';
          }
          return `
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-secondary" onclick="openEditProjectModal('${row.id}')"><i class="fas fa-edit"></i></button>
              <button class="btn btn-outline-danger" onclick="deleteProject('${row.id}', '${row.name}')"><i class="fas fa-trash"></i></button>
            </div>
          `;
        }
      }
    ]
  });
}

// BUILDINGS TABLE
function initBuildingsTable() {
  buildingsTable = CRM.initDataTable("#buildingsTable", {
    ajax: {
      url: "/api/buildings/",
      dataSrc: "data"
    },
    columns: [
      { data: "name", className: "fw-bold text-dark" },
      { data: "projectName", defaultContent: "-" },
      {
        data: "totalFloors",
        render: function(data) {
          return `${data} Floors`;
        }
      },
      { data: "notes", defaultContent: "-" },
      {
        data: null,
        orderable: false,
        className: "text-end",
        render: function(data, type, row) {
          const user = CRM.getUser();
          if (!user || (user.role !== "Super Admin" && user.role !== "Admin")) {
            return '<span class="text-muted small">View Only</span>';
          }
          return `
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-secondary" onclick="openEditBuildingModal('${row.id}')"><i class="fas fa-edit"></i></button>
              <button class="btn btn-outline-danger" onclick="deleteBuilding('${row.id}', '${row.name}')"><i class="fas fa-trash"></i></button>
            </div>
          `;
        }
      }
    ]
  });
}

// UNIT MODAL ACTIONS
function openAddUnitModal() {
  const form = document.getElementById("unitForm");
  form.reset();
  document.getElementById("unitId").value = "";
  document.getElementById("unitModalTitle").innerHTML = '<i class="fas fa-door-open text-primary me-2"></i>Add Property Unit';
  document.getElementById("unitStatusField").value = "Available";
  new bootstrap.Modal(document.getElementById("unitModal")).show();
}

async function openEditUnitModal(unitId) {
  try {
    const res = await CRM.api(`/api/units/${unitId}`);
    if (res.status === "success" && res.data) {
      const u = res.data;
      const form = document.getElementById("unitForm");
      form.reset();
      CRM.fillForm(form, u);
      document.getElementById("unitId").value = u.id;
      document.getElementById("unitModalTitle").innerHTML = '<i class="fas fa-edit text-primary me-2"></i>Edit Unit Details';

      if (u.project) {
        document.getElementById("unitProjectSelect").value = u.project;
        populateBuildingSelectForUnit(u.project, u.building);
      }

      new bootstrap.Modal(document.getElementById("unitModal")).show();
    }
  } catch (e) {
    CRM.error("Could not load unit details.");
  }
}

async function saveUnit(e) {
  e.preventDefault();
  const form = document.getElementById("unitForm");
  const data = CRM.serializeForm(form);
  const unitId = document.getElementById("unitId").value;
  delete data.unitId;
  const isEdit = Boolean(unitId);

  try {
    let res;
    if (isEdit) {
      res = await CRM.api(`/api/units/${unitId}`, "PUT", data);
    } else {
      res = await CRM.api("/api/units/", "POST", data);
    }

    if (res.status === "success") {
      bootstrap.Modal.getInstance(document.getElementById("unitModal")).hide();
      CRM.success(isEdit ? "Unit updated successfully" : "Unit added successfully");
      if (unitsTable) unitsTable.ajax.reload();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to save unit");
  }
}

async function deleteUnit(id, number) {
  const ok = await CRM.confirm("Delete Unit?", `Remove unit "${number}" permanently?`, "Yes, Delete");
  if (!ok) return;
  try {
    await CRM.api(`/api/units/${id}`, "DELETE");
    CRM.success("Unit deleted successfully");
    if (unitsTable) unitsTable.ajax.reload();
  } catch (e) {
    CRM.error(e.message || "Failed to delete unit");
  }
}

// PROJECT MODAL ACTIONS
function openAddProjectModal() {
  const form = document.getElementById("projectForm");
  form.reset();
  document.getElementById("projectId").value = "";
  document.getElementById("projectModalTitle").innerHTML = '<i class="fas fa-city text-primary me-2"></i>Add Project';
  new bootstrap.Modal(document.getElementById("projectModal")).show();
}

async function openEditProjectModal(projectId) {
  try {
    const res = await CRM.api(`/api/projects/${projectId}`);
    if (res.status === "success" && res.data) {
      const p = res.data;
      const form = document.getElementById("projectForm");
      form.reset();
      CRM.fillForm(form, p);
      document.getElementById("projectId").value = p.id;
      document.getElementById("projectModalTitle").innerHTML = '<i class="fas fa-edit text-primary me-2"></i>Edit Project';
      new bootstrap.Modal(document.getElementById("projectModal")).show();
    }
  } catch (e) {
    CRM.error("Could not load project details.");
  }
}

async function saveProject(e) {
  e.preventDefault();
  const form = document.getElementById("projectForm");
  const data = CRM.serializeForm(form);
  const projectId = document.getElementById("projectId").value;
  delete data.projectId;
  const isEdit = Boolean(projectId);

  try {
    let res;
    if (isEdit) {
      res = await CRM.api(`/api/projects/${projectId}`, "PUT", data);
    } else {
      res = await CRM.api("/api/projects/", "POST", data);
    }

    if (res.status === "success") {
      bootstrap.Modal.getInstance(document.getElementById("projectModal")).hide();
      CRM.success(isEdit ? "Project updated successfully" : "Project added successfully");
      await loadProjectsAndBuildings();
      if (projectsTable) projectsTable.ajax.reload();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to save project");
  }
}

async function deleteProject(id, name) {
  const ok = await CRM.confirm("Delete Project?", `Are you sure you want to delete project "${name}" and all associated buildings/units?`, "Yes, Delete");
  if (!ok) return;
  try {
    await CRM.api(`/api/projects/${id}`, "DELETE");
    CRM.success("Project deleted successfully");
    await loadProjectsAndBuildings();
    if (projectsTable) projectsTable.ajax.reload();
    if (buildingsTable) buildingsTable.ajax.reload();
    if (unitsTable) unitsTable.ajax.reload();
  } catch (e) {
    CRM.error(e.message || "Failed to delete project");
  }
}

// BUILDING MODAL ACTIONS
function openAddBuildingModal() {
  const form = document.getElementById("buildingForm");
  form.reset();
  document.getElementById("buildingId").value = "";
  document.getElementById("buildingModalTitle").innerHTML = '<i class="fas fa-building text-primary me-2"></i>Add Building';
  new bootstrap.Modal(document.getElementById("buildingModal")).show();
}

async function openEditBuildingModal(buildingId) {
  try {
    const res = await CRM.api(`/api/buildings/${buildingId}`);
    if (res.status === "success" && res.data) {
      const b = res.data;
      const form = document.getElementById("buildingForm");
      CRM.fillForm(form, b);
      document.getElementById("buildingId").value = b.id;
      if (b.project) {
        document.getElementById("buildingProjectSelect").value = b.project;
      }
      document.getElementById("buildingModalTitle").innerHTML = '<i class="fas fa-edit text-primary me-2"></i>Edit Building';
      new bootstrap.Modal(document.getElementById("buildingModal")).show();
    }
  } catch (err) {
    CRM.error("Could not load building details.");
  }
}

async function saveBuilding(e) {
  e.preventDefault();
  const form = document.getElementById("buildingForm");
  const data = CRM.serializeForm(form);
  const buildingId = document.getElementById("buildingId").value;
  delete data.buildingId;
  const isEdit = Boolean(buildingId);

  try {
    let res;
    if (isEdit) {
      res = await CRM.api(`/api/buildings/${buildingId}`, "PUT", data);
    } else {
      res = await CRM.api("/api/buildings/", "POST", data);
    }

    if (res.status === "success") {
      bootstrap.Modal.getInstance(document.getElementById("buildingModal")).hide();
      CRM.success(isEdit ? "Building updated successfully" : "Building added successfully");
      await loadProjectsAndBuildings();
      if (buildingsTable) buildingsTable.ajax.reload();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to save building");
  }
}

async function deleteBuilding(id, name) {
  const ok = await CRM.confirm("Delete Building?", `Are you sure you want to delete building "${name}"?`, "Yes, Delete");
  if (!ok) return;
  try {
    await CRM.api(`/api/buildings/${id}`, "DELETE");
    CRM.success("Building deleted successfully");
    await loadProjectsAndBuildings();
    if (buildingsTable) buildingsTable.ajax.reload();
    if (unitsTable) unitsTable.ajax.reload();
  } catch (e) {
    CRM.error(e.message || "Failed to delete building");
  }
}
