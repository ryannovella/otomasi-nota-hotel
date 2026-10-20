/**
 * Otomasi Nota Hotel - Interactive Frontend Logic
 * Author: BPPW Jateng / Antigravity
 */

// --- Terbilang Helper in JS (mirrors Python generator) ---
function terbilangAngka(n) {
  const satuan = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"];
  n = Math.floor(n);
  if (n < 12) return satuan[n];
  if (n < 20) return terbilangAngka(n - 10) + " belas";
  if (n < 100) return terbilangAngka(Math.floor(n / 10)) + " puluh " + satuan[n % 10];
  if (n < 200) return "seratus " + terbilangAngka(n - 100);
  if (n < 1000) return terbilangAngka(Math.floor(n / 100)) + " ratus " + terbilangAngka(n % 100);
  if (n < 2000) return "seribu " + terbilangAngka(n - 1000);
  if (n < 1000000) return terbilangAngka(Math.floor(n / 1000)) + " ribu " + terbilangAngka(n % 1000);
  if (n < 1000000000) return terbilangAngka(Math.floor(n / 1000000)) + " juta " + terbilangAngka(n % 1000000);
  if (n < 1000000000000) return terbilangAngka(Math.floor(n / 1000000000)) + " milyar " + terbilangAngka(n % 1000000000);
  return n.toString();
}

function terbilang(n) {
  if (!n || n <= 0) return "NOL RUPIAH";
  const res = terbilangAngka(n).replace(/\s+/g, ' ').trim();
  return (res + " rupiah").toUpperCase();
}

function formatRupiah(n) {
  return "Rp " + Math.floor(n).toLocaleString('id-ID');
}

// --- Application State ---
const state = {
  hotels: [],
  employees: [],
  selectedHotelId: "karanganyar_facade",
  selectedEmpIds: new Set(),
  guestRows: [], // [{ id, name, room_no, folio_no, rate, subtotal }]
  checkinDate: "",
  checkoutDate: "",
  nights: 1,
  applyStamp: true,
  lastGenerated: null
};

// --- DOM Elements ---
const el = {
  tabBtns: document.querySelectorAll('.nav-tab'),
  tabViews: document.querySelectorAll('.tab-view'),
  themeToggleBtn: document.getElementById('theme-toggle-btn'),
  
  // Generator
  hotelSelect: document.getElementById('hotel-select'),
  hotelCityTxt: document.getElementById('hotel-city-txt'),
  hotelRateTxt: document.getElementById('hotel-rate-txt'),
  checkinInput: document.getElementById('checkin-date'),
  checkoutInput: document.getElementById('checkout-date'),
  stayDurationTxt: document.getElementById('stay-duration-txt'),
  stampToggle: document.getElementById('stamp-toggle'),
  selectedEmpCount: document.getElementById('selected-emp-count'),
  btnSelectAll: document.getElementById('btn-select-all'),
  btnClearAll: document.getElementById('btn-clear-all'),
  empSearch: document.getElementById('employee-search'),
  empListContainer: document.getElementById('employee-list-container'),
  
  // Table
  guestsTableBody: document.getElementById('guests-table-body'),
  btnRandomizeFolio: document.getElementById('btn-randomize-folio'),
  summaryTotalGuests: document.getElementById('summary-total-guests'),
  summaryTotalNights: document.getElementById('summary-total-nights'),
  summaryTotalCost: document.getElementById('summary-total-cost'),
  summaryTerbilangTxt: document.getElementById('summary-terbilang-txt'),
  btnGenerate: document.getElementById('btn-generate'),

  // Master views
  empCountBadge: document.getElementById('emp-count-badge'),
  masterEmpTableBody: document.getElementById('master-employee-table-body'),
  hotelsGridContainer: document.getElementById('hotels-grid-container'),
  historyListContainer: document.getElementById('history-list-container'),
  btnAddEmployee: document.getElementById('btn-add-employee'),

  // Modals
  modalSuccess: document.getElementById('modal-success'),
  successMergedName: document.getElementById('success-merged-name'),
  successFolderPath: document.getElementById('success-folder-path'),
  btnOpenPdfDirect: document.getElementById('btn-open-pdf-direct'),
  btnOpenFolderDirect: document.getElementById('btn-open-folder-direct'),
  btnCloseModal: document.getElementById('btn-close-modal'),
  modalEmployee: document.getElementById('modal-employee'),
  newEmpName: document.getElementById('new-emp-name'),
  newEmpAgency: document.getElementById('new-emp-agency'),
  btnCancelEmp: document.getElementById('btn-cancel-emp'),
  btnSaveEmp: document.getElementById('btn-save-emp')
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
  initDates();
  initTheme();
  setupEventListeners();
  await loadHotels();
  await loadEmployees();
  renderHistory();
});

