const express=require('express');
const axios=require('axios');
const cheerio=require('cheerio');
const cors=require('cors');
const fs=require('fs');
const path=require('path');

const app=express();
app.use(cors());
app.use(express.json({limit:'1mb'}));

const ROOT=path.resolve(__dirname,'..');
const DATA=path.join(ROOT,'data');

function readJson(file,fallback=null){
  try{return JSON.parse(fs.readFileSync(path.join(DATA,file),'utf8'));}
  catch{return fallback;}
}
function unwrap(payload){
  if(payload&&typeof payload.content==='string'){
    try{return JSON.parse(payload.content);}catch{}
  }
  return payload;
}
function rows(payload){
  payload=unwrap(payload);
  if(Array.isArray(payload))return payload;
  if(payload&&typeof payload==='object'){
    for(const key of ['stocks','data','items','rows','companies']) if(Array.isArray(payload[key])) return payload[key];
  }
  return [];
}
function symbolOf(s){return String(s?.symbol||s?.ticker||s?.securitySymbol||'').trim().toUpperCase();}
function nameOf(s){return s?.name||s?.companyName||s?.company||s?.securityName||symbolOf(s);}
function numberOf(v){const n=Number(v);return Number.isFinite(n)?n:0;}
function localStocks(){
  const payload=readJson('live.json',{stocks:[]});
  return rows(payload).map(s=>({...s,symbol:symbolOf(s),name:nameOf(s)})).filter(s=>s.symbol);
}
function companyIndex(){return unwrap(readJson('companies.json',{companies:{}}))?.companies||{};}
function stockHistory(symbol){
  const wanted=String(symbol||'').toUpperCase();
  const manifest=unwrap(readJson('history/manifest.json',{months:[]}));
  const months=Array.isArray(manifest?.months)?manifest.months:[];
  const points=[];
  for(const month of months){
    const file=String(month?.file||'').replace(/^\//,'');
    if(!file)continue;
    const payload=unwrap(readJson(file,null));
    if(!payload||!Array.isArray(payload.dates)||!payload.series||!Array.isArray(payload.series[wanted]))continue;
    for(const row of payload.series[wanted]){
      if(!Array.isArray(row)||row.length<2)continue;
      const index=Number(row[0]);
      const ltp=numberOf(row[1]);
      if(!Number.isInteger(index)||index<0||index>=payload.dates.length||ltp<=0)continue;
      points.push({
        timestamp:`${payload.dates[index]}T15:00:00+05:45`,
        date:payload.dates[index],
        ltp,
        volume:numberOf(row[2]),
        turnover:numberOf(row[3]),
        transactions:numberOf(row[4])
      });
    }
  }
  const todayFile=path.join(DATA,'intraday',`${new Date().toISOString().slice(0,10)}.json`);
  const todayRaw=(()=>{try{return JSON.parse(fs.readFileSync(todayFile,'utf8'))}catch{return null}})();
  const snapshots=Array.isArray(todayRaw?.snapshots)?todayRaw.snapshots:Array.isArray(todayRaw)?todayRaw:[];
  for(const p of snapshots){
    const list=rows(p);const s=list.find(x=>symbolOf(x)===wanted);if(!s)continue;
    const ltp=numberOf(s.ltp??s.lastTradedPrice??s.lastPrice);if(ltp<=0)continue;
    points.push({timestamp:p.timestamp||p.time||p.updatedAt||null,ltp,change:numberOf(s.change??s.pointChange),volume:numberOf(s.volume??s.totalTradedQuantity),turnover:numberOf(s.turnover??s.totalTradedValue),transactions:numberOf(s.transactions??s.transactionCount)});
  }
  const seen=new Set();
  return points.filter(p=>{const key=`${p.timestamp}|${p.ltp}|${p.volume}`;if(seen.has(key))return false;seen.add(key);return true;}).sort((a,b)=>String(a.timestamp||'').localeCompare(String(b.timestamp||'')));
}

app.get('/health',(req,res)=>res.json({ok:true,service:'nepse-api',version:'2.2'}));

app.get('/api/stocks',(req,res)=>{
  let stocks=localStocks();
  const q=String(req.query.q||'').trim().toUpperCase();
  const movement=String(req.query.movement||'all');
  const sort=String(req.query.sort||'symbol');
  const sector=String(req.query.sector||'').trim().toUpperCase();
  const limit=Math.min(Math.max(Number(req.query.limit)||500,1),1000);
  if(q) stocks=stocks.filter(s=>symbolOf(s).includes(q)||nameOf(s).toUpperCase().includes(q));
  if(sector) stocks=stocks.filter(s=>String(s.sector||s.sectorName||'OTHER').toUpperCase()===sector);
  if(movement==='gainers')stocks=stocks.filter(s=>numberOf(s.change??s.pointChange)>0);
  if(movement==='losers')stocks=stocks.filter(s=>numberOf(s.change??s.pointChange)<0);
  if(movement==='unchanged')stocks=stocks.filter(s=>numberOf(s.change??s.pointChange)===0);
  const value=s=>sort==='turnover'?numberOf(s.turnover??s.totalTradedValue):sort==='change'?numberOf(s.percent_change??s.percentChange??s.perChange):sort==='ltp'?numberOf(s.ltp??s.lastTradedPrice??s.lastPrice):sort==='volume'?numberOf(s.volume??s.totalTradedQuantity):symbolOf(s);
  stocks.sort((a,b)=>typeof value(a)==='string'?value(a).localeCompare(value(b)):value(b)-value(a));
  res.set('Cache-Control','public,max-age=30').json({updatedAt:unwrap(readJson('live.json',{}))?.updatedAt||null,count:stocks.length,stocks:stocks.slice(0,limit)});
});

app.get('/api/stocks/:symbol',(req,res)=>{
  const symbol=String(req.params.symbol||'').toUpperCase();
  const stock=localStocks().find(s=>symbolOf(s)===symbol);
  if(!stock)return res.status(404).json({error:'Stock not found',symbol});
  const companies=companyIndex();
  const c=companies[symbol]||{};
  res.json({symbol,name:nameOf(stock),stock,profile:c.profile||{},financials:c.financials||{},history:stockHistory(symbol)});
});

app.get('/api/stocks/:symbol/history',(req,res)=>{
  const symbol=String(req.params.symbol||'').toUpperCase();
  if(!localStocks().some(s=>symbolOf(s)===symbol))return res.status(404).json({error:'Stock not found',symbol});
  const points=stockHistory(symbol);
  res.json({symbol,count:points.length,source:'local-history-shards',points});
});

app.get('/api/search',(req,res)=>{
  const q=String(req.query.q||'').trim().toUpperCase();
  if(!q)return res.json({results:[]});
  res.json({results:localStocks().filter(s=>symbolOf(s).includes(q)||nameOf(s).toUpperCase().includes(q)).slice(0,20).map(s=>({symbol:symbolOf(s),name:nameOf(s),ltp:numberOf(s.ltp??s.lastTradedPrice??s.lastPrice),change:numberOf(s.change??s.pointChange),percentChange:numberOf(s.percent_change??s.percentChange??s.perChange)}))});
});

app.get('/api/sectors',(req,res)=>res.json(unwrap(readJson('sectors.json',{sectors:[]}))));
app.get('/api/sectors/:sector',(req,res)=>{
  const wanted=String(req.params.sector||'').toUpperCase();
  const stocks=localStocks().filter(s=>String(s.sector||s.sectorName||'OTHER').toUpperCase()===wanted);
  if(!stocks.length)return res.status(404).json({error:'Sector not found',sector:req.params.sector});
  const adv=stocks.filter(s=>numberOf(s.change??s.pointChange)>0).length;
  const dec=stocks.filter(s=>numberOf(s.change??s.pointChange)<0).length;
  const turnover=stocks.reduce((n,s)=>n+numberOf(s.turnover??s.totalTradedValue),0);
  res.json({sector:req.params.sector,count:stocks.length,advancing:adv,declining:dec,unchanged:stocks.length-adv-dec,turnover,stocks});
});
app.get('/api/index-history',(req,res)=>res.json(unwrap(readJson('index-history.json',{index:'NEPSE',points:[]}))));

app.get('/stocks',async(req,res)=>{
  const local=localStocks();
  if(local.length)return res.json(local);
  try{
    const {data}=await axios.get('https://merolagani.com/LatestMarket.aspx',{headers:{'User-Agent':'Mozilla/5.0'},timeout:15000});
    const $=cheerio.load(data),stocks=[];
    $('#ctl00_ContentPlaceHolder1_divLatestMarket table tr').each((i,row)=>{
      const c=$(row).find('td');
      if(c.length>10){
        const symbol=$(c[0]).find('a').text().trim()||$(c[0]).text().trim();
        const name=$(c[0]).text().trim();
        const ltp=parseFloat($(c[2]).text().replace(/,/g,''));
        const change=parseFloat($(c[4]).text().replace(/,/g,''));
        const volume=parseInt($(c[10]).text().replace(/,/g,''),10);
        if(Number.isFinite(ltp)&&Number.isFinite(change))stocks.push({symbol,name,ltp,change,percentChange:ltp-change?change/(ltp-change)*100:0,volume,turnover:ltp*volume});
      }
    });
    res.set('Cache-Control','public,max-age=30').json(stocks);
  }catch(err){
    console.error(err.message);
    res.status(502).json({error:'Failed to fetch NEPSE market data'});
  }
});

const PORT=process.env.PORT||3000;
app.listen(PORT,()=>console.log(`NEPSE API listening on ${PORT}`));
