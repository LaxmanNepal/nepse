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
function rows(payload){
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
  let stocks=rows(payload);
  // Some historical builds stored the full payload as a JSON string in `content`.
  if(!stocks.length&&typeof payload?.content==='string'){
    try{stocks=rows(JSON.parse(payload.content));}catch{}
  }
  return stocks.map(s=>({...s,symbol:symbolOf(s),name:nameOf(s)})).filter(s=>s.symbol);
}
function companyIndex(){return readJson('companies.json',{companies:{}})?.companies||{};}

app.get('/health',(req,res)=>res.json({ok:true,service:'nepse-api',version:'2.0'}));

// Local, reproducible dataset endpoints. These are preferred by the website because
// they do not depend on a third-party page being available at request time.
app.get('/api/stocks',(req,res)=>{
  let stocks=localStocks();
  const q=String(req.query.q||'').trim().toUpperCase();
  const movement=String(req.query.movement||'all');
  const sort=String(req.query.sort||'symbol');
  const limit=Math.min(Math.max(Number(req.query.limit)||500,1),1000);
  if(q) stocks=stocks.filter(s=>symbolOf(s).includes(q)||nameOf(s).toUpperCase().includes(q));
  if(movement==='gainers')stocks=stocks.filter(s=>numberOf(s.change??s.pointChange)>0);
  if(movement==='losers')stocks=stocks.filter(s=>numberOf(s.change??s.pointChange)<0);
  if(movement==='unchanged')stocks=stocks.filter(s=>numberOf(s.change??s.pointChange)===0);
  const value=s=>sort==='turnover'?numberOf(s.turnover??s.totalTradedValue):sort==='change'?numberOf(s.percent_change??s.percentChange??s.perChange):sort==='ltp'?numberOf(s.ltp??s.lastTradedPrice??s.lastPrice):sort==='volume'?numberOf(s.volume??s.totalTradedQuantity):symbolOf(s);
  stocks.sort((a,b)=>typeof value(a)==='string'?value(a).localeCompare(value(b)):value(b)-value(a));
  res.set('Cache-Control','public,max-age=30').json({updatedAt:readJson('live.json',{})?.updatedAt||null,count:stocks.length,stocks:stocks.slice(0,limit)});
});

app.get('/api/stocks/:symbol',(req,res)=>{
  const symbol=String(req.params.symbol||'').toUpperCase();
  const stock=localStocks().find(s=>symbolOf(s)===symbol);
  if(!stock)return res.status(404).json({error:'Stock not found',symbol});
  const companies=companyIndex();
  const c=companies[symbol]||{};
  res.json({symbol,name:nameOf(stock),stock,profile:c.profile||{},financials:c.financials||{}});
});

app.get('/api/search',(req,res)=>{
  const q=String(req.query.q||'').trim().toUpperCase();
  if(!q)return res.json({results:[]});
  res.json({results:localStocks().filter(s=>symbolOf(s).includes(q)||nameOf(s).toUpperCase().includes(q)).slice(0,20).map(s=>({symbol:symbolOf(s),name:nameOf(s),ltp:numberOf(s.ltp??s.lastTradedPrice??s.lastPrice),change:numberOf(s.change??s.pointChange),percentChange:numberOf(s.percent_change??s.percentChange??s.perChange)}))});
});

app.get('/api/sectors',(req,res)=>res.json(readJson('sectors.json',{sectors:[]})));
app.get('/api/index-history',(req,res)=>res.json(readJson('index-history.json',{index:'NEPSE',points:[]})));

// Compatibility endpoint: live scrape fallback for deployments that have no local data yet.
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
