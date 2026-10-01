(function () {
  const $ = (sel) => document.querySelector(sel);

  const state = {
    stats: null,
    timer: null,
    polling: null,
    pie: null,
    line: null,
  };

  // 所有来自数据库的内容先转义再拼进 HTML，防止备注、姓名里藏 <script> 等代码（XSS）
  function esc(v){
    return String(v ?? '').replace(/[&<>"']/g, (c) => ({
      '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
    })[c]);
  }

  function pad(n){ return String(n).padStart(2,'0'); }
  function formatNow(){
    const d = new Date();
    const w = ['星期日','星期一','星期二','星期三','星期四','星期五','星期六'][d.getDay()];
    return `${d.getFullYear()}年${pad(d.getMonth()+1)}月${pad(d.getDate())}日 ${w} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function updateTime(){
    $('#nowTime').textContent = formatNow();
  }

  async function fetchStats(){
    const res = await fetch('/front/api/stats', { cache: 'no-store' });
    const json = await res.json();
    if (json && json.code === 200) return json.data;
    throw new Error(json?.msg || '获取统计数据失败');
  }

  function calcRate(present, total){
    if (!total) return 0;
    return Math.round((present / total) * 100);
  }

  function setCards(data){
    const total = data.total_students ?? 0;
    const ta = data.today_attendance || {};
    const present = ta.present ?? 0;
    const absent = ta.absent ?? 0;
    const late = ta.late ?? 0;
    const leave = ta.leave ?? 0;
    // 实到 = 正常 + 迟到；出勤率直接用后端算好的 today_rate，
    // 保证卡片和趋势图今天那个点是同一个数。
    const attended = ta.attended ?? (present + late);
    const rate = data.today_rate ?? calcRate(attended, total);

    $('#cTotal').textContent = total;
    $('#cPresent').textContent = attended;
    $('#cRate').textContent = Math.round(rate) + '%';
    $('#cLate').textContent = late;
    $('#cLeave').textContent = leave;
    $('#cAbsent').textContent = absent;
    $('#cUnreg').textContent = ta.unregistered ?? 0;

    // 标题里的班级名取自学生名册
    if (data.class_name) {
      $('#className').textContent = data.class_name;
      document.title = data.class_name + '考勤可视化大屏';
    }

    $('#lastUpdate').textContent = new Date().toLocaleTimeString();
  }

  // 每种状态固定颜色（原来用 ECharts 默认配色，"正常"反而是红色，容易误读）
  const COLORS = { '正常':'#3ad29f', '迟到':'#ffba38', '请假':'#46b4ff', '旷课':'#ff5a78', '未登记':'#6b7a93' };

  function last7Labels(){
    const labels = [];
    const d = new Date();
    for (let i=6; i>=0; i--){
      const x = new Date(d.getTime() - i*24*3600*1000);
      labels.push(`${pad(x.getMonth()+1)}/${pad(x.getDate())}`);
    }
    return labels;
  }

  function renderPie(data){
    const total = data.total_students ?? 0;
    const ta = data.today_attendance || {};
    const present = ta.present ?? 0;
    const absent = ta.absent ?? 0;
    const late = ta.late ?? 0;
    const leave = ta.leave ?? 0;
    const unreg = ta.unregistered ?? 0;
    const rate = data.today_rate ?? calcRate(present + late, total);

    const chart = state.pie || echarts.init($('#pieChart'));
    state.pie = chart;

    const seriesData = [
      { name:'正常', value: present },
      { name:'迟到', value: late },
      { name:'请假', value: leave },
      { name:'旷课', value: absent },
      { name:'未登记', value: unreg },
    ].map(d => ({
      ...d,
      itemStyle: { color: COLORS[d.name] },
      // 人数为 0 的扇区不画标签和引线
      label: { show: d.value > 0 },
      labelLine: { show: d.value > 0 },
    }));

    chart.setOption({
      tooltip: { trigger: 'item', formatter: (p) => `${p.name}：${p.value} 人（${p.percent}%）` },
      legend: { top: 10, left: 10, textStyle: { color: 'rgba(215,243,255,.85)' } },
      series: [{
        name: '班级考勤构成',
        type: 'pie',
        radius: ['58%','78%'],
        center: ['50%','58%'],
        avoidLabelOverlap: true,
        label: {
          // 人数为 0 的扇区不显示标签，避免 0% 标签挤在一起
          formatter: (p) => p.value ? `${p.name}\n${p.value}人` : '',
          color: 'rgba(215,243,255,.9)',
          fontWeight: 700
        },
        labelLine: { length: 10, length2: 12 },
        minShowLabelAngle: 1,
        data: seriesData
      }],
      graphic: [{
        type: 'text',
        left: 'center',
        top: '52%',
        style: {
          // 中心显示与顶部卡片相同口径的出勤率
          text: `出勤率\n${Math.round(rate)}%`,
          textAlign: 'center',
          fill: 'rgba(140,255,210,.95)',
          fontSize: 18,
          fontWeight: 800
        }
      }]
    }, true);
  }

  function renderLine(data){
    const chart = state.line || echarts.init($('#lineChart'));
    state.line = chart;

    const y = (data.weekly_rate || []).slice(-7);
    // 日期标签用后端给的，和数据同一个"今天"，避免浏览器与服务器日期不一致时错位
    const x = data.weekly_labels || last7Labels();

    chart.setOption({
      grid: { left: 44, right: 18, top: 30, bottom: 30 },
      tooltip: {
        trigger: 'axis',
        formatter: (ps) => {
          const p = ps[0];
          return `${p.axisValue}<br/>出勤率：${p.value == null ? '无记录' : p.value + '%'}`;
        }
      },
      xAxis: {
        type: 'category',
        data: x,
        axisLine: { lineStyle: { color: 'rgba(120,240,255,.25)' } },
        axisLabel: { color: 'rgba(215,243,255,.8)' }
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        interval: 20,
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(120,240,255,.10)' } },
        axisLabel: { color: 'rgba(215,243,255,.75)', formatter: '{value}%' }
      },
      series: [{
        name: '出勤率',
        type: 'line',
        smooth: false,          // 折线如实反映每天的值，不做平滑夸张
        connectNulls: false,    // 无记录的日子断开，不连成假趋势
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#58eaff' },
        lineStyle: { color: '#58eaff', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(88,234,255,.35)' }, { offset: 1, color: 'rgba(88,234,255,0)' }]) },
        label: { show: true, position: 'top', color: 'rgba(215,243,255,.85)',
                 formatter: (p) => p.value == null ? '' : Math.round(p.value) + '%' },
        data: y
      }]
    }, true);
  }

  function renderAbnormalList(data){
    const list = Array.isArray(data.abnormal_list) ? data.abnormal_list : [];
    const tbody = $('#abnormalBody');
    tbody.innerHTML = '';
    $('#abnCount').textContent = list.length ? `（${list.length} 人）` : '';
    if(list.length === 0){
      const tr = document.createElement('tr');
      tr.innerHTML = `<td colspan="4" style="text-align:center;opacity:.75;">今天全员正常 🎉</td>`;
      tbody.appendChild(tr);
      return;
    }
    list.forEach((r) => {
      const tr = document.createElement('tr');
      const t = r.type || r.status || '';
      const tagCls = { '迟到':'tag-late', '请假':'tag-leave', '未登记':'tag-unreg' }[t] || 'tag-absent';
      tr.innerHTML = `
        <td>${esc(r.name || r.student_name)}</td>
        <td><span class="row-tag ${tagCls}">${esc(t)}</span></td>
        <td>${esc(r.time || '--')}</td>
        <td>${esc(r.remark)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  async function refresh(){
    try{
      const data = await fetchStats();
      state.stats = data;
      setCards(data);
      renderPie(data);
      renderLine(data);
      renderAbnormalList(data);
    }catch(e){
      console.error(e);
      $('#lastUpdate').textContent = '获取失败';
    }
  }

  function start(){
    updateTime();
    state.timer = setInterval(updateTime, 1000);
    refresh();
        state.polling = setInterval(refresh, 30000);

    window.addEventListener('resize', () => {
      state.pie && state.pie.resize();
      state.line && state.line.resize();
    });
  }

  document.addEventListener('DOMContentLoaded', start);
})();