// Setup Initial Dates (Today -> Tomorrow)
function initDates() {
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);

  const formatDate = (d) => d.toISOString().split('T')[0];
  state.checkinDate = formatDate(today);
  state.checkoutDate = formatDate(tomorrow);

  el.checkinInput.value = state.checkinDate;
  el.checkoutInput.value = state.checkoutDate;
  calculateNights();
}

function calculateNights() {
  const cin = new Date(el.checkinInput.value);
  const cout = new Date(el.checkoutInput.value);
  const diffTime = cout - cin;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  state.nights = diffDays > 0 ? diffDays : 1;
  state.checkinDate = el.checkinInput.value;
  state.checkoutDate = el.checkoutInput.value;

  el.stayDurationTxt.textContent = `${state.nights} Malam`;
  updateTableSubtotals();
}

// --- Theme Management ---
function initTheme() {
  const saved = localStorage.getItem('app-theme') || 'dark-theme';
  document.body.className = saved;
}

el.themeToggleBtn.addEventListener('click', () => {
  const isDark = document.body.classList.contains('dark-theme');
  const newTheme = isDark ? 'light-theme' : 'dark-theme';
  document.body.className = newTheme;
  localStorage.setItem('app-theme', newTheme);
});

// --- Tab Navigation ---
function setupEventListeners() {
  el.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabTarget = btn.dataset.tab;
      el.tabBtns.forEach(b => b.classList.remove('active'));
      el.tabViews.forEach(v => v.classList.remove('active'));

      btn.classList.add('active');
      document.getElementById(`view-${tabTarget}`).classList.add('active');

      if (tabTarget === 'history') renderHistory();
    });
  });

  el.checkinInput.addEventListener('change', calculateNights);
  el.checkoutInput.addEventListener('change', calculateNights);
  el.stampToggle.addEventListener('change', (e) => {
    state.applyStamp = e.target.checked;
  });

  el.hotelSelect.addEventListener('change', (e) => {
    state.selectedHotelId = e.target.value;
    updateHotelMeta();
    syncGuestRowsWithDefaults();
  });

  el.btnSelectAll.addEventListener('click', selectAllEmployees);
  el.btnClearAll.addEventListener('click', clearAllEmployees);
  el.empSearch.addEventListener('input', filterEmployeeList);
  el.btnRandomizeFolio.addEventListener('click', randomizeAllFolios);
  el.btnGenerate.addEventListener('click', handleGeneratePdf);

  // Success modal actions
  el.btnCloseModal.addEventListener('click', () => {
    el.modalSuccess.classList.remove('active');
  });
  el.btnOpenPdfDirect.addEventListener('click', () => {
    if (state.lastGenerated && state.lastGenerated.merged_pdf) {
      fetch('/api/open_file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: state.lastGenerated.merged_pdf })
      });
    }
  });
  el.btnOpenFolderDirect.addEventListener('click', () => {
    if (state.lastGenerated && state.lastGenerated.output_folder) {
      fetch('/api/open_folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: state.lastGenerated.output_folder })
      });
    }
  });

  // Employee Modal
  el.btnAddEmployee.addEventListener('click', () => {
    el.newEmpName.value = '';
    el.modalEmployee.classList.add('active');
  });
  el.btnCancelEmp.addEventListener('click', () => {
    el.modalEmployee.classList.remove('active');
  });
  el.btnSaveEmp.addEventListener('click', handleSaveNewEmployee);
}

