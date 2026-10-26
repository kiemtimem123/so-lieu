(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const state = { commodities: [], selectedId: null, chart: null, stockChart: null };

  const GROUPS = {
    29387: 'metals',
    29388: 'metals',
    29380: 'metals',
    33414: 'metals',
    29406: 'agriculture',
    66457: 'agriculture',
    33392: 'agriculture',
    33408: 'agriculture',
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

  async function loadTrendingCommodities() {
    const root = $('#trendingCommodityCards');
    const status = $('#trendingCommodityStatus');
    if (!root) return;
    try {
      const response = await fetchDataFile('trending-commodities.json');
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data) || !snapshot.data.length) throw new Error('Snapshot chưa có mặt hàng hợp lệ');
      root.innerHTML = snapshot.data.slice(0, 10).map(item => {
        const change = Number(item.changePct);
        const trend = change > 0 ? 'up' : change < 0 ? 'down' : 'flat';
        const pct = Number.isFinite(change) ? (change > 0 ? '+' : '') + fmt(change, 2) + '%' : '—';
        return '<a class="trending-commodity-card ' + trend + '" href="' + escapeHtml(item.url || 'https://www.thitruonghanghoa.com/') + '" target="_blank" rel="noopener noreferrer">' +
          '<span class="trending-card-top"><small>' + escapeHtml(item.category || 'HÀNG HÓA') + '</small><span class="trending-trend-icon">' + (trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→') + '</span></span>' +
          '<strong class="trending-card-name">' + escapeHtml(item.name) + '</strong><span class="trending-card-en">' + escapeHtml(item.label || '') + '</span>' +
          '<span class="trending-card-bottom"><b class="trending-change">' + escapeHtml(pct) + '</b><b class="trending-price">' + escapeHtml(fmt(item.price, 3)) + (item.unit ? ' <small>' + escapeHtml(item.unit) + '</small>' : '') + '</b></span></a>';
      }).join('');
      if (status) status.innerHTML = 'Nguồn duy nhất: <a href="https://www.thitruonghanghoa.com/" target="_blank" rel="noopener noreferrer">Thị Trường Hàng Hóa</a> · cập nhật snapshot ' + escapeHtml(dateFmt(snapshot.fetchedAt || '')) + '.';
    } catch (error) {
      root.innerHTML = '<div class="empty-state"><h3>Chưa tải được biến động giá</h3><p>Chưa có snapshot hợp lệ từ Thị Trường Hàng Hóa. Không thay thế bằng nguồn khác.</p><a href="https://www.thitruonghanghoa.com/" target="_blank" rel="noopener noreferrer">Mở trang nguồn ↗</a></div>';
      console.error('[trending-commodities]', error);
    }
  }

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
    if (source) source.innerHTML = item.sourceUrl ? 'Nguồn: <a href="' + escapeHtml(item.sourceUrl) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(item.source || 'Dữ Liệu Kinh Tế') + '</a>' : 'Nguồn: ' + escapeHtml(item.source || 'Dữ Liệu Kinh Tế API') + ' · giá trị gần nhất được đồng bộ';
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
      if (source) source.innerHTML = (item.sourceUrl ? 'Nguồn: <a href="' + escapeHtml(item.sourceUrl) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(item.source || 'Dữ Liệu Kinh Tế') + '</a>' : 'Nguồn: ' + escapeHtml(item.source || 'Dữ Liệu Kinh Tế API')) + ' · ' + history.length + ' quan sát';
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
    const loadSummary = $('#stockSyncSummary');
    const symbols = ['MBB','ACB','FPT','SHB','TCX','HCM','VND','SHS','NLG','BSR','TCB','VHM','TPB','VPB','STB','VCB','CTG','BID','VCI','VCK','VIX','SSI','VDS','KDH','NVL','HHV','DPG','GAS','PLX','IDC','KBC','GEG'];
    const industryBySymbol = { MBB:'banking', ACB:'banking', SHB:'banking', TCB:'banking', TPB:'banking', VPB:'banking', STB:'banking', VCB:'banking', CTG:'banking', BID:'banking', FPT:'technology', HCM:'securities', VND:'securities', SHS:'securities', TCX:'securities', VCI:'securities', VCK:'securities', VIX:'securities', SSI:'securities', VDS:'securities', NLG:'real_estate', VHM:'real_estate', KDH:'real_estate', NVL:'real_estate', IDC:'real_estate', KBC:'real_estate', BSR:'oil_gas', GAS:'oil_gas', PLX:'oil_gas', GEG:'energy', HHV:'construction', DPG:'construction' };
    const industryLabels = { banking:'Ngân hàng', securities:'Chứng khoán', real_estate:'Bất động sản & khu công nghiệp', technology:'Công nghệ', oil_gas:'Dầu khí', energy:'Năng lượng', construction:'Xây dựng & hạ tầng' };
    const industryFor = ticker => industryBySymbol[ticker] || 'other';
    const revenueLabelFor = ticker => {
      const industry = industryFor(String(ticker || '').toUpperCase());
      return industry === 'banking' ? 'Tổng thu nhập hoạt động'
        : industry === 'securities' ? 'Doanh thu hoạt động'
        : 'Doanh thu thuần';
    };
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
      pb: { label: 'P/B', unit: 'lần' },
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
    // Scope-blocked/unconfirmed reports may retain source OCR values for audit, but
    // never let those values enter public charts, comparisons, overview KPIs, or tables.
    const scopeUnverifiedMetricField = /^(?:revenue|cost_of_goods_sold|gross_profit|financial_income|financial_expense|interest_expense|selling_expense|admin_expense|operating_profit|income_tax(?:_current|_deferred)?|pretax_profit|net_profit(?:_attributable)?|total_assets|total_liabilities|equity|roa|roe|pb|pe|eps|price|market_cap|enterprise_value|ev_ebitda|current_assets|non_current_assets|short_term_.*|current_liabilities|long_term_liabilities|fixed_assets|inventory|cash(?:_.*)?|retained_earnings|capital_expenditure(?:_ytd)?|dividends_paid(?:_ytd)?|operating_cash_flow(?:_ytd)?|investing_cash_flow(?:_ytd)?|financing_cash_flow(?:_ytd)?|bank_.*|broker_.*)$/i;
    const hasUnverifiedReportScope = item =>
      item?.source_validation?.scope_validation_required === true ||
      item?.source_validation?.manual_review_blocking_automatic_extraction === true;
    const rowsFor = ticker => {
      const snapshot = snapshots.get(ticker);
      return (snapshot?.items || []).filter(item => item && validPeriod(item.period)).map(item => {
        const rawVerification = String(item?.verification_status || '').toLowerCase();
        const rawCoreStatus = String(item?.core_financial_extraction_status || '').toLowerCase();
        const blockForManualExtraction = rawVerification === 'manual_review_required_pending_extraction' ||
          rawCoreStatus === 'manual_review_required_pending_extraction';
        if (!hasUnverifiedReportScope(item) && !blockForManualExtraction) return item;

        const safe = { ...item };
        Object.keys(safe).forEach(key => {
          if (scopeUnverifiedMetricField.test(key) && validNumber(safe[key])) safe[key] = null;
        });
        if (hasUnverifiedReportScope(item)) {
          safe.report_type = 'BCTC quý ' + ticker + ' ' + safe.period + ' (phạm vi hợp nhất chưa xác nhận; số liệu tạm ẩn)';
          safe.verification_status_note = String(item?.source_validation?.manual_review_reason || 'Phạm vi báo cáo chưa được VietstockFinance xác nhận là hợp nhất.') + ' Các số liệu chưa xác minh không hiển thị.';
        } else {
          safe.report_type = String(item.report_type || ('BCTC quý ' + ticker + ' ' + safe.period)) + ' (chờ trích xuất/xác minh; số liệu tạm ẩn)';
          safe.verification_status_note = String(item?.verification_status_note || 'Kỳ này được đánh dấu cần rà soát thủ công; số liệu chưa xác minh được ẩn khỏi biểu đồ và thống kê.');
        }
        safe.verification_status = 'manual_review_required_pending_extraction';
        safe.core_financial_extraction_status = 'manual_review_required_pending_extraction';
        safe.financial_line_items_status = 'manual_review_required';
        return safe;
      }).slice().sort((a,b)=>a.period.localeCompare(b.period));
    };
    const hasNumericFinancialData = item => ['revenue','pretax_profit','net_profit','total_assets','total_liabilities','equity','roa','roe','pb'].some(field => validNumber(item?.[field]));
    const hasCoreFinancialData = item => ['pretax_profit','net_profit','total_assets','total_liabilities','equity','roa','roe','pb'].some(field => validNumber(item?.[field]));
    const verificationBadge = item => {
      const detailStatus = String(item?.financial_line_items_status || '').toLowerCase();
      if (detailStatus.includes('pending_visual_review')) return { label: 'Chờ rà soát chỉ tiêu chi tiết', kind: 'review' };
      const raw = String(item?.verification_status || '').toLowerCase();
      if (raw === 'auto_pending_extraction') return { label: 'Chờ trích xuất', kind: 'pending' };
      if (raw === 'manual_review_required_pending_extraction') return { label: 'Cần rà soát PDF thủ công', kind: 'review' };
      if (raw.includes('pending_visual_review') || raw === 'auto_extracted_pending_visual_review') return { label: 'Chờ rà soát PDF', kind: 'review' };
      if (raw.includes('manual_visual')) return { label: 'Đã kiểm tra PDF', kind: 'ready' };
      if (raw.includes('derived')) return { label: 'Đối chiếu từ lũy kế', kind: 'review' };
      if (raw.includes('ocr')) return { label: 'Đã đối chiếu OCR', kind: 'review' };
      if (raw.includes('verified') || raw.includes('reconciled')) return { label: 'Đã đối chiếu nguồn', kind: 'ready' };
      return hasNumericFinancialData(item)
        ? { label: 'Có số liệu · cần rà soát', kind: 'review' }
        : { label: 'Chờ dữ liệu', kind: 'pending' };
    };
    const allPeriods = () => [...new Set(symbols.flatMap(ticker => rowsFor(ticker).filter(hasNumericFinancialData).map(item => item.period)))].sort();

    function populateYearOptions() {
      if (!yearSelect) return;
      const knownYears = symbols.flatMap(ticker => rowsFor(ticker).map(item => Number(item.period.slice(0, 4)))).filter(Number.isFinite);
      const currentYear = new Date().getFullYear();
      const priorYear = Number(yearSelect.value) || currentYear;
      const maxYear = Math.max(2022, currentYear, ...knownYears);
      const years = [];
      for (let year = 2022; year <= maxYear; year++) years.push(year);
      yearSelect.innerHTML = years.map(year => '<option value="' + year + '">' + year + '</option>').join('');
      const newestYear = knownYears.length ? Math.max(...knownYears) : currentYear;
      yearSelect.value = String(newestYear > priorYear ? newestYear : (years.includes(priorYear) ? priorYear : maxYear));
    }

    // Enriched snapshots can be processed after their original download time. Use
    // processing/reconciliation timestamps first so a newer extraction is not hidden
    // by an older or stale Hostinger copy with a later fetchedAt value.
    function snapshotProcessingTimestamp(snapshot) {
      const timestamps = [];
      const add = value => {
        if (!value) return;
        const parsed = Date.parse(String(value));
        if (Number.isFinite(parsed)) timestamps.push(parsed);
      };
      add(snapshot?.processedAt);
      add(snapshot?.dataUpdatedAt);
      for (const item of Array.isArray(snapshot?.items) ? snapshot.items : []) {
        if (!item || typeof item !== 'object') continue;
        add(item.financial_line_items_schema_updated_at);
        add(item.financial_line_items_updated_at);
        add(item.core_financial_extraction_updated_at);
        add(item.source_validation?.reviewed_at);
        add(item.visual_review?.checked_at);
      }
      return timestamps.length ? Math.max(...timestamps) : 0;
    }

    async function fetchLatestFinancialSnapshot(ticker) {
      const filename = 'financials-' + ticker + '.json';
      const cacheBust = Date.now();
      const candidates = [
        { label: 'website', url: 'data/' + filename + '?v=' + cacheBust, priority: 0 },
        { label: 'GitHub', url: DATA_FALLBACK_BASE + encodeURIComponent(filename) + '?v=' + cacheBust, priority: 1 }
      ];
      const settled = await Promise.allSettled(candidates.map(async candidate => {
        const controller = new AbortController();
        const timeoutMs = candidate.label === 'website' ? 3500 : 8000;
        const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
        let response;
        try {
          response = await fetch(candidate.url, {
            cache: 'no-store',
            headers: { 'Cache-Control': 'no-cache' },
            signal: controller.signal
          });
        } finally {
          window.clearTimeout(timeoutId);
        }
        if (!response.ok) throw new Error('HTTP ' + response.status + ' (' + candidate.label + ')');
        const contentType = (response.headers.get('content-type') || '').toLowerCase();
        if (contentType.includes('text/html')) throw new Error('HTML thay vì JSON (' + candidate.label + ')');
        const snapshot = await response.json();
        if (!snapshot || snapshot.symbol !== ticker || !Array.isArray(snapshot.items)) throw new Error('Snapshot không đúng schema (' + candidate.label + ')');
        return { ...candidate, snapshot };
      }));
      const usable = settled.filter(result => result.status === 'fulfilled').map(result => result.value);
      if (!usable.length) {
        const reasons = settled.map(result => result.status === 'rejected' ? result.reason?.message : '').filter(Boolean).join('; ');
        throw new Error(reasons || 'Không tải được snapshot từ website hoặc GitHub');
      }
      usable.sort((a, b) => {
        const processedA = snapshotProcessingTimestamp(a.snapshot);
        const processedB = snapshotProcessingTimestamp(b.snapshot);
        if (processedA !== processedB && (processedA || processedB)) return processedB - processedA;
        const timeA = Date.parse(a.snapshot.fetchedAt || '') || 0;
        const timeB = Date.parse(b.snapshot.fetchedAt || '') || 0;
        if (timeA !== timeB) return timeB - timeA;
        if (a.snapshot.items.length !== b.snapshot.items.length) return b.snapshot.items.length - a.snapshot.items.length;
        return a.priority - b.priority;
      });
      return { ...usable[0].snapshot, _loadedFrom: usable[0].label };
    }

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
        {field:'revenue',label:revenueLabelFor(ticker)},
        {field:'pretax_profit',label:'Lợi nhuận trước thuế'},
        {field:'net_profit',label:'Lợi nhuận sau thuế'}
      ].map(item=>({ ...item, values:rows.map(row=>statementNumericValue(row[item.field],row)) }));
      const financialAvailable = financial.filter(series=>series.values.some(value=>value!==null));
      drawChart('profit','stockProfitChart','stockProfitNote',{
        labels, points:financialAvailable.flatMap(s=>s.values.filter(v=>v!==null)),
        datasets:financialAvailable.map(s=>({label:s.label,data:s.values,borderWidth:2,tension:.18,pointRadius:rows.length>32?0:3,spanGaps:false})),
        note:financialAvailable.length ? 'Đơn vị: ' + ((unitSelect?.value || 'billion') === 'billion' ? 'tỷ đồng' : 'triệu đồng') + '. Nguồn: snapshot báo cáo tài chính; kỳ chưa trích xuất hoặc chưa xác minh được để trống, không nội suy.' : '',
        emptyMessage:'Chưa có trường doanh thu hoặc lợi nhuận hợp lệ trong snapshot. Hãy trích xuất từ báo cáo gốc; website không tự ước tính.'
      });
      const balance = [
        {field:'total_assets',label:'Tổng tài sản'},
        {field:'total_liabilities',label:'Nợ phải trả'},
        {field:'equity',label:'Vốn chủ sở hữu'}
      ].map(item=>({ ...item, values:rows.map(row=>statementNumericValue(row[item.field],row)) }));
      const balanceAvailable=balance.filter(series=>series.values.some(value=>value!==null));
      drawChart('balance','stockBalanceChart','stockBalanceNote',{
        labels,points:balanceAvailable.flatMap(s=>s.values.filter(v=>v!==null)),
        datasets:balanceAvailable.map(s=>({label:s.label,data:s.values,borderWidth:2,tension:.18,pointRadius:rows.length>32?0:3,spanGaps:false})),
        note:balanceAvailable.length?'Đơn vị: ' + ((unitSelect?.value || 'billion') === 'billion' ? 'tỷ đồng' : 'triệu đồng') + '. Kiểm tra trạng thái kỳ báo cáo và cơ sở hợp nhất/riêng lẻ trong bảng trước khi so sánh.':'',
        emptyMessage:'Chưa có số liệu tài sản, nợ hoặc vốn chủ sở hữu hợp lệ.'
      });
      const ratios=[
        {field:'roa',label:'ROA (%)'},
        {field:'roe',label:'ROE (%)'}
      ].map(item=>({ ...item, values:rows.map(row=>statementNumericValue(row[item.field],row,true)) }));
      const ratiosAvailable=ratios.filter(series=>series.values.some(value=>value!==null));
      drawChart('ratios','stockRatiosChart','stockRatiosNote',{
        labels,points:ratiosAvailable.flatMap(s=>s.values.filter(v=>v!==null)),
        datasets:ratiosAvailable.map(s=>({label:s.label,data:s.values,borderWidth:2,tension:.18,pointRadius:rows.length>32?0:3,spanGaps:false})),
        note:ratiosAvailable.length?'ROA/ROE lấy từ snapshot có nguồn. Các kỳ cần rà soát vẫn được đánh dấu ở bảng; không tự tính khi thiếu đầu vào.':'',
        emptyMessage:'Chưa có ROA/ROE được xác minh. Không tính tỷ số nếu thiếu dữ liệu đầu vào hoặc công thức nguồn.'
      });
    }

    function drawComparison() {
      const metric = $('#stockCompareMetric')?.value || 'net_profit';
      const period = $('#stockComparePeriod')?.value || '';
      const baseMeta = fieldMeta[metric] || fieldMeta.net_profit;
      const meta = metric === 'revenue'
        ? { ...baseMeta, label: revenueLabelFor(String(symbolSelect?.value || 'MBB').toUpperCase()) }
        : baseMeta;
      const compareIndustry = $('#stockCompareIndustry')?.value || 'all';
      const selectedIndustry = industryFor(String(symbolSelect?.value || 'MBB').toUpperCase());
      const compareSymbols = symbols.filter(ticker => compareIndustry === 'all' || industryFor(ticker) === selectedIndustry);
      const values = compareSymbols.map(ticker => {
        const row = rowsFor(ticker).find(item=>item.period===period);
        const isRatio = ['roa','roe','pb'].includes(metric);
        return {ticker, value:row ? statementNumericValue(row[metric],row,isRatio) : null, row};
      }).filter(item=>item.value!==null);
      drawChart('compare','stockCompareChart','stockCompareNote',{
        type:'bar', labels:values.map(item=>item.ticker), points:values.map(item=>item.value),
        datasets:values.length?[{label:meta.label+((meta.unit==='%'?' (%)':meta.unit==='lần'?' (lần)':'')),data:values.map(item=>item.value),borderWidth:1}]:[],
        beginAtZero:true,
        note:values.length?'Kỳ '+periodLabel(period)+' · '+meta.label+'. Giá trị tiền tệ đã quy đổi sang cùng đơn vị hiển thị; doanh thu có thể khác định nghĩa tùy ngành.':'',
        emptyMessage:'Chưa có dữ liệu đã xác minh cho chỉ tiêu và kỳ so sánh đã chọn.'
      });
      const table = $('#stockCompareTable');
      if (table) {
        table.innerHTML = values.length
          ? '<table><thead><tr><th>Mã</th><th>Kỳ</th><th>'+escapeHtml(meta.label)+'</th><th>Đơn vị</th></tr></thead><tbody>'+values.map(item=>'<tr><td><strong>'+item.ticker+'</strong></td><td>'+escapeHtml(periodLabel(period))+'</td><td>'+numberOrDash(item.value)+'</td><td>'+escapeHtml(['roa','roe'].includes(metric)?'%' : ['pb','pe','ev_ebitda'].includes(metric)?'lần':(unitSelect?.value || 'billion')==='billion'?'tỷ đồng':'triệu đồng')+'</td></tr>').join('')+'</tbody></table>'
          : '<div class="empty-state"><h3>Chưa có dữ liệu để so sánh</h3><p>Chỉ những giá trị có nguồn kiểm chứng mới được hiển thị.</p></div>';
      }
    }

    let activeStatement = 'balance';
    let periodOffset = 0;
    const statementPageSize = 9;
    const statementHead = $('#stockStatementHead');
    const statementHint = $('#stockStatementHint');
    const peerOptions = $('#stockPeerOptions');
    const unitSelect = $('#stockUnit');
    const basisSelect = $('#stockReportBasis');
    const tableCompareMetric = $('#stockTableCompareMetric');

    const rowsForBasis = ticker => {
      const basis = basisSelect?.value || 'consolidated';
      return rowsFor(ticker).filter(item => {
        // Keep scope-blocked source rows visible in consolidated mode for audit,
        // but their financial values are blanked by rowsFor until the scope is verified.
        if (hasUnverifiedReportScope(item)) return basis !== 'separate';
        const description = String(item.report_type || '').toLowerCase();
        if (basis === 'separate') return /riêng lẻ|riêng/.test(description) && !/hợp nhất/.test(description);
        return !/riêng lẻ|riêng/.test(description);
      });
    };
    const displayPeriod = value => String(value || '').replace(/^(\d{4})-Q([1-4])$/, (_, year, quarter) => 'Q' + quarter + '/' + year);
    const overviewNumber = (value, item, suffix = '') => {
      if (!validNumber(value)) return '—';
      const base = statementNumber(value, item, true);
      return base === '—' ? base : base + suffix;
    };
    const overviewMoney = (value, item) => {
      if (!validNumber(value)) return '—';
      const unit = (unitSelect?.value || 'billion') === 'billion' ? ' tỷ' : ' triệu';
      return statementNumber(value, item, false) + unit;
    };
    const firstNumber = (item, names) => {
      for (const name of names) if (validNumber(item?.[name])) return item[name];
      return null;
    };
    const firstValue = (item, names) => {
      for (const name of names) if (item?.[name] !== null && item?.[name] !== undefined && String(item[name]).trim() !== '') return item[name];
      return null;
    };
    const formatPct = value => validNumber(value)
      ? new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2, minimumFractionDigits: 1 }).format(Number(value)) + '%'
      : '—';
    const formatPlain = value => validNumber(value)
      ? new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(Number(value))
      : '—';
    const styleChange = (id, value) => {
      const element = document.getElementById(id);
      if (!element) return;
      const textValue = String(value ?? '').trim();
      element.classList.toggle('is-negative', textValue.startsWith('-'));
      element.classList.toggle('is-positive', textValue !== '—' && textValue !== '' && !textValue.startsWith('-') && !/^0([,.]0+)?%$/.test(textValue));
    };
    const percentageChange = (field, current, rows) => {
      if (!current || !validNumber(current[field])) return '—';
      const match = String(current.period || '').match(/^(\d{4})-Q([1-4])$/);
      if (!match) return '—';
      const previousPeriod = (Number(match[1]) - 1) + '-Q' + match[2];
      const previous = rows.find(row => row.period === previousPeriod);
      if (!previous || !validNumber(previous[field]) || Number(previous[field]) === 0) return '—';
      const change = (Number(current[field]) - Number(previous[field])) / Math.abs(Number(previous[field])) * 100;
      if (!Number.isFinite(change)) return '—';
      const formatted = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1, minimumFractionDigits: 1 }).format(change);
      return (change > 0 ? '+' : '') + formatted + '%';
    };
    function renderFinancialOverview(ticker) {
      const allRows = rowsForBasis(ticker);
      const latest = allRows.slice().reverse().find(hasCoreFinancialData);
      const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value == null || value === '' ? '—' : String(value);
      };
      const allSummaryIds = [
        'stockStatsSymbol','stockStatsMeta','stockStatsUnit','stockStatMarketPeriod','stockStatPeriod','stockStatRevenue','stockStatRevenueYoY',
        'stockStatPretax','stockStatPretaxYoY','stockStatNet','stockStatNetYoY','stockStatPrice','stockStatVolume15d','stockStatChange1d',
        'stockStatChange1w','stockStatChange1m','stockStatChange3m','stockStatChange1y','stockStatRange52w','stockStatMarketCap',
        'stockStatEnterpriseValue','stockStatEps','stockStatPe','stockStatPeg','stockStatPb','stockStatEvEbitda','stockStatPs','stockStatBasis',
        'stockStatAssets','stockStatCurrentAssets','stockStatCash','stockStatShortInvestments','stockStatInventory','stockStatCurrentLiabilities',
        'stockStatLiabilities','stockStatEquity','stockStatOperatingCash','stockStatInvestingCash','stockStatFinancingCash','stockStatCapex',
        'stockStatFcf','stockStatGrossMargin','stockStatNetMargin','stockStatDebtAssets','stockStatDebtEquity','stockStatEquityAssets',
        'stockStatRoa','stockStatRoe','stockStatCurrentRatio'
      ];
      setText('stockStatsSymbol', ticker);
      setText('stockStatsUnit', 'Đơn vị: ' + ((unitSelect?.value || 'billion') === 'billion' ? 'tỷ đồng' : 'triệu đồng'));
      if (!latest) {
        setText('stockStatsMeta', 'Chưa có kỳ báo cáo đủ dữ liệu cho mã và phạm vi đang chọn.');
        allSummaryIds.filter(id => id !== 'stockStatsSymbol' && id !== 'stockStatsMeta' && id !== 'stockStatsUnit').forEach(id => setText(id, '—'));
        setText('stockStatsSourceNote', 'Chưa có snapshot tài chính để hiển thị nguồn và trạng thái kiểm chứng.');
        const sourceLink = document.getElementById('stockStatsSource');
        if (sourceLink) sourceLink.hidden = true;
        const statusBadge = document.getElementById('stockStatStatus');
        if (statusBadge) { statusBadge.textContent = 'Chưa có dữ liệu'; statusBadge.className = 'financial-status financial-status-pending'; }
        return;
      }
      const period = displayPeriod(latest.period);
      const rows = allRows;
      const statusBadgeData = verificationBadge(latest);
      const statusBadge = document.getElementById('stockStatStatus');
      setText('stockStatsMeta', period + ' · ' + (basisSelect?.value === 'separate' ? 'Báo cáo riêng lẻ' : 'Báo cáo hợp nhất') + ' · Nguồn: ' + (snapshots.get(ticker)?.sourceName || 'snapshot tài chính'));
      setText('stockStatPeriod', period);
      setText('stockStatRevenue', overviewMoney(latest.revenue, latest));
      setText('stockStatRevenueLabel', revenueLabelFor(ticker) + ' kỳ gần nhất');
      setText('stockStatRevenueYoYLabel', revenueLabelFor(ticker) + ' (YoY)');
      const revenueYoY = percentageChange('revenue', latest, rows);
      const pretaxYoY = percentageChange('pretax_profit', latest, rows);
      const netYoY = percentageChange('net_profit', latest, rows);
      setText('stockStatRevenueYoY', revenueYoY);
      setText('stockStatPretax', overviewMoney(latest.pretax_profit, latest));
      setText('stockStatPretaxYoY', pretaxYoY);
      setText('stockStatNet', overviewMoney(latest.net_profit, latest));
      setText('stockStatNetYoY', netYoY);
      [['stockStatRevenueYoY',revenueYoY],['stockStatPretaxYoY',pretaxYoY],['stockStatNetYoY',netYoY]].forEach(([id,value]) => styleChange(id,value));

      const price = firstNumber(latest, ['price','last_price','current_price','close','market_price']);
      const high52 = firstNumber(latest, ['high_52w','high_52_week','fifty_two_week_high','week52_high']);
      const low52 = firstNumber(latest, ['low_52w','low_52_week','fifty_two_week_low','week52_low']);
      setText('stockStatPrice', price === null ? '—' : formatPlain(price) + ' đ');
      setText('stockStatVolume15d', formatPlain(firstNumber(latest, ['avg_volume_15d','average_volume_15d','volume_avg_15d','avg_volume_15_days'])));
      const change1d = formatPct(firstNumber(latest, ['change_1d_pct','pct_change_1d','change_day_pct','daily_change_pct']));
      const change1w = formatPct(firstNumber(latest, ['change_1w_pct','pct_change_1w','change_week_pct','weekly_change_pct']));
      const change1m = formatPct(firstNumber(latest, ['change_1m_pct','pct_change_1m','change_month_pct','monthly_change_pct']));
      const change3m = formatPct(firstNumber(latest, ['change_3m_pct','pct_change_3m','quarter_change_pct']));
      const change1y = formatPct(firstNumber(latest, ['change_1y_pct','pct_change_1y','year_change_pct','yearly_change_pct']));
      setText('stockStatChange1d', change1d);
      setText('stockStatChange1w', change1w);
      setText('stockStatChange1m', change1m);
      setText('stockStatChange3m', change3m);
      setText('stockStatChange1y', change1y);
      [['stockStatChange1d',change1d],['stockStatChange1w',change1w],['stockStatChange1m',change1m],['stockStatChange3m',change3m],['stockStatChange1y',change1y]].forEach(([id,value]) => styleChange(id,value));
      setText('stockStatRange52w', high52 !== null || low52 !== null ? (high52 === null ? '—' : formatPlain(high52)) + ' / ' + (low52 === null ? '—' : formatPlain(low52)) + ' đ' : '—');
      setText('stockStatMarketCap', overviewNumber(firstNumber(latest, ['market_cap','market_cap_vnd']), latest));
      setText('stockStatEnterpriseValue', overviewNumber(firstNumber(latest, ['enterprise_value','ev']), latest));
      setText('stockStatEps', overviewNumber(latest.eps, latest, ' đ/cp'));
      setText('stockStatPe', overviewNumber(latest.pe, latest, ' lần'));
      setText('stockStatPeg', overviewNumber(latest.peg, latest, ' lần'));
      setText('stockStatPb', overviewNumber(latest.pb, latest, ' lần'));
      setText('stockStatEvEbitda', overviewNumber(firstNumber(latest, ['ev_ebitda','evToEbitda']), latest, ' lần'));
      setText('stockStatPs', overviewNumber(firstNumber(latest, ['ps','p_s']), latest, ' lần'));
      setText('stockStatBasis', basisSelect?.value === 'separate' ? 'Riêng lẻ' : 'Hợp nhất');
      for (const [id, key] of [
        ['stockStatAssets','total_assets'],['stockStatCurrentAssets','current_assets'],['stockStatCash','cash_and_equivalents'],
        ['stockStatShortInvestments','short_term_investments'],['stockStatInventory','inventory'],
        ['stockStatCurrentLiabilities','current_liabilities'],['stockStatLiabilities','total_liabilities'],['stockStatEquity','equity'],
        ['stockStatOperatingCash','operating_cash_flow'],['stockStatInvestingCash','investing_cash_flow'],['stockStatFinancingCash','financing_cash_flow'],
        ['stockStatCapex','capital_expenditure']
      ]) setText(id, overviewMoney(firstNumber(latest, [key]), latest));

      const operatingCash = firstNumber(latest, ['operating_cash_flow']);
      const capex = firstNumber(latest, ['capital_expenditure']);
      const fcf = operatingCash !== null && capex !== null ? operatingCash - Math.abs(capex) : null;
      setText('stockStatFcf', fcf === null ? '—' : overviewMoney(fcf, latest));
      const grossProfit = firstNumber(latest, ['gross_profit']);
      const revenue = firstNumber(latest, ['revenue']);
      const netProfit = firstNumber(latest, ['net_profit']);
      setText('stockStatGrossMargin', grossProfit !== null && revenue !== null && revenue !== 0 ? formatPct(grossProfit/revenue*100) : '—');
      setText('stockStatNetMargin', netProfit !== null && revenue !== null && revenue !== 0 ? formatPct(netProfit/revenue*100) : '—');

      const assets = firstNumber(latest, ['total_assets']);
      const liabilities = firstNumber(latest, ['total_liabilities']);
      const equity = firstNumber(latest, ['equity']);
      const debtAssets = assets !== null && assets !== 0 && liabilities !== null ? liabilities / assets * 100 : null;
      const debtEquity = equity !== null && equity !== 0 && liabilities !== null ? liabilities / equity : null;
      const equityAssets = assets !== null && assets !== 0 && equity !== null ? equity / assets * 100 : null;
      const currentAssets = firstNumber(latest, ['current_assets']);
      const currentLiabilities = firstNumber(latest, ['current_liabilities']);
      const currentRatio = currentAssets !== null && currentLiabilities !== null && currentLiabilities !== 0 ? currentAssets / currentLiabilities : null;
      setText('stockStatDebtAssets', formatPct(debtAssets));
      setText('stockStatDebtEquity', debtEquity === null ? '—' : formatPlain(debtEquity) + ' lần');
      setText('stockStatEquityAssets', formatPct(equityAssets));
      setText('stockStatCurrentRatio', currentRatio === null ? '—' : formatPlain(currentRatio) + ' lần');
      setText('stockStatRoa', overviewNumber(latest.roa, latest, '%'));
      setText('stockStatRoe', overviewNumber(latest.roe, latest, '%'));
      if (statusBadge) { statusBadge.textContent = statusBadgeData.label; statusBadge.className = 'financial-status financial-status-' + statusBadgeData.kind; }
      const detailReview = latest.financial_line_items_status === 'auto_extracted_pending_visual_review'
        ? ' · Chỉ tiêu chi tiết: trích xuất tự động, chờ đối chiếu PDF'
        : latest.financial_line_items_status === 'manual_review_required'
          ? ' · Chỉ tiêu chi tiết: thiếu số đáng tin cậy, cần rà soát PDF thủ công'
          : '';
      setText('stockStatsSourceNote', (latest.report_type || 'Báo cáo tài chính') + (latest.published_at ? ' · Công bố: ' + dateFmt(latest.published_at) : '') + (latest.source_pages ? ' · ' + latest.source_pages : '') + detailReview);
      const sourceLink = document.getElementById('stockStatsSource');
      if (sourceLink) {
        const url = typeof latest.source_url === 'string' && /^https?:\/\//i.test(latest.source_url) ? latest.source_url : '';
        if (url) { sourceLink.href = url; sourceLink.hidden = false; }
        else sourceLink.hidden = true;
      }
    }
    // Convert source monetary units consistently for tables, KPI cards and all charts.
    // Ratio fields (ROA/ROE, multiples) are passed with isRatio=true and are not scaled.
    const statementNumericValue = (value, item, isRatio = false) => {
      if (!validNumber(value)) return null;
      let numeric = Number(value);
      if (!isRatio) {
        const sourceUnit = String(item?.unit || '').toLowerCase();
        const sourceIsMillion = /triệu|million/.test(sourceUnit);
        const sourceIsBillion = /tỷ|billion/.test(sourceUnit);
        if ((unitSelect?.value || 'billion') === 'billion') {
          if (sourceIsMillion) numeric /= 1000;
          else if (!sourceIsBillion && /vnd|đồng/.test(sourceUnit)) numeric /= 1e9;
        } else {
          if (sourceIsBillion) numeric *= 1000;
          else if (!sourceIsMillion && /vnd|đồng/.test(sourceUnit)) numeric /= 1e6;
        }
      }
      return Number.isFinite(numeric) ? numeric : null;
    };
    const statementNumber = (value, item, isRatio = false) => {
      const numeric = statementNumericValue(value, item, isRatio);
      if (numeric === null) return '—';
      return new Intl.NumberFormat('en-US', { maximumFractionDigits: 1, minimumFractionDigits: 0 }).format(numeric);
    };
    const getStatementRows = () => {
      const activeTicker = String(symbolSelect?.value || 'MBB').toUpperCase();
      const activeIndustry = industryFor(activeTicker);
      const revenueRowLabel = activeIndustry === 'banking'
        ? 'Tổng thu nhập hoạt động'
        : activeIndustry === 'securities'
          ? 'Doanh thu hoạt động'
          : 'Doanh thu thuần';
      if (activeStatement === 'balance') {
        if (activeIndustry === 'banking') return [
          { label: 'A. TÀI SẢN NGÂN HÀNG', type: 'section' },
          { label: 'Tiền mặt, vàng bạc, đá quý', key: 'bank_cash_on_hand', level: 1 },
          { label: 'Tiền gửi tại Ngân hàng Nhà nước', key: 'bank_deposits_at_state_bank', level: 1 },
          { label: 'Tiền gửi và cho vay các tổ chức tín dụng khác', key: 'bank_deposits_and_loans_to_credit_institutions', level: 1 },
          { label: 'Cho vay khách hàng (số dư thuần)', key: 'bank_customer_loans', level: 1 },
          { label: 'Trong đó: dư nợ cho vay gộp', key: 'bank_customer_loans_gross', level: 2 },
          { label: 'Trong đó: dự phòng rủi ro cho vay', key: 'bank_customer_loan_loss_allowance', level: 2 },
          { label: 'Chứng khoán kinh doanh', key: 'bank_trading_securities', level: 1 },
          { label: 'Công cụ tài chính phái sinh và tài sản tài chính khác', key: 'bank_derivatives_and_other_financial_assets', level: 1 },
          { label: 'Chứng khoán đầu tư', key: 'bank_investment_securities', level: 1 },
          { label: 'Trong đó: chứng khoán sẵn sàng để bán', key: 'bank_available_for_sale_securities', level: 2 },
          { label: 'Trong đó: chứng khoán giữ đến ngày đáo hạn', key: 'bank_held_to_maturity_securities', level: 2 },
          { label: 'Trong đó: dự phòng giảm giá chứng khoán', key: 'bank_investment_securities_allowance', level: 2 },
          { label: 'Góp vốn, đầu tư dài hạn', key: 'bank_contributions_and_long_term_investments', level: 1 },
          { label: 'Bất động sản đầu tư', key: 'bank_investment_property', level: 1 },
          { label: 'Tài sản cố định', key: 'fixed_assets', level: 1 },
          { label: 'Tài sản có khác', key: 'bank_other_assets', level: 1 },
          { label: 'TỔNG CỘNG TÀI SẢN', key: 'total_assets', strong: true },
          { label: 'B. NỢ PHẢI TRẢ NGÂN HÀNG', type: 'section' },
          { label: 'Nợ Chính phủ và Ngân hàng Nhà nước', key: 'bank_government_and_state_bank_liabilities', level: 1 },
          { label: 'Tiền gửi và vay từ các tổ chức tín dụng khác', key: 'bank_deposits_and_borrowings_from_credit_institutions', level: 1 },
          { label: 'Công cụ tài chính phái sinh và các khoản nợ tài chính khác', key: 'bank_derivatives_and_other_financial_liabilities', level: 1 },
          { label: 'Tiền gửi khách hàng', key: 'bank_customer_deposits', level: 1 },
          { label: 'Phát hành giấy tờ có giá', key: 'bank_valuable_papers', level: 1 },
          { label: 'Vốn tài trợ, ủy thác đầu tư', key: 'bank_funding_and_trust_liabilities', level: 1 },
          { label: 'Nợ khác', key: 'bank_other_liabilities', level: 1 },
          { label: 'Trong đó: lãi, phí phải trả', key: 'bank_interest_payable', level: 2 },
          { label: 'Trong đó: thuế TNDN hoãn lại phải trả', key: 'bank_deferred_tax_liability', level: 2 },
          { label: 'Trong đó: khoản phải trả và công nợ khác', key: 'bank_other_payables_and_liabilities', level: 2 },
          { label: 'Trong đó: dự phòng rủi ro phải trả khác', key: 'bank_other_provisions', level: 2 },
          { label: 'TỔNG NỢ PHẢI TRẢ', key: 'total_liabilities', strong: true },
          { label: 'Vốn chủ sở hữu', key: 'equity', level: 1 },
          { label: 'Vốn và các quỹ của tổ chức tín dụng', key: 'bank_capital_and_funds', level: 2 },
          { label: 'Quỹ của tổ chức tín dụng', key: 'bank_reserves', level: 2 },
          { label: 'Chênh lệch tỷ giá hối đoái', key: 'bank_fx_difference', level: 2 },
          { label: 'Lợi nhuận sau thuế chưa phân phối', key: 'retained_earnings', level: 1 },
          { label: 'TỔNG NỢ VÀ VỐN CHỦ SỞ HỮU', formula: 'total_sources', strong: true }
        ];
        if (activeIndustry === 'securities') return [
          { label: 'A. TÀI SẢN CÔNG TY CHỨNG KHOÁN', type: 'section' },
          { label: 'Tiền và tương đương tiền', key: 'cash_and_equivalents', level: 1 },
          { label: 'Tài sản tài chính FVTPL', key: 'broker_fvtpl_assets', level: 1 },
          { label: 'Đầu tư nắm giữ đến ngày đáo hạn', key: 'broker_held_to_maturity_assets', level: 1 },
          { label: 'Các khoản cho vay', key: 'broker_lending_assets', level: 1 },
          { label: 'Tài sản tài chính sẵn sàng để bán', key: 'broker_afs_assets', level: 1 },
          { label: 'Các khoản phải thu', key: 'broker_receivables', level: 1 },
          { label: 'Tài sản dài hạn', key: 'non_current_assets', level: 1 },
          { label: 'Tài sản cố định', key: 'fixed_assets', level: 1 },
          { label: 'TỔNG CỘNG TÀI SẢN', key: 'total_assets', strong: true },
          { label: 'B. NỢ PHẢI TRẢ CÔNG TY CHỨNG KHOÁN', type: 'section' },
          { label: 'Vay ngắn hạn', key: 'broker_short_term_borrowings', level: 1 },
          { label: 'Trái phiếu phát hành ngắn hạn', key: 'broker_short_term_bonds', level: 1 },
          { label: 'Trái phiếu phát hành dài hạn', key: 'broker_long_term_bonds', level: 1 },
          { label: 'Tiền gửi của khách hàng', key: 'broker_customer_deposits', level: 1 },
          { label: 'TỔNG NỢ PHẢI TRẢ', key: 'total_liabilities', strong: true },
          { label: 'Vốn chủ sở hữu', key: 'equity', level: 1 },
          { label: 'Lợi nhuận sau thuế chưa phân phối', key: 'retained_earnings', level: 1 },
          { label: 'TỔNG NỢ VÀ VỐN CHỦ SỞ HỮU', formula: 'total_sources', strong: true }
        ];
        return [
        { label: 'A. TÀI SẢN', type: 'section' },
        { label: 'I. Tài sản ngắn hạn', key: 'current_assets', level: 1 },
        { label: 'Tiền và tương đương tiền', key: 'cash_and_equivalents', level: 1 },
        { label: 'Đầu tư tài chính ngắn hạn', key: 'short_term_investments', level: 1 },
        { label: 'Các khoản phải thu ngắn hạn', key: 'short_term_receivables', level: 1 },
        { label: 'Hàng tồn kho', key: 'inventory', level: 1 },
        { label: 'II. Tài sản dài hạn', key: 'non_current_assets', level: 1 },
        { label: 'Tài sản cố định', key: 'fixed_assets', level: 1 },
        { label: 'TỔNG CỘNG TÀI SẢN', key: 'total_assets', strong: true },
        { label: 'B. NỢ PHẢI TRẢ VÀ VỐN CHỦ SỞ HỮU', type: 'section' },
        { label: 'I. Nợ ngắn hạn', key: 'current_liabilities', level: 1 },
        { label: 'II. Nợ dài hạn', key: 'long_term_liabilities', level: 1 },
        { label: 'Tổng nợ phải trả', key: 'total_liabilities', strong: true },
        { label: 'III. Vốn chủ sở hữu', key: 'equity', level: 1 },
        { label: 'Lợi nhuận sau thuế chưa phân phối', key: 'retained_earnings', level: 1 },
        { label: 'TỔNG NỢ VÀ VỐN CHỦ SỞ HỮU', formula: 'total_sources', strong: true }
        ];
      }
      if (activeStatement === 'income') {
        if (activeIndustry === 'banking') return [
          { label: 'KẾT QUẢ HOẠT ĐỘNG KINH DOANH NGÂN HÀNG', type: 'section' },
          { label: 'Tổng thu nhập hoạt động', key: 'revenue', strong: true },
          { label: 'Thu nhập lãi và các khoản thu nhập tương tự', key: 'bank_interest_income', level: 1 },
          { label: 'Chi phí lãi và các khoản chi phí tương tự', key: 'bank_interest_expense', level: 1 },
          { label: 'Thu nhập lãi thuần', key: 'bank_net_interest_income', strong: true },
          { label: 'Thu nhập từ hoạt động dịch vụ', key: 'bank_service_income', level: 1 },
          { label: 'Chi phí hoạt động dịch vụ', key: 'bank_service_expense', level: 1 },
          { label: 'Lãi thuần từ hoạt động dịch vụ', key: 'bank_net_service_income', level: 1 },
          { label: 'Lãi thuần kinh doanh ngoại hối', key: 'bank_fx_net_income', level: 1 },
          { label: 'Lãi thuần từ chứng khoán kinh doanh', key: 'bank_trading_securities_net', level: 1 },
          { label: 'Lãi thuần từ chứng khoán đầu tư', key: 'bank_investment_securities_net', level: 1 },
          { label: 'Lãi thuần từ hoạt động kinh doanh khác', key: 'bank_other_operating_net', level: 1 },
          { label: 'Thu nhập góp vốn, mua cổ phần', key: 'bank_dividend_and_capital_income', level: 1 },
          { label: 'Tổng chi phí hoạt động', key: 'bank_operating_expenses', level: 1 },
          { label: 'Lợi nhuận trước dự phòng rủi ro', key: 'bank_pre_provision_operating_profit', strong: true },
          { label: 'Chi phí dự phòng rủi ro', key: 'bank_provision_expense', level: 1 },
          { label: 'Lợi nhuận trước thuế', key: 'pretax_profit', strong: true },
          { label: 'Thuế thu nhập doanh nghiệp (tổng)', key: 'income_tax', level: 1 },
          { label: 'Thuế TNDN hiện hành', key: 'income_tax_current', level: 1 },
          { label: 'Thuế TNDN hoãn lại', key: 'income_tax_deferred', level: 1 },
          { label: 'Lợi nhuận sau thuế', key: 'net_profit', strong: true },
          { label: 'Lợi ích cổ đông không kiểm soát', key: 'bank_non_controlling_profit', level: 1 },
          { label: 'Lợi nhuận sau thuế thuộc ngân hàng', key: 'net_profit_attributable', level: 1 }
        ];
        if (activeIndustry === 'securities') return [
          { label: 'KẾT QUẢ HOẠT ĐỘNG KINH DOANH CÔNG TY CHỨNG KHOÁN', type: 'section' },
          { label: 'Doanh thu hoạt động', key: 'revenue', strong: true },
          { label: 'Tổng doanh thu hoạt động theo BCTC CTCK', key: 'broker_total_operating_revenue', level: 1 },
          { label: 'Lãi/(lỗ) tài sản tài chính FVTPL', key: 'broker_fvtpl_gain', level: 1 },
          { label: 'Lỗ từ tài sản tài chính FVTPL', key: 'broker_fvtpl_loss', level: 1 },
          { label: 'Lãi từ đầu tư nắm giữ đến ngày đáo hạn', key: 'broker_held_to_maturity_income', level: 1 },
          { label: 'Thu nhập từ khoản cho vay và phải thu', key: 'broker_lending_income', level: 1 },
          { label: 'Lãi từ tài sản tài chính sẵn sàng để bán', key: 'broker_afs_income', level: 1 },
          { label: 'Doanh thu môi giới chứng khoán', key: 'broker_brokerage_revenue', level: 1 },
          { label: 'Doanh thu bảo lãnh, đại lý phát hành', key: 'broker_underwriting_revenue', level: 1 },
          { label: 'Doanh thu tư vấn đầu tư chứng khoán', key: 'broker_advisory_revenue', level: 1 },
          { label: 'Doanh thu lưu ký chứng khoán', key: 'broker_custody_revenue', level: 1 },
          { label: 'Doanh thu tư vấn tài chính', key: 'broker_financial_advisory_revenue', level: 1 },
          { label: 'Thu nhập hoạt động khác', key: 'broker_other_operating_income', level: 1 },
          { label: 'Tổng chi phí hoạt động theo BCTC CTCK', key: 'broker_total_operating_expenses', level: 1 },
          { label: 'Chi phí đi vay của các khoản cho vay', key: 'broker_lending_cost', level: 1 },
          { label: 'Chi phí hoạt động tự doanh', key: 'broker_trading_expense', level: 1 },
          { label: 'Chi phí tư vấn tài chính', key: 'broker_advisory_expense', level: 1 },
          { label: 'Lỗ từ tự doanh FVTPL', key: 'broker_fvtpl_loss', level: 1 },
          { label: 'Chi phí môi giới chứng khoán', key: 'broker_brokerage_expense', level: 1 },
          { label: 'Chi phí lưu ký chứng khoán', key: 'broker_custody_expense', level: 1 },
          { label: 'Chi phí hoạt động khác', key: 'broker_other_operating_expense', level: 1 },
          { label: 'Chi phí hoạt động', key: 'broker_operating_expenses', level: 1 },
          { label: 'Doanh thu hoạt động tài chính', key: 'broker_financial_income', level: 1 },
          { label: 'Chi phí tài chính', key: 'broker_financial_expense', level: 1 },
          { label: 'Trong đó: Chi phí lãi vay', key: 'broker_interest_expense', level: 1 },
          { label: 'Chi phí quản lý công ty chứng khoán', key: 'broker_admin_expenses', level: 1 },
          { label: 'Lợi nhuận thuần từ hoạt động kinh doanh', key: 'broker_net_operating_profit', strong: true },
          { label: 'Lợi nhuận trước thuế', key: 'pretax_profit', strong: true },
          { label: 'Thuế thu nhập doanh nghiệp', key: 'income_tax', level: 1 },
          { label: 'Lợi nhuận sau thuế', key: 'net_profit', strong: true },
          { label: 'LNST thuộc cổ đông công ty mẹ', key: 'net_profit_attributable', level: 1 },
          { label: 'EPS cơ bản (đồng/cp)', key: 'eps', ratio: true, level: 1 }
        ];
        return [
        { label: 'KẾT QUẢ HOẠT ĐỘNG KINH DOANH', type: 'section' },
        { label: revenueRowLabel, key: 'revenue', level: 1 },
        { label: 'Giá vốn hàng bán', key: 'cost_of_goods_sold', level: 1 },
        { label: 'Lợi nhuận gộp', key: 'gross_profit', strong: true },
        { label: 'Doanh thu hoạt động tài chính', key: 'financial_income', level: 1 },
        { label: 'Chi phí tài chính', key: 'financial_expense', level: 1 },
        { label: 'Trong đó: Chi phí lãi vay', key: 'interest_expense', level: 1 },
        { label: 'Chi phí bán hàng', key: 'selling_expense', level: 1 },
        { label: 'Chi phí quản lý doanh nghiệp', key: 'admin_expense', level: 1 },
        { label: 'Lợi nhuận từ hoạt động kinh doanh', key: 'operating_profit', strong: true },
        { label: 'Lợi nhuận trước thuế', key: 'pretax_profit', strong: true },
        { label: 'Thuế thu nhập doanh nghiệp (tổng)', key: 'income_tax', level: 1 },
        { label: 'Thuế TNDN hiện hành', key: 'income_tax_current', level: 1 },
        { label: 'Thuế TNDN hoãn lại', key: 'income_tax_deferred', level: 1 },
        { label: 'Lãi cơ bản trên cổ phiếu (EPS)', key: 'eps', ratio: true, level: 1 },
        { label: 'Lợi nhuận sau thuế', key: 'net_profit', strong: true },
        { label: 'Trong đó: LNST thuộc cổ đông công ty mẹ', key: 'net_profit_attributable', level: 1 }
        ];
      }
      if (activeStatement === 'cashflow') return [
        { label: 'LƯU CHUYỂN TIỀN TỆ', type: 'section' },
        { label: 'Lưu chuyển tiền thuần từ hoạt động kinh doanh', key: 'operating_cash_flow', strong: true },
        { label: 'Chi đầu tư tài sản cố định', key: 'capital_expenditure', level: 1 },
        { label: 'Lưu chuyển tiền thuần từ hoạt động đầu tư', key: 'investing_cash_flow', strong: true },
        { label: 'Lưu chuyển tiền thuần từ hoạt động tài chính', key: 'financing_cash_flow', strong: true },
        { label: 'Ảnh hưởng thay đổi tỷ giá ngoại tệ', key: 'foreign_exchange_effect', level: 1 },
        { label: 'Cổ tức, lợi nhuận đã trả cho chủ sở hữu', key: 'dividends_paid', level: 1 },
        { label: 'Lưu chuyển tiền thuần trong kỳ', key: 'net_cash_change', strong: true },
        { label: 'Tiền và tương đương tiền đầu kỳ', key: 'cash_beginning', level: 1 },
        { label: 'Tiền và tương đương tiền cuối kỳ', key: 'cash_ending', strong: true }
      ];
      if (activeStatement === 'ratios') return [
        { label: 'KHẢ NĂNG SINH LỜI', type: 'section' },
        { label: 'ROA (%)', key: 'roa', ratio: true, level: 1 },
        { label: 'ROE (%)', key: 'roe', ratio: true, level: 1 },
        { label: 'Biên lợi nhuận gộp (%)', formula: 'gross_margin', ratio: true, level: 1 },
        { label: 'Biên lợi nhuận ròng (%)', formula: 'net_margin', ratio: true, level: 1 },
        { label: 'CƠ CẤU NGUỒN VỐN', type: 'section' },
        { label: 'Nợ phải trả / Tổng tài sản (%)', formula: 'liabilities_to_assets', ratio: true, level: 1 },
        { label: 'Vốn chủ sở hữu / Tổng tài sản (%)', formula: 'equity_to_assets', ratio: true, level: 1 },
        { label: 'Nợ phải trả / Vốn chủ sở hữu (lần)', formula: 'liabilities_to_equity', ratio: true, level: 1 },
        { label: 'KHẢ NĂNG THANH TOÁN', type: 'section' },
        { label: 'Hệ số thanh toán hiện hành (lần)', formula: 'current_ratio', ratio: true, level: 1 },
        { label: 'Hệ số thanh toán nhanh (lần)', formula: 'quick_ratio', ratio: true, level: 1 },
        { label: 'Cơ sở tính ROA', key: 'roa_formula', text: true },
        { label: 'Cơ sở tính ROE', key: 'roe_formula', text: true },
        { label: 'Đơn vị tỷ số', key: 'ratio_unit', text: true }
      ];
      if (activeStatement === 'valuation') return [
        { label: 'CHỈ SỐ ĐỊNH GIÁ', type: 'section' },
        { label: 'Giá cổ phiếu (đồng/cp)', key: 'price', ratio: true, level: 1 },
        { label: 'EPS — lợi nhuận trên mỗi cổ phiếu (đồng/cp)', key: 'eps', ratio: true, level: 1 },
        { label: 'P/E (lần)', key: 'pe', ratio: true, level: 1 },
        { label: 'P/B (lần)', key: 'pb', ratio: true, level: 1 },
        { label: 'EV/EBITDA (lần)', key: 'ev_ebitda', ratio: true, level: 1 },
        { label: 'Vốn hóa thị trường', key: 'market_cap', level: 1 },
        { label: 'Giá trị doanh nghiệp (EV)', key: 'enterprise_value', level: 1 },
        { label: 'GIẢI THÍCH', type: 'section' },
        { label: 'Trường dữ liệu định giá được cung cấp', key: 'valuation_source', text: true },
        { label: 'Đơn vị định giá', key: 'valuation_unit', text: true }
      ];
      if (activeStatement === 'notes') return [
        { label: 'THÔNG TIN NGUỒN BÁO CÁO', type: 'section' },
        { label: 'Trạng thái kiểm chứng', key: 'verification_status', text: true, status: true },
        { label: 'Loại báo cáo', key: 'report_type', text: true },
        { label: 'Ngày công bố', key: 'published_at', text: true },
        { label: 'Phạm vi trang PDF', key: 'source_pages', text: true },
        { label: 'Cơ sở số liệu lợi nhuận theo quý', key: 'quarter_profit_basis', text: true },
        { label: 'Trạng thái trích xuất chỉ tiêu chi tiết', key: 'financial_line_items_status', text: true },
        { label: 'Các trường chi tiết đã trích xuất', key: 'financial_line_items_extracted_fields', text: true },
        { label: 'Ghi chú rà soát chỉ tiêu chi tiết', key: 'financial_line_items_note', text: true },
        { label: 'Chỉ tiêu bị ẩn do không khớp', key: 'financial_line_items_rejected_fields', text: true },
        { label: 'Công thức doanh thu tái lập', key: 'revenue_calculation', text: true },
        { label: 'Nguồn báo cáo gốc', key: 'source_url', link: true },
        { label: 'Trang tài liệu VietstockFinance', key: 'source_index_url', link: true }
      ];
      return [];
    };

    function renderStatementTable(ticker) {
      const sourceRows = rowsForBasis(ticker);
      const allTablePeriods = activeStatement === 'peers'
        ? allPeriods().slice().reverse()
        : [...new Set(sourceRows.map(item => item.period))].sort().reverse();
      const maxOffset = Math.max(0, Math.floor(Math.max(0, allTablePeriods.length - 1) / statementPageSize) * statementPageSize);
      periodOffset = Math.min(periodOffset, maxOffset);
      const periods = allTablePeriods.slice(periodOffset, periodOffset + statementPageSize);
      const periodRange = $('#stockPeriodRange');
      if (periodRange) periodRange.textContent = periods.length
        ? displayPeriod(periods[0]) + ' - ' + displayPeriod(periods[periods.length - 1])
        : 'Chưa có kỳ báo cáo';
      const first = $('#stockPeriodFirst'), prev = $('#stockPeriodPrev'), next = $('#stockPeriodNext'), last = $('#stockPeriodLast');
      if (first) first.disabled = periodOffset === 0 || !allTablePeriods.length;
      if (prev) prev.disabled = periodOffset === 0 || !allTablePeriods.length;
      if (next) next.disabled = periodOffset + statementPageSize >= allTablePeriods.length;
      if (last) last.disabled = periodOffset + statementPageSize >= allTablePeriods.length;
      if (peerOptions) peerOptions.hidden = activeStatement !== 'peers';
      if (statementHint) {
        const unitName = (unitSelect?.value || 'billion') === 'billion' ? 'tỷ đồng' : 'triệu đồng';
        const hints = {
          balance: 'Bảng cân đối kế toán: các khoản mục chi tiết được điền từ dòng báo cáo có thể nhận diện và giữ trống nếu không khớp tổng tài sản/nợ.',
          income: activeIndustry === 'banking'
            ? 'Báo cáo ngân hàng: thu nhập lãi, thu nhập dịch vụ, chi phí hoạt động và dự phòng được lấy theo mẫu BCTC ngân hàng; chỉ tiêu không nhận diện chắc chắn sẽ để trống.'
            : activeIndustry === 'securities'
              ? 'Báo cáo công ty chứng khoán: doanh thu môi giới, cho vay, tự doanh, bảo lãnh và lưu ký được tách theo mẫu báo cáo CTCK; trường thiếu hoặc chưa khớp sẽ để trống.'
              : 'Kết quả kinh doanh: chỉ tiêu chi tiết lấy từ BCTC quý; doanh thu có thể được tái lập từ lợi nhuận gộp và giá vốn khi OCR sai chữ số, có ghi công thức trong ghi chú.',
          cashflow: 'Lưu chuyển tiền tệ chỉ hiển thị khi các luồng tiền khớp biến động tiền thuần; kỳ có số OCR mâu thuẫn sẽ để trống và ghi rõ ở ghi chú.',
          notes: 'Thông tin nguồn, kỳ công bố và trạng thái kiểm chứng lấy từ bản ghi báo cáo; mở PDF để xem chi tiết gốc.',
          ratios: 'ROA/ROE và P/B chỉ lấy từ trường dữ liệu đã có trong snapshot; không tự tính P/B khi thiếu giá thị trường và giá trị sổ sách trên mỗi cổ phiếu.',
          peers: 'So sánh các mã cùng nhóm ngành đã cấu hình, cùng kỳ và cùng chỉ tiêu. P/B chỉ hiển thị khi snapshot có dữ liệu được cung cấp; không tự suy đoán giá thị trường.'
        };
        statementHint.textContent = hints[activeStatement] + ' Đơn vị tiền tệ đang chọn: ' + unitName + '.';
      }
      if (!periods.length) {
        if (tableWrap) tableWrap.classList.add('hidden');
        if (stateBox) {
          stateBox.classList.remove('hidden');
          const heading = $('h3', stateBox), paragraph = $('p', stateBox);
          if (heading) heading.textContent = activeStatement === 'cashflow' ? 'Chưa có dữ liệu lưu chuyển tiền tệ' : 'Chưa có báo cáo phù hợp';
          if (paragraph) paragraph.textContent = activeStatement === 'cashflow'
            ? 'Snapshot hiện tại chưa có trường lưu chuyển tiền tệ được trích xuất từ VietstockFinance.'
            : 'Không tìm thấy kỳ báo cáo phù hợp với mã và loại báo cáo đang chọn.';
        }
        if (tableBody) tableBody.innerHTML = '';
        if (statementHead) statementHead.innerHTML = '<tr><th>Chỉ tiêu</th></tr>';
        return { periods, rows: sourceRows };
      }

      if (stateBox) stateBox.classList.add('hidden');
      if (tableWrap) tableWrap.classList.remove('hidden');
      if (statementHead) statementHead.innerHTML = '<tr><th class="statement-first-col">' + (activeStatement === 'peers' ? 'Mã chứng khoán' : 'Chỉ tiêu') + '</th>' +
        periods.map(period => '<th class="statement-period">' + escapeHtml(displayPeriod(period)) + '</th>').join('') + '</tr>';

      let body = '';
      const cashflowFields = ['operating_cash_flow','capital_expenditure','investing_cash_flow','financing_cash_flow','foreign_exchange_effect','dividends_paid','net_cash_change','cash_beginning','cash_ending'];
      const cashflowAvailable = activeStatement === 'cashflow' && sourceRows.some(row => cashflowFields.some(field => validNumber(row[field])));
      if (activeStatement === 'cashflow' && !cashflowAvailable) {
        body = '<tr><td colspan="' + (periods.length + 1) + '" class="statement-no-data">Chưa có trường lưu chuyển tiền tệ đã trích xuất trong snapshot hiện tại. Danh mục chuẩn đã sẵn sàng; các ô chỉ được điền khi bộ trích xuất xác minh được dữ liệu từ báo cáo gốc.</td></tr>';
      } else if (activeStatement === 'peers') {
        const metric = tableCompareMetric?.value || 'net_profit';
        const meta = fieldMeta[metric] || fieldMeta.net_profit;
        const industryMode = $('#stockPeerIndustry')?.value || 'same';
        const selectedIndustry = industryFor(String(symbolSelect?.value || 'MBB').toUpperCase());
        const peerSymbols = symbols.filter(symbol => industryMode === 'all' || industryFor(symbol) === selectedIndustry);
        body = peerSymbols.map(symbol => {
          const items = rowsForBasis(symbol);
          return '<tr><td class="statement-row-label"><strong>' + escapeHtml(symbol) + '</strong><small>' + escapeHtml(meta.label) + '</small></td>' +
            periods.map(period => {
              const item = items.find(row => row.period === period);
              const value = item && validNumber(item[metric]) ? statementNumber(item[metric], item, ['roa','roe','pb'].includes(metric)) + ((metric === 'roa' || metric === 'roe') ? '%' : '') : '—';
              return '<td>' + value + '</td>';
            }).join('') + '</tr>';
        }).join('');
      } else {
        const defs = getStatementRows();
        body = defs.map(def => {
          const rowClass = [def.type === 'section' ? 'statement-section' : '', def.strong ? 'statement-strong' : '', def.level ? 'statement-level-' + def.level : ''].filter(Boolean).join(' ');
          const label = '<td class="statement-row-label">' + escapeHtml(def.label) + '</td>';
          const cells = periods.map(period => {
            const item = sourceRows.find(row => row.period === period);
            if (!item || def.type === 'section' && !def.key) return '<td' + (def.type === 'section' ? ' class="statement-section-empty"' : '') + '></td>';
            if (def.formula === 'total_sources') {
              return '<td>' + (validNumber(item.total_liabilities) && validNumber(item.equity)
                ? statementNumber(Number(item.total_liabilities) + Number(item.equity), item)
                : '—') + '</td>';
            }
            if (def.formula && def.formula !== 'total_sources') {
              const numeric = key => validNumber(item[key]) ? Number(item[key]) : null;
              const assets = numeric('total_assets'), liabilities = numeric('total_liabilities'), equity = numeric('equity');
              const revenue = numeric('revenue'), grossProfit = numeric('gross_profit'), netProfit = numeric('net_profit');
              const currentAssets = numeric('current_assets'), currentLiabilities = numeric('current_liabilities');
              let computed = null;
              if (def.formula === 'liabilities_to_assets' && assets !== null && assets !== 0 && liabilities !== null) computed = liabilities / assets * 100;
              if (def.formula === 'equity_to_assets' && assets !== null && assets !== 0 && equity !== null) computed = equity / assets * 100;
              if (def.formula === 'liabilities_to_equity' && equity !== null && equity !== 0 && liabilities !== null) computed = liabilities / equity;
              if (def.formula === 'gross_margin' && revenue !== null && revenue !== 0 && grossProfit !== null) computed = grossProfit / revenue * 100;
              if (def.formula === 'net_margin' && revenue !== null && revenue !== 0 && netProfit !== null) computed = netProfit / revenue * 100;
              if (def.formula === 'current_ratio' && currentLiabilities !== null && currentLiabilities !== 0 && currentAssets !== null) computed = currentAssets / currentLiabilities;
              if (def.formula === 'quick_ratio' && currentLiabilities !== null && currentLiabilities !== 0) {
                const quickAssets = ['cash_and_equivalents','short_term_investments','short_term_receivables'].map(numeric);
                if (quickAssets.every(value => value !== null)) computed = quickAssets.reduce((sum, value) => sum + value, 0) / currentLiabilities;
              }
              const validComputed = computed !== null && Number.isFinite(computed);
              const rendered = validComputed ? new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(computed) : '—';
              const suffix = ['liabilities_to_equity','current_ratio','quick_ratio'].includes(def.formula) ? ' lần' : '%';
              return '<td>' + rendered + (validComputed ? suffix : '') + '</td>';
            }
            const value = item[def.key];
            if (def.link) {
              return '<td>' + (typeof value === 'string' && /^https?:\/\//i.test(value)
                ? '<a class="statement-source-link" href="' + escapeHtml(value) + '" target="_blank" rel="noopener noreferrer">Mở nguồn ↗</a>'
                : '—') + '</td>';
            }
            if (def.status) {
              const badge = verificationBadge(item);
              return '<td><span class="financial-status financial-status-' + badge.kind + '">' + escapeHtml(badge.label) + '</span></td>';
            }
            if (def.text) return '<td class="statement-text-cell">' + escapeHtml(value || '—') + '</td>';
            const displayed = statementNumber(value, item, Boolean(def.ratio));
            const ratioSuffix = ['pb','pe','ev_ebitda'].includes(def.key) ? ' lần'
              : def.key === 'eps' ? ' đ/cp'
              : ['price'].includes(def.key) ? ' đ'
              : def.ratio ? '%' : '';
            return '<td>' + (displayed !== '—' && def.ratio ? displayed + ratioSuffix : displayed) + '</td>';
          }).join('');
          return '<tr class="' + rowClass + '">' + label + cells + '</tr>';
        }).join('');
      }
      if (tableBody) tableBody.innerHTML = body;
      return { periods, rows: sourceRows };
    }

    function renderSelected() {
      const ticker = String(symbolSelect?.value || 'MBB').toUpperCase();
      const snapshot = snapshots.get(ticker);
      const sourceRows = rowsForBasis(ticker);
      const tableResult = renderStatementTable(ticker);
      const populated = sourceRows.filter(hasNumericFinancialData).length;
      const waiting = sourceRows.filter(item => !hasNumericFinancialData(item)).length;
      const review = sourceRows.filter(item => hasNumericFinancialData(item) && verificationBadge(item).kind !== 'ready').length;
      const sourceLabel = snapshot?._loadedFrom === 'GitHub' ? 'GitHub mới nhất' : 'website/GitHub';
      if (status) {
        status.textContent = (snapshot?.sourceName || 'VietstockFinance snapshot') +
          ' · ' + populated + '/' + sourceRows.length + ' kỳ có số liệu · ' + waiting + ' kỳ đang chờ trích xuất · ' +
          review + ' kỳ có số liệu cần rà soát · Nạp từ: ' + sourceLabel +
          ' · Đồng bộ: ' + (snapshot?.fetchedAt ? dateFmt(snapshot.fetchedAt) : 'chưa ghi nhận') + '.';
      }
      if (loadSummary) loadSummary.textContent = 'Mã ' + ticker + ' · ' + sourceRows.length + ' kỳ có liên kết nguồn · Chế độ ' +
        (basisSelect?.value === 'separate' ? 'riêng lẻ' : 'hợp nhất') + ' · các kỳ mới sẽ tự xuất hiện sau lần đồng bộ tiếp theo.';
      renderFinancialOverview(ticker);
      drawSelectedCharts(ticker);
      return tableResult;
    }

    function populateComparePeriods() {
      const select = $('#stockComparePeriod');
      if (!select) return;
      const periods = allPeriods();
      const previous = select.value;
      select.innerHTML = periods.slice().reverse().map(period => '<option value="' + escapeHtml(period) + '">' + escapeHtml(periodLabel(period)) + '</option>').join('');
      const metric = $('#stockCompareMetric')?.value || 'net_profit';
      const hasComparisonValue = period => symbols.some(ticker => {
        const row = rowsFor(ticker).find(item => item.period === period);
        return row && validNumber(row[metric]);
      });
      if (periods.includes(previous) && hasComparisonValue(previous)) select.value = previous;
      else {
        const preferred = periods.slice().reverse().find(hasComparisonValue) || periods[periods.length - 1];
        if (preferred) select.value = preferred;
      }
    }

    const tickerLoadPromises = new Map();

    async function loadTickerSnapshot(ticker) {
      if (tickerLoadPromises.has(ticker)) return tickerLoadPromises.get(ticker);
      const task = (async () => {
        try {
          const snapshot = await fetchLatestFinancialSnapshot(ticker);
          const items = snapshot.items.filter(record => Boolean(record && validPeriod(record.period) &&
            typeof record.source_url === 'string' && /^https?:\/\//i.test(record.source_url)));
          snapshots.set(ticker, { ...snapshot, items });
          return { ticker, ok: true, count: items.length, loadedFrom: snapshot._loadedFrom };
        } catch (error) {
          snapshots.set(ticker, { symbol: ticker, items: [], sourceName: 'Không tải được snapshot', fetchedAt: null });
          console.warn('[financial-dashboard]', ticker, error);
          return { ticker, ok: false, count: 0, loadedFrom: '' };
        } finally {
          tickerLoadPromises.delete(ticker);
        }
      })();
      tickerLoadPromises.set(ticker, task);
      return task;
    }

    async function loadAll() {
      if (isLoading) return;
      isLoading = true;
      if (loadButton) { loadButton.disabled = true; loadButton.textContent = 'Đang tải…'; }
      if (loadSummary) loadSummary.textContent = 'Đang tải mã đang chọn trước; các mã so sánh sẽ nạp tiếp theo từng nhóm…';
      const resultByTicker = new Map();
      try {
        const selectedTicker = symbols.includes(String(symbolSelect?.value || '').toUpperCase())
          ? String(symbolSelect.value).toUpperCase()
          : symbols[0];

        // Render the selected stock as soon as its two candidate snapshots resolve.
        // Do not block visible statistics/charts on 30+ peer-ticker network requests.
        const first = await loadTickerSnapshot(selectedTicker);
        resultByTicker.set(selectedTicker, first);
        populateYearOptions();
        populateComparePeriods();
        renderSelected();
        drawComparison();
        if (loadSummary) {
          loadSummary.textContent = first.ok
            ? 'Đã tải ' + selectedTicker + ' (' + first.count + ' kỳ có nguồn); đang nạp dần các mã dùng cho so sánh…'
            : 'Chưa tải được snapshot ' + selectedTicker + '; đang thử các mã còn lại. Kiểm tra kết nối nguồn nếu lỗi tiếp diễn.';
        }

        const peers = symbols.filter(ticker => ticker !== selectedTicker);
        const batchSize = 8;
        for (let start = 0; start < peers.length; start += batchSize) {
          const batch = peers.slice(start, start + batchSize);
          const results = await Promise.all(batch.map(loadTickerSnapshot));
          results.forEach(result => resultByTicker.set(result.ticker, result));

          // Keep comparison options fresh while peer data arrives, but never clear
          // the selected ticker's already-rendered figures in the meantime.
          populateYearOptions();
          populateComparePeriods();
          if (resultByTicker.has(String(symbolSelect?.value || '').toUpperCase())) renderSelected();
          drawComparison();

          if (loadSummary) {
            const completed = resultByTicker.size;
            const totalPeriods = [...resultByTicker.values()].reduce((sum, result) => sum + result.count, 0);
            loadSummary.textContent = 'Đã nạp ' + completed + '/' + symbols.length + ' mã · ' +
              totalPeriods + ' kỳ có liên kết nguồn · tiếp tục cập nhật bảng so sánh…';
          }
        }

        populateYearOptions();
        populateComparePeriods();
        renderSelected();
        drawComparison();
        const results = [...resultByTicker.values()];
        const total = results.reduce((sum, item) => sum + item.count, 0);
        const failed = results.filter(item => !item.ok).length;
        if (loadSummary) loadSummary.textContent = 'Đã kiểm tra ' + results.length + ' mã · ' + total +
          ' kỳ có liên kết nguồn · ' + failed + ' mã không tải được snapshot. Mã đang chọn và biểu đồ được hiển thị trước khi nạp xong toàn bộ danh sách.';
      } catch (error) {
        console.error('[financial-dashboard] loadAll failed', error);
        if (loadSummary) loadSummary.textContent = 'Lỗi khi nạp dữ liệu chứng khoán: ' + String(error?.message || error);
        renderSelected();
      } finally {
        isLoading = false;
        if (loadButton) { loadButton.disabled = false; loadButton.textContent = 'Tải lại dữ liệu'; }
      }
    }

    loadButton?.addEventListener('click',loadAll);
    symbolSelect?.addEventListener('change', async () => {
      periodOffset = 0;
      const ticker = String(symbolSelect?.value || symbols[0]).toUpperCase();
      if (snapshots.has(ticker)) {
        renderSelected();
        return;
      }
      if (loadSummary && !isLoading) loadSummary.textContent = 'Đang tải dữ liệu ' + ticker + ' và các biểu đồ liên quan…';
      await loadTickerSnapshot(ticker);
      if (String(symbolSelect?.value || '').toUpperCase() !== ticker) return;
      populateYearOptions();
      populateComparePeriods();
      renderSelected();
      drawComparison();
      if (loadSummary && !isLoading) {
        const snapshot = snapshots.get(ticker);
        loadSummary.textContent = snapshot?.items?.length
          ? 'Đã tải ' + ticker + ' · ' + snapshot.items.length + ' kỳ có liên kết nguồn.'
          : 'Chưa tải được dữ liệu ' + ticker + ' từ website hoặc GitHub. Bấm “Tải lại dữ liệu” để thử lại.';
      }
    });
    yearSelect?.addEventListener('change',renderSelected);
    basisSelect?.addEventListener('change', () => { periodOffset = 0; renderSelected(); });
    unitSelect?.addEventListener('change',renderSelected);
    tableCompareMetric?.addEventListener('change',renderSelected);
    $('#stockPeerIndustry')?.addEventListener('change',renderSelected);
    $('#stockCompareIndustry')?.addEventListener('change',drawComparison);
    $('#stockPeriodFirst')?.addEventListener('click', () => { periodOffset = 0; renderSelected(); });
    $('#stockPeriodPrev')?.addEventListener('click', () => { periodOffset = Math.max(0, periodOffset - statementPageSize); renderSelected(); });
    $('#stockPeriodNext')?.addEventListener('click', () => { periodOffset += statementPageSize; renderSelected(); });
    $('#stockPeriodLast')?.addEventListener('click', () => {
      const allTablePeriods = activeStatement === 'peers' ? allPeriods().slice().reverse() : [...new Set(rowsForBasis(String(symbolSelect?.value || 'MBB').toUpperCase()).map(item => item.period))].sort().reverse();
      periodOffset = allTablePeriods.length ? Math.floor((allTablePeriods.length - 1) / statementPageSize) * statementPageSize : 0;
      renderSelected();
    });
    $('#stockStatementTabs')?.querySelectorAll('[data-statement]').forEach(button => button.addEventListener('click', () => {
      activeStatement = button.dataset.statement || 'balance';
      periodOffset = 0;
      $('#stockStatementTabs').querySelectorAll('[data-statement]').forEach(tab => {
        const active = tab === button;
        tab.classList.toggle('is-active', active);
        tab.setAttribute('aria-selected', active ? 'true' : 'false');
      });
      renderSelected();
    }));
    $('#stockExportExcel')?.addEventListener('click', () => {
      const table = $('#stockTableWrap table');
      if (!table || table.closest('.hidden')) return;
      const csv = [...table.querySelectorAll('tr')].map(row => [...row.querySelectorAll('th,td')].map(cell => {
        const value = (cell.innerText || cell.textContent || '').replace(/\s+/g, ' ').trim();
        return '"' + value.replace(/"/g, '""') + '"';
      }).map(value => value).join(',')).join('\r\n');
      const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = (symbolSelect?.value || 'stock') + '-' + activeStatement + '-financials.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    });
    $('#stockCompareMetric')?.addEventListener('change', () => { populateComparePeriods(); drawComparison(); });
    $('#stockComparePeriod')?.addEventListener('change',drawComparison);
    // Keep the chart comparison metric aligned with the statement-table comparison view.
    $('#stockCompareMetric')?.addEventListener('change', () => {
      if (tableCompareMetric) tableCompareMetric.value = $('#stockCompareMetric').value;
      if (activeStatement === 'peers') renderSelected();
    });
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


  async function setupResearchLibrary() {
    const panel = $('#stockResearchPanel');
    if (!panel) return;
    const status = $('#researchStatus');
    const list = $('#researchReportList');
    const symbol = $('#researchSymbol');
    const category = $('#researchCategory');
    const search = $('#researchSearch');
    let reports = [];
    const esc = (value) => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
    const labels = {
      stock_analysis: 'Báo cáo phân tích cổ phiếu',
      forecast_earnings: 'Dự phóng kết quả kinh doanh',
      recommendation_valuation: 'Khuyến nghị và định giá',
      industry_report: 'Báo cáo phân tích ngành',
      market_strategy: 'Chiến lược thị trường và vĩ mô',
      brokerage_research: 'Báo cáo nghiên cứu khác'
    };
    const render = () => {
      const q = (search.value || '').trim().toLocaleLowerCase('vi');
      const filtered = reports.filter(item =>
        (!symbol.value || item.symbol === symbol.value) &&
        (!category.value || item.category === category.value) &&
        (!q || [item.title, item.symbol, item.source, item.broker, item.company, item.url].some(v => String(v || '').toLocaleLowerCase('vi').includes(q)))
      );
      if (!filtered.length) {
        list.innerHTML = '<div class="empty-state"><h3>Chưa tìm thấy báo cáo phù hợp</h3><p>Thử đổi mã chứng khoán, danh mục hoặc từ khóa. Danh sách không tự tạo báo cáo khi nguồn chưa có kết quả.</p></div>';
        return;
      }
      list.innerHTML = filtered.map(item => { const summary = item.summary ? '<p class="research-summary">'+esc(item.summary)+'</p>' : ''; const metrics = Array.isArray(item.metrics) ? item.metrics.filter(m => m && m.review_status === 'approved' && m.value !== null && m.value !== undefined).map(m => '<span class="status-pill neutral">'+esc(m.name)+': '+esc(m.value)+(m.unit ? ' '+esc(m.unit) : '')+'</span>').join(' ') : ''; return '<article class="research-report-card"><div class="research-report-meta"><span class="status-pill neutral">'+esc(item.symbol || 'Nhiều mã')+'</span><span>'+esc(labels[item.category] || labels.brokerage_research)+'</span></div><h4><a href="'+esc(item.url)+'" target="_blank" rel="noopener noreferrer">'+esc(item.title || 'Báo cáo phân tích')+'</a></h4><p>'+esc(item.broker || item.source || item.source_name || item.host || 'Nguồn công khai')+'</p>'+summary+(metrics ? '<div class="research-report-metrics">'+metrics+'</div>' : '')+'<div class="research-report-foot"><span>'+esc(item.publishedAt || item.report_date || item.publication_date || 'Chưa xác định ngày phát hành')+'</span><a href="'+esc(item.url)+'" target="_blank" rel="noopener noreferrer">Mở tài liệu ↗</a></div><p class="small muted">Báo cáo phân tích / nghiên cứu; không phải số liệu BCTC thực tế.</p></article>'; }).join('');
    };
    [symbol, category, search].forEach(el => el?.addEventListener('input', render));
    try {
      // Prefer the website database when configured; keep the existing JSON snapshot as a safe fallback.
      let payload = null;
      try {
        const dbResponse = await fetch('/api/analysis-reports.php?limit=100', { cache: 'no-store', headers: { 'Accept': 'application/json' } });
        if (dbResponse.ok) {
          const dbPayload = await dbResponse.json();
          if (dbPayload && dbPayload.ok && Array.isArray(dbPayload.reports)) {
            payload = {
              reports: dbPayload.reports.map(item => ({
                ...item,
                url: item.source_url || item.url,
                source: item.publisher || item.source_name || item.source,
                publishedAt: item.report_date || item.publishedAt,
                summary: item.summary || '',
                metrics: Array.isArray(item.metrics) ? item.metrics : []
              }))
            };
          }
        }
      } catch (dbError) {
        console.info('[research-library] Database API unavailable; using static snapshot.');
      }
      if (!payload) {
        const res = await fetchDataFile('analysis-reports.json');
        payload = res && typeof res === 'object' ? res : {};
      }
      reports = Array.isArray(payload.reports) ? payload.reports : [];
      status.textContent = reports.length ? reports.length + ' tài liệu trong danh mục' : 'Chưa có tài liệu';
      render();
    } catch (error) {
      console.warn('[research-library]', error);
      status.textContent = 'Chưa đồng bộ được';
      list.innerHTML = '<div class="empty-state"><h3>Chưa tải được danh mục báo cáo</h3><p>Worker chưa tạo snapshot công khai hoặc nguồn tạm thời không truy cập được.</p></div>';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    loadOverviewKpis();
    setupCommodityFilters();
    setupFinancials();
    setupReportQueue();
    setupResearchLibrary();
    setupEmptyEconomicChart();
    setupSearchShortcut();
    loadMarketSnapshot();
    loadTrendingCommodities();
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