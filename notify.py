import os, re, requests, yfinance as yf, pandas as pd
from openai import OpenAI

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
ETF_FLOW_COLUMNS = ["IBIT","FBTC","BITB","ARKB","BTCO","EZBC","BRRR","HODL","BTCW","GBTC","BTC","TOTAL"]
ETF_PLACEHOLDERS = {"", "-", "—", "nan", "None", "null"}

def jtxt(url, timeout=20):
    s = requests.Session(); s.trust_env = False
    h = dict(HEADERS); h["Accept"] = "text/plain, text/markdown, */*"
    r = s.get(url, headers=h, timeout=timeout); r.raise_for_status(); return r.text

def jget(url, timeout=20):
    s = requests.Session(); s.trust_env = False
    r = s.get(url, headers=HEADERS, timeout=timeout); r.raise_for_status(); return r.json()

def pnum(x):
    if x is None or str(x).strip() in ETF_PLACEHOLDERS: return None
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip().replace("$","").replace("%","").replace(",","").replace("BTC","").strip()
    neg = s.startswith("(") and s.endswith(")"); s = s[1:-1] if neg else s
    mul = 1.0
    if s.endswith("T"): mul, s = 1e12, s[:-1]
    elif s.endswith("B"): mul, s = 1e9, s[:-1]
    elif s.endswith("M"): mul, s = 1e6, s[:-1]
    try:
        v = float(s) * mul
        return -v if neg else v
    except: return None

def mcap_fmt(v):
    if v is None: return "—"
    if v >= 1e12: return f"${v/1e12:.2f}T"
    if v >= 1e9: return f"${v/1e9:.1f}B"
    return f"${v/1e6:.1f}M"

def flow_fmt(v):
    n = pnum(v)
    if n is None: return "—"
    if abs(n) >= 1e6: n /= 1e6
    return f"{n:.1f}M $"

def parse_tv_cap(text):
    m = re.search(r"Market open\s+([0-9]+(?:\.[0-9]+)?)\s*([TBM])\s*R USD", text) or re.search(r"Market closed\s+([0-9]+(?:\.[0-9]+)?)\s*([TBM])\s*R USD", text)
    if not m: raise ValueError("tv cap not found")
    return float(m.group(1)) * {"T":1e12, "B":1e9, "M":1e6}[m.group(2)]

def latest_etf_row(text):
    rows = [l.strip() for l in text.splitlines() if re.match(r"^\|\s*\d{2}\s+[A-Za-z]{3}\s+\d{4}\s*\|", l.strip())]
    for row in reversed(rows):
        parts = [p.strip() for p in row.split("|")[1:-1]]
        if len(parts) < len(ETF_FLOW_COLUMNS) + 1: continue
        vals = parts[1:1 + len(ETF_FLOW_COLUMNS)]
        if sum(v not in ETF_PLACEHOLDERS for v in vals[:-1]) == 0: continue
        return parts[0], vals
    return None