// --- Data Fetching ---
async function loadHotels() {
  try {
    const res = await fetch('/api/hotels');
    state.hotels = await res.json();
    
    el.hotelSelect.innerHTML = state.hotels.map(h => 
      `<option value="${h.id}">${h.name} (${h.city})</option>`
    ).join('');

    state.selectedHotelId = state.hotels[0].id;
    updateHotelMeta();
    renderHotelsProfile();
  } catch (err) {
    console.error("Gagal memuat hotel:", err);
  }
}

function updateHotelMeta() {
  const current = state.hotels.find(h => h.id === state.selectedHotelId);
  if (current) {
    el.hotelCityTxt.textContent = current.city;
    el.hotelRateTxt.textContent = `${formatRupiah(current.default_rate)} / malam`;
  }
}

async function loadEmployees() {
  try {
    const res = await fetch('/api/employees');
    state.employees = await res.json();
    el.empCountBadge.textContent = state.employees.length;
    renderEmployeePickerList();
    renderMasterEmployeeTable();
  } catch (err) {
    console.error("Gagal memuat pegawai:", err);
  }
}

// --- Employee Picker Rendering ---
function renderEmployeePickerList() {
  const query = el.empSearch.value.toLowerCase().trim();
  const filtered = state.employees.filter(e => e.name.toLowerCase().includes(query));

  el.empListContainer.innerHTML = filtered.map(emp => {
    const isChecked = state.selectedEmpIds.has(emp.id) ? 'checked' : '';
    return `
      <label class="emp-check-item">
        <input type="checkbox" value="${emp.id}" ${isChecked} onchange="toggleEmployeeSelection('${emp.id}')">
        <span class="emp-name-txt">${emp.name}</span>
      </label>
    `;
  }).join('');

  el.selectedEmpCount.textContent = state.selectedEmpIds.size;
}

function filterEmployeeList() {
  renderEmployeePickerList();
}

window.toggleEmployeeSelection = function(empId) {
  if (state.selectedEmpIds.has(empId)) {
    state.selectedEmpIds.delete(empId);
    state.guestRows = state.guestRows.filter(r => r.id !== empId);
  } else {
    state.selectedEmpIds.add(empId);
    const emp = state.employees.find(e => e.id === empId);
    if (emp) {
      addGuestRow(emp);
    }
  }
  el.selectedEmpCount.textContent = state.selectedEmpIds.size;
  renderGuestsTable();
};

function selectAllEmployees() {
  state.employees.forEach(emp => {
    if (!state.selectedEmpIds.has(emp.id)) {
      state.selectedEmpIds.add(emp.id);
      addGuestRow(emp);
    }
  });
  renderEmployeePickerList();
  renderGuestsTable();
}

function clearAllEmployees() {
  state.selectedEmpIds.clear();
  state.guestRows = [];
  renderEmployeePickerList();
  renderGuestsTable();
}

// --- Smart Default Generator for Guest Rows ---
function getGoldenAvailableRoom(existingRows = []) {
  // Golden Hotel hanya tersedia rentang 16 kamar (001 s.d. 016)
  const usedRooms = new Set(existingRows.map(r => r.room_no));
  const pool = [];
  for (let i = 1; i <= 16; i++) {
    const rStr = String(i).padStart(3, '0');
    if (!usedRooms.has(rStr)) {
      pool.push(rStr);
    }
  }
  if (pool.length > 0) {
    const idx = Math.floor(Math.random() * pool.length);
    return pool[idx];
  }
  const randNum = Math.floor(1 + Math.random() * 16);
  return String(randNum).padStart(3, '0');
}

