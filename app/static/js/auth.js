/**
 * auth.js - Handles Login and Registration workflows
 */

document.addEventListener("DOMContentLoaded", () => {
  // If user is already authenticated with valid token, redirect to dashboard
  const token = CRM.getToken();
  const user = CRM.getUser();
  if (token && user) {
    window.location.href = "/dashboard";
  }
});

// Login Handler
async function handleLogin(e) {
  e.preventDefault();
  const identifier = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const submitBtn = document.getElementById("loginSubmitBtn");
  const btnText = document.getElementById("btnText");
  const btnSpinner = document.getElementById("btnSpinner");

  if (!identifier || !password) {
    CRM.error("Please enter your email or username and password.", "Missing Fields");
    return;
  }

  // Loading state
  submitBtn.disabled = true;
  btnText.textContent = "Verifying...";
  btnSpinner.classList.remove("d-none");

  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: identifier, username: identifier, password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Invalid credentials");
    }

    // Save JWT token and User Profile
    CRM.setAuth(data.token, data.user);

    // SweetAlert2 notification
    Swal.fire({
      icon: "success",
      title: "Welcome Back!",
      text: `Signed in as ${data.user.name} (${data.user.role})`,
      showConfirmButton: false,
      timer: 1400,
      timerProgressBar: true
    }).then(() => {
      window.location.href = data.redirect || "/dashboard";
    });

  } catch (err) {
    CRM.error(err.message || "Failed to authenticate. Please check your credentials.");
  } finally {
    submitBtn.disabled = false;
    btnText.textContent = "Sign In to Dashboard";
    btnSpinner.classList.add("d-none");
  }
}

// Registration Handler
async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("regName").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const phoneNumber = document.getElementById("regPhone").value.trim();
  const password = document.getElementById("regPassword").value;
  const confirmPassword = document.getElementById("regConfirmPassword").value;
  const roleEl = document.getElementById("regRole");
  const role = roleEl ? roleEl.value : "Sales Employee";

  const submitBtn = document.getElementById("registerSubmitBtn");
  const btnText = document.getElementById("regBtnText");
  const btnSpinner = document.getElementById("regBtnSpinner");

  if (!name || !email || !password) {
    CRM.error("Please fill in all required fields.", "Missing Information");
    return;
  }

  if (password.length < 6) {
    CRM.warning("Password should be at least 6 characters long.", "Weak Password");
    return;
  }

  if (password !== confirmPassword) {
    CRM.error("Passwords do not match. Please re-enter.", "Password Mismatch");
    return;
  }

  // Loading state
  submitBtn.disabled = true;
  btnText.textContent = "Creating Account...";
  btnSpinner.classList.remove("d-none");

  try {
    const payload = {
      name: name,
      email: email,
      phoneNumber: phoneNumber,
      password: password,
      role: role
    };

    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Registration failed");
    }

    // Auto-login with returned token and user profile
    CRM.setAuth(data.token, data.user);

    Swal.fire({
      icon: "success",
      title: "Registration Successful!",
      text: `Account created for ${data.user.name} with role: ${data.user.role}`,
      showConfirmButton: false,
      timer: 1600,
      timerProgressBar: true
    }).then(() => {
      window.location.href = "/dashboard";
    });

  } catch (err) {
    CRM.error(err.message || "Could not complete registration.");
  } finally {
    submitBtn.disabled = false;
    btnText.textContent = "Create Account";
    btnSpinner.classList.add("d-none");
  }
}
