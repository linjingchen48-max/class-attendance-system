(function () {
  const $ = (sel) => document.querySelector(sel);

  const state = {
    stats: null,
    timer: null,
    polling: null,
    pie: null,
    line: null,
  };

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
    const rate = calcRate(present, total);

    $('#cTotal').textContent = total;
    $('#cPresent').textContent = present;
    $('#cRate').textContent = rate + '%';
    $('#cLate').textContent = late;
    $('#cLeave').textContent = leave;
    $('#cAbsent').textContent = absent;

    $('#lastUpdate').textContent = new Date().toLocaleTimeString();
  }

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

    const chart = state.pie || echarts.init($('#pieChart'));
    state.pie = chart;

    const seriesData = [
      { name:'正常', value: present },
      { name:'迟到', value: late },
      { name:'请假', value: leave },
      { name:'旷课', value: absent },
    ];

    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { top: 10, left: 10, textStyle: { color: 'rgba(215,243,255,.85)' } },
      series: [{
        name: '班级考勤构成',
        type: 'pie',
        radius: ['58%','78%'],
        center: ['50%','58%'],
        avoidLabelOverlap: true,
        label: {
          formatter: (p) => `${p.name}\n${p.percent}%`,
          color: 'rgba(215,243,255,.9)',
          fontWeight: 700
        },
        labelLine: { length: 10, length2: 12 },
        data: seriesData
      }],
      graphic: [{
        type: 'text',
        left: 'center',
        top: '52%',
        style: {
          text: `正常\n${calcRate(present,total)}%`,
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
    const x = last7Labels();

    chart.setOption({
      grid: { left: 44, right: 18, top: 30, bottom: 30 },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: x,
        axisLine: { lineStyle: { color: 'rgba(120,240,255,.25)' } },
        axisLabel: { color: 'rgba(215,243,255,.8)' }
      },
      yAxis: {
        type: 'value',
        min: 80,
        max: 100,
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(120,240,255,.10)' } },
        axisLabel: { color: 'rgba(215,243,255,.75)', formatter: '{value}%' }
      },
      series: [{
        name: '出勤率',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        areaStyle: { opacity: 0.18 },
        data: y
      }]
    }, true);
  }

  function renderAbnormalList(data){
    const list = Array.isArray(data.abnormal_list) ? data.abnormal_list : [];
    const tbody = $('#abnormalBody');
    tbody.innerHTML = '';
    if(list.length === 0){
      const tr = document.createElement('tr');
      tr.innerHTML = `<td colspan="4" style="text-align:center;opacity:.75;">暂无异常记录</td>`;
      tbody.appendChild(tr);
      return;
    }
    list.forEach((r) => {
      const tr = document.createElement('tr');
      const t = r.type || r.status || '';
      const tagCls = t === '迟到' ? 'tag-late' : (t === '请假' ? 'tag-leave' : 'tag-absent');
      tr.innerHTML = `
        <td>${r.name || r.student_name || ''}</td>
        <td><span class="row-tag ${tagCls}">${t}</span></td>
        <td>${r.time || '--'}</td>
        <td>${r.remark || ''}</td>
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
