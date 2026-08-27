"""
Build a self-contained inline dashboard HTML with embedded data.
"""
import json

with open('03_dashboard/dashboard_data.json', encoding='utf-8') as f:
    data = json.load(f)

with open('03_dashboard/index.html', encoding='utf-8') as f:
    html = f.read()

data_json = json.dumps(data, default=str)

# Find the SECOND script block (our inline script, not the CDN one)
first_script_end = html.find('</script>') + 9  # end of CDN script
script_start = html.find('<script>', first_script_end)
script_end = html.find('</script>', script_start) + 9  # include </script>

# Build new script block
new_script_parts = []
new_script_parts.append('<script>')
new_script_parts.append('// === INLINE DATA ===')
new_script_parts.append(f'const _dashboardData = {data_json};')
new_script_parts.append('')
new_script_parts.append('// === CHART DEFAULTS ===')
new_script_parts.append("Chart.defaults.color = '#8b8fa3';")
new_script_parts.append("Chart.defaults.borderColor = '#2a2d3a';")
new_script_parts.append("Chart.defaults.font.family = \"'Segoe UI', system-ui, sans-serif\";")
new_script_parts.append('')
new_script_parts.append("const tierColors = { Platinum: '#a78bfa', Gold: '#fbbf24', Silver: '#94a3b8', Bronze: '#d97706' };")
new_script_parts.append("const tierOrder = ['Platinum', 'Gold', 'Silver', 'Bronze'];")
new_script_parts.append('')
new_script_parts.append("function fmt(n) { return n.toLocaleString('en-US'); }")
new_script_parts.append("function fmtD(n) { return '$' + fmt(n); }")

# renderStats
new_script_parts.append('''
function renderStats(s) {
  const bar = document.getElementById('statsBar');
  const items = [
    { value: fmt(s.total_customers), label: 'Total Customers' },
    { value: fmtD(s.total_revenue), label: 'Total Revenue' },
    { value: fmtD(s.avg_spend), label: 'Avg Spend/Customer' },
    { value: s.avg_rating + '\u2605', label: 'Avg Rating' },
    { value: s.avg_loyalty, label: 'Avg Loyalty Score' },
    { value: s.avg_promo_dep + '%', label: 'Avg Promo Dependency' },
    { value: s.pct_subscribed + '%', label: 'Subscribed' },
  ];
  bar.innerHTML = items.map(i =>
    '<div class="stat-card"><div class="value">' + i.value + '</div><div class="label">' + i.label + '</div></div>'
  ).join('');
}''')

# renderPyramid
new_script_parts.append('''
function renderPyramid(pyramid) {
  const labels = tierOrder;
  const custData = tierOrder.map(t => { const r = pyramid.find(p => p.tier === t); return r ? r.customer_count : 0; });
  const revData = tierOrder.map(t => { const r = pyramid.find(p => p.tier === t); return r ? r.revenue_pct : 0; });
  const colors = tierOrder.map(t => tierColors[t]);
  new Chart(document.getElementById('pyramidChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Customer Count', data: custData, backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 1, yAxisID: 'y' },
        { label: 'Revenue %', data: revData, type: 'line', borderColor: '#6366f1', backgroundColor: '#6366f133', pointBackgroundColor: '#6366f1', pointRadius: 5, tension: 0.3, fill: true, yAxisID: 'y1' }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { title: { display: true, text: 'Customers' }, grid: { color: '#2a2d3a' } },
        y1: { position: 'right', title: { display: true, text: 'Revenue %' }, grid: { display: false }, min: 0, max: 50 }
      },
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16 } } }
    }
  });
  const topTier = pyramid.find(p => p.tier === 'Platinum');
  const botTier = pyramid.find(p => p.tier === 'Bronze');
  document.getElementById('pyramidInsight').innerHTML =
    '<strong>Key Insight:</strong> Platinum customers (' + topTier.customer_count + ', ' + topTier.revenue_pct + '% revenue) generate disproportionate value. Bronze has the most customers (' + botTier.customer_count + ') but lowest avg spend ($' + botTier.avg_spend + ').';
}''')

# renderScatter
new_script_parts.append('''
function renderScatter(scatter) {
  const tierBuckets = {};
  scatter.forEach(d => { if (!tierBuckets[d.tier]) tierBuckets[d.tier] = []; tierBuckets[d.tier].push({ x: d.promo_dep, y: d.loyalty }); });
  const datasets = tierOrder.map(tier => ({
    label: tier, data: tierBuckets[tier] || [], backgroundColor: tierColors[tier] + '88', borderColor: tierColors[tier], borderWidth: 1, pointRadius: 3, pointHoverRadius: 6
  }));
  new Chart(document.getElementById('scatterChart'), {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      scales: {
        x: { title: { display: true, text: 'Promo Dependency Score' }, min: 0, max: 100, grid: { color: '#2a2d3a' } },
        y: { title: { display: true, text: 'Loyalty Score' }, min: 0, max: 100, grid: { color: '#2a2d3a' } }
      },
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16 } } }
    }
  });
  document.getElementById('scatterInsight').innerHTML = '<strong>Key Insight:</strong> Upper-left = loyal organic buyers. Lower-right = promo-dependent. Platinum clusters in the upper half regardless of promo use.';
}''')

