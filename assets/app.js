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
  });
})();