function generateFolioForHotel(hotelId, roomNo) {
  const now = new Date(state.checkinDate || new Date());
  if (hotelId === 'wonogiri_golden') {
    const months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
    let rStr = "014";
    if (roomNo) {
      const digits = String(roomNo).replace(/\D/g, '');
      rStr = digits ? digits.padStart(3, '0') : String(roomNo);
    } else {
      const r = Math.floor(1 + Math.random() * 16);
      rStr = String(r).padStart(3, '0');
    }
    return `${rStr}/GuestBill/GH/${months[now.getMonth()]}/${now.getFullYear()}`;
  } else if (hotelId === 'wonogiri_golden_v2') {
    // Golden Hotel v2.0 Format Invoice: 1271341
    const baseInv = 1271340;
    const r = Math.floor(1000 + Math.random() * 8999);
    return `127${r}`;
  } else if (hotelId === 'kebumen_trio_azana' || hotelId === 'sragen_frontone' || hotelId === 'purworejo_ardiana' || hotelId === 'banjarnegara_surya_yudha' || hotelId === 'purbalingga_braling') {
    // Trio Azana, Front One Sragen, Ardiana, Surya Yudha & Braling Format: FL.26001881  /  0
    const yr = String(now.getFullYear()).slice(-2);
    const r = Math.floor(1000 + Math.random() * 8999);
    return `FL.${yr}00${r}  /  0`;
  } else if (hotelId === 'magelang_artos') {
    // Grand Artos Bill No: 333577 / 1
    const r = Math.floor(333500 + Math.random() * 99);
    return `${r} / 1`;
  } else if (hotelId === 'cilacap_atrium') {
    // Atrium Premiere Cilacap Bill No: 127211 / 1
    const r = Math.floor(127200 + Math.random() * 99);
    return `${r} / 1`;
  } else if (hotelId === 'banyumas_wisata_niaga') {
    // Hotel Wisata Niaga Purwokerto Folio No: MSAQ902026
    const r = Math.floor(902000 + Math.random() * 999);
    return `MSAQ${r}`;
  } else if (hotelId === 'temanggung_aliyana') {
    // Hotel Aliyana Temanggung Bill No: 00079943
    const r = Math.floor(70000 + Math.random() * 20000);
    return `000${r}`;
  } else {
    // Facade / Azana PMS Format
    const yr = String(now.getFullYear()).slice(-2);
    const r = Math.floor(100000 + Math.random() * 899999);
    return `FL.${yr}${r} / 0`;
  }
}

function addGuestRow(emp) {
  const hotel = state.hotels.find(h => h.id === state.selectedHotelId) || state.hotels[0];
  const rowIndex = state.guestRows.length;
  
  let roomNo = "";
  if (hotel.id === 'karanganyar_facade' || hotel.id === 'kebumen_trio_azana') {
    // 201, 202, 203, 205, 206... (bypass 4)
    const base = hotel.default_room_start || 201;
    let roomNum = base + rowIndex;
    if (roomNum === 204) roomNum = 205;
    roomNo = roomNum.toString();
  } else if (hotel.id === 'sragen_frontone' || hotel.id === 'purworejo_ardiana' || hotel.id === 'banjarnegara_surya_yudha' || hotel.id === 'magelang_artos' || hotel.id === 'cilacap_atrium' || hotel.id === 'banyumas_wisata_niaga' || hotel.id === 'purbalingga_braling' || hotel.id === 'temanggung_aliyana') {
    // Front One Sragen, Ardiana, Surya Yudha, Grand Artos, Atrium Cilacap, Braling & Aliyana (kamar berurutan dari default_room_start)
    const base = hotel.default_room_start || 201;
    let roomNum = base + rowIndex;
    roomNo = roomNum.toString();
  } else if (hotel.id === 'wonogiri_golden' || hotel.id === 'wonogiri_golden_v2') {
    // Acak dari rentang 16 kamar (001 s.d. 016) tanpa duplikat
    roomNo = getGoldenAvailableRoom(state.guestRows);
  } else {
    roomNo = (101 + rowIndex).toString();
  }

  const rate = hotel.default_rate || 680000;
  const folio = generateFolioForHotel(hotel.id, roomNo);
  const agency = hotel.default_agency || emp.agency || "KEMENTRIAN PU JATENG";

  state.guestRows.push({
    id: emp.id,
    name: emp.name,
    agency: agency,
    room_no: roomNo,
    room_suffix: hotel.room_suffix || "DLT",
    room_type: hotel.default_room_type || "1 Familly room",
    folio_no: folio,
    rate: rate,
    subtotal: rate * state.nights
  });
}

