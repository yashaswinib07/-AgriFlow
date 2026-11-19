/**
 * AgriFlow – Client-side Core Logic and API Helper
 */

// Auto-detect API base URL: If running on port 8000, use relative paths; otherwise connect to localhost:8000
const API_BASE = "";

// ----------------- Auth & Session Helpers -----------------
const Auth = {
  getToken() {
    return localStorage.getItem("agriflow_token");
  },
  getRole() {
    return localStorage.getItem("agriflow_role");
  },
  getUser() {
    const raw = localStorage.getItem("agriflow_user");
    return raw ? JSON.parse(raw) : null;
  },
  setSession(token, role, user) {
    localStorage.setItem("agriflow_token", token);
    localStorage.setItem("agriflow_role", role);
    localStorage.setItem("agriflow_user", JSON.stringify(user));
  },
  logout() {
    localStorage.removeItem("agriflow_token");
    localStorage.removeItem("agriflow_role");
    localStorage.removeItem("agriflow_user");
    window.location.href = "index.html";
  },
  isLoggedIn() {
    return !!this.getToken();
  },
  isFarmer() {
    return this.getRole() === "farmer";
  },
  isBuyer() {
    return this.getRole() === "buyer";
  },
  getAuthHeaders() {
    const token = this.getToken();
    return token ? { "Authorization": `Bearer ${token}` } : {};
  }
};

// ----------------- API Fetch Wrapper -----------------
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...Auth.getAuthHeaders(),
    ...(options.headers || {})
  };

  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.detail || (Array.isArray(data) ? data[0]?.msg : null) || "An error occurred";
      throw new Error(errorMsg);
    }
    return data;
  } catch (err) {
    console.error(`API Error on [${endpoint}]:`, err);
    if (err.name === "TypeError" && (err.message.toLowerCase().includes("fetch") || err.message.toLowerCase().includes("network"))) {
      throw new Error("Cannot connect to backend server. Please make sure the backend is running on port 8000 ('python backend/main.py').");
    }
    throw err;
  }
}

// ----------------- Toast Notifications -----------------
function showToast(message, type = "success") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  
  const icon = type === "success" ? "✓" : (type === "error" ? "✕" : "ℹ");
  toast.innerHTML = `<span style="font-weight: bold; margin-right: 6px;">${icon}</span> <span>${message}</span>`;
  
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ----------------- Formatters -----------------
function formatCurrency(val) {
  if (val === undefined || val === null) return "₹0";
  return "₹" + Number(val).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

function formatKg(val) {
  if (val === undefined || val === null) return "0 kg";
  return Number(val).toLocaleString("en-IN") + " kg";
}

// ----------------- Navbar Dynamic Updater -----------------
function updateNavbar() {
  const authNav = document.getElementById("nav-auth");
  if (!authNav) return;

  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    const isFarmer = Auth.isFarmer();
    const dashboardLink = isFarmer ? "farmer-dashboard.html" : "buyer-dashboard.html";
    const roleLabel = isFarmer ? "Farmer Dashboard" : "Buyer Dashboard";

    authNav.innerHTML = `
      <span style="font-size: 0.9rem; color: #4b5563; font-weight: 500;">
        Hello, <strong>${user ? user.full_name : 'User'}</strong>
      </span>
      <a href="${dashboardLink}" class="btn btn-outline btn-sm">
        ${roleLabel}
      </a>
      <button onclick="Auth.logout()" class="btn btn-danger btn-sm">
        Logout
      </button>
    `;
  } else {
    authNav.innerHTML = `
      <a href="farmer-login.html" class="btn btn-outline btn-sm">Farmer Login</a>
      <a href="buyer-login.html" class="btn btn-primary btn-sm">Buyer Login</a>
    `;
  }
}

// ----------------- Modal Control -----------------
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add("active");
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("active");
}

// Close modals on clicking overlay backdrop
document.addEventListener("DOMContentLoaded", () => {
  updateNavbar();
  
  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.classList.remove("active");
      }
    });
  });
});
