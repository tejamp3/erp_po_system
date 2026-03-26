// create_po.js — Dynamic PO form logic

const API = "http://127.0.0.1:8000/api";

function getToken() { return localStorage.getItem("token"); }
function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${getToken()}`
  };
}

// ── Store products list globally for dropdowns ──
let allProducts = [];

// ── Load vendors into the select dropdown ──────
async function loadVendors() {
  try {
    const res = await fetch(`${API}/vendors/`, { headers: authHeaders() });
    const vendors = await res.json();

    const sel = document.getElementById("vendorSelect");
    sel.innerHTML = `<option value="">— Select a Vendor —</option>` +
      vendors.map(v =>
        `<option value="${v.id}">${v.name} (Rating: ${v.rating ?? "N/A"})</option>`
      ).join("");
  } catch (err) {
    showAlert("Failed to load vendors. Is the backend running?", "danger");
  }
}

// ── Load products list (used in every row dropdown) ─
async function loadProducts() {
  try {
    const res = await fetch(`${API}/products/`, { headers: authHeaders() });
    allProducts = await res.json();
  } catch (err) {
    showAlert("Failed to load products.", "danger");
  }
}

// ── Add a new product row to the table ─────────
let rowCount = 0;

function addRow() {
  rowCount++;
  const rowId = `row-${rowCount}`;

  const productOptions = allProducts.map(p =>
    `<option value="${p.id}" data-price="${p.unit_price}">
       ${p.name} (SKU: ${p.sku})
     </option>`
  ).join("");

  const tr = document.createElement("tr");
  tr.id = rowId;
  tr.innerHTML = `
    <td>
      <select class="form-select form-select-sm product-select"
              onchange="onProductChange(this, '${rowId}')">
        <option value="">— Select Product —</option>
        ${productOptions}
      </select>
      <!-- AI Description button (bonus feature) -->
      <button class="btn btn-link btn-sm p-0 mt-1 text-secondary ai-btn d-none"
              onclick="generateAIDesc(this, '${rowId}')" type="button">
        <i class="bi bi-stars"></i> Auto-describe
      </button>
      <div class="ai-desc-text small text-muted mt-1 fst-italic" id="desc-${rowId}"></div>
    </td>
    <td>
      <input type="number" class="form-control form-control-sm qty-input"
             id="qty-${rowId}" min="1" value="1"
             oninput="recalcRow('${rowId}')"/>
    </td>
    <td>
      <input type="number" class="form-control form-control-sm price-input"
             id="price-${rowId}" min="0" step="0.01" value="0"
             oninput="recalcRow('${rowId}')"/>
    </td>
    <td>
      <span class="fw-semibold text-success" id="linetotal-${rowId}">₹0.00</span>
    </td>
    <td>
      <button class="btn btn-sm btn-outline-danger" onclick="removeRow('${rowId}')">
        <i class="bi bi-trash"></i>
      </button>
    </td>`;

  document.getElementById("itemsBody").appendChild(tr);
  recalcAll();
}

// ── When product selected — auto-fill price ────
function onProductChange(selectEl, rowId) {
  const selected = selectEl.options[selectEl.selectedIndex];
  const price = selected?.dataset?.price || 0;

  document.getElementById(`price-${rowId}`).value = parseFloat(price).toFixed(2);

  // Show AI button if product selected
  const aiBtn = selectEl.closest("td").querySelector(".ai-btn");
  if (selected.value) aiBtn.classList.remove("d-none");
  else aiBtn.classList.add("d-none");

  recalcRow(rowId);
}

// ── Recalculate a single row's line total ──────
function recalcRow(rowId) {
  const qty   = parseFloat(document.getElementById(`qty-${rowId}`).value)   || 0;
  const price = parseFloat(document.getElementById(`price-${rowId}`).value) || 0;
  const total = qty * price;

  document.getElementById(`linetotal-${rowId}`).textContent =
    "₹" + total.toFixed(2);

  recalcAll();
}

// ── Recalculate subtotal / tax / total ─────────
function recalcAll() {
  const lineTotals = [...document.querySelectorAll("[id^='linetotal-']")]
    .map(el => parseFloat(el.textContent.replace("₹", "")) || 0);

  const subtotal = lineTotals.reduce((a, b) => a + b, 0);
  const tax      = subtotal * 0.05;
  const total    = subtotal + tax;

  document.getElementById("summarySubtotal").textContent = "₹" + subtotal.toFixed(2);
  document.getElementById("summaryTax").textContent      = "₹" + tax.toFixed(2);
  document.getElementById("summaryTotal").textContent    = "₹" + total.toFixed(2);
}

// ── Remove a row ───────────────────────────────
function removeRow(rowId) {
  document.getElementById(rowId)?.remove();
  recalcAll();
}

// ── AI Auto-Description (Bonus Feature) ────────
async function generateAIDesc(btn, rowId) {
  const row        = document.getElementById(rowId);
  const selectEl   = row.querySelector(".product-select");
  const productId  = selectEl.value;
  const product    = allProducts.find(p => p.id == productId);

  if (!product) return;

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Generating…`;

  try {
    const res = await fetch(`${API}/products/ai-description`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        product_name : product.name,
        category     : product.category || "General"
      })
    });

    const data = await res.json();
    document.getElementById(`desc-${rowId}`).textContent = data.description;
  } catch (err) {
    document.getElementById(`desc-${rowId}`).textContent = "AI unavailable.";
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="bi bi-stars"></i> Auto-describe`;
  }
}

// ── Submit the PO ──────────────────────────────
async function submitPO() {
  const vendorId = document.getElementById("vendorSelect").value;
  const notes    = document.getElementById("poNotes").value.trim();

  if (!vendorId) {
    showAlert("Please select a vendor.", "warning");
    return;
  }

  // Collect all rows
  const rows = [...document.querySelectorAll("#itemsBody tr")];

  if (rows.length === 0) {
    showAlert("Please add at least one product row.", "warning");
    return;
  }

  const items = [];
  for (const row of rows) {
    const productId = row.querySelector(".product-select").value;
    const qty       = parseInt(row.querySelector(".qty-input").value);
    const price     = parseFloat(row.querySelector(".price-input").value);

    if (!productId) {
      showAlert("Please select a product for every row.", "warning");
      return;
    }
    if (!qty || qty < 1) {
      showAlert("Quantity must be at least 1 for every row.", "warning");
      return;
    }
    if (!price || price <= 0) {
      showAlert("Unit price must be greater than 0 for every row.", "warning");
      return;
    }

    items.push({ product_id: parseInt(productId), quantity: qty, unit_price: price });
  }

  // Build payload
  const payload = { vendor_id: parseInt(vendorId), notes, items };

  try {
    const res = await fetch(`${API}/purchase-orders/`, {
      method  : "POST",
      headers : authHeaders(),
      body    : JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.ok) {
      showAlert(
        `✅ PO <strong>${data.reference_no}</strong> created! 
         Total: ₹${data.total_amount.toFixed(2)} (incl. 5% tax)`,
        "success"
      );
      // Clear form after 2 seconds, redirect to dashboard
      setTimeout(() => { window.location.href = "index.html"; }, 2000);
    } else {
      showAlert("Error: " + (data.detail || "Unknown error"), "danger");
    }
  } catch (err) {
    showAlert("Network error: " + err.message, "danger");
  }
}

// ── Show alert banner ──────────────────────────
function showAlert(msg, type) {
  const box = document.getElementById("alertBox");
  box.className  = `alert alert-${type}`;
  box.innerHTML  = msg;
  box.classList.remove("d-none");
  box.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Init ───────────────────────────────────────
(async () => {
  await loadVendors();
  await loadProducts();
  addRow(); // Start with one empty row
})();