/**
 * users.js - Team & User Management (Super Admin & Admin only)
 */

let usersTable = null;

document.addEventListener("DOMContentLoaded", () => {
  // Only Super Admin and Admin can access Users page
  if (!CRM.requireAuth(["Super Admin", "Admin"])) return;
  initUsersTable();
});

function initUsersTable() {
  usersTable = CRM.initDataTable("#usersTable", {
    ajax: {
      url: "/api/users/",
      dataSrc: "data"
    },
    columns: [
      {
        data: "name",
        render: function(data) {
          return `
            <div class="d-flex align-items-center gap-2">
              <div class="user-avatar" style="width:32px; height:32px; font-size:0.8rem;">${data ? data.charAt(0).toUpperCase() : 'U'}</div>
              <div class="fw-semibold text-dark">${data}</div>
            </div>
          `;
        }
      },
      { data: "email" },
      { data: "phoneNumber", defaultContent: "-" },
      {
        data: "role",
        render: function(data) {
          let cls = "role-sales";
          if (data === "Super Admin") cls = "role-super-admin";
          else if (data === "Admin") cls = "role-admin";
          return `<span class="badge-crm ${cls}"><i class="fas fa-user-shield me-1"></i>${data}</span>`;
        }
      },
      {
        data: "isActive",
        render: function(data) {
          return data
            ? `<span class="badge bg-success-subtle text-success"><i class="fas fa-check-circle me-1"></i>Active</span>`
            : `<span class="badge bg-danger-subtle text-danger"><i class="fas fa-times-circle me-1"></i>Inactive</span>`;
        }
      },
      {
        data: "addedTime",
        render: function(data) {
          return `<span class="text-secondary small">${CRM.formatDate(data)}</span>`;
        }
      },
      {
        data: null,
        orderable: false,
        className: "text-end",
        render: function(data, type, row) {
          const toggleIcon = row.isActive ? "fa-user-slash text-danger" : "fa-user-check text-success";
          const toggleTitle = row.isActive ? "Deactivate User" : "Activate User";
          const deleteBtn = !row.isActive
            ? `<button class="btn btn-outline-danger" onclick="permanentlyDeleteUser('${row.id}', '${row.name}')" title="Permanently Delete Inactive User"><i class="fas fa-trash"></i></button>`
            : "";

          return `
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-secondary" onclick="openEditUserModal('${row.id}')" title="Edit User"><i class="fas fa-edit"></i></button>
              <button class="btn btn-outline-warning" onclick="openResetPasswordModal('${row.id}', '${row.name}')" title="Reset Password"><i class="fas fa-key"></i></button>
              <button class="btn btn-outline-danger" onclick="toggleUserStatus('${row.id}', '${row.name}', ${row.isActive})" title="${toggleTitle}"><i class="fas ${toggleIcon}"></i></button>
              ${deleteBtn}
            </div>
          `;
        }
      }
    ]
  });
}

function openAddUserModal() {
  const form = document.getElementById("userForm");
  form.reset();
  document.getElementById("userId").value = "";
  document.getElementById("userModalTitle").innerHTML = '<i class="fas fa-user-plus text-primary me-2"></i>Add User';
  document.getElementById("passwordRow").style.display = "";
  document.getElementById("userPasswordField").required = true;
  document.getElementById("userEmailField").disabled = false;
  new bootstrap.Modal(document.getElementById("userModal")).show();
}

async function openEditUserModal(userId) {
  try {
    const res = await CRM.api(`/api/users/${userId}`);
    if (res.status === "success" && res.data) {
      const u = res.data;
      const form = document.getElementById("userForm");
      form.reset();
      CRM.fillForm(form, u);
      document.getElementById("userId").value = u.id;
      document.getElementById("userModalTitle").innerHTML = '<i class="fas fa-user-edit text-primary me-2"></i>Edit User';
      document.getElementById("userEmailField").disabled = true;
      document.getElementById("passwordRow").style.display = "none";
      document.getElementById("userPasswordField").required = false;

      document.getElementById("userIsActiveSelect").value = String(u.isActive);

      new bootstrap.Modal(document.getElementById("userModal")).show();
    }
  } catch (e) {
    CRM.error("Could not load user details");
  }
}

async function saveUser(e) {
  e.preventDefault();
  const form = document.getElementById("userForm");
  const data = CRM.serializeForm(form);
  const userId = document.getElementById("userId").value;
  delete data.userId;
  const isEdit = Boolean(userId);

  if (isEdit && !data.password) {
    delete data.password;
  }

  data.isActive = data.isActive === "true";

  try {
    let res;
    if (isEdit) {
      res = await CRM.api(`/api/users/${userId}`, "PUT", data);
    } else {
      res = await CRM.api("/api/users/", "POST", data);
    }

    if (res.status === "success") {
      bootstrap.Modal.getInstance(document.getElementById("userModal")).hide();
      CRM.success(isEdit ? "User updated successfully" : "User created successfully");
      if (usersTable) usersTable.ajax.reload();
    }
  } catch (err) {
    CRM.error(err.message || "Failed to save user");
  }
}

async function toggleUserStatus(userId, name, currentStatus) {
  const action = currentStatus ? "deactivate" : "activate";
  const ok = await CRM.confirm(
    `${action.charAt(0).toUpperCase() + action.slice(1)} User?`,
    `Are you sure you want to ${action} account for "${name}"?`,
    `Yes, ${action}`
  );
  if (!ok) return;

  try {
    if (currentStatus) {
      await CRM.api(`/api/users/${userId}`, "DELETE");
    } else {
      await CRM.api(`/api/users/${userId}`, "PUT", { isActive: true });
    }
    CRM.success(`User has been ${action}d.`);
    if (usersTable) usersTable.ajax.reload();
  } catch (e) {
    CRM.error(e.message || "Failed to change user status");
  }
}

function openResetPasswordModal(userId, name) {
  document.getElementById("resetUserId").value = userId;
  document.getElementById("resetUserNameDisplay").textContent = name;
  document.getElementById("newResetPassword").value = "";
  new bootstrap.Modal(document.getElementById("resetPwdModal")).show();
}

async function handleResetPassword(e) {
  e.preventDefault();
  const userId = document.getElementById("resetUserId").value;
  const newPassword = document.getElementById("newResetPassword").value;

  if (!newPassword || newPassword.length < 5) {
    CRM.warning("Password must be at least 5 characters long");
    return;
  }

  try {
    const res = await CRM.api(`/api/users/${userId}`, "PUT", { password: newPassword });
    if (res.status === "success") {
      bootstrap.Modal.getInstance(document.getElementById("resetPwdModal")).hide();
      CRM.success("Password has been reset successfully!");
    }
  } catch (e) {
    CRM.error(e.message || "Failed to reset password");
  }
}

async function permanentlyDeleteUser(userId, name) {
  const currentUser = CRM.getUser();
  if (currentUser && currentUser.id === userId) {
    CRM.warning("You cannot delete your own logged-in account.");
    return;
  }

  const ok = await CRM.confirm(
    "Permanently Delete User?",
    `Are you sure you want to permanently delete '${name}'? This user is currently inactive. All their lead assignments will be unassigned. This action cannot be undone.`,
    "Yes, Delete Permanently"
  );
  if (!ok) return;

  try {
    const res = await CRM.api(`/api/users/${userId}?permanent=true`, "DELETE");
    CRM.success(res.message || `User '${name}' permanently deleted.`);
    if (usersTable) usersTable.ajax.reload();
  } catch (e) {
    CRM.error(e.message || "Failed to delete user");
  }
}

window.permanentlyDeleteUser = permanentlyDeleteUser;