function syncGuestRowsWithDefaults() {
  const hotel = state.hotels.find(h => h.id === state.selectedHotelId);
  if (!hotel) return;

  if (hotel.id === 'wonogiri_golden' || hotel.id === 'wonogiri_golden_v2') {
    // Acak kamar unik dari 16 kamar yang tersedia
    const shuffledRooms = Array.from({length: 16}, (_, i) => String(i + 1).padStart(3, '0')).sort(() => Math.random() - 0.5);
    state.guestRows.forEach((row, i) => {
      row.room_no = shuffledRooms[i % shuffledRooms.length];
      row.room_type = hotel.default_room_type || (hotel.id === 'wonogiri_golden_v2' ? "1 family  room" : "1 Familly room");
      row.rate = hotel.default_rate;
      row.agency = hotel.default_agency || row.agency || "KEMENTRIAN PU JATENG";
      row.folio_no = generateFolioForHotel(hotel.id, row.room_no);
      row.subtotal = row.rate * state.nights;
    });
  } else {
    state.guestRows.forEach((row, i) => {
      if (hotel.id === 'karanganyar_facade' || hotel.id === 'kebumen_trio_azana') {
        let roomNum = (hotel.default_room_start || 201) + i;
        if (roomNum === 204) roomNum = 205;
        row.room_no = roomNum.toString();
      } else if (hotel.id === 'sragen_frontone' || hotel.id === 'purworejo_ardiana' || hotel.id === 'banjarnegara_surya_yudha' || hotel.id === 'magelang_artos' || hotel.id === 'cilacap_atrium' || hotel.id === 'banyumas_wisata_niaga' || hotel.id === 'purbalingga_braling' || hotel.id === 'temanggung_aliyana') {
        let roomNum = (hotel.default_room_start || 201) + i;
        row.room_no = roomNum.toString();
      } else {
        row.room_no = (101 + i).toString();
      }
      row.rate = hotel.default_rate;
      row.agency = hotel.default_agency || row.agency || "KEMENTRIAN PU JATENG";
      row.folio_no = generateFolioForHotel(hotel.id, row.room_no);
      row.subtotal = row.rate * state.nights;
    });
  }
  renderGuestsTable();
}

function randomizeAllFolios() {
  if (state.selectedHotelId === 'wonogiri_golden' || state.selectedHotelId === 'wonogiri_golden_v2') {
    const shuffledRooms = Array.from({length: 16}, (_, i) => String(i + 1).padStart(3, '0')).sort(() => Math.random() - 0.5);
    state.guestRows.forEach((row, i) => {
      row.room_no = shuffledRooms[i % shuffledRooms.length];
      row.folio_no = generateFolioForHotel(state.selectedHotelId, row.room_no);
    });
  } else {
    state.guestRows.forEach(row => {
      row.folio_no = generateFolioForHotel(state.selectedHotelId, row.room_no);
    });
  }
  renderGuestsTable();
}

function updateTableSubtotals() {
  state.guestRows.forEach(row => {
    row.subtotal = row.rate * state.nights;
  });
  renderGuestsTable();
}

