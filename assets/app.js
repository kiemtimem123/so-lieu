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


  async function loadOmoData() {
    const content = $('#omoDataContent');
    const updated = $('#omoDataUpdated');
    if (!content) return;
    try {
      const response = await fetch('data/omo-latest.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data) || !snapshot.fetchedAt) throw new Error('Snapshot OMO không hợp lệ');
      const wanted = ['omo-buy-total', 'omo-net-outstanding'];
      const rows = snapshot.data.filter(item =>
        wanted.includes(item.category) && item.name && item.date && item.url && item.unit &&
        Number.isFinite(Number(item.value)) && /^\\d{4}-\\d{2}-\\d{2}$/.test(item.date)
      );
      if (rows.length !== 2) throw new Error('Snapshot phải có đủ hai chỉ tiêu OMO hợp lệ');
      const now = Date.now();
      const isStale = item => {
        const date = new Date(item.date + 'T00:00:00Z').getTime();
        return !Number.isFinite(date) || now - date > 5 * 24 * 60 * 60 * 1000;
      };
      const newest = rows.reduce((latest, item) => item.date > latest ? item.date : latest, rows[0].date);
      const anyStale = rows.some(isStale);
      content.innerHTML = `<table><thead><tr><th>Chỉ tiêu</th><th>Giá trị</th><th>Đơn vị</th><th>Ngày dữ liệu</th><th>Trạng thái</th><th>Nguồn</th></tr></thead><tbody>${rows.map(item => `
        <tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${fmt(item.value, 2)}</td><td>${escapeHtml(item.unit)}</td><td>${escapeHtml(dateFmt(item.date))}</td><td>${isStale(item) ? '<span class="status-pill warning">Dữ liệu cũ</span>' : '<span class="status-pill neutral">Mới</span>'}</td><td><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Xem nguồn</a></td></tr>`).join('')}</tbody></table><p class="muted">Snapshot đồng bộ lúc ${escapeHtml(dateFmt(snapshot.fetchedAt))}. Khối lượng mua OMO là tổng giao dịch mua trúng thầu trong ngày; chênh lệch lưu hành OMO − tín phiếu là chỉ tiêu tồn lượng. Hai chỉ tiêu này không thay thế cho bơm/hút ròng trong ngày. Cảnh báo dữ liệu cũ nếu kỳ quan sát quá 5 ngày.</p>`;
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
      const response = await fetch('data/policy-rates.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      if (!Array.isArray(snapshot.data) || !snapshot.data.length || !snapshot.sourceUrl || !snapshot.confirmedThrough) {
        throw new Error('Snapshot lãi suất điều hành không hợp lệ');
      }
      const rows = snapshot.data.filter(item => item.name && Number.isFinite(Number(item.value)) && item.unit === '%/năm' && item.effectiveDate);
      if (!rows.length) throw new Error('Không có mức lãi suất hợp lệ');
      content.innerHTML = `<table><thead><tr><th>Chỉ tiêu</th><th>Mức lãi suất</th><th>Đơn vị</th><th>Ngày hiệu lực</th></tr></thead><tbody>${rows.map(item => `<tr><td><strong>${escapeHtml(item.name)}</strong></td><td>${fmt(item.value, 2)}</td><td>${escapeHtml(item.unit)}</td><td>${escapeHtml(dateFmt(item.effectiveDate))}</td></tr>`).join('')}</tbody></table><p class="muted">Đối chiếu trạng thái đến ${escapeHtml(dateFmt(snapshot.confirmedThrough))}. <a href="${escapeHtml(snapshot.sourceUrl)}" target="_blank" rel="noopener noreferrer">Xem nguồn chính</a></p>`;
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
      const response = await fetch('data/credit-growth.json', { cache: 'no-store' });
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

  async function loadUsdVndReference() {
    const content = $('#usdVndReferenceContent');
    const updated = $('#usdVndReferenceUpdated');
    if (!content) return;
    try {
      const response = await fetch('data/currency-rates.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const snapshot = await response.json();
      const usd = snapshot.data?.find(item => item.code === 'USD');
      if (!usd || !Number.isFinite(Number(usd.vndPerUnit)) || Number(usd.vndPerUnit) <= 0 || !snapshot.lastUpdatedUtc) {
        throw new Error('Snapshot không có tỷ giá USD/VND tham khảo hợp lệ');
      }
      content.innerHTML = `<table><thead><tr><th>Chỉ tiêu</th><th>Giá trị</th><th>Đơn vị</th><th>Thời điểm nguồn cập nhật</th></tr></thead><tbody><tr><td><strong>USD/VND tham khảo</strong></td><td>${fmt(usd.vndPerUnit, 2)}</td><td>VND / 1 USD</td><td>${escapeHtml(dateFmt(snapshot.lastUpdatedUtc))}</td></tr></tbody></table>`;
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
      const response = await fetch('data/category-data.json', { cache: 'no-store' });
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
        if (updated) {
          updated.textContent = 'Kỳ mới nhất: ' + dateFmt(latest.date);
          updated.className = 'status-pill positive';
        }
        if (canvas && window.Chart) {
          if (categoryCharts[category]) categoryCharts[category].destroy();
          categoryCharts[category] = new Chart(canvas, {
            type: 'line',
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
          if (note) note.textContent = 'Nguồn: ' + item.source + ' · Đơn vị: ' + (item.unit || 'theo nguồn') + ' · ' + observations.length + ' quan sát. Các kỳ tương lai bị loại khỏi hiển thị.';
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
        const response = await fetch('data/category-data.json', { cache: 'no-store' });
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
    loadUsdVndReference();
    loadCreditGrowth();
    loadOmoData();
  loadPolicyRates();
    loadFinancialRates();
    loadCategoryData();
  });
})();