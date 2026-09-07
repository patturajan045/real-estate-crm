/**
 * Real Estate CRM - Reusable Low-Code Core JavaScript Library
 * Handles: JWT Authentication, SweetAlert2 Dialogs & Toasts, API requests,
 * DataTables initialization, Dynamic Form Binding, and RBAC visibility.
 */

window.CRM = (function () {
  const TOKEN_KEY = "crm_jwt_token";
  const USER_KEY = "crm_user_profile";

  // --------------------------------------------------------------------------
  // 1. Authentication & Session Management
  // --------------------------------------------------------------------------
  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function getUser() {
    try {
      const userStr = localStorage.getItem(USER_KEY);
      return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
      return null;
    }
  }

  function setAuth(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function requireAuth(allowedRoles = []) {
    const token = getToken();
    const user = getUser();

    if (!token || !user) {
      window.location.href = "/login";
      return false;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
      Swal.fire({
        icon: "warning",
        title: "Access Restricted",
        text: `The ${user.role} role does not have permission to view this page.`,
        confirmButtonColor: "#2563eb",
      }).then(() => {
        window.location.href = "/dashboard";
      });
      return false;
    }

    // Apply role-based visibility in the DOM
    applyRoleVisibility();
    populateUserProfileUI();
    return true;
  }

  function applyRoleVisibility() {
    const user = getUser();
    if (!user) return;

    document.querySelectorAll("[data-roles]").forEach((el) => {
      const allowedRoles = el.getAttribute("data-roles").split(",").map((r) => r.trim());
      if (!allowedRoles.includes(user.role)) {
        el.style.display = "none";
      } else {
        el.style.display = "";
      }
    });
  }

  function populateUserProfileUI() {
    const user = getUser();
    if (!user) return;

    const nameEl = document.getElementById("navUserName");
    const roleEl = document.getElementById("navUserRole");
    const avatarEl = document.getElementById("navUserAvatar");

    if (nameEl) nameEl.textContent = user.name || "User";
    if (roleEl) {
      roleEl.textContent = user.role || "Employee";
      roleEl.className = "badge-crm " + getRoleBadgeClass(user.role);
    }
    if (avatarEl && user.name) {
      avatarEl.textContent = user.name.charAt(0).toUpperCase();
    }
  }

  function logout() {
    Swal.fire({
      title: "Log Out?",
      text: "Are you sure you want to log out of Real Estate CRM?",
      icon: "question",
      showCancelButton: true,
      confirmButtonColor: "#dc2626",
      cancelButtonColor: "#64748b",
      confirmButtonText: "Yes, Log out",
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await api("/api/auth/logout", "POST");
        } catch (e) {
          // Ignore network errors on logout
        }
        clearAuth();
        window.location.href = "/login";
      }
    });
  }

  // --------------------------------------------------------------------------
  // 2. Central API Client (with JWT & SweetAlert Integration)
  // --------------------------------------------------------------------------
  async function api(url, method = "GET", body = null) {
    const token = getToken();
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const options = {
      method: method.toUpperCase(),
      headers: headers,
    };

    if (body && ["POST", "PUT", "PATCH"].includes(options.method)) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);

      // Session expired or unauthorized
      if (response.status === 401) {
        clearAuth();
        if (window.location.pathname !== "/login") {
          Swal.fire({
            icon: "warning",
            title: "Session Expired",
            text: "Your session has timed out. Please log in again.",
            confirmButtonColor: "#2563eb",
          }).then(() => {
            window.location.href = "/login";
          });
        }
        throw new Error("Unauthorized");
      }

      const resData = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = sanitizeUserMessage(resData.message || `Request failed (${response.status})`);
        const error = new Error(errorMsg);
        error.status = response.status;
        error.response = resData;
        throw error;
      }

      return resData;
    } catch (err) {
      console.error(`API Error on [${method}] ${url}:`, err);
      throw err;
    }
  }

  // --------------------------------------------------------------------------
  // 3. User Message Sanitizer (Friendly, Clean SweetAlert Words Only)
  // --------------------------------------------------------------------------
  function sanitizeUserMessage(msg) {
    if (!msg || typeof msg !== "string") {
      return "Unable to complete request. Please try again.";
    }
    const clean = msg.trim();
    if (clean.startsWith("{") || clean.startsWith("[") || clean.includes("[object")) {
      return "An unexpected response was received. Please try again.";
    }
    if (clean.includes("Traceback") || clean.includes("mongoengine") || clean.includes("DoesNotExist") || clean.includes("ValidationError") || clean.includes("Exception:")) {
      if (clean.toLowerCase().includes("already registered") || clean.toLowerCase().includes("already exists")) {
        return "An account with this email already exists.";
      }
      if (clean.toLowerCase().includes("not found")) {
        return "The requested record was not found.";
      }
      return "Please verify your input values and try again.";
    }
    return clean;
  }

  // --------------------------------------------------------------------------
  // 4. Password Show / Hide Eye Toggle
  // --------------------------------------------------------------------------
  function togglePassword(inputId, btnEl) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const icon = btnEl ? btnEl.querySelector("i") : null;
    if (input.type === "password") {
      input.type = "text";
      if (icon) {
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      }
    } else {
      input.type = "password";
      if (icon) {
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    }
  }

  // --------------------------------------------------------------------------
  // 5. Responsive Collapsible Sidebar (Movable Icon-Only Mode)
  // --------------------------------------------------------------------------
  function toggleSidebarCollapse() {
    const wrapper = document.querySelector(".crm-wrapper");
    const sidebar = document.getElementById("sidebar");
    if (window.innerWidth < 992) {
      if (sidebar) sidebar.classList.toggle("show");
    } else {
      if (wrapper) {
        wrapper.classList.toggle("sidebar-collapsed");
        const isCollapsed = wrapper.classList.contains("sidebar-collapsed");
        localStorage.setItem("crm_sidebar_collapsed", isCollapsed ? "true" : "false");
      }
    }
  }

  // --------------------------------------------------------------------------
  // 6. SweetAlert2 Methods (Popups & Toasts)
  // --------------------------------------------------------------------------
  function alert(title, text = "", icon = "info") {
    return Swal.fire({
      title: title,
      text: sanitizeUserMessage(text),
      icon: icon,
      confirmButtonColor: "#2563eb",
    });
  }

  function success(text, title = "Success!") {
    return Swal.fire({
      title: title,
      text: sanitizeUserMessage(text),
      icon: "success",
      confirmButtonColor: "#059669",
    });
  }

  function error(text, title = "Notice") {
    return Swal.fire({
      title: title,
      text: sanitizeUserMessage(text),
      icon: "error",
      confirmButtonColor: "#dc2626",
    });
  }

  function warning(text, title = "Warning") {
    return Swal.fire({
      title: title,
      text: text,
      icon: "warning",
      confirmButtonColor: "#d97706",
    });
  }

  function confirm(title, text, confirmButtonText = "Yes, proceed", icon = "warning") {
    return Swal.fire({
      title: title,
      text: text,
      icon: icon,
      showCancelButton: true,
      confirmButtonColor: "#2563eb",
      cancelButtonColor: "#64748b",
      confirmButtonText: confirmButtonText,
    }).then((res) => res.isConfirmed);
  }

  function toast(message, icon = "success") {
    const Toast = Swal.mixin({
      toast: true,
      position: "top-end",
      showConfirmButton: false,
      timer: 3000,
      timerProgressBar: true,
      didOpen: (toast) => {
        toast.addEventListener("mouseenter", Swal.stopTimer);
        toast.addEventListener("mouseleave", Swal.resumeTimer);
      },
    });
    Toast.fire({
      icon: icon,
      title: message,
    });
  }

  // --------------------------------------------------------------------------
  // 4. Formatting Helpers
  // --------------------------------------------------------------------------
  function formatCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) return "$0";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(amount);
  }

  function formatDate(dateStr) {
    if (!dateStr) return "-";
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch (e) {
      return dateStr;
    }
  }

  function formatDateTime(dateStr) {
    if (!dateStr) return "-";
    try {
      const d = new Date(dateStr);
      return d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (e) {
      return dateStr;
    }
  }

  function getStageBadge(stage) {
    const stageClassMap = {
      New: "stage-new",
      Contacted: "stage-contacted",
      "Site Visit": "stage-site-visit",
      Interested: "stage-interested",
      Negotiation: "stage-negotiation",
      Booked: "stage-booked",
      Lost: "stage-lost",
    };
    const cls = stageClassMap[stage] || "stage-new";
    return `<span class="badge-crm ${cls}"><i class="fas fa-circle" style="font-size:0.45rem;"></i> ${stage}</span>`;
  }

  function getStatusBadge(status) {
    const statusClassMap = {
      Available: "unit-available",
      Blocked: "unit-blocked",
      Booked: "unit-booked",
      Sold: "unit-sold",
      Confirmed: "unit-available",
      Pending: "unit-blocked",
      Cancelled: "unit-booked",
    };
    const cls = statusClassMap[status] || "unit-available";
    return `<span class="badge-crm ${cls}">${status}</span>`;
  }

  function getRoleBadgeClass(role) {
    if (role === "Super Admin") return "role-super-admin";
    if (role === "Admin") return "role-admin";
    return "role-sales";
  }

  // --------------------------------------------------------------------------
  // 5. Dynamic DataTables Initializer
  // --------------------------------------------------------------------------
  function initDataTable(selector, options = {}) {
    const defaultOptions = {
      responsive: true,
      pageLength: 10,
      lengthMenu: [5, 10, 25, 50],
      columnDefs: [{ defaultContent: "", targets: "_all" }],
      language: {
        search: '<i class="fas fa-search text-muted me-1"></i>',
        searchPlaceholder: "",
        lengthMenu: "Show _MENU_ entries",
        info: "Showing _START_ to _END_ of _TOTAL_ entries",
        paginate: {
          previous: '<i class="fas fa-chevron-left"></i>',
          next: '<i class="fas fa-chevron-right"></i>',
        },
      },
    };

    if ($.fn.DataTable.isDataTable(selector)) {
      $(selector).DataTable().destroy();
    }

    return $(selector).DataTable(Object.assign({}, defaultOptions, options));
  }

  // --------------------------------------------------------------------------
  // 6. Dynamic Form Helpers
  // --------------------------------------------------------------------------
  function serializeForm(formEl) {
    const formData = new FormData(formEl);
    const data = {};
    for (let [key, val] of formData.entries()) {
      data[key] = val.trim();
    }
    return data;
  }

  function fillForm(formEl, data) {
    if (!formEl || !data) return;
    for (const [key, val] of Object.entries(data)) {
      const field = formEl.elements[key];
      if (field) {
        if (field.type === "checkbox") {
          field.checked = Boolean(val);
        } else if (field.type === "datetime-local" && val) {
          try {
            field.value = new Date(val).toISOString().slice(0, 16);
          } catch (e) {
            field.value = val;
          }
        } else {
          field.value = val !== null && val !== undefined ? val : "";
        }
      }
    }
  }

  // --------------------------------------------------------------------------
  // 7. Dynamic CMS / Headings Loader (Cloud Storage UI)
  // --------------------------------------------------------------------------
  let contentMap = {};

  async function loadDynamicContent() {
    try {
      const res = await api("/api/cms/content");
      if (res.status === "success" && res.data) {
        contentMap = res.data;
        applyDynamicContent();
      }
    } catch (e) {
      console.warn("Could not load dynamic headings. Using defaults.");
    }
  }

  function applyDynamicContent() {
    if (!contentMap || Object.keys(contentMap).length === 0) return;
    document.querySelectorAll("[data-cms]").forEach((el) => {
      const key = el.getAttribute("data-cms");
      if (contentMap[key] !== undefined) {
        if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
          // Do not set placeholders
        } else {
          el.textContent = contentMap[key];
        }
      }
    });
  }

  function getContent(key, fallback = "") {
    return contentMap[key] || fallback;
  }

  // --------------------------------------------------------------------------
  // In-App Notification Center
  // --------------------------------------------------------------------------
  let lastSeenNotificationIds = new Set();
  let notificationPollingInitialized = false;

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  async function loadNotifications() {
    const token = getToken();
    if (!token) return;

    try {
      const res = await api("/api/notifications/");
      if (res.status === "success") {
        const badgeEl = document.getElementById("notificationBadge");
        const listEl = document.getElementById("notificationListBody");
        const unreadCount = res.unreadCount || 0;
        const items = res.data || [];

        // Update Badge
        if (badgeEl) {
          if (unreadCount > 0) {
            badgeEl.textContent = unreadCount > 99 ? "99+" : unreadCount;
            badgeEl.classList.remove("d-none");
          } else {
            badgeEl.textContent = "0";
            badgeEl.classList.add("d-none");
          }
        }

        // Render Dropdown items
        if (listEl) {
          if (items.length === 0) {
            listEl.innerHTML = '<div class="p-3 text-center text-muted small">No notifications yet</div>';
          } else {
            listEl.innerHTML = items
              .map((item) => {
                const isReadClass = item.isRead ? "bg-white text-muted" : "bg-light text-dark fw-semibold";
                const badgeClass = item.entityType === "booking" ? "bg-success" : "bg-primary";
                return `
                  <div class="p-2 px-3 border-bottom ${isReadClass} notification-item" 
                       style="cursor: pointer; transition: background 0.15s ease;"
                       onclick="CRM.markNotificationRead('${item.id}', '${item.entityType}', '${item.entityId}')">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                      <span class="badge ${badgeClass}" style="font-size: 0.65rem;">${escapeHtml(item.title)}</span>
                      <span class="text-muted small" style="font-size: 0.68rem;">${escapeHtml(item.timeAgo || "")}</span>
                    </div>
                    <div class="small" style="line-height: 1.35;">${escapeHtml(item.message)}</div>
                  </div>
                `;
              })
              .join("");
          }
        }

        // Check for new notifications to trigger toast
        const newUnread = items.filter((n) => !n.isRead && !lastSeenNotificationIds.has(n.id));
        if (newUnread.length > 0) {
          if (notificationPollingInitialized) {
            const latest = newUnread[0];
            toast(latest.message, "info");
          }
          items.forEach((n) => lastSeenNotificationIds.add(n.id));
        }
        notificationPollingInitialized = true;
      }
    } catch (e) {
      // Silently fail if notification fetch fails
    }
  }

  async function markNotificationRead(notifId, entityType, entityId) {
    try {
      await api(`/api/notifications/${notifId}/read`, "POST");
      await loadNotifications();
      if (entityType === "lead" && window.location.pathname !== "/leads") {
        window.location.href = "/leads";
      } else if (entityType === "booking" && window.location.pathname !== "/bookings") {
        window.location.href = "/bookings";
      }
    } catch (e) {
      console.warn("Could not mark notification read:", e);
    }
  }

  async function markAllNotificationsRead(event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    try {
      await api("/api/notifications/mark-all-read", "POST");
      await loadNotifications();
      toast("All notifications marked as read", "success");
    } catch (e) {
      console.warn("Could not mark all notifications as read:", e);
    }
  }

  // Auto-run CMS loader and restore sidebar state on DOM ready
  document.addEventListener("DOMContentLoaded", () => {
    loadDynamicContent();
    if (getToken()) {
      loadNotifications();
      setInterval(loadNotifications, 30000);
    }
    const dateEl = document.getElementById("currentDateDisplay");
    if (dateEl) {
      const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
      dateEl.textContent = new Date().toLocaleDateString('en-US', options);
    }
    if (localStorage.getItem("crm_sidebar_collapsed") === "true" && window.innerWidth >= 992) {
      document.querySelector(".crm-wrapper")?.classList.add("sidebar-collapsed");
    }
  });

  function toggleSidebar() {
    toggleSidebarCollapse();
  }

  window.toggleSidebar = toggleSidebar;

  // Public API
  return {
    getToken,
    getUser,
    setAuth,
    clearAuth,
    requireAuth,
    applyRoleVisibility,
    logout,
    api,
    alert,
    success,
    error,
    warning,
    confirm,
    toast,
    formatCurrency,
    formatDate,
    formatDateTime,
    getStageBadge,
    getStatusBadge,
    initDataTable,
    serializeForm,
    fillForm,
    loadDynamicContent,
    applyDynamicContent,
    getContent,
    togglePassword,
    toggleSidebarCollapse,
    escapeHtml,
    loadNotifications,
    markNotificationRead,
    markAllNotificationsRead,
  };
})();
