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
      const response = await fetch('data/market-prices.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data)) throw new Error('Cấu trúc dữ liệu không hợp lệ');
      state.commodities = snapshot.data
        .filter(item => Number.isFinite(Number(item.value)) && item.date && item.name)
        .map(item => ({ ...item, group: GROUPS[item.id] || 'other' }))
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
    if (empty) {
      empty.style.display = 'grid';
      empty.textContent = 'Snapshot hiện lưu giá trị gần nhất, chưa có chuỗi lịch sử để vẽ biểu đồ.';
    }
    if (state.chart) { state.chart.destroy(); state.chart = null; }
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
      const response = await fetch('data/currency-rates.json', { cache: 'no-store' });
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
      if (updated) {
        updated.textContent = 'Cập nhật nguồn: ' + dateFmt(snapshot.lastUpdatedUtc);
        updated.className = 'status-pill positive';
      }
      if (status) status.textContent = 'Nguồn: ExchangeRate-API Open Access · tỷ giá tham khảo';
      const disclaimer = $('#currencyDisclaimer');
      if (disclaimer) disclaimer.textContent = (snapshot.rateType || 'Tỷ giá tham khảo') + '. Dữ liệu nguồn cập nhật: ' + snapshot.lastUpdatedUtc + '. Tỷ giá chéo được tính từ các tỷ giá cùng nguồn; không dùng thay tỷ giá giao dịch ngân hàng.';
    } catch (error) {
      table.innerHTML = '<div class="empty-state"><h3>Chưa tải được tỷ giá</h3><p>Kiểm tra file data/currency-rates.json và GitHub Actions đã chạy thành công chưa.</p></div>';
      if (updated) { updated.textContent = 'Chưa có dữ liệu'; updated.className = 'status-pill neutral'; }
      if (status) status.textContent = 'Chưa đồng bộ được tỷ giá';
      console.error('[currency-rates]', error);
    }
  }

  async function loadFinancialRates() {
    const bondTable = $('#bondYieldsTable');
    const interestTable = $('#interestRatesTable');
    const bondUpdated = $('#bondYieldsUpdated');
    const interestUpdated = $('#interestRatesUpdated');
    try {
      const response = await fetch('data/financial-rates.json', { cache: 'no-store' });
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

  async function loadCategoryData() {
    const targets = {
      transport: { table: '#transportDataTable', updated: '#transportUpdated' },
      agriculture: { table: '#agricultureDataTable', updated: '#agricultureUpdated' },
      ports: { table: '#portsDataTable', updated: '#portsUpdated' },
      property: { table: '#propertyDataTable', updated: '#propertyUpdated' },
      labor: { table: '#laborDataTable', updated: '#laborUpdated' }
    };
    try {
      const response = await fetch('data/category-data.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data)) throw new Error('Snapshot không có mảng data');
      for (const [category, target] of Object.entries(targets)) {
        const table = $(target.table);
        const updated = $(target.updated);
        if (!table) continue;
        const item = snapshot.data.find(row => row.category === category);
        if (!item || !Array.isArray(item.observations) || !item.observations.length) {
          table.innerHTML = '<div class="empty-state"><h3>Chưa có dữ liệu</h3><p>Nguồn chưa trả về chuỗi hợp lệ cho danh mục này.</p></div>';
          if (updated) { updated.textContent = 'Chưa có dữ liệu'; updated.className = 'status-pill neutral'; }
          continue;
        }
        const rows = item.observations.slice(-24).reverse();
        table.innerHTML = `<table><thead><tr><th>Chỉ tiêu</th><th>Giá trị</th><th>Đơn vị</th><th>Kỳ dữ liệu</th><th>Nguồn</th></tr></thead><tbody>${rows.map(point => `
          <tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${fmt(point.value, 3)}</td><td>${escapeHtml(item.unit || '—')}</td><td>${escapeHtml(dateFmt(point.date))}</td><td><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.source)}</a></td></tr>`).join('')}</tbody></table>`;
        if (updated) {
          updated.textContent = 'Kỳ mới nhất: ' + dateFmt(item.date);
          updated.className = 'status-pill positive';
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

  function setupFinancials() {
    const symbol = $('#stockSymbol');
    const year = $('#stockYear');
    const button = $('#loadStock');
    const stateBox = $('#stockState');
    const wrap = $('#stockTableWrap');
    async function load() {
      if (wrap) wrap.classList.add('hidden');
      if (stateBox) {
        stateBox.classList.remove('hidden');
        const title = $('h3', stateBox);
        const p = $('p', stateBox);
        if (title) title.textContent = 'Chưa có báo cáo được đồng bộ';
        if (p) p.textContent = 'Chưa có dữ liệu tài chính đã xác minh cho ' + (symbol?.value || '') + ' từ năm ' + (year?.value || '') + '. Website không tự tạo số liệu để lấp chỗ trống.';
      }
    }
    button?.addEventListener('click', load);
    symbol?.addEventListener('change', load);
    year?.addEventListener('change', load);
  }

  function setupEmptyEconomicChart() {
    const select = $('#economicSeriesSelect');
    const empty = $('#economicChartEmpty');
    const source = $('#economicChartSource');
    select?.addEventListener('change', () => {
      if (empty) {
        empty.style.display = 'grid';
        empty.textContent = 'Chưa có chuỗi dữ liệu đã xác minh cho chỉ tiêu này.';
      }
      if (source) source.textContent = 'Nguồn: dulieukinhte.com API · Chưa có snapshot cho chỉ tiêu đã chọn';
    });
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

  document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupCommodityFilters();
    setupFinancials();
    setupEmptyEconomicChart();
    setupSearchShortcut();
    loadMarketSnapshot();
    loadCurrencyRates();
    loadFinancialRates();
    loadCategoryData();
  });
})();