# renderGeo
new_script_parts.append('''
function renderGeo(geo) {
  const top15 = geo.slice(0, 15);
  const labels = top15.map(g => g.state);
  const oppScore = top15.map(g => g.organic_opportunity_score);
  const spend = top15.map(g => g.avg_spend);
  const colors = top15.map(g => g.organic_opportunity_score >= 40 ? '#34d399' : g.organic_opportunity_score >= 37 ? '#60a5fa' : '#94a3b8');
  new Chart(document.getElementById('geoChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Organic Opportunity Score', data: oppScore, backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 1, yAxisID: 'y' },
        { label: 'Avg Spend ($)', data: spend, type: 'line', borderColor: '#fbbf24', backgroundColor: '#fbbf2433', pointBackgroundColor: '#fbbf24', pointRadius: 4, tension: 0.3, yAxisID: 'y1' }
      ]
    },
    options: {
      responsive: true, indexAxis: 'y',
      scales: {
        x: { title: { display: true, text: 'Opportunity Score' }, grid: { color: '#2a2d3a' } },
        y: { grid: { display: false } }
      },
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16 } } }
    }
  });
  const top = geo[0];
  document.getElementById('geoInsight').innerHTML = '<strong>Key Insight:</strong> ' + top.state + ' leads with organic opportunity score of ' + top.organic_opportunity_score + ' (high spend $' + top.avg_spend + ', low promo dep ' + top.avg_promo_dep + '%).';
}''')

# renderCategory
new_script_parts.append('''
function renderCategory(cats) {
  const labels = cats.map(c => c.category);
  const prevPurchases = cats.map(c => c.avg_prev_purchases);
  const avgSpend = cats.map(c => c.avg_spend);
  const colors = ['#6366f1', '#34d399', '#fbbf24', '#f87171'];
  new Chart(document.getElementById('categoryChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Avg Previous Purchases', data: prevPurchases, backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 1, yAxisID: 'y' },
        { label: 'Avg Spend ($)', data: avgSpend, type: 'line', borderColor: '#a78bfa', backgroundColor: '#a78bfa33', pointBackgroundColor: '#a78bfa', pointRadius: 5, tension: 0.3, yAxisID: 'y1' }
      ]
    },
    options: {
      responsive: true,
      scales: {
        y: { title: { display: true, text: 'Avg Prev Purchases' }, grid: { color: '#2a2d3a' } },
        y1: { position: 'right', title: { display: true, text: 'Avg Spend ($)' }, grid: { display: false } }
      },
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16 } } }
    }
  });
  const top = cats[0];
  document.getElementById('categoryInsight').innerHTML = '<strong>Key Insight:</strong> ' + top.category + ' has highest retention signal (avg ' + top.avg_prev_purchases + ' previous purchases) at $' + top.avg_spend + ' avg spend.';
}''')

# renderSegments
new_script_parts.append('''
function renderSegments(segments) {
  const tbody = document.querySelector('#segmentsTable tbody');
  tbody.innerHTML = segments.map(s => {
    const tierClass = s.loyalty_segment.includes('Organic') ? 'tier-platinum' : s.loyalty_segment.includes('Loyal') ? 'tier-gold' : s.loyalty_segment.includes('Occasional') ? 'tier-silver' : 'tier-bronze';
    const profile = s.loyalty_segment.includes('Organic') ? 'High loyalty, no promos' : s.loyalty_segment.includes('Loyal but') ? 'High value, needs promos' : s.loyalty_segment.includes('Occasional') ? 'Low loyalty, potential upsell' : 'Only buys with discounts';
    return '<tr><td><span class="tier-badge ' + tierClass + '">' + s.loyalty_segment + '</span></td><td>' + fmt(s.customer_count) + '</td><td>' + fmtD(s.total_revenue) + '</td><td>' + s.avg_loyalty + '</td><td>' + s.avg_promo_dep + '%</td><td style="font-size:0.8rem;color:#8b8fa3">' + profile + '</td></tr>';
  }).join('');
}''')

# Init block
new_script_parts.append('''
(function() {
  const data = _dashboardData;
  renderStats(data.summary);
  renderPyramid(data.pyramid);
  renderScatter(data.scatter);
  renderGeo(data.geo);
  renderCategory(data.category_funnel);
  renderSegments(data.loyalty_segments);
})();
</script>''')

new_script = '\n'.join(new_script_parts)
new_html = html[:script_start] + new_script + html[script_end:]

with open('03_dashboard/index_inline.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'Created: {len(new_html)} bytes, {new_html.count(chr(10))} lines')
print(f'Title count: {new_html.count("Customer Intelligence Dashboard")}')
