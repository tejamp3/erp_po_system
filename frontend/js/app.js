// app.js — Dashboard logic: fetch POs, render table, stats, search, status update

const API = "http://127.0.0.1:8000/api";

// ── Auth helpers ──────────────────────────────
function getToken() { return localStorage.getItem("token"); }

function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${getToken()}`
  };
}

// Redirect to login page if no token
// (We'll build the login page later — for now just log a warning)
if (!getToken()) {
  console.warn("No token found. Add login page in Step 11.");
}

// ── Fetch and render all POs ──────────────────
async function loadPOs() {
  try {
    const res = await fetch(`${API}/purchase-orders/`, {
      headers: authHeaders()
    });

    if (res.status === 401) {
      alert("Session expired. Please log in again.");
      return;
    }

    const pos = await res.json();
    renderStats(pos);
    renderTable(pos);

    // Store for search filtering
    window._allPOs = pos;

  } catch (err) {
    document.getElementById("poTableBody").innerHTML =
      `<tr><td colspan="9" class="text-center text-danger py-3">
        Failed to load data. Is the backend running?
      </td></tr>`;
  }
}

// ── Render summary stat cards ─────────────────
function renderStats(pos) {
  document.getElementById("totalPOs").textContent      = pos.length;
  document.getElementById("confirmedPOs").textContent  = pos.filter(p => p.status === "Confirmed").length;
  document.getElementById("draftPOs").textContent      = pos.filter(p => p.status === "Draft").length;

  const total = pos.reduce((sum, p) => sum + (p.total_amount || 0), 0);
  document.getElementById("totalValue").textContent    = "₹" + total.toLocaleString("en-IN", { minimumFractionDigits: 2 });
}

// ── Render PO table rows ──────────────────────
function renderTable(pos) {
  const tbody = document.getElementById("poTableBody");

  if (pos.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No purchase orders found.</td></tr>`;
    return;
  }

  tbody.innerHTML = pos.map(po => {
    const badgeClass = {
      Draft: "badge-draft", Confirmed: "badge-confirmed",
      Received: "badge-received", Cancelled: "badge-cancelled"
    }[po.status] || "bg-secondary";

    const date = po.created_at
      ? new Date(po.created_at).toLocaleDateString("en-IN")
      : "—";

    const vendorName = po.vendor?.name || `Vendor #${po.vendor_id}`;
    const itemCount  = po.items?.length ?? "—";

    return `
      <tr>
        <td><span class="fw-semibold text-primary">${po.reference_no}</span></td>
        <td>${vendorName}</td>
        <td><span class="badge bg-light text-dark border">${itemCount}</span></td>
        <td>₹${(po.subtotal || 0).toFixed(2)}</td>
        <td>₹${(po.tax_amount || 0).toFixed(2)}</td>
        <td class="fw-bold">₹${(po.total_amount || 0).toFixed(2)}</td>
        <td><span class="badge ${badgeClass}">${po.status}</span></td>
        <td>${date}</td>
        <td>
          <button class="btn btn-sm btn-outline-secondary me-1"
                  onclick="openStatusModal(${po.id}, '${po.status}')">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger"
                  onclick="deletePO(${po.id})">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>`;
  }).join("");
}

// ── Search / filter ───────────────────────────
document.getElementById("searchInput").addEventListener("input", function () {
  const q = this.value.toLowerCase();
  const filtered = (window._allPOs || []).filter(po =>
    po.reference_no.toLowerCase().includes(q) ||
    (po.vendor?.name || "").toLowerCase().includes(q)
  );
  renderTable(filtered);
});

// ── Status modal ──────────────────────────────
function openStatusModal(poId, currentStatus) {
  document.getElementById("modalPoId").value    = poId;
  document.getElementById("modalStatus").value  = currentStatus;
  new bootstrap.Modal(document.getElementById("statusModal")).show();
}

document.getElementById("confirmStatusBtn").addEventListener("click", async () => {
  const poId   = document.getElementById("modalPoId").value;
  const status = document.getElementById("modalStatus").value;

  try {
    const res = await fetch(`${API}/purchase-orders/${poId}/status`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ status })
    });

    if (res.ok) {
      bootstrap.Modal.getInstance(document.getElementById("statusModal")).hide();
      loadPOs();  // Refresh table
    } else {
      alert("Failed to update status.");
    }
  } catch (err) {
    alert("Network error: " + err.message);
  }
});

// ── Delete PO ─────────────────────────────────
async function deletePO(poId) {
  if (!confirm(`Delete PO #${poId}? This cannot be undone.`)) return;

  try {
    const res = await fetch(`${API}/purchase-orders/${poId}`, {
      method: "DELETE",
      headers: authHeaders()
    });

    if (res.ok || res.status === 204) {
      loadPOs();
    } else {
      alert("Failed to delete PO.");
    }
  } catch (err) {
    alert("Network error: " + err.message);
  }
}

// ── Logout ─────────────────────────────────────
document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("token");
  alert("Logged out.");
  window.location.href = "login.html";
  // Redirect to login page once built
});

// ── Init ──────────────────────────────────────
loadPOs();