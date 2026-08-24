/* Deep-link bridge for /company.html?symbol=XXXX. Keeps company research usable even when generated stock pages are stale. */
(function(){
  const params=new URLSearchParams(location.search);
  const symbol=(params.get('symbol')||'').trim().toUpperCase();
  if(!symbol)return;
  function openFromLoadedData(){
    const input=document.querySelector('#q');
    if(!input)return;
    input.value=symbol;
    input.dispatchEvent(new Event('input',{bubbles:true}));
    setTimeout(function(){
      const button=document.querySelector(`[data-symbol="${CSS.escape(symbol)}"]`);
      if(button)button.click();
      else input.value=symbol;
    },80);
  }
  document.addEventListener('nepse-data-ready',openFromLoadedData,{once:true});
  window.addEventListener('load',function(){setTimeout(openFromLoadedData,900);},{once:true});
})();