def walls(bids, asks, noise=250, bucket=100):
    cur = bids[0][0]; md = cur * 0.08
    bids = [(p,q) for p,q in bids if 0 < p <= cur and (cur-p) <= md] or bids
    asks = [(p,q) for p,q in asks if p >= cur and (p-cur) <= md] or asks
    fb = [(p,q) for p,q in bids if p < cur-noise] or bids[len(bids)//2:]
    fa = [(p,q) for p,q in asks if p > cur+noise] or asks[len(asks)//2:]
    def bkt(levels, fn):
        d = {}
        for p,q in levels: d[fn(p)] = d.get(fn(p), 0.0) + q
        return max(d.items(), key=lambda x: x[1])
    sw, sv = bkt(fb, lambda p: int(p/bucket)*bucket)
    rw, rv = bkt(fa, lambda p: int((p/bucket)+1)*bucket)
    ds, dr = cur-sw, rw-cur
    status = "Dirence Yakin" if dr < ds else ("Destege Yakin" if ds < dr else "Kanal Ortasi")
    return {"current": cur, "sup": sw, "supv": sv, "res": rw, "resv": rv, "status": status}

def order_signal(v):
    ex = [("", "Kraken"), ("OKX_", "OKX"), ("KUCOIN_", "KuCoin"), ("GATE_", "Gate.io"), ("COINBASE_", "Coinbase")]
    sup = [name for pre, name in ex if "Dest" in v.get(f"{pre}Wall_Status","—")]
    res = [name for pre, name in ex if "Diren" in v.get(f"{pre}Wall_Status","—")]
    if len(sup) >= 2 and len(sup) > len(res): return "Ortak destek guclu"
    if len(res) >= 2 and len(res) > len(sup): return "Ortak direnc guclu"
    return "Seviyeler karisik"

def usdt_d():
    try:
        t = jtxt("https://r.jina.ai/http://www.tradingview.com/symbols/USDT.D/?exchange=CRYPTOCAP", 20)
        m = re.search(r"Market open\s+([0-9]+(?:\.[0-9]+)?)%R", t) or re.search(r"USDT\.D Market open\s+([0-9]+(?:\.[0-9]+)?)\sR%", t) or re.search(r"Market closed\s+([0-9]+(?:\.[0-9]+)?)%R", t)
        if not m: raise ValueError("tv usdt.d")
        return f"%{float(m.group(1)):.2f}", "TradingView"
    except:
        try:
            g = jget("https://api.coingecko.com/api/v3/global", 6)["data"]
            return f"%{g['market_cap_percentage']['usdt']:.2f}", "CoinGecko"
        except:
            try:
                cg = jget("https://api.coinpaprika.com/v1/global", 6); ur = jget("https://api.coinpaprika.com/v1/tickers/usdt-tether", 6)
                return f"%{ur['quotes']['USD']['market_cap']/cg['market_cap_usd']*100:.2f}", "Coinpaprika"
            except: return "—", "—"

def market_caps():
    try:
        urls = {
            "TOTAL": "https://r.jina.ai/http://www.tradingview.com/symbols/TOTAL/",
            "TOTAL2": "https://r.jina.ai/http://www.tradingview.com/symbols/TOTAL2/",
            "TOTAL3": "https://r.jina.ai/http://www.tradingview.com/symbols/TOTAL3/",
            "OTHERS": "https://r.jina.ai/http://www.tradingview.com/symbols/OTHERS/?exchange=CRYPTOCAP",
        }
        vals = {k: parse_tv_cap(jtxt(u, 20)) for k, u in urls.items()}
        return {**{f"{k}_CAP": mcap_fmt(v) for k, v in vals.items()}, **{f"{k}_CAP_NUM": v for k, v in vals.items()}, "TOTAL_CAP_SOURCE": "TradingView"}
    except:
        try:
            g = jget("https://api.coingecko.com/api/v3/global", 6)["data"]
            t = g["total_market_cap"]["usd"]; b = g["market_cap_percentage"].get("btc", 0); e = g["market_cap_percentage"].get("eth", 0)
            top10 = jget("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false", 8)
            o = max(t - sum(x.get("market_cap") or 0 for x in top10), 0); t2 = t*(1-b/100); t3 = t*(1-(b+e)/100)
            vals = {"TOTAL": t, "TOTAL2": t2, "TOTAL3": t3, "OTHERS": o}
            return {**{f"{k}_CAP": mcap_fmt(v) for k, v in vals.items()}, **{f"{k}_CAP_NUM": v for k, v in vals.items()}, "TOTAL_CAP_SOURCE": "CoinGecko fallback"}
        except:
            return {"TOTAL_CAP":"—","TOTAL2_CAP":"—","TOTAL3_CAP":"—","OTHERS_CAP":"—","TOTAL_CAP_NUM":None,"TOTAL2_CAP_NUM":None,"TOTAL3_CAP_NUM":None,"OTHERS_CAP_NUM":None,"TOTAL_CAP_SOURCE":"—"}

def veri_cek():
    v = {}; v.update(market_caps())
    for sym, cid in {"BTC":"btc-bitcoin","ETH":"eth-ethereum","SOL":"sol-solana","BNB":"bnb-binance-coin","XRP":"xrp-xrp","ADA":"ada-cardano","AVAX":"avax-avalanche","LINK":"link-chainlink","DOT":"dot-polkadot"}.items():
        try:
            q = jget(f"https://api.coinpaprika.com/v1/tickers/{cid}", 8)["quotes"]["USD"]
            v[f"{sym}_P"], v[f"{sym}_C"], v[f"{sym}_7D"] = f"${q['price']:,.2f}", f"{q['percent_change_24h']:.2f}%", f"{q['percent_change_7d']:.2f}%"
            if sym == "BTC": v["BTC_P"], v["Vol_24h"], v["MCap_BTC"] = f"${q['price']:,.0f}", f"${q['volume_24h']:,.0f}", f"${q['market_cap']/1e9:.1f}B"
        except: v[f"{sym}_P"], v[f"{sym}_C"], v[f"{sym}_7D"] = "—", "—", "—"
    try:
        g = jget("https://api.coinpaprika.com/v1/global", 6)
        v["Dom"], v["Total_MCap"], v["Total_Vol"] = f"%{g['bitcoin_dominance_percentage']:.2f}", f"${g['market_cap_usd']/1e12:.2f}T", f"${g['volume_24h_usd']/1e9:.1f}B"
    except: v["Dom"], v["Total_MCap"], v["Total_Vol"] = "—", "—", "—"
    try:
        eth = jget("https://api.coinpaprika.com/v1/tickers/eth-ethereum", 5); total = v.get("TOTAL_CAP_NUM")
        v["ETH_Dom"] = f"%{float(eth['quotes']['USD']['market_cap'])/total*100:.2f}" if total else "—"
    except: v["ETH_Dom"] = "—"
    for key, sym in {"SP500":"^GSPC","NASDAQ":"^IXIC","DAX":"^GDAXI","NIKKEI":"^N225","BIST100":"XU100.IS","VIX":"^VIX","DXY":"DX-Y.NYB","US10Y":"^TNX","GOLD":"GC=F","SILVER":"SI=F","OIL":"CL=F","NATGAS":"NG=F","USDTRY":"TRY=X","EURUSD":"EURUSD=X","USDJPY":"JPY=X"}.items():
        try:
            df = yf.Ticker(sym).history(period="5d"); c, p = df["Close"].iloc[-1], df["Close"].iloc[-2]
            v[key] = f"${c:,.2f}" if key in {"GOLD","SILVER","OIL","NATGAS"} else (f"{c:.4f}" if key in {"DXY","US10Y","USDTRY","EURUSD","USDJPY"} else f"{c:,.2f}")
            v[f"{key}_C"] = f"{(c-p)/p*100:.2f}%"
        except: v[key], v[f"{key}_C"] = "—", "—"
    for sym in ["IBIT","FBTC","BITB","ARKB","GBTC"]:
        try:
            df = yf.Ticker(sym).history(period="10d"); c, p = df["Close"].iloc[-1], df["Close"].iloc[-2]
            v[f"{sym}_P"], v[f"{sym}_C"] = f"${c:.2f}", f"{(c-p)/p*100:.2f}%"
        except: v[f"{sym}_P"], v[f"{sym}_C"] = "—", "—"
    for s in ETF_FLOW_COLUMNS: v[f"ETF_FLOW_{s}"] = "—"
    v["ETF_FLOW_DATE"], v["ETF_FLOW_SOURCE"] = "—", "—"
    for url in ["https://r.jina.ai/http://farside.co.uk/bitcoin-etf-flow-all-data/","https://r.jina.ai/http://farside.co.uk/btc/","https://farside.co.uk/bitcoin-etf-flow-all-data/"]:
        try:
            row = latest_etf_row(jtxt(url, 20))
            if not row: continue
            v["ETF_FLOW_DATE"] = row[0]; v["ETF_FLOW_SOURCE"] = "Farside"
            for sym, raw in zip(ETF_FLOW_COLUMNS, row[1]): v[f"ETF_FLOW_{sym}"] = flow_fmt(raw)
            break
        except: pass
    try:
        f = jget("https://api.alternative.me/fng/?limit=2", 5)["data"]; v["FNG"], v["FNG_PREV"] = f"{f[0]['value']} ({f[0]['value_classification']})", f"{f[1]['value']} ({f[1]['value_classification']})"
    except: v["FNG"], v["FNG_PREV"] = "—", "—"
    try:
        ob = jget("https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=500", 8); pk = list(ob["result"].keys())[0]
        lv = walls([(float(p),float(q)) for p,q,*_ in ob["result"][pk]["bids"]], [(float(p),float(q)) for p,q,*_ in ob["result"][pk]["asks"]])
        for k, val in {"Sup_Wall":f"${lv['sup']:,}","Sup_Vol":f"{lv['supv']:.1f} BTC" if lv['supv'] < 10 else f"{lv['supv']:.0f} BTC","Res_Wall":f"${lv['res']:,}","Res_Vol":f"{lv['resv']:.1f} BTC" if lv['resv'] < 10 else f"{lv['resv']:.0f} BTC","Wall_Status":lv["status"],"BTC_Now":f"${lv['current']:,.0f}"}.items(): v[k] = val
    except: v["Sup_Wall"], v["Sup_Vol"], v["Res_Wall"], v["Res_Vol"], v["Wall_Status"], v["BTC_Now"] = "—","—","—","—","—","—"
    for prefix, url, bg, ag in [
        ("OKX","https://www.okx.com/api/v5/market/books?instId=BTC-USDT&sz=400", lambda x: x["data"][0]["bids"], lambda x: x["data"][0]["asks"]),
        ("KUCOIN","https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol=BTC-USDT", lambda x: x["data"]["bids"], lambda x: x["data"]["asks"]),
        ("GATE","https://api.gateio.ws/api/v4/spot/order_book?currency_pair=BTC_USDT&limit=200&with_id=true", lambda x: x["bids"], lambda x: x["asks"]),
        ("COINBASE","https://api.exchange.coinbase.com/products/BTC-USD/book?level=2", lambda x: x["bids"], lambda x: x["asks"]),
    ]:
        try:
            x = jget(url, 8); lv = walls([(float(p),float(q)) for p,q,*_ in bg(x)], [(float(p),float(q)) for p,q,*_ in ag(x)])
            for k, val in {"Sup_Wall":f"${lv['sup']:,}","Sup_Vol":f"{lv['supv']:.1f} BTC" if lv['supv'] < 10 else f"{lv['supv']:.0f} BTC","Res_Wall":f"${lv['res']:,}","Res_Vol":f"{lv['resv']:.1f} BTC" if lv['resv'] < 10 else f"{lv['resv']:.0f} BTC","Wall_Status":lv["status"]}.items(): v[f"{prefix}_{k}"] = val
        except:
            for k in ["Sup_Wall","Sup_Vol","Res_Wall","Res_Vol","Wall_Status"]: v[f"{prefix}_{k}"] = "—"
    v["ORDERBOOK_SIGNAL"] = order_signal(v)
    try:
        fr = jget("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP", 6); v["FR"] = f"%{float(fr['data'][0]['fundingRate'])*100:.4f}"
    except: v["FR"] = "—"
    try:
        oi = jget("https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP", 6); v["OI"] = f"{float(oi['data'][0]['oi']):,.0f} BTC"
    except: v["OI"] = "—"
    try:
        tk = jget("https://www.okx.com/api/v5/rubik/stat/taker-volume?ccy=BTC&instType=contracts&period=1H", 6); bv, sv = float(tk["data"][0][1]), float(tk["data"][0][2]); v["Taker"] = f"{bv/sv:.3f}" if sv > 0 else "1.000"
    except: v["Taker"] = "1.000"
    ls_done = False
    for url in ["https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio-contract-top-trader?instId=BTC-USDT-SWAP&period=1H","https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&period=1H"]:
        if ls_done: break
        try:
            r = jget(url, 6); d = r.get("data", []); d0 = d[0] if d else None
            if not d0: continue
            if isinstance(d0, dict) and "longRatio" in d0: lp, sp = float(d0["longRatio"])*100, float(d0["shortRatio"])*100; ratio = lp/sp if sp > 0 else 1
            else: ratio = float(d0[1]) if isinstance(d0, list) else 1; lp, sp = ratio/(1+ratio)*100, 100-ratio/(1+ratio)*100
            v["LS_Ratio"], v["Long_Pct"], v["Short_Pct"], v["LS_Signal"] = f"{ratio:.3f}", f"%{lp:.1f}", f"%{sp:.1f}", ("Long Agirlikli" if ratio > 1 else "Short Agirlikli"); ls_done = True
        except: pass
    if not ls_done:
        try:
            g = jget("https://api.gateio.ws/api/v4/futures/usdt/contract_stats?contract=BTC_USDT&interval=1h&limit=1", 6); lp = float(g[0].get("lsr_taker",1)); lpp = lp/(1+lp)*100
            v["LS_Ratio"], v["Long_Pct"], v["Short_Pct"], v["LS_Signal"] = f"{lp:.3f}", f"%{lpp:.1f}", f"%{100-lpp:.1f}", ("Long Agirlikli" if lp > 1 else "Short Agirlikli"); ls_done = True
        except: pass
    if not ls_done: v["LS_Ratio"], v["Long_Pct"], v["Short_Pct"], v["LS_Signal"] = "—","—","—","—"
    try:
        sc = jget("https://stablecoins.llama.fi/stablecoins?includePrices=true", 8)["peggedAssets"]; total = sum(c.get("circulating",{}).get("peggedUSD",0) for c in sc)
        def cap(sym):
            c = next((x for x in sc if x["symbol"].upper()==sym), None); return c["circulating"]["peggedUSD"] if c else 0
        usdt, usdc, dai = cap("USDT"), cap("USDC"), cap("DAI")
        v["Total_Stable_Num"], v["Total_Stable"], v["USDT_MCap"], v["USDC_MCap"], v["DAI_MCap"] = total, f"${total/1e9:.1f}B", f"${usdt/1e9:.1f}B", f"${usdc/1e9:.1f}B", f"${dai/1e9:.1f}B"
        v["USDT_Dom_Stable"], v["STABLE_C_D"] = (f"%{usdt/total*100:.1f}" if total > 0 else "—"), (f"%{total/v['TOTAL_CAP_NUM']*100:.2f}" if v.get("TOTAL_CAP_NUM") else "—")
    except: v["Total_Stable"], v["USDT_MCap"], v["USDC_MCap"], v["DAI_MCap"], v["USDT_Dom_Stable"], v["STABLE_C_D"] = "—","—","—","—","—","—"
    v["USDT_D"], v["USDT_D_SOURCE"] = usdt_d()
    try:
        cd = yf.download(["BTC-USD","^GSPC","GC=F"], period="30d", progress=False)["Close"]; cm = cd.corr(); v["Corr_SP500"], v["Corr_Gold"] = f"{cm.loc['BTC-USD','^GSPC']:.2f}", f"{cm.loc['BTC-USD','GC=F']:.2f}"
    except: v["Corr_SP500"], v["Corr_Gold"] = "—", "—"
    try:
        s = jget("https://api.blockchain.info/stats", 5); v["Hash"], v["BTC_Active"] = f"{s['hash_rate']/1e9:.2f} EH/s", f"{s['n_blocks_mined']*2100:,}"
    except: v["Hash"], v["BTC_Active"] = "—", "—"
    try:
        m2 = jget(f"https://api.stlouisfed.org/fred/series/observations?series_id=M2SL&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=13", 6)["observations"]; v["M2"] = f"%{(float(m2[0]['value'])-float(m2[12]['value']))/float(m2[12]['value'])*100:.2f}"
    except: v["M2"] = "—"
    try:
        fed = jget(f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1", 6)["observations"]; v["FED"] = f"%{fed[0]['value']}"
    except: v["FED"] = "—"
    return v

def takvim_cek():
    try:
        rss = jtxt("https://tradingeconomics.com/rss/calendar.aspx", 8)
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", rss)[1:15]
        kritik = [t for t in titles if any(k in t for k in ["USD","EUR","Fed","CPI","NFP","GDP","PMI","FOMC","Powell","Interest Rate","Inflation"])]
        return kritik[:5] if kritik else titles[:4]
    except:
        try:
            rss = jtxt("https://nfs.faireconomy.media/ff_calendar_thisweek.xml", 8)
            titles = re.findall(r"<title>(.*?)</title>", rss)[1:10]
            return titles[:5] if titles else ["Takvim verisi simdilik alinamadi."]
        except:
            return ["Takvim verisi simdilik alinamadi."]

def haber_cek():
    try:
        rss = jtxt("https://www.coindesk.com/arc/outboundfeeds/rss/", 8)
        return re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", rss)[1:6]
    except:
        try:
            data = jget("https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest&limit=5", 8)
            return [item["title"] for item in data.get("Data", [])[:5]]
        except:
            return []

def ai_raporu(v, takvim, haberler):
    bugun = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d %B %Y, %A")
    takvim_str = "\n".join(f"- {x}" for x in takvim) if takvim else "- Veri yok"
    haber_str = "\n".join(f"- {x}" for x in haberler) if haberler else "- Haber yok"
    prompt = f"""
Sen SA Finance Alpha Terminal icin sabah bulteni yazan Sen 20 yıllık deneyime sahip bir makro-kripto fon yöneticisi ve quant analistsin.
Turkce, profesyonel, rakamsal bir bulten yaz. Her iddiayi sayi ile destekle. Derinlikli, rakamsal ve eyleme dönüşebilir bir bülten yaz.
Asagidaki basliklari aynen kullan ve hicbirini atlama.

TARIH: {bugun}
BTC: {v.get('BTC_P','—')} | 24s {v.get('BTC_C','—')} | 7g {v.get('BTC_7D','—')} | Hacim {v.get('Vol_24h','—')}
DOMINANCE: BTC {v.get('Dom','—')} | ETH {v.get('ETH_Dom','—')}
MARKET CAP BREADTH: TOTAL {v.get('TOTAL_CAP','—')} | TOTAL2 {v.get('TOTAL2_CAP','—')} | Kaynak {v.get('TOTAL_CAP_SOURCE','—')}
TANIMLAR: TOTAL = toplam kripto piyasa degeri. TOTAL2 = BTC haric toplam piyasa degeri.
ETF: Tarih {v.get('ETF_FLOW_DATE','—')} | Toplam {v.get('ETF_FLOW_TOTAL','—')} | IBIT {v.get('ETF_FLOW_IBIT','—')} | FBTC {v.get('ETF_FLOW_FBTC','—')} | GBTC {v.get('ETF_FLOW_GBTC','—')}
STABLECOINS: Toplam {v.get('Total_Stable','—')} | Stable.C.D {v.get('STABLE_C_D','—')} | USDT.D {v.get('USDT_D','—')} | USDT kaynak {v.get('USDT_D_SOURCE','—')} | USDT stable dominance {v.get('USDT_Dom_Stable','—')}
STABLE TANIMLARI: Stable.C.D = toplam stablecoin market cap / toplam kripto market cap. USDT.D = USDT market cap / toplam kripto market cap. USDT stable dominance = USDT market cap / toplam stablecoin market cap.
ORDER BOOK: {v.get('ORDERBOOK_SIGNAL','—')} | Kraken {v.get('Sup_Wall','—')} / {v.get('Res_Wall','—')} | OKX {v.get('OKX_Sup_Wall','—')} / {v.get('OKX_Res_Wall','—')} | KuCoin {v.get('KUCOIN_Sup_Wall','—')} / {v.get('KUCOIN_Res_Wall','—')} | Gate.io {v.get('GATE_Sup_Wall','—')} / {v.get('GATE_Res_Wall','—')} | Coinbase {v.get('COINBASE_Sup_Wall','—')} / {v.get('COINBASE_Res_Wall','—')}
TUREV: OI {v.get('OI','—')} | Funding {v.get('FR','—')} | Taker {v.get('Taker','—')} | L/S {v.get('LS_Ratio','—')} ({v.get('LS_Signal','—')})
MAKRO: FED {v.get('FED','—')} | M2 son 12 ay degisimi {v.get('M2','—')} | US10Y {v.get('US10Y','—')} ({v.get('US10Y_C','—')}) | DXY {v.get('DXY','—')} ({v.get('DXY_C','—')}) | VIX {v.get('VIX','—')} ({v.get('VIX_C','—')})
ENDEKSLER: SP500 {v.get('SP500','—')} ({v.get('SP500_C','—')}) | NASDAQ {v.get('NASDAQ','—')} ({v.get('NASDAQ_C','—')}) | DAX {v.get('DAX','—')} ({v.get('DAX_C','—')}) | NIKKEI {v.get('NIKKEI','—')} ({v.get('NIKKEI_C','—')})
FOREX: EURUSD {v.get('EURUSD','—')} ({v.get('EURUSD_C','—')}) | USDJPY {v.get('USDJPY','—')} ({v.get('USDJPY_C','—')}) | USDTRY {v.get('USDTRY','—')} ({v.get('USDTRY_C','—')})
EMTIALAR: GOLD {v.get('GOLD','—')} ({v.get('GOLD_C','—')}) | SILVER {v.get('SILVER','—')} ({v.get('SILVER_C','—')}) | OIL {v.get('OIL','—')} ({v.get('OIL_C','—')}) | NATGAS {v.get('NATGAS','—')} ({v.get('NATGAS_C','—')})
ONCHAIN: Hash {v.get('Hash','—')} | Active {v.get('BTC_Active','—')} | Corr SP500 {v.get('Corr_SP500','—')} | Corr Gold {v.get('Corr_Gold','—')}
ALTCOIN_7G: ETH {v.get('ETH_7D','—')} | SOL {v.get('SOL_7D','—')} | BNB {v.get('BNB_7D','—')} | XRP {v.get('XRP_7D','—')} | ADA {v.get('ADA_7D','—')} | AVAX {v.get('AVAX_7D','—')} | LINK {v.get('LINK_7D','—')} | DOT {v.get('DOT_7D','—')}
ALTCOIN_24S: ETH {v.get('ETH_C','—')} | SOL {v.get('SOL_C','—')} | BNB {v.get('BNB_C','—')} | XRP {v.get('XRP_C','—')} | ADA {v.get('ADA_C','—')} | AVAX {v.get('AVAX_C','—')} | LINK {v.get('LINK_C','—')} | DOT {v.get('DOT_C','—')}
TAKVIM:
{takvim_str}
HABERLER:
{haber_str}

ZORUNLU KURALLAR:
- Tam olarak asagidaki 7 basligi kullan.
- Her baslik altinda en az 2 cumle olsun.
- 5. bolum, TAKVIM listesinden en az bir maddeyi anip olasi piyasa etkisini yorumlasin.
- 6. bolum, HABERLER listesinden en az bir maddeyi anip BTC/kripto etkisini yorumlasin.
- Eger takvim veya haber verisi zayifsa bunu acikca belirt ama yine de o bolumu yaz.
- Long, short ve bekle senaryolarinda net seviye ve kosul ver.
- Zaman ufuklarini karistirma: 7 gunluk kiyas sadece 7g verilerle yapilsin; 24 saatlik momentum yorumu sadece 24s verilerle yapilsin.
- Altcoin relatif guc analizinde BTC ile altcoinleri ayni periyotta karsilastir. BTC 7g kullaniliyorsa ETH/SOL/BNB/XRP/ADA/AVAX/LINK/DOT icin de 7g verileri kullan.
- Eger 24s ile 7g farkli hikaye anlatiyorsa bunu acikca ayir: once 7g trendi, sonra 24s kisa vadeli momentum.
- Haftalik altcoin yorumu yazarken yalnizca ALTCOIN_7G satirini kullan. ALTCOIN_24S satiri haftalik sonuc cikarmak icin kullanilamaz.
- 7 gunluk relatif guc cumlesinde ETH/SOL/BNB/XRP/ADA/AVAX/LINK/DOT icin yazilan her yuzde mutlaka ilgili 7g veri satirindaki sayiyla ayni olmali.
- VIX ve M2 icin haftalik, onceki hafta, degisim hizi veya yuzdesel periyot farki uydurma. Elinde sadece mevcut seviye varsa yalnizca mevcut seviyeyi yorumla.
- VIX icin sadece mevcut seviye ve varsa gunluk degisim; M2 icin sadece verilen "M2 son 12 ay degisimi" degeri kullanilabilir. M2'yi gunluk, haftalik veya aylik yeni degisim gibi yazma; acikca 12 aylik para arzi degisimi olarak anlat.
- Market Cap Breadth yorumunda sadece TOTAL ve TOTAL2 kullan. TOTAL3 ve OTHERS'i raporda anma.
- Her iddiayı mutlaka rakamla destekle. "VIX yüksek" değil, "VIX {v['VIX']} ({v.get('VIX_C','—')}) seviyesinde" yaz.
- Tüm veri kategorilerini mutlaka kullan.

- Makro bolumde yalnizca terminalde gunluk degisimi olan metriklerde gunluk yuzde degisimi kullan: US10Y_C, DXY_C, VIX_C, SP500_C, NASDAQ_C, DAX_C, NIKKEI_C, EURUSD_C, USDJPY_C, USDTRY_C, GOLD_C, SILVER_C, OIL_C, NATGAS_C.
- FED ve M2 icin gunluk degisim verme; bu iki metrikte sadece mevcut seviye yorumlanabilir.
- Makro Ortam ve Risk Istahi bolumunde GOLD ve OIL icin en az birer ayri cumle yorum zorunlu.
- Emtia yorumunda altini guvenli liman ve enflasyon, petrolu buyume, enflasyon ve jeopolitik risk cercevesinde degerlendir.
- 4. bolumde altcoinlerin genel durumunu anlatan ayri bir paragraf yaz. Bu paragraf once BTC 7g ile ALTCOIN_7G verilerini ayni periyotta karsilastirsin, sonra ALTCOIN_24S verileriyle kisa vadeli toparlanma veya zayifligi ayri bir cumlede anlatsin.
- Altcoin paragrafinda "genel durum" sonucu net olsun: haftalik bazda BTC'ye gore goreceli guc mu zayiflik mi var, 24 saatlik bazda senkron toparlanma mi ayrisma mi var bunu acikca soyle.

KULLANILACAK BASLIKLAR:
1. SA Finance Alpha Terminal Sabah Bulteni
2. Makro Ortam ve Risk Istahi
3. BTC, Turev ve Order Book Analizi
4. ETF, Stablecoin ve Market Cap Breadth
5. Ekonomik Takvim ve Olasi Etkiler
6. Onemli Haberler ve Piyasa Yorumu
7. Long / Short / Bekle ve Kritik Risk
"""
    resp = client.chat.completions.create(model="google/gemini-2.5-flash", messages=[{"role":"user","content":prompt}], max_tokens=8000)
    return resp.choices[0].message.content

def telegram_gonder(mesaj):
    parts = []
    remaining = mesaj.strip()
    limit = 3600
    while remaining:
        if len(remaining) <= limit:
            parts.append(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, limit)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        parts.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    for part in parts:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id":TELEGRAM_CHAT_ID,"text":part,"parse_mode":"Markdown"}, timeout=10)
        if not r.ok:
            r2 = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id":TELEGRAM_CHAT_ID,"text":part}, timeout=10)
            if not r2.ok: raise RuntimeError(r2.text)

if __name__ == "__main__":
    print("Veriler cekiliyor..."); v = veri_cek()
    print("Takvim ve haberler cekiliyor..."); takvim, haberler = takvim_cek(), haber_cek()
    print("AI raporu olusturuluyor..."); rapor = ai_raporu(v, takvim, haberler)
    print("Telegram'a gonderiliyor..."); telegram_gonder(rapor)