// --- Guests Table Rendering ---
function renderGuestsTable() {
  if (state.guestRows.length === 0) {
    el.guestsTableBody.innerHTML = `
      <tr class="empty-row">
        <td colspan="7">
          <div class="empty-state">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="11" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>
            <p>Silakan centang personel di panel sebelah kiri untuk menambahkan ke daftar nota.</p>
          </div>
        </td>
      </tr>
    `;
    el.btnGenerate.disabled = true;
    updateSummary(0);
    return;
  }

  el.btnGenerate.disabled = false;
  let totalCost = 0;

  el.guestsTableBody.innerHTML = state.guestRows.map((row, idx) => {
    totalCost += row.subtotal;
    return `
      <tr>
        <td style="color: var(--text-muted); font-weight: 600;">${idx + 1}</td>
        <td>
          <input type="text" class="table-input font-semibold" value="${row.name}" 
                 onchange="updateRowField(${idx}, 'name', this.value)">
        </td>
        <td>
          <input type="text" class="table-input" value="${row.room_no}" 
                 onchange="updateRowField(${idx}, 'room_no', this.value)">
        </td>
        <td>
          <input type="text" class="table-input" value="${row.folio_no}" 
                 onchange="updateRowField(${idx}, 'folio_no', this.value)">
        </td>
        <td>
          <input type="number" class="table-input" value="${row.rate}" step="1000"
                 onchange="updateRowField(${idx}, 'rate', Number(this.value))">
        </td>
        <td><strong style="color: var(--accent-primary);">${formatRupiah(row.subtotal)}</strong></td>
        <td style="text-align: center;">
          <button class="btn-del" title="Hapus dari daftar" onclick="removeGuestRow(${idx})">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  updateSummary(totalCost);
}

window.updateRowField = function(idx, field, value) {
  if (state.guestRows[idx]) {
    state.guestRows[idx][field] = value;
    if (field === 'rate') {
      state.guestRows[idx].subtotal = value * state.nights;
    }
    // Sinkronisasi khusus Golden Hotel: nomor kamar adalah teks depan folio
    if (state.selectedHotelId === 'wonogiri_golden') {
      if (field === 'room_no') {
        const digits = String(value).replace(/\D/g, '');
        const cleanRoom = digits ? digits.padStart(3, '0') : value;
        state.guestRows[idx].room_no = cleanRoom;
        if (state.guestRows[idx].folio_no && state.guestRows[idx].folio_no.includes('/GuestBill')) {
          state.guestRows[idx].folio_no = state.guestRows[idx].folio_no.replace(/^[^/]+/, cleanRoom);
        } else {
          state.guestRows[idx].folio_no = generateFolioForHotel('wonogiri_golden', cleanRoom);
        }
      } else if (field === 'folio_no') {
        const match = String(value).match(/^(\d+)\/GuestBill/);
        if (match) {
          state.guestRows[idx].room_no = match[1].padStart(3, '0');
        }
      }
    }
    renderGuestsTable();
  }
};

window.removeGuestRow = function(idx) {
  const row = state.guestRows[idx];
  if (row) {
    state.selectedEmpIds.delete(row.id);
    state.guestRows.splice(idx, 1);
    el.selectedEmpCount.textContent = state.selectedEmpIds.size;
    renderEmployeePickerList();
    renderGuestsTable();
  }
};

function updateSummary(totalCost) {
  el.summaryTotalGuests.textContent = `${state.guestRows.length} Orang`;
  el.summaryTotalNights.textContent = `${state.nights} Malam`;
  el.summaryTotalCost.textContent = formatRupiah(totalCost);
  el.summaryTerbilangTxt.textContent = terbilang(totalCost);
}

// --- Action: Generate PDF ---
async function handleGeneratePdf() {
  if (state.guestRows.length === 0) return;

  const btn = el.btnGenerate;
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `
    <svg class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>
    Sedang Memproses Nota...
  `;

  try {
    const payload = {
      hotel_id: state.selectedHotelId,
      checkin: state.checkinDate,
      checkout: state.checkoutDate,
      apply_stamp: state.applyStamp,
      guests: state.guestRows
    };

    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.status === 'success') {
      state.lastGenerated = result;
      el.successMergedName.textContent = result.merged_pdf.split('\\').pop();
      el.successFolderPath.textContent = result.output_folder;
      el.modalSuccess.classList.add('active');
    } else {
      alert("Terjadi kesalahan:\n\n" + (result.message || "Gagal membuat PDF."));
    }
  } catch (err) {
    console.error("Generate error:", err);
    alert("Gagal menghubungi server generator.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// --- Master Employee Table ---
function renderMasterEmployeeTable() {
  el.masterEmpTableBody.innerHTML = state.employees.map((emp, i) => `
    <tr>
      <td style="color: var(--text-muted); font-weight: 600;">${i + 1}</td>
      <td><strong>${emp.name}</strong></td>
      <td>${emp.agency || 'BPPW Jawa Tengah'}</td>
      <td>
        <button class="secondary-btn" style="padding: 4px 8px; font-size: 0.78rem;" onclick="deleteEmployee('${emp.id}')">
          Hapus
        </button>
      </td>
    </tr>
  `).join('');
}

window.deleteEmployee = async function(id) {
  if (confirm("Hapus pegawai ini dari master data?")) {
    state.employees = state.employees.filter(e => e.id !== id);
    await saveEmployeesMaster();
  }
};

async function handleSaveNewEmployee() {
  const name = el.newEmpName.value.trim();
  const agency = el.newEmpAgency.value.trim() || "BPPW Jawa Tengah / Kementerian PU";
  if (!name) return alert("Nama pegawai tidak boleh kosong.");

  const newId = `emp_${Date.now()}`;
  state.employees.push({ id: newId, name, agency });
  await saveEmployeesMaster();

  el.modalEmployee.classList.remove('active');
}

async function saveEmployeesMaster() {
  try {
    await fetch('/api/employees', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.employees)
    });
    el.empCountBadge.textContent = state.employees.length;
    renderEmployeePickerList();
    renderMasterEmployeeTable();
  } catch (err) {
    console.error("Gagal menyimpan pegawai:", err);
  }
}

// --- Hotels Profile Render ---
function renderHotelsProfile() {
  el.hotelsGridContainer.innerHTML = state.hotels.map(h => `
    <div class="hotel-card">
      <div class="hotel-card-header">
        <span class="hotel-badge">${h.group}</span>
      </div>
      <h3>${h.name}</h3>
      <p>${h.city}</p>
      
      <div class="hotel-meta-row">
        <span>Format Layout</span>
        <span class="val">${h.format_type === 'golden_bill' ? 'Direct Guest Bill (v1.0)' : (h.format_type === 'golden_invoice_v2' ? 'Golden Invoice (v2.0)' : (h.format_type === 'azana_trio' ? 'Azana Style Kebumen' : (h.format_type === 'ardiana_purworejo' ? 'Ardiana PMS Purworejo' : (h.format_type === 'surya_yudha' ? 'Surya Yudha Banjarnegara' : (h.format_type === 'magelang_artos' ? 'Grand Artos Magelang' : (h.format_type === 'atrium_cilacap' ? 'Atrium Premiere Cilacap' : (h.format_type === 'wisata_niaga_banyumas' ? 'Wisata Niaga PMS Banyumas' : (h.format_type === 'braling_purbalingga' ? 'Braling Grand Purbalingga' : (h.format_type === 'temanggung_aliyana' ? 'Aliyana Hotel Temanggung' : 'Azana PMS Format')))))))))}</span>
      </div>
      <div class="hotel-meta-row">
        <span>Tarif Standar</span>
        <span class="val" style="color: var(--success);">${formatRupiah(h.default_rate)}</span>
      </div>
      <div class="hotel-meta-row">
        <span>Stempel Digital</span>
        <span class="val">${h.has_stamp ? 'Tersedia (PNG)' : 'Polos'}</span>
      </div>
    </div>
  `).join('');
}

// --- History Render ---
async function renderHistory() {
  try {
    const res = await fetch('/api/history');
    const items = await res.json();
    if (items.length === 0) {
      el.historyListContainer.innerHTML = `
        <div class="empty-state">
          <p>Belum ada riwayat nota yang digenerate.</p>
        </div>
      `;
      return;
    }

    el.historyListContainer.innerHTML = items.map(item => {
      const dt = new Date(item.created_time * 1000);
      const dateStr = dt.toLocaleString('id-ID');
      const filename = item.merged_pdf.split('\\').pop();
      return `
        <div class="history-item">
          <div class="history-info">
            <h4>${filename}</h4>
            <p>Dibuat: ${dateStr} • Folder: <code>${item.folder_name}</code></p>
          </div>
          <div class="history-actions">
            <button class="secondary-btn" onclick="openPath('${item.merged_pdf.replace(/\\/g, '\\\\')}', 'file')">
              Buka PDF
            </button>
            <button class="secondary-btn" onclick="openPath('${item.folder_path.replace(/\\/g, '\\\\')}', 'folder')">
              Buka Folder
            </button>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error("Gagal memuat riwayat:", err);
  }
}

window.openPath = function(path, type) {
  const endpoint = type === 'file' ? '/api/open_file' : '/api/open_folder';
  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
};
