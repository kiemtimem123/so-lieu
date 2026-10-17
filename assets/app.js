(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const state = { commodities: [], selectedId: null, chart: null, stockChart: null };

  const GROUPS = {
    37694: 'energy',
    37695: 'energy',
    37826: 'energy',
    37827: 'energy',
    37828: 'energy'
  };

  const fmt = (value, maximumFractionDigits = 3) => {
    if (value === null || value === undefined || value === '' || !Number.isFinite(Number(value))) return '—';
    return new Intl.NumberFormat('vi-VN', { maximumFractionDigits }).format(Number(value));
  };

  const DATA_FALLBACK_BASE = 'https://raw.githubusercontent.com/kiemtimem123/so-lieu/main/data/';

  // Hostinger can occasionally serve a stale deployment or its index.html for a
  // missing JSON path. Prefer same-origin snapshots, then fall back to the
  // current public snapshot committed in this repository.
  async function fetchDataFile(filename) {
    const localUrl = 'data/' + filename;
    try {
      const local = await fetch(localUrl, { cache: 'no-store' });
      const contentType = (local.headers.get('content-type') || '').toLowerCase();
      if (local.ok && (!contentType || contentType.includes('json'))) return local;
      console.warn('[data-fallback]', filename, 'Local snapshot unavailable; trying repository copy.', local.status, contentType);
    } catch (error) {
      console.warn('[data-fallback]', filename, 'Local snapshot request failed; trying repository copy.', error);
    }

    const remote = await fetch(DATA_FALLBACK_BASE + encodeURIComponent(filename), { cache: 'no-store' });
    if (!remote.ok) throw new Error('HTTP ' + remote.status + ' loading ' + filename + ' from repository fallback');
    const remoteType = (remote.headers.get('content-type') || '').toLowerCase();
    if (remoteType.includes('text/html')) throw new Error('Repository fallback returned HTML instead of JSON for ' + filename);
    return remote;
  }

  const dateFmt = value => {
    if (!value) return '—';
    const d = new Date(value.length === 10 ? value + 'T00:00:00' : value);
    return Number.isNaN(d.getTime()) ? value : new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium' }).format(d);
  };

  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[char]);

  async function loadMarketSnapshot() {
    const list = $('#commodityList');
    try {
      const response = await fetchDataFile('market-prices.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data)) throw new Error('Cấu trúc dữ liệu không hợp lệ');
      state.commodities = snapshot.data
        .filter(item => Number.isFinite(Number(item.value)) && item.date && item.name)
        .map(item => ({ ...item, group: item.group || GROUPS[item.id] || 'other' }))
        .sort((a, b) => a.name.localeCompare(b.name, 'vi'));
      renderCommodities();
      updateMarketSource(snapshot);
      if (state.commodities.length) selectCommodity(state.commodities[0].id);
      else if (list) list.innerHTML = '<div class="empty-state"><h3>Chưa có dữ liệu hàng hóa</h3><p>Snapshot hiện chưa có giá hợp lệ.</p></div>';
      updateBrentHighlight();
    } catch (error) {
      if (list) list.innerHTML = '<div class="empty-state"><h3>Không tải được dữ liệu</h3><p>Không đọc được data/market-prices.json. Kiểm tra file đã được triển khai trên Hostinger chưa.</p></div>';
      const source = $('#commoditySource');
      if (source) source.textContent = 'Nguồn: chưa tải được snapshot';
      console.error('[market-prices]', error);
    }
  }

  function renderCommodities() {
    const list = $('#commodityList');
    if (!list) return;
    const query = ($('#commoditySearch')?.value || '').trim().toLocaleLowerCase('vi');
    const group = $('#commodityGroup')?.value || 'all';
    const filtered = state.commodities.filter(item =>
      (group === 'all' || item.group === group) &&
      (item.name.toLocaleLowerCase('vi').includes(query) || String(item.id).includes(query))
    );
    if (!filtered.length) {
      list.innerHTML = '<div class="empty-state"><h3>Không tìm thấy mặt hàng</h3><p>Thử từ khóa khác hoặc chọn tất cả nhóm.</p></div>';
      return;
    }
    list.innerHTML = filtered.map(item => `
      <button type="button" class="commodity-item ${String(item.id) === String(state.selectedId) ? 'selected' : ''}" data-commodity-id="${escapeHtml(item.id)}">
        <span class="commodity-symbol">${item.group === 'energy' ? '◈' : '◇'}</span>
        <span class="commodity-info"><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.unit || 'Đơn vị chưa xác định')} · ${escapeHtml(dateFmt(item.date))}</small></span>
        <span class="commodity-price"><strong>${escapeHtml(fmt(item.value))}</strong><small>${escapeHtml(item.unit || '')}</small></span>
      </button>`).join('');
    $$('[data-commodity-id]', list).forEach(button => button.addEventListener('click', () => selectCommodity(button.dataset.commodityId)));
  }

  function selectCommodity(id) {
    const item = state.commodities.find(entry => String(entry.id) === String(id));
    if (!item) return;
    state.selectedId = item.id;
    renderCommodities();
    const detail = $('#commodityDetail');
    if (!detail) return;
    const title = $('h3', detail);
    if (title) title.textContent = item.name;
    const pill = $('.status-pill', detail);
    if (pill) { pill.textContent = 'Có dữ liệu'; pill.className = 'status-pill positive'; }
    const metrics = $$('.metric strong', detail);
    if (metrics.length >= 4) {
      metrics[0].textContent = '—';
      metrics[1].textContent = fmt(item.value) + ' ' + (item.unit || '');
      metrics[2].textContent = '—';
      metrics[3].textContent = '—';
    }
    const source = $('#commoditySource');
    const timestamp = $('#commodityTimestamp');
    if (source) source.textContent = 'Nguồn: DulieuKinhte API · Giá trị gần nhất được đồng bộ';
    if (timestamp) timestamp.textContent = 'Ngày dữ liệu: ' + dateFmt(item.date);
    const empty = $('#chartEmpty');
    const history = (item.observations || []).filter(p => p && p.date && Number.isFinite(Number(p.value))).sort((a,b)=>a.date.localeCompare(b.date));
    if (state.chart) { state.chart.destroy(); state.chart = null; }
    const canvas = $('#commodityChart');
    if (history.length && canvas && window.Chart) {
      if (empty) empty.style.display = 'none';
      state.chart = new Chart(canvas, {
        type: 'line',
        data: { labels: history.map(p => dateFmt(p.date)), datasets: [{ label: item.name, data: history.map(p => Number(p.value)), borderWidth: 2, tension: .18, pointRadius: history.length > 40 ? 0 : 2 }] },
        options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { display: true, position: 'bottom' } }, scales: { x: { ticks: { maxTicksLimit: 8, maxRotation: 0 }, grid: { display: false } }, y: { beginAtZero: false } } }
      });
      if (source) source.textContent = 'Nguồn: Dữ Liệu Kinh Tế API · ' + history.length + ' quan sát';
    } else if (empty) {
      empty.style.display = 'grid';
      empty.textContent = 'Chưa có đủ chuỗi lịch sử hợp lệ để vẽ biểu đồ. Chỉ giá mới nhất được hiển thị.';
    }
  }

  function updateMarketSource(snapshot) {
    const foot = $('#footerBuild');
    if (foot) foot.textContent = 'Giá hàng hóa đồng bộ lúc ' + dateFmt(snapshot.fetchedAt);
  }

  function updateBrentHighlight() {
    const brent = state.commodities.find(item => Number(item.id) === 37827);
    if (!brent) return;
    const highlight = $$('.highlight-grid article').find(card => /Dầu Brent/i.test(card.textContent));
    if (highlight) {
      const strong = $('strong', highlight);
      const em = $('em', highlight);
      if (strong) strong.textContent = fmt(brent.value) + ' ' + brent.unit;
      if (em) em.textContent = 'Dữ liệu ngày ' + dateFmt(brent.date);
    }
  }


  async function loadCurrencyRates() {
    const table = $('#currencyRatesTable');
    const updated = $('#currencyUpdated');
    const status = $('#currencySourceStatus');
    if (!table) return;
    try {
      const response = await fetchDataFile('currency-rates.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data) || !snapshot.data.length || !snapshot.lastUpdatedUtc) {
        throw new Error('Snapshot tỷ giá không hợp lệ');
      }
      const rows = snapshot.data.filter(item =>
        item && item.code && item.name && Number.isFinite(Number(item.vndPerUnit)) && Number(item.vndPerUnit) > 0
      );
      if (!rows.length) throw new Error('Không có tỷ giá hợp lệ');
      table.innerHTML = `<table><thead><tr><th>Mã</th><th>Tên ngoại tệ</th><th>VND / 1 đơn vị</th><th>Phương pháp</th></tr></thead><tbody>${rows.map(item => `
        <tr><td><strong>${escapeHtml(item.code)}</strong></td><td>${escapeHtml(item.name)}</td>
        <td>${fmt(item.vndPerUnit, 4)}</td><td>${item.method === 'direct' ? 'Nguồn trực tiếp' : 'Tỷ giá chéo tính toán'}</td></tr>`).join('')}</tbody></table>`;
      const sourceUpdated = Date.parse(snapshot.lastUpdatedUtc);
      const ageDays = Number.isFinite(sourceUpdated) ? Math.max(0, Math.floor((Date.now() - sourceUpdated) / 86400000)) : Infinity;
      const stale = ageDays > 3;
      if (updated) {
        updated.textContent = (stale ? 'Cảnh báo tỷ giá cũ · ' : 'Nguồn cập nhật: ') + dateFmt(snapshot.lastUpdatedUtc);
        updated.className = 'status-pill ' + (stale ? 'warning' : 'positive');
      }
      if (status) status.innerHTML = 'Nguồn: <a href="https://www.exchangerate-api.com" target="_blank" rel="noopener noreferrer">ExchangeRate-API Open Access</a> · tỷ giá tham khảo, cập nhật khoảng mỗi 24 giờ';
      const disclaimer = $('#currencyDisclaimer');
      if (disclaimer) disclaimer.textContent = (snapshot.rateType || 'Tỷ giá tham khảo') + '. Thời điểm cập nhật theo nhà cung cấp: ' + snapshot.lastUpdatedUtc + '. Tỷ giá ngoài USD được tính chéo từ cùng nguồn. ' + (stale ? 'CẢNH BÁO: dữ liệu đã cũ ' + ageDays + ' ngày.' : '') + ' Không dùng thay tỷ giá mua/bán ngân hàng hoặc tỷ giá trung tâm NHNN.';
    } catch (error) {
      table.innerHTML = '<div class="empty-state"><h3>Chưa tải được tỷ giá</h3><p>Kiểm tra file data/currency-rates.json và GitHub Actions đã chạy thành công chưa.</p></div>';
      if (updated) { updated.textContent = 'Chưa có dữ liệu'; updated.className = 'status-pill neutral'; }
      if (status) status.textContent = 'Chưa đồng bộ được tỷ giá';
      console.error('[currency-rates]', error);
    }
  }


  let omoHistoryChartInstance = null;
  async function setupOmoChartControls() {
    const canvas = $('#omoHistoryChart');
    const note = $('#omoHistoryChartNote');
    const table = $('#omoLatestTable');
    const chartWrap = $('#omoHistoryChartWrap');
    const typeSelect = $('#omoChartType');
    const rangeSelect = $('#omoChartRange');
    const toolbar = $('#omoDataContent .data-view-toolbar');
    if (!canvas || !window.Chart || !toolbar) return;
    let seriesPicker = $('#omoChartSeriesPicker');
    if (!seriesPicker) {
      seriesPicker = document.createElement('div');
      seriesPicker.id = 'omoChartSeriesPicker';
      seriesPicker.className = 'chart-series-picker';
      seriesPicker.setAttribute('aria-label', 'Chọn các chỉ tiêu đưa vào biểu đồ');
      toolbar.insertAdjacentElement('afterend', seriesPicker);
    }
    toolbar.querySelectorAll('[data-omo-view]').forEach(button => button.addEventListener('click', () => {
      toolbar.querySelectorAll('[data-omo-view]').forEach(b => b.classList.toggle('is-active', b === button));
      const showChart = button.dataset.omoView === 'chart';
      if (chartWrap) chartWrap.hidden = !showChart;
      if (table) table.hidden = showChart;
    }));
    try {
      const response = await fetchDataFile('category-data.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      const keys = ['omo-buy-total', 'omo-net-outstanding', 'omo-buy-63d', 'omo-buy-91d'];
      const items = (snapshot.data || []).filter(item => keys.includes(item.category) && Array.isArray(item.observations));
      seriesPicker.innerHTML = items.map((item, index) => '<label><input type="checkbox" data-series-index="' + index + '" checked> ' + escapeHtml(item.name) + '</label>').join('');
      seriesPicker.querySelectorAll('input[type="checkbox"]').forEach(input => input.addEventListener('change', () => draw()));
      const draw = () => {
        const selectedIndexes = [...seriesPicker.querySelectorAll('input[type="checkbox"]:checked')].map(input => Number(input.dataset.seriesIndex));
        const days = rangeSelect.value === 'all' ? Infinity : Number(rangeSelect.value);
        const cutoff = Number.isFinite(days) ? new Date(Date.now() - days * 86400000).toISOString().slice(0,10) : '0000-01-01';
        const points = items.filter((item, index) => selectedIndexes.includes(index)).map(item => ({
          ...item,
          observations: item.observations.filter(p => p && /^\d{4}-\d{2}-\d{2}$/.test(p.date) && p.date <= new Date().toISOString().slice(0,10) && p.date >= cutoff && Number.isFinite(Number(p.value))).sort((a,b)=>a.date.localeCompare(b.date))
        })).filter(item => item.observations.length);
        if (!points.length) {
          if (omoHistoryChartInstance) { omoHistoryChartInstance.destroy(); omoHistoryChartInstance = null; }
          if (note) note.textContent = 'Hãy tick chọn ít nhất một chỉ tiêu có dữ liệu trong khoảng thời gian đã chọn.';
          return;
        }
        const dates = [...new Set(points.flatMap(item => item.observations.map(p=>p.date)))].sort();
        if (!dates.length) {
          if (note) note.textContent = 'Chưa có chuỗi lịch sử OMO hợp lệ để vẽ; dữ liệu không được tự tạo.';
          return;
        }
        if (omoHistoryChartInstance) omoHistoryChartInstance.destroy();
        const combo = typeSelect.value === 'combo';
        omoHistoryChartInstance = new Chart(canvas, {
          type: combo ? 'bar' : typeSelect.value,
          data: { labels: dates.map(dateFmt), datasets: points.map((item,index) => {
            const values = new Map(item.observations.map(p=>[p.date,Number(p.value)]));
            return { type: combo ? (index === 0 ? 'bar' : 'line') : typeSelect.value, label:item.name, data:dates.map(d=>values.has(d)?values.get(d):null), borderWidth:2, pointRadius:dates.length>48?0:2, tension:0.15, spanGaps:false, yAxisID:'y' };
          })},
          options: { responsive:true, maintainAspectRatio:false, interaction:{mode:'index',intersect:false}, plugins:{legend:{display:true,position:'bottom'},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+fmt(ctx.parsed.y,2)+' '+(points[ctx.datasetIndex]?.unit||'')}}}, scales:{x:{ticks:{maxTicksLimit:9,maxRotation:0},grid:{display:false}},y:{beginAtZero:false,ticks:{callback:v=>fmt(v,2)},title:{display:true,text:'Giá trị theo đơn vị nguồn'}}}}
        });
        if (note) note.textContent = 'Nguồn: Dữ Liệu Kinh Tế · ' + dates.length + ' ngày có quan sát. Các ngày thiếu dữ liệu không được nội suy. Chọn “Kết hợp cột + đường” để phân biệt hai chỉ tiêu.';
      };
      typeSelect.addEventListener('change',draw);
      rangeSelect.addEventListener('change',draw);
      draw();
    } catch(error) {
      if(note) note.textContent='Không tải được chuỗi lịch sử OMO từ snapshot.';
      console.error('[omo-history-chart]',error);
    }
  }

  async function loadOmoData() {
    const content = $('#omoDataContent');
    const updated = $('#omoDataUpdated');
    if (!content) return;
    try {
      const response = await fetchDataFile('omo-latest.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data) || !snapshot.fetchedAt) throw new Error('Snapshot OMO không hợp lệ');
      const wanted = ['omo-buy-total', 'omo-net-outstanding'];
      const rows = snapshot.data.filter(item =>
        wanted.includes(item.category) && item.name && item.date && item.url && item.unit &&
        Number.isFinite(Number(item.value)) && /^\d{4}-\d{2}-\d{2}$/.test(item.date)
      );
      if (rows.length !== 2) throw new Error('Snapshot phải có đủ hai chỉ tiêu OMO hợp lệ');
      const now = Date.now();
      const isStale = item => {
        const date = new Date(item.date + 'T00:00:00Z').getTime();
        return !Number.isFinite(date) || now - date > 5 * 24 * 60 * 60 * 1000;
      };
      const newest = rows.reduce((latest, item) => item.date > latest ? item.date : latest, rows[0].date);
      const anyStale = rows.some(isStale);
      content.innerHTML = `<div class="data-view-toolbar"><div class="view-switch" role="group" aria-label="Chế độ hiển thị OMO"><button type="button" data-omo-view="chart" class="is-active">Biểu đồ</button><button type="button" data-omo-view="table">Bảng số liệu</button></div><label class="chart-type-label">Kiểu biểu đồ <select id="omoChartType" aria-label="Kiểu biểu đồ OMO"><option value="line">Đường</option><option value="bar">Cột</option><option value="combo">Kết hợp cột + đường</option></select></label><label class="chart-type-label">Khoảng thời gian <select id="omoChartRange" aria-label="Khoảng thời gian OMO"><option value="90">90 ngày</option><option value="365" selected>1 năm</option><option value="all">Tất cả</option></select></label></div><div id="omoHistoryChartWrap" class="data-chart-view"><div class="chart-canvas-wrap"><canvas id="omoHistoryChart" role="img" aria-label="Biểu đồ lịch sử hoạt động OMO"></canvas></div><p class="muted data-chart-note" id="omoHistoryChartNote">Đang tải chuỗi lịch sử OMO.</p></div><div id="omoLatestTable" hidden><table><thead><tr><th>Chỉ tiêu</th><th>Giá trị</th><th>Đơn vị</th><th>Ngày dữ liệu</th><th>Trạng thái</th><th>Nguồn</th></tr></thead><tbody>${rows.map(item => `
        <tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${fmt(item.value, 2)}</td><td>${escapeHtml(item.unit)}</td><td>${escapeHtml(dateFmt(item.date))}</td><td>${isStale(item) ? '<span class="status-pill warning">Dữ liệu cũ</span>' : '<span class="status-pill neutral">Mới</span>'}</td><td><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Xem nguồn</a></td></tr>`).join('')}</tbody></table></div><p class="muted">Snapshot đồng bộ lúc ${escapeHtml(dateFmt(snapshot.fetchedAt))}. Khối lượng mua OMO là tổng giao dịch mua trúng thầu trong ngày; chênh lệch lưu hành OMO − tín phiếu là chỉ tiêu tồn lượng. Hai chỉ tiêu này không thay thế cho bơm/hút ròng trong ngày. Cảnh báo dữ liệu cũ nếu kỳ quan sát quá 5 ngày.</p>`;
      setupOmoChartControls();
      if (updated) {
        updated.textContent = anyStale ? 'Cảnh báo: dữ liệu OMO cũ' : 'Ngày mới nhất: ' + dateFmt(newest);
        updated.className = anyStale ? 'status-pill warning' : 'status-pill positive';
      }
    } catch (error) {
      content.innerHTML = '<div class="empty-state"><h3>Chưa tải được dữ liệu OMO mới</h3><p>Snapshot OMO riêng chưa có hoặc không hợp lệ. Không dùng dữ liệu lịch sử cũ để giả lập số liệu mới.</p></div>';
      if (updated) { updated.textContent = 'Chưa có dữ liệu mới'; updated.className = 'status-pill neutral'; }
      console.error('[omo-data]', error);
    }
  }

  async function loadPolicyRates() {
    const content = $('#policyRatesContent');
    const updated = $('#policyRatesUpdated');
    if (!content) return;
    try {
      const response = await fetchDataFile('policy-rates.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data) || !snapshot.data.length || !snapshot.sourceUrl || !snapshot.confirmedThrough) {
        throw new Error('Snapshot lãi suất điều hành không hợp lệ');
      }
      const rows = snapshot.data.filter(item => item.name && Number.isFinite(Number(item.value)) && item.unit === '%/năm' && item.effectiveDate);
      if (!rows.length) throw new Error('Không có mức lãi suất hợp lệ');
      content.innerHTML = `<table><thead><tr><th>Chỉ tiêu</th><th>Mức lãi suất</th><th>Đơn vị</th><th>Ngày hiệu lực</th></tr></thead><tbody>${rows.map(item => `<tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${fmt(item.value, 2)}</td><td>${escapeHtml(item.unit)}</td><td>${escapeHtml(dateFmt(item.effectiveDate))}</td></tr>`).join('')}</tbody></table><p class="muted">Đối chiếu trạng thái đến ${escapeHtml(dateFmt(snapshot.confirmedThrough))}. <a href="${escapeHtml(snapshot.sourceUrl)}" target="_blank" rel="noopener noreferrer">Xem nguồn chính</a></p>`;
      const policyChartBox = document.createElement('div');
      policyChartBox.className = 'extra-money-series';
      policyChartBox.innerHTML = '<div class="data-view-toolbar"><div class="view-switch"><button type="button" data-view="chart" class="is-active">Biểu đồ</button><button type="button" data-view="table">Bảng số liệu</button></div><label class="chart-type-label">Kiểu biểu đồ <select class="extra-chart-type"><option value="line">Đường</option><option value="bar">Cột</option></select></label></div><div class="chart-canvas-wrap"><canvas role="img" aria-label="Biểu đồ lãi suất điều hành NHNN"></canvas></div><p class="muted extra-chart-note">Mức lãi suất hiện hành; không phải chuỗi lịch sử theo ngày.</p>';
      content.insertAdjacentElement('afterend', policyChartBox);
      const policyCanvas = policyChartBox.querySelector('canvas');
      let policyChart = null;
      const drawPolicyChart = () => {
        if (policyChart) policyChart.destroy();
        if (!window.Chart) return;
        policyChart = new Chart(policyCanvas, { type: policyChartBox.querySelector('.extra-chart-type').value, data: { labels: rows.map(item => item.name), datasets: [{ label: 'Lãi suất (%/năm)', data: rows.map(item => Number(item.value)), borderWidth: 2 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { maxRotation: 0 } }, y: { beginAtZero: true } } } });
      };
      policyChartBox.querySelector('.extra-chart-type').addEventListener('change', drawPolicyChart);
      policyChartBox.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
        policyChartBox.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('is-active', b === button));
        const showChart = button.dataset.view === 'chart';
        policyChartBox.querySelector('.chart-canvas-wrap').hidden = !showChart;
        content.hidden = showChart;
      }));
      drawPolicyChart();
      if (updated) { updated.textContent = 'Xác minh đến ' + dateFmt(snapshot.confirmedThrough); updated.className = 'status-pill neutral'; }
    } catch (error) {
      content.innerHTML = '<div class="empty-state"><h3>Chưa tải được lãi suất điều hành</h3><p>Không có snapshot hợp lệ; không hiển thị giá trị thay thế.</p></div>';
      if (updated) { updated.textContent = 'Chưa có dữ liệu'; updated.className = 'status-pill neutral'; }
      console.error('[policy-rates]', error);
    }
  }

  async function loadCreditGrowth() {
    const content = $('#creditGrowthContent');
    const updated = $('#creditGrowthUpdated');
    if (!content) return;
    try {
      const response = await fetchDataFile('credit-growth.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data) || !snapshot.data.length || !snapshot.sourceUrl || !snapshot.observationDate) {
        throw new Error('Snapshot tăng trưởng tín dụng không hợp lệ');
      }
      const rows = snapshot.data.filter(item => item && item.name && item.unit && Number.isFinite(Number(item.value)));
      if (!rows.length) throw new Error('Không có chỉ tiêu hợp lệ');
      content.innerHTML = `<table><thead><tr><th>Chỉ tiêu</th><th>Giá trị</th><th>Đơn vị</th><th>Ngày dữ liệu</th></tr></thead><tbody>${rows.map(item => `<tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${fmt(item.value, 2)}</td><td>${escapeHtml(item.unit)}</td><td>${escapeHtml(dateFmt(snapshot.observationDate))}</td></tr>`).join('')}</tbody></table><p class="muted">Công bố ngày ${escapeHtml(dateFmt(snapshot.publishedDate))}. <a href="${escapeHtml(snapshot.sourceUrl)}" target="_blank" rel="noopener noreferrer">Xem nguồn gốc</a></p>`;
      if (updated) { updated.textContent = 'Ngày dữ liệu: ' + dateFmt(snapshot.observationDate); updated.className = 'status-pill neutral'; }
    } catch (error) {
      content.innerHTML = '<div class="empty-state"><h3>Chưa tải được dữ liệu</h3><p>Snapshot thiếu hoặc không hợp lệ; không hiển thị số liệu thay thế.</p></div>';
      if (updated) { updated.textContent = 'Chưa có dữ liệu'; updated.className = 'status-pill neutral'; }
      console.error('[credit-growth]', error);
    }
  }

  async function loadCreditGrowthHistoryChart() {
    const canvas = $('#creditGrowthHistoryChart');
    const note = $('#creditGrowthHistoryNote');
    if (!canvas || !window.Chart) return;
    try {
      const response = await fetchDataFile('category-data.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      const series = (snapshot.data || []).find(item => item.category === 'credit-growth' && Array.isArray(item.observations));
      const points = (series?.observations || []).filter(p => p && /^\d{4}-\d{2}-\d{2}$/.test(p.date) && Number.isFinite(Number(p.value))).sort((a,b)=>a.date.localeCompare(b.date));
      if (!points.length) throw new Error('Không có chuỗi lịch sử tăng trưởng tín dụng');
      new Chart(canvas, { type:'line', data:{labels:points.map(p=>dateFmt(p.date)),datasets:[{label:series.name || 'Tăng trưởng tín dụng so đầu năm',data:points.map(p=>Number(p.value)),borderWidth:2,tension:.2,pointRadius:2,spanGaps:false}]}, options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,position:'bottom'}},scales:{x:{ticks:{maxTicksLimit:8,maxRotation:0},grid:{display:false}},y:{title:{display:true,text:'%'},beginAtZero:false}}}});
      if(note) note.textContent = 'Nguồn: NHNN qua Dữ Liệu Kinh Tế · Cập nhật đến ' + dateFmt(points[points.length-1].date) + '. Đây là chuỗi tăng trưởng lũy kế từ đầu năm, khác với số tăng so cùng kỳ trong bảng trên.';
    } catch(error) { if(note) note.textContent='Chưa có chuỗi lịch sử biểu đồ; bảng số liệu công bố vẫn được giữ riêng.'; console.error('[credit-growth-chart]',error); }
  }

  async function loadBalanceOfPayments() {
    const content = $('#bopContent');
    const updated = $('#bopUpdated');
    const canvas = $('#bopChart');
    const note = $('#bopChartNote');
    if (!content) return;
    try {
      const response = await fetchDataFile('category-data.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      const keys = ['bop-current-capital','bop-financial','bop-overall'];
      const series = (snapshot.data || []).filter(item => keys.includes(item.category) && Array.isArray(item.observations));
      const labels = { 'bop-current-capital':'Cán cân vãng lai + vốn','bop-financial':'Cán cân tài chính','bop-overall':'Cán cân tổng thể' };
      if (!series.length) throw new Error('Snapshot chưa có chuỗi cán cân thanh toán');
      const rows = series.map(item => {
        const p = [...item.observations].filter(x=>x && /^\d{4}-\d{2}-\d{2}$/.test(x.date) && Number.isFinite(Number(x.value))).sort((a,b)=>a.date.localeCompare(b.date)).slice(-1)[0];
        return p ? { ...item, latest:p } : null;
      }).filter(Boolean);
      content.innerHTML = '<div class="table-scroll"><table><thead><tr><th>Chỉ tiêu</th><th>Giá trị mới nhất</th><th>Đơn vị</th><th>Kỳ dữ liệu</th><th>Nguồn</th></tr></thead><tbody>' + rows.map(item=>'<tr><td><strong>'+escapeHtml(item.name)+'</strong></td><td>'+fmt(item.latest.value,2)+'</td><td>'+escapeHtml(item.unit)+'</td><td>'+escapeHtml(dateFmt(item.latest.date))+'</td><td><a href="'+escapeHtml(item.url)+'" target="_blank" rel="noopener noreferrer">Xem nguồn</a></td></tr>').join('') + '</tbody></table></div>';
      if (canvas && window.Chart) {
        const quarters = [...new Set(series.flatMap(item=>item.observations.map(p=>p.date)))].sort();
        const datasets = series.map(item=>{ const map=new Map(item.observations.map(p=>[p.date,Number(p.value)])); return {label:labels[item.category] || item.name,data:quarters.map(q=>map.has(q)?map.get(q):null),borderWidth:2,tension:.15,pointRadius:3,spanGaps:false};});
        if(canvas._bopChart) canvas._bopChart.destroy();
        canvas._bopChart = new Chart(canvas,{type:'line',data:{labels:quarters.map(dateFmt),datasets},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,position:'bottom'}},scales:{x:{ticks:{maxTicksLimit:8,maxRotation:0},grid:{display:false}},y:{title:{display:true,text:'Tỷ theo nguồn'}}}}});
      }
      const newest = rows.map(x=>x.latest.date).sort().pop();
      if(updated){updated.textContent='Kỳ mới nhất: '+dateFmt(newest);updated.className='status-pill positive';}
      if(note) note.textContent='Nguồn: NHNN qua Dữ Liệu Kinh Tế. Chuỗi theo quý; các kỳ thiếu không được nội suy. Giá trị có thể được nguồn điều chỉnh.';
    } catch(error) {
      content.innerHTML='<div class="empty-state"><h3>Chưa có dữ liệu cán cân thanh toán</h3><p>Chưa đồng bộ được các chuỗi quý có nguồn xác minh. Không tự tạo hoặc ước tính số liệu.</p></div>';
      if(updated){updated.textContent='Chưa có dữ liệu';updated.className='status-pill neutral';}
      if(note) note.textContent='Biểu đồ sẽ hiển thị sau khi API đồng bộ thành công.';
      console.error('[balance-of-payments]',error);
    }
  }

  async function loadUsdVndReference() {
    const content = $('#usdVndReferenceContent');
    const updated = $('#usdVndReferenceUpdated');
    if (!content) return;
    try {
      const response = await fetchDataFile('currency-rates.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      const usd = snapshot.data?.find(item => item.code === 'USD');
      if (!usd || !Number.isFinite(Number(usd.vndPerUnit)) || Number(usd.vndPerUnit) <= 0 || !snapshot.lastUpdatedUtc) {
        throw new Error('Snapshot không có tỷ giá USD/VND tham khảo hợp lệ');
      }
      content.innerHTML = `<table><thead><tr><th>Chỉ tiêu</th><th>Giá trị</th><th>Đơn vị</th><th>Thời điểm nguồn cập nhật</th></tr></thead><tbody><tr><td><strong>USD/VND tham khảo</strong></td><td>${fmt(usd.vndPerUnit, 2)}</td><td>VND / 1 USD</td><td>${escapeHtml(dateFmt(snapshot.lastUpdatedUtc))}</td></tr></tbody></table>`;
      const usdChartBox = document.createElement('div');
      usdChartBox.className = 'extra-money-series';
      usdChartBox.innerHTML = '<div class="data-view-toolbar"><div class="view-switch"><button type="button" data-view="chart" class="is-active">Biểu đồ</button><button type="button" data-view="table">Bảng số liệu</button></div><label class="chart-type-label">Kiểu biểu đồ <select class="extra-chart-type"><option value="line">Đường</option><option value="bar">Cột</option></select></label></div><div class="chart-canvas-wrap"><canvas role="img" aria-label="Tỷ giá USD/VND tham khảo"></canvas></div><p class="muted extra-chart-note">Snapshot hiện chỉ có một mốc tỷ giá; cần tích lũy lịch sử qua các lần đồng bộ để thể hiện xu hướng theo thời gian.</p>';
      content.insertAdjacentElement('afterend', usdChartBox);
      const usdCanvas = usdChartBox.querySelector('canvas');
      let usdChart = null;
      const drawUsdChart = () => {
        if (usdChart) usdChart.destroy();
        if (!window.Chart) return;
        usdChart = new Chart(usdCanvas, { type: usdChartBox.querySelector('.extra-chart-type').value, data: { labels: [dateFmt(snapshot.lastUpdatedUtc)], datasets: [{ label: 'VND / 1 USD', data: [Number(usd.vndPerUnit)], borderWidth: 2 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: false } } } });
      };
      usdChartBox.querySelector('.extra-chart-type').addEventListener('change', drawUsdChart);
      usdChartBox.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
        usdChartBox.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('is-active', b === button));
        const showChart = button.dataset.view === 'chart';
        usdChartBox.querySelector('.chart-canvas-wrap').hidden = !showChart;
        content.hidden = showChart;
      }));
      drawUsdChart();
      if (updated) {
        updated.textContent = 'Nguồn cập nhật: ' + dateFmt(snapshot.lastUpdatedUtc);
        updated.className = 'status-pill positive';
      }
    } catch (error) {
      content.innerHTML = '<div class="empty-state"><h3>Chưa tải được tỷ giá tham khảo</h3><p>Không có dữ liệu hợp lệ trong snapshot. Vui lòng thử lại sau khi đồng bộ nguồn.</p></div>';
      if (updated) { updated.textContent = 'Chưa có dữ liệu'; updated.className = 'status-pill neutral'; }
      console.error('[usd-vnd-reference]', error);
    }
  }

  async function loadFinancialRates() {
    const bondTable = $('#bondYieldsTable');
    const interestTable = $('#interestRatesTable');
    const bondUpdated = $('#bondYieldsUpdated');
    const interestUpdated = $('#interestRatesUpdated');
    try {
      const response = await fetchDataFile('financial-rates.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data) || !snapshot.data.length) throw new Error('Snapshot lãi suất không hợp lệ');
      const valid = snapshot.data.filter(item =>
        item && item.name && item.date && Number.isFinite(Number(item.value)) && item.unit === '%/năm'
      );
      if (!valid.length) throw new Error('Không có dữ liệu lãi suất hợp lệ');

      const renderTable = rows => rows.length
        ? `<table><thead><tr><th>Chỉ tiêu</th><th>Giá trị mới nhất</th><th>Đơn vị</th><th>Ngày dữ liệu</th><th>Nguồn</th></tr></thead><tbody>${rows.map(item => `
          <tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${fmt(item.value, 4)}</td><td>${escapeHtml(item.unit)}</td><td>${escapeHtml(dateFmt(item.date))}</td><td>${escapeHtml(item.source)}</td></tr>`).join('')}</tbody></table>`
        : '<div class="empty-state"><h3>Chưa có dữ liệu</h3><p>Snapshot không có chuỗi phù hợp cho danh mục này.</p></div>';

      const bonds = valid.filter(item => item.category === 'bond').sort((a, b) => a.id - b.id);
      const rates = valid.filter(item => item.category === 'interest').sort((a, b) => a.id - b.id);
      if (bondTable) bondTable.innerHTML = renderTable(bonds);
      if (interestTable) interestTable.innerHTML = renderTable(rates);
      const updatedText = 'Snapshot: ' + dateFmt(snapshot.fetchedAt);
      if (bondUpdated) { bondUpdated.textContent = updatedText; bondUpdated.className = 'status-pill positive'; }
      if (interestUpdated) { interestUpdated.textContent = updatedText; interestUpdated.className = 'status-pill positive'; }

      const chartState = { bond: null, interest: null };
      const renderHistoryChart = (category, rows, canvasId, rangeId, noteId) => {
        const canvas = document.getElementById(canvasId);
        const rangeControl = document.getElementById(rangeId);
        const note = document.getElementById(noteId);
        if (!canvas || !rangeControl) return;
        const draw = () => {
          if (chartState[category]) { chartState[category].destroy(); chartState[category] = null; }
          if (typeof Chart === 'undefined') {
            if (note) note.textContent = 'Không tải được thư viện biểu đồ Chart.js.';
            return;
          }
          const days = Number(rangeControl.value) || 30;
          const cutoff = new Date();
          cutoff.setDate(cutoff.getDate() - days);
          const series = rows.map(item => ({
            label: item.name,
            points: (Array.isArray(item.observations) ? item.observations : [])
              .filter(point => point && point.date && Number.isFinite(Number(point.value)) && new Date(point.date + 'T00:00:00') >= cutoff)
              .sort((a, b) => a.date.localeCompare(b.date))
          })).filter(item => item.points.length);
          const dates = [...new Set(series.flatMap(item => item.points.map(point => point.date)))].sort();
          if (!dates.length) {
            if (note) note.textContent = 'Nguồn hiện chưa cung cấp quan sát lịch sử trong khoảng này. Hãy chạy lại workflow để lấy chuỗi lịch sử; không tạo dữ liệu giả.';
            return;
          }
          chartState[category] = new Chart(canvas, {
            type: 'line',
            data: {
              labels: dates.map(dateFmt),
              datasets: series.map((item, index) => {
                const values = new Map(item.points.map(point => [point.date, Number(point.value)]));
                return {
                  label: item.label,
                  data: dates.map(date => values.has(date) ? values.get(date) : null),
                  spanGaps: false,
                  tension: 0.2,
                  pointRadius: 2,
                  pointHoverRadius: 5,
                  borderWidth: 2
                };
              })
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: { mode: 'nearest', intersect: false },
              plugins: { legend: { display: true, position: 'bottom' } },
              scales: {
                x: { title: { display: true, text: 'Ngày dữ liệu' } },
                y: { title: { display: true, text: '%/năm' }, beginAtZero: false }
              }
            }
          });
          if (note) note.textContent = 'Hiển thị ' + dates.length + ' ngày có quan sát trong ' + days + ' ngày gần nhất. Các ngày thiếu dữ liệu được để trống, không nội suy.';
        };
        rangeControl.addEventListener('change', draw);
        draw();
      };
      renderHistoryChart('interest', rates, 'interestRatesChart', 'interestChartRange', 'interestChartNote');
      renderHistoryChart('bond', bonds, 'bondYieldsChart', 'bondChartRange', 'bondChartNote');
    } catch (error) {
      const message = '<div class="empty-state"><h3>Chưa tải được dữ liệu</h3><p>Kiểm tra data/financial-rates.json và trạng thái workflow GitHub Actions.</p></div>';
      if (bondTable) bondTable.innerHTML = message;
      if (interestTable) interestTable.innerHTML = message;
      if (bondUpdated) { bondUpdated.textContent = 'Chưa có dữ liệu'; bondUpdated.className = 'status-pill neutral'; }
      if (interestUpdated) { interestUpdated.textContent = 'Chưa có dữ liệu'; interestUpdated.className = 'status-pill neutral'; }
      console.error('[financial-rates]', error);
    }
  }

  const categoryCharts = {};
  async function loadCategoryData() {
    const targets = {
      transport: { table: '#transportDataTable', updated: '#transportUpdated', canvas: '#transportHistoryChart', note: '#transportChartNote' },
      agriculture: { table: '#agricultureDataTable', updated: '#agricultureUpdated', canvas: '#agricultureHistoryChart', note: '#agricultureChartNote' },
      ports: { table: '#portsDataTable', updated: '#portsUpdated', canvas: '#portsHistoryChart', note: '#portsChartNote' },
      property: { table: '#propertyDataTable', updated: '#propertyUpdated', canvas: '#propertyHistoryChart', note: '#propertyChartNote' },
      labor: { table: '#laborDataTable', updated: '#laborUpdated', canvas: '#laborHistoryChart', note: '#laborChartNote' },
      passengers: { table: '#passengersDataTable', updated: '#passengersUpdated', canvas: '#passengersHistoryChart', note: '#passengersChartNote' },
      'agri-price': { table: '#agriPriceDataTable', updated: '#agriPriceUpdated', canvas: '#agriPriceHistoryChart', note: '#agriPriceChartNote' },
      retail: { table: '#retailDataTable', updated: '#retailUpdated', canvas: '#retailHistoryChart', note: '#retailChartNote' },
      exports: { table: '#exportsDataTable', updated: '#exportsUpdated', canvas: '#exportsHistoryChart', note: '#exportsChartNote' },
      imports: { table: '#importsDataTable', updated: '#importsUpdated', canvas: '#importsHistoryChart', note: '#importsChartNote' },
      cpi: { table: '#cpiDataTable', updated: '#cpiUpdated', canvas: '#cpiHistoryChart', note: '#cpiChartNote' },
      'logistics-index': { table: '#logisticsIndexTable', updated: '#logisticsIndexUpdated', canvas: '#logisticsIndexChart', note: '#logisticsIndexNote' },
      'sea-freight': { table: '#seaFreightTable', updated: '#seaFreightUpdated', canvas: '#seaFreightChart', note: '#seaFreightNote' },
      'corporate-bonds-property': { table: '#propertyBondsTable', updated: '#propertyBondsUpdated', canvas: '#propertyBondsChart', note: '#propertyBondsNote' },
      'agri-exports-rubber': { table: '#rubberExportsTable', updated: '#rubberExportsUpdated', canvas: '#rubberExportsChart', note: '#rubberExportsNote' },
      'agri-imports-rubber': { table: '#rubberImportsTable', updated: '#rubberImportsUpdated', canvas: '#rubberImportsChart', note: '#rubberImportsNote' },
      'credit-balance': { table: '#creditBalanceTable', updated: '#creditBalanceUpdated', canvas: '#creditBalanceChart', note: '#creditBalanceNote' },
      'credit-growth': { table: '#creditGrowthTable', updated: '#creditGrowthUpdated', canvas: '#creditGrowthChart', note: '#creditGrowthNote' },
      'labor-force': { table: '#laborForceTable', updated: '#laborForceUpdated', canvas: '#laborForceChart', note: '#laborForceNote' },
      'global-rice': { table: '#globalRiceTable', updated: '#globalRiceUpdated', canvas: '#globalRiceChart', note: '#globalRiceNote' },
      'global-rubber': { table: '#globalRubberTable', updated: '#globalRubberUpdated', canvas: '#globalRubberChart', note: '#globalRubberNote' },
      'global-steel': { table: '#globalSteelTable', updated: '#globalSteelUpdated', canvas: '#globalSteelChart', note: '#globalSteelNote' },
      'housing-cpi': { table: '#housingCpiTable', updated: '#housingCpiUpdated', canvas: '#housingCpiChart', note: '#housingCpiNote' },
      'coastal-shipping-index': { table: '#coastalShippingTable', updated: '#coastalShippingUpdated', canvas: '#coastalShippingChart', note: '#coastalShippingNote' }

    };
    try {
      const response = await fetchDataFile('category-data.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data)) throw new Error('Snapshot không có mảng data');
      for (const [category, target] of Object.entries(targets)) {
        const table = $(target.table);
        const updated = $(target.updated);
        const canvas = $(target.canvas);
        const note = $(target.note);
        if (!table) continue;
        const item = snapshot.data.find(row => row.category === category);
        const observations = (item?.observations || []).filter(point =>
          point && /^\d{4}-\d{2}-\d{2}$/.test(point.date) &&
          Number.isFinite(Number(point.value)) && point.date <= new Date().toISOString().slice(0, 10)
        ).sort((a, b) => a.date.localeCompare(b.date));
        if (!item || !observations.length) {
          table.innerHTML = '<div class="empty-state"><h3>Chưa có dữ liệu hợp lệ</h3><p>Nguồn chưa trả về quan sát đã xác minh cho danh mục này.</p></div>';
          if (updated) { updated.textContent = 'Chưa có dữ liệu'; updated.className = 'status-pill neutral'; }
          if (note) note.textContent = 'Chưa có quan sát lịch sử hợp lệ để vẽ biểu đồ.';
          continue;
        }
        const latest = observations[observations.length - 1];
        const rows = observations.slice(-24).reverse();
        table.innerHTML = `<table><thead><tr><th>Chỉ tiêu</th><th>Giá trị</th><th>Đơn vị</th><th>Kỳ dữ liệu</th><th>Nguồn</th></tr></thead><tbody>${rows.map(point => `
          <tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${fmt(point.value, 3)}</td><td>${escapeHtml(item.unit || '—')}</td><td>${escapeHtml(dateFmt(point.date))}</td><td><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.source)}</a></td></tr>`).join('')}</tbody></table>`;
        const ageDays = Math.max(0, Math.floor((Date.now() - new Date(latest.date + 'T00:00:00Z').getTime()) / 86400000));
        const staleAfterDays = ({
          'global-rice': 14, 'global-rubber': 14, 'global-steel': 14,
          'omo-buy-total': 5, 'omo-net-outstanding': 5,
          'logistics-index': 150, 'coastal-shipping-index': 150,
          'agri-price': 120, 'cpi': 120, 'housing-cpi': 120,
          'credit-balance': 90, 'credit-growth': 90,
          'property': 180, 'corporate-bonds-property': 90
        })[category] || 75;
        const stale = ageDays > staleAfterDays;
        if (updated) {
          updated.textContent = (stale ? 'Cảnh báo dữ liệu cũ · ' : 'Kỳ mới nhất: ') + dateFmt(latest.date);
          updated.className = 'status-pill ' + (stale ? 'warning' : 'positive');
        }
        if (canvas && window.Chart) {
          const panel = table.closest('.currency-panel') || table.parentElement;
          let toolbar = panel.querySelector('.category-chart-toolbar');
          if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.className = 'data-view-toolbar category-chart-toolbar';
            toolbar.innerHTML = '<div class="view-switch" role="group" aria-label="Chế độ dữ liệu"><button type="button" data-mode="chart" class="is-active">Biểu đồ</button><button type="button" data-mode="table">Bảng số liệu</button></div><label class="chart-type-label">Kiểu biểu đồ <select class="category-chart-type"><option value="line">Đường</option><option value="bar">Cột</option></select></label>';
            table.parentNode.insertBefore(toolbar, table);
            toolbar.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => {
              toolbar.querySelectorAll('[data-mode]').forEach(b => b.classList.toggle('is-active', b === button));
              const chartMode = button.dataset.mode === 'chart';
              const chartWrap = panel.querySelector(target.canvas)?.closest('.chart-panel, .data-chart-view');
              if (chartWrap) chartWrap.hidden = !chartMode;
              table.hidden = chartMode;
            }));
            toolbar.querySelector('.category-chart-type').addEventListener('change', () => drawCategoryChart(toolbar.querySelector('.category-chart-type').value));
          }
          const drawCategoryChart = type => {
            if (categoryCharts[category]) categoryCharts[category].destroy();
            categoryCharts[category] = new Chart(canvas, {
              type: type || 'line',
              data: {
                labels: observations.map(point => dateFmt(point.date)),
                datasets: [{
                  label: item.name,
                  data: observations.map(point => Number(point.value)),
                  borderWidth: 2,
                  pointRadius: observations.length > 48 ? 0 : 2,
                  pointHoverRadius: 4,
                  tension: 0.15,
                  fill: false
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                  legend: { display: false },
                  tooltip: { callbacks: { label: context => fmt(context.parsed.y, 3) + ' ' + (item.unit || '') } }
                },
                scales: {
                  x: { ticks: { maxTicksLimit: 8, maxRotation: 0 }, grid: { display: false } },
                  y: { beginAtZero: false, ticks: { callback: value => fmt(value, 2) } }
                }
              }
            });
          };
          table.hidden = true;
          const chartWrap = canvas.closest('.chart-panel, .data-chart-view');
          if (chartWrap) chartWrap.hidden = false;
          drawCategoryChart(toolbar.querySelector('.category-chart-type').value);
          if (note) note.textContent = 'Nguồn: ' + item.source + ' · Đơn vị: ' + (item.unit || 'theo nguồn') + ' · ' + observations.length + ' quan sát. ' + (stale ? 'Cảnh báo: kỳ mới nhất đã cũ ' + ageDays + ' ngày.' : 'Các kỳ tương lai bị loại khỏi hiển thị.');
        } else if (note) {
          note.textContent = 'Không tải được thư viện Chart.js; bảng số liệu vẫn hoạt động.';
        }
      }
    } catch (error) {
      for (const target of Object.values(targets)) {
        const table = $(target.table);
        const updated = $(target.updated);
        if (table) table.innerHTML = '<div class="empty-state"><h3>Chưa tải được dữ liệu</h3><p>Kiểm tra data/category-data.json và workflow đồng bộ danh mục.</p></div>';
        if (updated) { updated.textContent = 'Chưa đồng bộ'; updated.className = 'status-pill neutral'; }
      }
      console.error('[category-data]', error);
    }
  }


  function drawEconomicPanelChart(panel, items, chartType) {
    const canvas = panel.querySelector('.data-chart-view canvas');
    const note = panel.querySelector('.data-chart-note');
    if (!canvas || !window.Chart || !items.length) return;
    const existing = canvas._economicChart;
    if (existing) existing.destroy();
    const allDates = [...new Set(items.flatMap(item => (item.observations || [])
      .filter(point => point && /^\d{4}-\d{2}-\d{2}$/.test(point.date) &&
        Number.isFinite(Number(point.value)) && point.date <= new Date().toISOString().slice(0, 10))
      .map(point => point.date)))].sort();
    const datasets = items.map((item, index) => {
      const values = new Map((item.observations || []).map(point => [point.date, Number(point.value)]));
      return {
        label: item.name,
        data: allDates.map(date => values.has(date) ? values.get(date) : null),
        borderWidth: 2,
        pointRadius: allDates.length > 48 ? 0 : 2,
        tension: 0.18,
        spanGaps: false
      };
    });
    canvas._economicChart = new Chart(canvas, {
      type: chartType || 'line',
      data: { labels: allDates.map(dateFmt), datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: items.length > 1, position: 'bottom' },
          tooltip: { callbacks: { label: context => context.dataset.label + ': ' + fmt(context.parsed.y, 3) + ' ' + (items[context.datasetIndex]?.unit || '') } }
        },
        scales: {
          x: { ticks: { maxTicksLimit: 8, maxRotation: 0 }, grid: { display: false } },
          y: { beginAtZero: false, ticks: { callback: value => fmt(value, 2) } }
        }
      }
    });
    if (note) note.textContent = 'Nguồn: Dữ Liệu Kinh Tế · ' + allDates.length + ' kỳ có dữ liệu. Khoảng trống được giữ nguyên, không nội suy.';
  }

  async function loadDLKTEconomicPanels() {
    const groups = {
      m2: { content: '#m2DataContent', updated: '#m2DataUpdated', categories: ['m2', 'household-deposits', 'corporate-deposits'], staleDays: 75 },
      deposits: { content: '#depositRatesContent', updated: '#depositRatesUpdated', categories: ['deposit-mb-12m'], staleDays: 45 },
      gold: { content: '#goldDataContent', updated: '#goldDataUpdated', categories: ['gold-doji-buy', 'gold-btmc-buy', 'gold-btmc-sell'], staleDays: 14 }
    };
    try {
      const response = await fetchDataFile('category-data.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data)) throw new Error('Snapshot không có mảng data');
      for (const group of Object.values(groups)) {
        const target = $(group.content);
        const updated = $(group.updated);
        if (!target) continue;
        const items = snapshot.data.filter(item => group.categories.includes(item.category) &&
          Array.isArray(item.observations) && item.observations.length &&
          Number.isFinite(Number(item.value)) && item.date);
        if (!items.length) {
          target.innerHTML = '<div class="empty-state"><h3>Chưa có dữ liệu hợp lệ</h3><p>Workflow đồng bộ chưa trả về các chuỗi cần thiết; không hiển thị số liệu tự tạo.</p></div>';
          if (updated) { updated.textContent = 'Chưa có dữ liệu'; updated.className = 'status-pill neutral'; }
          continue;
        }
        target.innerHTML = '<table><thead><tr><th>Chỉ tiêu</th><th>Giá trị mới nhất</th><th>Đơn vị</th><th>Kỳ dữ liệu</th><th>Nguồn</th></tr></thead><tbody>' +
          items.map(item => '<tr><td><strong>' + escapeHtml(item.name) + '</strong></td><td>' + fmt(item.value, 3) + '</td><td>' + escapeHtml(item.unit || '—') + '</td><td>' + escapeHtml(dateFmt(item.date)) + '</td><td><a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(item.source || 'Dữ Liệu Kinh Tế') + '</a></td></tr>').join('') +
          '</tbody></table>';
        const panel = target.closest('.currency-panel');
        if (panel && window.Chart) {
          let toolbar = panel.querySelector('.data-view-toolbar');
          if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.className = 'data-view-toolbar';
            toolbar.innerHTML = '<div class="view-switch" role="group" aria-label="Cách hiển thị dữ liệu"><button type="button" data-view="chart" class="is-active">Biểu đồ</button><button type="button" data-view="table">Bảng số liệu</button></div><label class="chart-type-label">Kiểu biểu đồ <select class="data-chart-type" aria-label="Kiểu biểu đồ"><option value="line">Đường</option><option value="bar">Cột</option></select></label>';
            target.parentNode.insertBefore(toolbar, target);
            const chartPanel = document.createElement('div');
            chartPanel.className = 'data-chart-view';
            chartPanel.innerHTML = '<div class="chart-canvas-wrap"><canvas role="img" aria-label="Biểu đồ chuỗi dữ liệu"></canvas></div><p class="muted data-chart-note"></p>';
            target.insertAdjacentElement('afterend', chartPanel);
            toolbar.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
              toolbar.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('is-active', b === button));
              const showChart = button.dataset.view === 'chart';
              target.hidden = showChart;
              chartPanel.hidden = !showChart;
            }));
            toolbar.querySelector('.data-chart-type').addEventListener('change', () => drawEconomicPanelChart(panel, items, toolbar.querySelector('.data-chart-type').value));
          }
          target.hidden = true;
          const chartPanel = panel.querySelector('.data-chart-view');
          if (chartPanel) chartPanel.hidden = false;
          drawEconomicPanelChart(panel, items, toolbar.querySelector('.data-chart-type').value);
        }
        const latest = items.map(item => item.date).sort().pop();
        const latestTime = new Date(latest.length === 10 ? latest + 'T00:00:00' : latest).getTime();
        const ageDays = Number.isFinite(latestTime) ? Math.floor((Date.now() - latestTime) / 86400000) : Infinity;
        const stale = ageDays > group.staleDays;
        if (updated) {
          updated.textContent = (stale ? 'Dữ liệu cũ · ' : 'Kỳ mới nhất: ') + dateFmt(latest);
          updated.className = 'status-pill ' + (stale ? 'neutral' : 'positive');
          updated.title = stale ? 'Dữ liệu đã quá ' + group.staleDays + ' ngày; kiểm tra nguồn trước khi sử dụng.' : 'Ngày quan sát mới nhất trong snapshot.';
        }
      }
    } catch (error) {
      console.error('[DLKT economic panels]', error);
      for (const group of Object.values(groups)) {
        const target = $(group.content), updated = $(group.updated);
        if (target) target.innerHTML = '<div class="empty-state"><h3>Chưa tải được dữ liệu</h3><p>Kiểm tra snapshot và workflow đồng bộ danh mục.</p></div>';
        if (updated) { updated.textContent = 'Chưa đồng bộ'; updated.className = 'status-pill neutral'; }
      }
    }
  }

  function setupNavigation() {
    const sidebar = $('#siteSidebar');
    $('#mobileMenu')?.addEventListener('click', () => sidebar?.classList.toggle('sidebar-open'));
    $$('#mainNav a').forEach(link => link.addEventListener('click', () => sidebar?.classList.remove('sidebar-open')));
    $('#siteSearch')?.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        const query = event.currentTarget.value.trim().toLocaleLowerCase('vi');
        if (!query) return;
        const target = [
          ['hàng hóa', '#hang-hoa'], ['dầu', '#hang-hoa'], ['brent', '#hang-hoa'],
          ['vĩ mô', '#vi-mo'], ['gdp', '#vi-mo'], ['cpi', '#vi-mo'],
          ['chứng khoán', '#co-phieu'], ['tài chính', '#co-phieu'],
          ['nguồn', '#nguon'], ['tỷ giá', '#tien-te'], ['bất động sản', '#bat-dong-san']
        ].find(([term]) => term.includes(query) || query.includes(term));
        if (target) document.querySelector(target[1])?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        else {
          const commodityInput = $('#commoditySearch');
          if (commodityInput) {
            commodityInput.value = event.currentTarget.value;
            renderCommodities();
            $('#hang-hoa')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      }
    });
  }

  function setupCommodityFilters() {
    $('#commoditySearch')?.addEventListener('input', renderCommodities);
    $('#commodityGroup')?.addEventListener('change', renderCommodities);
  }


  function setupReportQueue() {
    const form = $('#reportQueueForm');
    const body = $('#reportQueueBody');
    const summary = $('#queueSummary');
    const notice = $('#queueNotice');
    const jobs = [];
    const existingSymbols = new Set(['MBB','ACB','FPT','SHB','TCX','HCM','VND','SHS','NLG','BSR','TCB','VHM']);
    const reportLabel = value => ({consolidated:'Hợp nhất',separate:'Riêng lẻ',both:'Cả hai'}[value] || value);
    const render = () => {
      if (summary) summary.textContent = jobs.length + ' yêu cầu mới trong phiên';
      if (!body) return;
      if (!jobs.length) { body.innerHTML = '<tr><td colspan="4">Chưa có yêu cầu mới trong phiên này. Danh sách chính thức nằm trong config/report-queue.json.</td></tr>'; return; }
      body.innerHTML = jobs.map(job => '<tr><td><strong>'+escapeHtml(job.symbol)+'</strong>'+(job.company?'<br><small>'+escapeHtml(job.company)+'</small>':'')+'</td><td>Từ '+job.startYear+' · '+escapeHtml(reportLabel(job.reportType))+'</td><td><span class="status-pill neutral">queued · chờ đưa vào repository</span></td><td>'+escapeHtml(dateFmt(job.createdAt))+'</td></tr>').join('');
    };
    form?.addEventListener('submit', event => {
      event.preventDefault();
      const symbol = ($('#queueSymbol')?.value || '').trim().toUpperCase();
      const company = ($('#queueCompany')?.value || '').trim();
      const startYear = Number($('#queueStartYear')?.value || 2024);
      const reportType = $('#queueReportType')?.value || 'consolidated';
      if (!/^[A-Z0-9]{3,10}$/.test(symbol)) { if(notice) notice.textContent = 'Mã không hợp lệ. Dùng 3–10 chữ cái hoặc chữ số.'; return; }
      if (jobs.some(job => job.symbol === symbol && job.startYear === startYear && job.reportType === reportType)) { if(notice) notice.textContent = 'Yêu cầu tương tự đã có trong danh sách phiên này.'; return; }
      const now = new Date().toISOString();
      jobs.push({id:'fin-'+symbol.toLowerCase()+'-'+Date.now(),symbol,company,startYear,reportType,status:'queued',createdAt:now,attempts:0,lastError:null,sourceCandidates:[],downloadedFiles:[],verifiedPeriods:[]});
      existingSymbols.add(symbol);
      render();
      if(notice) notice.textContent = 'Đã tạo yêu cầu trong trình duyệt. Tải JSON rồi ghép vào config/report-queue.json để đưa vào hàng chờ tự động.';
      form.reset();
      if ($('#queueStartYear')) $('#queueStartYear').value = '2024';
    });
    $('#downloadQueue')?.addEventListener('click', () => {
      if (!jobs.length) { if(notice) notice.textContent = 'Chưa có yêu cầu mới để xuất.'; return; }
      const payload = {schemaVersion:1,updatedAt:new Date().toISOString(),jobs};
      const blob = new Blob([JSON.stringify(payload,null,2)+'\\n'],{type:'application/json'});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url; link.download = 'report-queue-additions.json'; link.click();
      URL.revokeObjectURL(url);
      if(notice) notice.textContent = 'Đã xuất tệp JSON. Ghép các mục jobs vào config/report-queue.json rồi commit lên GitHub.';
    });
    render();
  }

  function setupFinancials() {
    const symbolSelect = $('#stockSymbol');
    const yearSelect = $('#stockYear');
    const loadButton = $('#loadStock');
    const stateBox = $('#stockState');
    const tableWrap = $('#stockTableWrap');
    const tableBody = $('#stockTableBody');
    const status = $('#stockSourceStatus');
    const symbols = ['MBB','ACB','FPT','SHB','TCX','HCM','VND','SHS','NLG','BSR','TCB','VHM'];
    const snapshots = new Map();
    const charts = {};
    let isLoading = false;

    const numberOrDash = value => {
      if (value === null || value === undefined || value === '' || !Number.isFinite(Number(value))) return '—';
      return fmt(value, 2);
    };
    const validPeriod = value => /^\d{4}-Q[1-4]$/.test(String(value || ''));
    const validNumber = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
    const periodLabel = value => String(value || '').replace('-Q', ' · Quý ');
    const fieldMeta = {
      revenue: { label: 'Doanh thu', unit: 'theo snapshot' },
      pretax_profit: { label: 'Lợi nhuận trước thuế', unit: 'theo snapshot' },
      net_profit: { label: 'Lợi nhuận sau thuế', unit: 'theo snapshot' },
      total_assets: { label: 'Tổng tài sản', unit: 'theo snapshot' },
      total_liabilities: { label: 'Nợ phải trả', unit: 'theo snapshot' },
      equity: { label: 'Vốn chủ sở hữu', unit: 'theo snapshot' },
      roa: { label: 'ROA', unit: '%' },
      roe: { label: 'ROE', unit: '%' }
    };
    const setEmpty = (title, message) => {
      if (tableWrap) tableWrap.classList.add('hidden');
      if (stateBox) {
        stateBox.classList.remove('hidden');
        const heading = $('h3', stateBox);
        const paragraph = $('p', stateBox);
        if (heading) heading.textContent = title;
        if (paragraph) paragraph.textContent = message;
      }
      if (tableBody) tableBody.innerHTML = '';
    };
    const rowsFor = ticker => {
      const snapshot = snapshots.get(ticker);
      return (snapshot?.items || []).filter(item => item && validPeriod(item.period)).slice().sort((a,b)=>a.period.localeCompare(b.period));
    };
    const allPeriods = () => [...new Set(symbols.flatMap(ticker => rowsFor(ticker).map(item => item.period)))].sort();

    function drawChart(key, canvasId, noteId, config) {
      const canvas = document.getElementById(canvasId);
      const note = document.getElementById(noteId);
      if (charts[key]) { charts[key].destroy(); charts[key] = null; }
      if (!canvas) return;
      const points = config.points || [];
      if (!points.length) {
        if (note) note.textContent = config.emptyMessage || 'Chưa có số liệu đã xác minh cho biểu đồ này. Không tạo hoặc nội suy số liệu.';
        return;
      }
      if (!window.Chart) {
        if (note) note.textContent = 'Không tải được thư viện Chart.js.';
        return;
      }
      charts[key] = new Chart(canvas, {
        type: config.type || 'line',
        data: { labels: config.labels, datasets: config.datasets },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: { legend: { display: true, position: 'bottom' } },
          scales: {
            x: { ticks: { maxTicksLimit: 12, maxRotation: 0 }, grid: { display: false } },
            y: { beginAtZero: config.beginAtZero ?? false, ticks: { callback: value => fmt(value, 2) } }
          }
        }
      });
      if (note) note.textContent = config.note || 'Chỉ hiển thị các kỳ có dữ liệu trong snapshot. Khoảng trống không được nội suy.';
    }

    function drawSelectedCharts(ticker) {
      const rows = rowsFor(ticker);
      const labels = rows.map(item => periodLabel(item.period));
      const numericSeries = (field, label, type='line') => {
        const values = rows.map(item => validNumber(item[field]) ? Number(item[field]) : null);
        const valid = values.some(value => value !== null);
        return { type, label, data: values, borderWidth: 2, tension: .18, pointRadius: rows.length > 32 ? 0 : 3, spanGaps: false, _valid: valid };
      };
      const financial = [
        {field:'revenue',label:'Doanh thu'},
        {field:'pretax_profit',label:'Lợi nhuận trước thuế'},
        {field:'net_profit',label:'Lợi nhuận sau thuế'}
      ].map(item=>({ ...item, values:rows.map(row=>validNumber(row[item.field])?Number(row[item.field]):null) }));
      const financialAvailable = financial.filter(series=>series.values.some(value=>value!==null));
      drawChart('profit','stockProfitChart','stockProfitNote',{
        labels, points:financialAvailable.flatMap(s=>s.values.filter(v=>v!==null)),
        datasets:financialAvailable.map(s=>({label:s.label,data:s.values,borderWidth:2,tension:.18,pointRadius:rows.length>32?0:3,spanGaps:false})),
        note:financialAvailable.length ? 'Nguồn: snapshot báo cáo tài chính đã lưu. Kiểm tra đơn vị và cách trình bày doanh thu/lợi nhuận trong từng báo cáo trước khi so sánh.' : '',
        emptyMessage:'Chưa có trường doanh thu hoặc lợi nhuận hợp lệ trong snapshot. Hãy trích xuất từ báo cáo gốc; website không tự ước tính.'
      });
      const balance = [
        {field:'total_assets',label:'Tổng tài sản'},
        {field:'total_liabilities',label:'Nợ phải trả'},
        {field:'equity',label:'Vốn chủ sở hữu'}
      ].map(item=>({ ...item, values:rows.map(row=>validNumber(row[item.field])?Number(row[item.field]):null) }));
      const balanceAvailable=balance.filter(series=>series.values.some(value=>value!==null));
      drawChart('balance','stockBalanceChart','stockBalanceNote',{
        labels,points:balanceAvailable.flatMap(s=>s.values.filter(v=>v!==null)),
        datasets:balanceAvailable.map(s=>({label:s.label,data:s.values,borderWidth:2,tension:.18,pointRadius:rows.length>32?0:3,spanGaps:false})),
        note:balanceAvailable.length?'Nguồn: snapshot báo cáo tài chính. So sánh theo cùng đơn vị và cùng cơ sở báo cáo (hợp nhất/riêng lẻ).':'',
        emptyMessage:'Chưa có số liệu tài sản, nợ hoặc vốn chủ sở hữu hợp lệ.'
      });
      const ratios=[
        {field:'roa',label:'ROA (%)'},
        {field:'roe',label:'ROE (%)'}
      ].map(item=>({ ...item, values:rows.map(row=>validNumber(row[item.field])?Number(row[item.field]):null) }));
      const ratiosAvailable=ratios.filter(series=>series.values.some(value=>value!==null));
      drawChart('ratios','stockRatiosChart','stockRatiosNote',{
        labels,points:ratiosAvailable.flatMap(s=>s.values.filter(v=>v!==null)),
        datasets:ratiosAvailable.map(s=>({label:s.label,data:s.values,borderWidth:2,tension:.18,pointRadius:rows.length>32?0:3,spanGaps:false})),
        note:ratiosAvailable.length?'ROA/ROE chỉ hiển thị nếu có trong snapshot đã xác minh. Cần ghi rõ công thức và dữ liệu bình quân đầu kỳ/cuối kỳ khi tự tính.':'',
        emptyMessage:'Chưa có ROA/ROE được xác minh. Không tính tỷ số nếu thiếu dữ liệu đầu vào hoặc công thức nguồn.'
      });
    }

    function drawComparison() {
      const metric = $('#stockCompareMetric')?.value || 'net_profit';
      const period = $('#stockComparePeriod')?.value || '';
      const meta = fieldMeta[metric] || fieldMeta.net_profit;
      const values = symbols.map(ticker => {
        const row = rowsFor(ticker).find(item=>item.period===period);
        return {ticker, value:row && validNumber(row[metric]) ? Number(row[metric]) : null};
      }).filter(item=>item.value!==null);
      drawChart('compare','stockCompareChart','stockCompareNote',{
        type:'bar', labels:values.map(item=>item.ticker), points:values.map(item=>item.value),
        datasets:values.length?[{label:meta.label+(meta.unit==='%'?' (%)':''),data:values.map(item=>item.value),borderWidth:1}]:[],
        beginAtZero:true,
        note:values.length?'Kỳ '+periodLabel(period)+' · '+meta.label+'. Chỉ so sánh các mã có dữ liệu, cùng đơn vị và cùng cơ sở báo cáo.':'',
        emptyMessage:'Chưa có dữ liệu đã xác minh cho chỉ tiêu và kỳ so sánh đã chọn.'
      });
      const table = $('#stockCompareTable');
      if (table) {
        table.innerHTML = values.length
          ? '<table><thead><tr><th>Mã</th><th>Kỳ</th><th>'+escapeHtml(meta.label)+'</th><th>Đơn vị</th></tr></thead><tbody>'+values.map(item=>'<tr><td><strong>'+item.ticker+'</strong></td><td>'+escapeHtml(periodLabel(period))+'</td><td>'+numberOrDash(item.value)+'</td><td>'+escapeHtml((metric==='roa'||metric==='roe')?'%':(rowsFor(item.ticker).find(row=>row.period===period)?.unit || meta.unit))+'</td></tr>').join('')+'</tbody></table>'
          : '<div class="empty-state"><h3>Chưa có dữ liệu để so sánh</h3><p>Chỉ những giá trị có nguồn kiểm chứng mới được hiển thị.</p></div>';
      }
    }

    function renderSelected() {
      const ticker = String(symbolSelect?.value || 'MBB').toUpperCase();
      const selectedYear = String(yearSelect?.value || '2022');
      const snapshot = snapshots.get(ticker);
      const rows = rowsFor(ticker).filter(item=>item.period.startsWith(selectedYear+'-Q'));
      if (!rows.length) {
        setEmpty('Chưa có báo cáo đã xác minh','Chưa có dữ liệu quý đã được kiểm chứng cho '+ticker+' năm '+selectedYear+'. Website vẫn giữ các biểu đồ trống cho tới khi snapshot được nạp từ báo cáo nguồn; không dùng số liệu minh họa.');
        if (status) status.textContent=(snapshot?.sourceName?'Nguồn khai báo: '+snapshot.sourceName+'. ':'')+'Số quý hợp lệ trong năm được chọn: 0.';
      } else {
        if (tableBody) tableBody.innerHTML=rows.map(item=>{
          const sourceUrl=typeof item.source_url==='string'&&/^https?:\/\///i.test(item.source_url)?item.source_url:'';
          return '<tr><td><strong>'+escapeHtml(periodLabel(item.period))+'</strong></td>'+
            '<td>'+numberOrDash(item.revenue)+'</td><td>'+numberOrDash(item.total_assets)+'</td>'+
            '<td>'+numberOrDash(item.total_liabilities)+'</td><td>'+numberOrDash(item.equity)+'</td>'+
            '<td>'+numberOrDash(item.pretax_profit)+'</td><td>'+numberOrDash(item.net_profit)+'</td>'+
            '<td>'+(validNumber(item.roa)?numberOrDash(item.roa)+'%':'—')+'</td>'+
            '<td>'+(validNumber(item.roe)?numberOrDash(item.roe)+'%':'—')+'</td>'+
            '<td>'+(sourceUrl?'<a href="'+escapeHtml(sourceUrl)+'" target="_blank" rel="noopener noreferrer">Báo cáo gốc</a>':'—')+'</td></tr>';
        }).join('');
        if (stateBox) stateBox.classList.add('hidden');
        if (tableWrap) tableWrap.classList.remove('hidden');
        if (status) status.textContent='Nguồn: '+(snapshot?.sourceName||'snapshot offline/repository')+' · '+rows.length+'/4 quý có dữ liệu · Đồng bộ: '+(snapshot?.fetchedAt?dateFmt(snapshot.fetchedAt):'chưa ghi nhận')+' · Đơn vị: '+(rows.find(item=>item.unit)?.unit||'theo snapshot')+'.';
      }
      drawSelectedCharts(ticker);
    }

    function populateComparePeriods() {
      const select=$('#stockComparePeriod');
      if(!select)return;
      const periods=allPeriods();
      const previous=select.value;
      select.innerHTML=periods.slice().reverse().map(period=>'<option value="'+escapeHtml(period)+'">'+escapeHtml(periodLabel(period))+'</option>').join('');
      if(periods.includes(previous))select.value=previous;
      else if(periods.length)select.value=periods[periods.length-1];
    }

    async function loadAll() {
      if(isLoading)return;
      isLoading=true;
      if(loadButton){loadButton.disabled=true;loadButton.textContent='Đang tải…';}
      if(status)status.textContent='Đang đọc snapshot offline và kiểm tra bản repository…';
      const results=await Promise.all(symbols.map(async ticker=>{
        try{
          const response=await fetchDataFile('financials-'+ticker+'.json');
          if(!response.ok)throw new Error('HTTP '+response.status);
          const snapshot=await response.json();
          if(!snapshot||snapshot.symbol!==ticker||!Array.isArray(snapshot.items))throw new Error('Snapshot không đúng schema');
          const items=snapshot.items.filter(item=>item&&validPeriod(item.period)&&item.source_url&&/^https?:\/\///i.test(item.source_url));
          snapshots.set(ticker,{...snapshot,items});
          return {ticker,ok:true,count:items.length};
        }catch(error){
          snapshots.set(ticker,{symbol:ticker,items:[],sourceName:'Không tải được snapshot',fetchedAt:null});
          console.warn('[financial-dashboard]',ticker,error);
          return {ticker,ok:false,count:0};
        }
      }));
      populateComparePeriods();
      renderSelected();
      drawComparison();
      const total=results.reduce((sum,item)=>sum+item.count,0);
      if(status)status.textContent='Đã kiểm tra '+results.length+' mã · '+total+' kỳ có URL nguồn hợp lệ trong snapshot. Đây là số bản ghi có schema hợp lệ, không thay thế việc đối chiếu số liệu với báo cáo gốc.';
      isLoading=false;
      if(loadButton){loadButton.disabled=false;loadButton.textContent='Tải báo cáo';}
    }

    loadButton?.addEventListener('click',loadAll);
    symbolSelect?.addEventListener('change',renderSelected);
    yearSelect?.addEventListener('change',renderSelected);
    $('#stockCompareMetric')?.addEventListener('change',drawComparison);
    $('#stockComparePeriod')?.addEventListener('change',drawComparison);
    loadAll();
  }

  function setupEmptyEconomicChart() {
    const select = $('#economicSeriesSelect');
    const empty = $('#economicChartEmpty');
    const source = $('#economicChartSource');
    const chart = $('#economicChart');
    const choices = {
      cpi: { category: 'cpi', label: 'CPI' },
      retail: { category: 'retail', label: 'Bán lẻ' },
      exchange_rate: { category: null, label: 'Tỷ giá' },
      interest_rate: { category: null, label: 'Lãi suất' },
      gdp_quarterly: { category: null, label: 'GDP theo quý' }
    };
    async function drawSelected() {
      const choice = choices[select?.value] || choices.gdp_quarterly;
      try {
        const response = await fetchDataFile('category-data.json');
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const snapshot = await response.json();
        const item = snapshot.data?.find(row => row.category === choice.category);
        const points = (item?.observations || []).filter(p => p.date <= new Date().toISOString().slice(0,10) && Number.isFinite(Number(p.value)));
        if (!item || !points.length || !chart || !window.Chart) {
          if (empty) { empty.style.display = 'grid'; empty.textContent = 'Chưa có chuỗi dữ liệu đã xác minh cho ' + choice.label + '.'; }
          if (source) source.textContent = 'Nguồn: dulieukinhte.com API · Chỉ hiển thị dữ liệu đã đồng bộ.';
          return;
        }
        if (empty) empty.style.display = 'none';
        if (window.economicChartInstance) window.economicChartInstance.destroy();
        window.economicChartInstance = new Chart(chart, {
          type: 'line',
          data: { labels: points.map(p => dateFmt(p.date)), datasets: [{ label: item.name, data: points.map(p => Number(p.value)), borderWidth: 2, tension: 0.15, pointRadius: points.length > 48 ? 0 : 2 }] },
          options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { display: false } }, scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { beginAtZero: false } } }
        });
        if (source) source.textContent = 'Nguồn: ' + item.source + ' · Đơn vị: ' + item.unit + ' · Kỳ mới nhất: ' + dateFmt(points[points.length - 1].date);
      } catch (error) {
        if (empty) { empty.style.display = 'grid'; empty.textContent = 'Không tải được snapshot kinh tế.'; }
        if (source) source.textContent = 'Không tải được data/category-data.json';
      }
    }
    select?.addEventListener('change', drawSelected);
    drawSelected();
  }

  async function loadOverviewKpis() {
    const container = $('#overviewKpis');
    if (!container) return;
    const definitions = [
      { category: 'gdp', title: 'GDP (giá hiện hành)', note: 'Tổng sản phẩm trong nước theo giá hiện hành.', target: '#vi-mo' },
      { category: 'cpi', title: 'Lạm phát (CPI)', note: 'Chỉ số CPI theo chuỗi nguồn; không đồng nhất với lạm phát so cùng kỳ.', target: '#vi-mo' },
      { category: 'retail', title: 'Bán lẻ HH & DV', note: 'Tổng mức bán lẻ hàng hóa và doanh thu dịch vụ tiêu dùng.', target: '#vi-mo' }
    ];
    try {
      const response = await fetchDataFile('category-data.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      container.innerHTML = definitions.map(def => {
        const item = (snapshot.data || []).find(row => row.category === def.category && Array.isArray(row.observations));
        const points = (item?.observations || []).filter(p => p && /^\d{4}-\d{2}-\d{2}$/.test(p.date) && p.date <= new Date().toISOString().slice(0, 10) && Number.isFinite(Number(p.value))).sort((a,b) => a.date.localeCompare(b.date));
        if (!item || !points.length) {
          return '<a class="overview-kpi ' + (def.category === 'gdp' ? 'kpi-gdp' : '') + '" href="' + def.target + '"><span>' + escapeHtml(def.title) + '</span><strong>Chưa có dữ liệu</strong><small>' + escapeHtml(def.note) + '</small><div class="kpi-spark empty-spark">Chưa có chuỗi dữ liệu đã xác minh</div></a>';
        }
        const latest = points[points.length - 1];
        const values = points.slice(-12).map(p => Number(p.value));
        const min = Math.min(...values), max = Math.max(...values), spread = max - min || 1;
        const coords = values.map((v,i) => (i/(Math.max(values.length-1,1))*100).toFixed(2)+','+(25-((v-min)/spread*21)).toFixed(2)).join(' ');
        const spark = '<svg viewBox="0 0 100 28" preserveAspectRatio="none" aria-label="Xu hướng 12 quan sát gần nhất"><polyline points="' + coords + '" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>';
        return '<a class="overview-kpi ' + (def.category === 'gdp' ? 'kpi-gdp' : '') + '" href="' + def.target + '"><span>' + escapeHtml(def.title) + '</span><strong>' + fmt(latest.value, 2) + ' ' + escapeHtml(item.unit || '') + '</strong><small>Kỳ gần nhất: ' + dateFmt(latest.date) + ' · ' + escapeHtml(item.source || 'Nguồn dữ liệu') + '</small><div class="kpi-spark">' + spark + '<span>' + points.length + ' kỳ dữ liệu</span></div></a>';
      }).join('');
    } catch (error) {
      console.error('[overview-kpis]', error);
      container.querySelectorAll('.overview-kpi small').forEach(el => { el.textContent = 'Chưa tải được snapshot dữ liệu'; });
    }
  }

  function setupSearchShortcut() {
    document.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        $('#siteSearch')?.focus();
      }
      if (event.key === 'Escape') {
        $('#siteSidebar')?.classList.remove('sidebar-open');
        if (document.activeElement === $('#siteSearch')) $('#siteSearch').blur();
      }
    });
  }


  async function loadAdditionalMoneySeries() {
    const definitions = [
      { category: 'lending-rate', panel: '#lai-suat-cho-vay', title: 'Lãi suất cho vay bình quân', unit: '%/năm', staleDays: 100 },
      { category: 'black-market-usd-buy', panel: '#ty-gia-cho-den', title: 'Tỷ giá USD chợ đen mua vào', unit: 'VND/USD', staleDays: 5 },
      { category: 'remittance-hcm', panel: '#kieu-hoi', title: 'Tổng kiều hối về TP. Hồ Chí Minh', unit: 'Triệu USD', staleDays: 150 }
    ];
    for (const def of definitions) {
      const panel = $(def.panel);
      if (!panel) continue;
      try {
        const response = await fetchDataFile('category-data.json');
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const snapshot = await response.json();
        const item = (snapshot.data || []).find(row => row.category === def.category);
        const points = (item?.observations || []).filter(p => p && /^\d{4}-\d{2}-\d{2}$/.test(p.date) && p.date <= new Date().toISOString().slice(0,10) && Number.isFinite(Number(p.value))).sort((x,y)=>x.date.localeCompare(y.date));
        const heading = panel.querySelector('.currency-panel-heading');
        let status = heading?.querySelector('.status-pill');
        if (!status && heading) { status = document.createElement('span'); status.className = 'status-pill neutral'; heading.appendChild(status); }
        if (!item || !points.length) {
          if (status) status.textContent = 'Chưa có dữ liệu';
          const old = panel.querySelector('.empty-state');
          if (old) old.innerHTML = '<h3>Chưa có dữ liệu đồng bộ</h3><p>Workflow cần chạy thành công và nguồn phải trả về quan sát hợp lệ. Không tự tạo số liệu.</p>';
          continue;
        }
        const latest = points[points.length - 1];
        const tableId = 'extra-' + def.category + '-table';
        const chartId = 'extra-' + def.category + '-chart';
        const old = panel.querySelector('.empty-state');
        if (old) old.remove();
        let area = panel.querySelector('.extra-money-series');
        if (!area) { area = document.createElement('div'); area.className = 'extra-money-series'; panel.appendChild(area); }
        area.innerHTML = '<div class="data-view-toolbar"><div class="view-switch" role="group" aria-label="Cách hiển thị dữ liệu"><button type="button" data-view="chart" class="is-active">Biểu đồ</button><button type="button" data-view="table">Bảng số liệu</button></div><label class="chart-type-label">Kiểu biểu đồ <select class="extra-chart-type"><option value="line">Đường</option><option value="bar">Cột</option></select></label></div><div class="chart-canvas-wrap"><canvas id="' + chartId + '" role="img" aria-label="' + escapeHtml(def.title) + '"></canvas></div><p class="muted extra-chart-note"></p><div id="' + tableId + '" class="table-scroll" hidden><table><thead><tr><th>Ngày/kỳ</th><th>Chỉ tiêu</th><th>Giá trị</th><th>Đơn vị</th><th>Nguồn</th></tr></thead><tbody>' + points.slice().reverse().map(p=>'<tr><td>'+escapeHtml(dateFmt(p.date))+'</td><td>'+escapeHtml(item.name)+'</td><td>'+fmt(p.value,3)+'</td><td>'+escapeHtml(item.unit||def.unit)+'</td><td><a href="'+escapeHtml(item.url)+'" target="_blank" rel="noopener noreferrer">'+escapeHtml(item.source||'Dữ Liệu Kinh Tế')+'</a></td></tr>').join('') + '</tbody></table></div>';
        if (status) { status.textContent = 'Kỳ mới nhất: ' + dateFmt(latest.date); status.className = 'status-pill ' + ((Date.now()-new Date(latest.date+'T00:00:00').getTime())/86400000 > def.staleDays ? 'warning' : 'positive'); }
        const canvas = area.querySelector('canvas'), note = area.querySelector('.extra-chart-note'), table = area.querySelector('#'+tableId), chartWrap = area.querySelector('.chart-canvas-wrap'), toolbar = area.querySelector('.data-view-toolbar');
        let chart = null;
        const draw = () => {
          if (chart) chart.destroy();
          if (!window.Chart) { note.textContent = 'Không tải được Chart.js; bảng số liệu vẫn dùng được.'; return; }
          chart = new Chart(canvas, { type: area.querySelector('.extra-chart-type').value, data: { labels: points.map(p=>dateFmt(p.date)), datasets: [{ label: item.name, data: points.map(p=>Number(p.value)), borderWidth:2, tension:.18, pointRadius: points.length>40?0:2 }] }, options: { responsive:true, maintainAspectRatio:false, interaction:{mode:'index',intersect:false}, plugins:{legend:{display:true,position:'bottom'}}, scales:{x:{ticks:{maxTicksLimit:8,maxRotation:0},grid:{display:false}},y:{beginAtZero:false}} } });
          note.textContent = 'Nguồn: ' + (item.source || 'Dữ Liệu Kinh Tế') + ' · ' + points.length + ' kỳ dữ liệu · đơn vị ' + (item.unit || def.unit) + '. Khoảng trống không được nội suy.';
        };
        toolbar.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{
          toolbar.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('is-active',b===button));
          const showChart=button.dataset.view==='chart'; chartWrap.hidden=!showChart; table.hidden=showChart;
        }));
        area.querySelector('.extra-chart-type').addEventListener('change',draw);
        draw();
      } catch (error) {
        console.error('[money-series '+def.category+']',error);
      }
    }
  }


  async function loadBondMarketSeries() {
    const section = $('#trai-phieu');
    if (!section) return;
    const defs = [
      { category:'bond-yield-1y', label:'TPCP 1 năm', unit:'%/năm' },
      { category:'bond-yield-2y', label:'TPCP 2 năm', unit:'%/năm' },
      { category:'bond-yield-10y', label:'TPCP 10 năm', unit:'%/năm' },
      { category:'bond-yield-20y', label:'TPCP 20 năm', unit:'%/năm' },
      { category:'corporate-bonds-total', label:'Tổng phát hành TPDN', unit:'Tỷ đồng' }
    ];
    try {
      const response = await fetchDataFile('category-data.json');
      if (!response.ok) throw new Error('HTTP '+response.status);
      const snapshot = await response.json();
      let host = $('#bondSeriesCharts');
      if (!host) {
        host = document.createElement('div');
        host.id = 'bondSeriesCharts';
        host.className = 'data-card-grid';
        const cards = section.querySelector('.data-card-grid');
        if (cards) cards.insertAdjacentElement('afterend', host);
        else section.appendChild(host);
      }
      host.innerHTML = defs.map((d,i)=>'<article class="currency-panel"><div class="currency-panel-heading"><div><h3>'+escapeHtml(d.label)+'</h3><p class="muted">'+escapeHtml(d.unit)+' · dữ liệu lịch sử theo nguồn</p></div><span class="status-pill neutral" id="bond-extra-status-'+i+'">Đang tải</span></div><div class="data-view-toolbar"><div class="view-switch" role="group"><button type="button" data-view="chart" class="is-active">Biểu đồ</button><button type="button" data-view="table">Bảng số liệu</button></div><label class="chart-type-label">Kiểu biểu đồ <select><option value="line">Đường</option><option value="bar">Cột</option></select></label></div><div class="chart-canvas-wrap"><canvas id="bond-extra-canvas-'+i+'"></canvas></div><div class="table-scroll" hidden id="bond-extra-table-'+i+'"></div><p class="muted" id="bond-extra-note-'+i+'"></p></article>').join('');
      defs.forEach((def,i)=>{
        const item=(snapshot.data||[]).find(x=>x.category===def.category);
        const points=(item?.observations||[]).filter(p=>p?.date&&Number.isFinite(Number(p.value))).sort((a,b)=>a.date.localeCompare(b.date));
        const status=$('#bond-extra-status-'+i), canvas=$('#bond-extra-canvas-'+i), table=$('#bond-extra-table-'+i), note=$('#bond-extra-note-'+i), card=canvas.closest('.currency-panel');
        if (!points.length) { status.textContent='Chưa có dữ liệu'; note.textContent='Chưa có quan sát hợp lệ trong snapshot. Không tạo số liệu giả.'; canvas.parentElement.hidden=true; return; }
        status.textContent='Kỳ mới nhất: '+dateFmt(points[points.length-1].date); status.className='status-pill positive';
        table.innerHTML='<table><thead><tr><th>Ngày/kỳ</th><th>Giá trị</th><th>Đơn vị</th><th>Nguồn</th></tr></thead><tbody>'+points.slice().reverse().map(p=>'<tr><td>'+escapeHtml(dateFmt(p.date))+'</td><td>'+fmt(p.value,4)+'</td><td>'+escapeHtml(item.unit||def.unit)+'</td><td><a href="'+escapeHtml(item.url||'#')+'" target="_blank" rel="noopener noreferrer">'+escapeHtml(item.source||'Nguồn dữ liệu')+'</a></td></tr>').join('')+'</tbody></table>';
        let chart=null;
        const draw=()=>{if(chart)chart.destroy();if(!window.Chart){note.textContent='Không tải được Chart.js.';return;}chart=new Chart(canvas,{type:card.querySelector('select').value,data:{labels:points.map(p=>dateFmt(p.date)),datasets:[{label:item.name||def.label,data:points.map(p=>Number(p.value)),borderWidth:2,tension:.2,pointRadius:points.length>40?0:2}]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,position:'bottom'}},scales:{x:{ticks:{maxTicksLimit:8,maxRotation:0},grid:{display:false}},y:{beginAtZero:false}}}});note.textContent='Nguồn: '+(item.source||'')+' · '+points.length+' quan sát · Không nội suy khoảng trống.';};
        card.querySelector('select').addEventListener('change',draw);
        card.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',()=>{card.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('is-active',b===btn));const show=btn.dataset.view==='chart';canvas.parentElement.hidden=!show;table.hidden=show;}));
        draw();
      });
    } catch(error) { console.error('[bond-series]',error); }
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    loadOverviewKpis();
    setupCommodityFilters();
    setupFinancials();
    setupReportQueue();
    setupEmptyEconomicChart();
    setupSearchShortcut();
    loadMarketSnapshot();
    loadCurrencyRates();
    loadUsdVndReference();
    loadCreditGrowth();
    loadCreditGrowthHistoryChart();
    loadBalanceOfPayments();
    loadOmoData();
  loadPolicyRates();
    loadFinancialRates();
    loadBondMarketSeries();
    loadCategoryData();
    loadDLKTEconomicPanels();
  });
})();