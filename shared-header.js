(function(){
  'use strict';
  const here=location.pathname.split('/').filter(Boolean);
  const i=here.indexOf('nepse');
  const rest=i>=0?here.slice(i+1):[];
  const depth=rest.length?Math.max(0,rest.length-1):0;
  const root='../'.repeat(depth)||'./';
  const isStock=rest[0]==='stock';
  const isNews=rest[0]==='news';
  const isIPO=rest[0]==='ipos';
  const isDashboard=!isStock&&!isNews&&!isIPO;
  const old=document.querySelector('.topbar,.terminal-nav');
  if(!old)return;

  const searchId=isStock?'search':'globalSearch';
  const searchPlaceholder=isStock?'Search company or symbol…':'Search company or symbol…';
  const header=document.createElement('header');
  header.className='topbar shared-topbar';
  header.innerHTML=`
    <a class="brand" href="${root}">
      <span class="brand-mark">N</span>
      <span><strong>NEPSE <b>Pulse</b></strong><small>नेपाल शेयर बजार</small></span>
    </a>
    <nav class="primary-nav shared-nav">
      <a class="${isDashboard?'active':''}" href="${root}">Dashboard</a>
      <a href="${root}#nepse-chart">NEPSE</a>
      <a href="${root}#activity">Market</a>
      <a href="${root}#sectors">Sectors</a>
      <a class="${isStock?'active':''}" href="${root}#stocks">Stocks</a>
      <a class="${isNews?'active':''}" href="${root}news/">News</a>
      <a class="${isIPO?'active':''}" href="${root}ipos/">IPO</a>
    </nav>
    <div class="top-actions shared-actions">
      <div class="nav-search shared-search">
        <span>⌕</span><input id="${searchId}" autocomplete="off" placeholder="${searchPlaceholder}"><kbd>⌘K</kbd>
        ${isStock?'<div id="suggestions"></div>':''}
      </div>
      ${isStock?'<span id="clock" class="status shared-clock">Market</span>':''}
      ${isDashboard?'<span id="marketStatus" class="status"><i></i> Loading</span><button id="refreshBtn" class="icon-btn" title="Refresh data">↻</button><button id="themeBtn" class="icon-btn" title="Theme">◐</button>':''}
    </div>
    <nav class="mobile-nav shared-mobile-nav">
      <a class="${isDashboard?'active':''}" href="${root}">Dashboard</a>
      <a href="${root}#nepse-chart">NEPSE</a>
      <a href="${root}#activity">Market</a>
      <a href="${root}#sectors">Sectors</a>
      <a class="${isStock?'active':''}" href="${root}#stocks">Stocks</a>
      <a class="${isNews?'active':''}" href="${root}news/">News</a>
      <a class="${isIPO?'active':''}" href="${root}ipos/">IPO</a>
    </nav>`;
  old.replaceWith(header);

  // Preserve the existing theme/keyboard behaviour while making navigation consistent.
  document.addEventListener('keydown',function(e){
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){
      e.preventDefault();const el=document.getElementById(searchId);if(el){el.focus();el.select();}
    }
  });
  const style=document.createElement('link');
  style.rel='stylesheet';style.href=root+'shared-header.css';document.head.appendChild(style);
})();
