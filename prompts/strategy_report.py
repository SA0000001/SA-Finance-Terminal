import pandas as pd


def build_strategy_report_prompt(data):
    bugun = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d %B %Y, %A — %H:%M")
    news_str = "\n".join(f"• {item['title']} ({item['source']})" for item in data.get("NEWS", [])[:6])

    return f"""Sen 20 yıllık deneyime sahip bir makro-kripto fon yöneticisi ve quant analistsin.
Aşağıdaki TÜM gerçek piyasa verilerini kullanarak Serhat için derinlikli, rakamsal ve eyleme dönüşebilir bir strateji raporu yaz.
Türkçe yaz. Rapor profesyonel, yapılandırılmış ve her iddia rakamla desteklenmiş olmalı.

TEMEL KURALLAR:
- Her iddiayı mutlaka rakamla destekle. "VIX yüksek" değil, "VIX {data.get('VIX','—')} seviyesinde" yaz.
- Seviyeleri kesin belirt: "$84,200 kırılırsa..." gibi somut eşikler ver.
- Yüzeysel geçme, her bölüm derinlikli analiz içersin.
- Tüm veri kategorilerini (makro, türev, on-chain, ETF, forex, emtia, altcoin) mutlaka kullan.
- "Dikkatli ol" gibi genel laflar yerine somut aksiyon ver.

YAZIM KURALLARI:
- Asla "bu rapor yatırım tavsiyesi değildir" veya benzeri yasal uyarı yazma.
- Asla LaTeX formatı ($65,000 yerine $65.000 gibi) kullanma, düz metin yaz.
- Markdown formatı kullan: **kalın**, başlıklar için ## kullan.
- Fiyatları her zaman düz yazı olarak yaz: 65000 dolar veya $65,000

━━━━━━━━ CANLI VERİLER ({bugun}) ━━━━━━━━

📌 BİTCOİN:
Fiyat: {data.get('BTC_P','—')} | 24s: {data.get('BTC_C','—')} | 7g: {data.get('BTC_7D','—')}
Hacim 24s: {data.get('Vol_24h','—')} | MCap: {data.get('BTC_MCap','—')}
BTC Dominance: {data.get('Dom','—')} | ETH Dominance: {data.get('ETH_Dom','—')}
Total MCap: {data.get('Total_MCap','—')} | Total Hacim: {data.get('Total_Vol','—')}

📌 TÜREV PİYASALAR:
Open Interest: {data.get('OI','—')}
Funding Rate: {data.get('FR','—')}
Taker Buy/Sell: {data.get('Taker','—')}
Long/Short Oranı: {data.get('LS_Ratio','—')} → {data.get('LS_Signal','—')}
Long %: {data.get('Long_Pct','—')} | Short %: {data.get('Short_Pct','—')}

📌 BALİNA DUVARLARI (Kraken + OKX + KuCoin + Gate.io + Coinbase):
Birleşik sinyal: {data.get('ORDERBOOK_SIGNAL','—')} | Detay: {data.get('ORDERBOOK_SIGNAL_DETAIL','—')}
Kraken → 🟢 Destek: {data.get('Sup_Wall','—')} — {data.get('Sup_Vol','—')} | 🔴 Direnç: {data.get('Res_Wall','—')} — {data.get('Res_Vol','—')} | Durum: {data.get('Wall_Status','—')}
OKX → 🟢 Destek: {data.get('OKX_Sup_Wall','—')} — {data.get('OKX_Sup_Vol','—')} | 🔴 Direnç: {data.get('OKX_Res_Wall','—')} — {data.get('OKX_Res_Vol','—')} | Durum: {data.get('OKX_Wall_Status','—')}
KuCoin → 🟢 Destek: {data.get('KUCOIN_Sup_Wall','—')} — {data.get('KUCOIN_Sup_Vol','—')} | 🔴 Direnç: {data.get('KUCOIN_Res_Wall','—')} — {data.get('KUCOIN_Res_Vol','—')} | Durum: {data.get('KUCOIN_Wall_Status','—')}
Gate.io → 🟢 Destek: {data.get('GATE_Sup_Wall','—')} — {data.get('GATE_Sup_Vol','—')} | 🔴 Direnç: {data.get('GATE_Res_Wall','—')} — {data.get('GATE_Res_Vol','—')} | Durum: {data.get('GATE_Wall_Status','—')}
Coinbase → 🟢 Destek: {data.get('COINBASE_Sup_Wall','—')} — {data.get('COINBASE_Sup_Vol','—')} | 🔴 Direnç: {data.get('COINBASE_Res_Wall','—')} — {data.get('COINBASE_Res_Vol','—')} | Durum: {data.get('COINBASE_Wall_Status','—')}

📌 KORKU & DUYGU:
Fear & Greed Index: {data.get('FNG','—')} (dün: {data.get('FNG_PREV','—')})

📌 GÜNLÜK ETF NETFLOW (Farside):
Tarih: {data.get('ETF_FLOW_DATE','—')} | Toplam: {data.get('ETF_FLOW_TOTAL','—')}
IBIT: {data.get('ETF_FLOW_IBIT','—')} | FBTC: {data.get('ETF_FLOW_FBTC','—')} | BITB: {data.get('ETF_FLOW_BITB','—')} | ARKB: {data.get('ETF_FLOW_ARKB','—')}
BTCO: {data.get('ETF_FLOW_BTCO','—')} | EZBC: {data.get('ETF_FLOW_EZBC','—')} | BRRR: {data.get('ETF_FLOW_BRRR','—')} | HODL: {data.get('ETF_FLOW_HODL','—')}
BTCW: {data.get('ETF_FLOW_BTCW','—')} | GBTC: {data.get('ETF_FLOW_GBTC','—')} | BTC: {data.get('ETF_FLOW_BTC','—')}

📌 STABLECOİN LİKİDİTESİ:
TOTAL: {data.get('TOTAL_CAP','—')} | TOTAL2: {data.get('TOTAL2_CAP','—')} | TOTAL3: {data.get('TOTAL3_CAP','—')} | OTHERS: {data.get('OTHERS_CAP','—')}
Toplam: {data.get('Total_Stable','—')} | USDT: {data.get('USDT_MCap','—')} | USDC: {data.get('USDC_MCap','—')} | DAI: {data.get('DAI_MCap','—')}
Stable.C.D (Piyasa %): {data.get('STABLE_C_D','—')} | USDT.D (Piyasa %): {data.get('USDT_D','—')} | USDT Dom (Stable içi): {data.get('USDT_Dom_Stable','—')}

📌 ON-CHAIN:
Hashrate: {data.get('Hash','—')} | Aktif Adres (est): {data.get('Active','—')}
BTC ↔ S&P500 Korelasyon (30g): {data.get('Corr_SP500','—')}
BTC ↔ Altın Korelasyon (30g): {data.get('Corr_Gold','—')}

📌 MAKRO PARA POLİTİKASI:
FED Faizi: {data.get('FED','—')} | M2 Büyümesi (YoY): {data.get('M2','—')}
ABD 10Y Tahvil: {data.get('US10Y','—')} ({data.get('US10Y_C','—')})
DXY: {data.get('DXY','—')} ({data.get('DXY_C','—')})
VIX: {data.get('VIX','—')} ({data.get('VIX_C','—')})

📌 GLOBAL HİSSE ENDEKSLERİ:
S&P500: {data.get('SP500','—')} ({data.get('SP500_C','—')})
NASDAQ: {data.get('NASDAQ','—')} ({data.get('NASDAQ_C','—')})
DOW: {data.get('DOW','—')} ({data.get('DOW_C','—')})
DAX: {data.get('DAX','—')} ({data.get('DAX_C','—')})
FTSE: {data.get('FTSE','—')} ({data.get('FTSE_C','—')})
NIKKEI: {data.get('NIKKEI','—')} ({data.get('NIKKEI_C','—')})
BIST100: {data.get('BIST100','—')} ({data.get('BIST100_C','—')})

📌 FOREX:
DXY: {data.get('DXY','—')} | EUR/USD: {data.get('EURUSD','—')} ({data.get('EURUSD_C','—')})
GBP/USD: {data.get('GBPUSD','—')} | USD/JPY: {data.get('USDJPY','—')} ({data.get('USDJPY_C','—')})
USD/TRY: {data.get('USDTRY','—')} ({data.get('USDTRY_C','—')}) | USD/CHF: {data.get('USDCHF','—')}

📌 EMTİALAR:
Altın: {data.get('GOLD','—')} ({data.get('GOLD_C','—')})
Gümüş: {data.get('SILVER','—')} ({data.get('SILVER_C','—')})
Ham Petrol: {data.get('OIL','—')} ({data.get('OIL_C','—')})
Doğalgaz: {data.get('NATGAS','—')} ({data.get('NATGAS_C','—')})
Bakır: {data.get('COPPER','—')} ({data.get('COPPER_C','—')})
Buğday: {data.get('WHEAT','—')} ({data.get('WHEAT_C','—')})

📌 ALTCOİNLER:
ETH: {data.get('ETH_P','—')} | 24s: {data.get('ETH_C','—')} | 7g: {data.get('ETH_7D','—')}
SOL: {data.get('SOL_P','—')} | 24s: {data.get('SOL_C','—')} | 7g: {data.get('SOL_7D','—')}
BNB: {data.get('BNB_P','—')} | 24s: {data.get('BNB_C','—')}
XRP: {data.get('XRP_P','—')} | 24s: {data.get('XRP_C','—')}
ADA: {data.get('ADA_P','—')} | AVAX: {data.get('AVAX_P','—')}
DOT: {data.get('DOT_P','—')} | LINK: {data.get('LINK_P','—')}

📌 SON KRİPTO HABERLERİ:
{news_str if news_str else 'Haber alınamadı'}

━━━━━━━━ RAPOR YAPISI (her bölümü eksiksiz doldur) ━━━━━━━━

**🌍 1. MAKRO ORTAM ANALİZİ**
- SP500 {data.get('SP500_C','—')}, NASDAQ {data.get('NASDAQ_C','—')}, VIX {data.get('VIX','—')} — risk iştahı ne söylüyor?
- DXY {data.get('DXY','—')} ve tahvil faizi {data.get('US10Y','—')} BTC için ne anlam taşıyor?
- M2 {data.get('M2','—')} + FED {data.get('FED','—')}: likidite koşulları gevşiyor mu sıkışıyor mu?
- BTC↔SP500 korelasyon {data.get('Corr_SP500','—')}: hangi yönde kullanılabilir?
- Altın {data.get('GOLD','—')} ve petrol {data.get('OIL','—')} enflasyon/risk sinyali ne veriyor?
- USDTRY {data.get('USDTRY','—')}: TL bazlı yatırımcı için BTC avantajlı mı?

**₿ 2. BİTCOİN TEKNİK & TÜREV ANALİZİ**
- Fiyat {data.get('BTC_P','—')}, hacim {data.get('Vol_24h','—')}, 24s {data.get('BTC_C','—')}, 7g {data.get('BTC_7D','—')} trendini yorumla.
- OI {data.get('OI','—')}: pozisyon birikimi tehlikeli seviyede mi?
- Funding Rate {data.get('FR','—')}: short squeeze mu long liquidation mu daha olası?
- L/S {data.get('LS_Ratio','—')} ({data.get('LS_Signal','—')}): kalabalık taraf nerede, squeeze ihtimali?
- Taker B/S {data.get('Taker','—')}: piyasaya agresif alıcı mı satıcı mı hakim?
- Birleşik sinyal {data.get('ORDERBOOK_SIGNAL','—')}: Kraken, OKX, KuCoin, Gate.io ve Coinbase seviyeleri aynı yöne bakıyor mu?
- Kraken destek {data.get('Sup_Wall','—')} ({data.get('Sup_Vol','—')}), OKX destek {data.get('OKX_Sup_Wall','—')} ({data.get('OKX_Sup_Vol','—')}), KuCoin destek {data.get('KUCOIN_Sup_Wall','—')} ({data.get('KUCOIN_Sup_Vol','—')}), Gate.io destek {data.get('GATE_Sup_Wall','—')} ({data.get('GATE_Sup_Vol','—')}) ve Coinbase destek {data.get('COINBASE_Sup_Wall','—')} ({data.get('COINBASE_Sup_Vol','—')}): ortak destek gerçekten güçlü mü?
- Kraken direnç {data.get('Res_Wall','—')} ({data.get('Res_Vol','—')}), OKX direnç {data.get('OKX_Res_Wall','—')} ({data.get('OKX_Res_Vol','—')}), KuCoin direnç {data.get('KUCOIN_Res_Wall','—')} ({data.get('KUCOIN_Res_Vol','—')}), Gate.io direnç {data.get('GATE_Res_Wall','—')} ({data.get('GATE_Res_Vol','—')}) ve Coinbase direnç {data.get('COINBASE_Res_Wall','—')} ({data.get('COINBASE_Res_Vol','—')}): kırılabilir mi?

**🏦 3. KURUMSAL AKIŞ & LİKİDİTE ANALİZİ**
- Günlük ETF netflow {data.get('ETF_FLOW_TOTAL','—')} ({data.get('ETF_FLOW_DATE','—')}): kurumsal para girişi/çıkışı trendi ne?
- ETF bazlı akış dağılımı BTC fiyatıyla örtüşüyor mu?
- TOTAL {data.get('TOTAL_CAP','—')}, TOTAL2 {data.get('TOTAL2_CAP','—')}, TOTAL3 {data.get('TOTAL3_CAP','—')} ve OTHERS {data.get('OTHERS_CAP','—')}: risk iştahı büyüklerde mi, geniş altcoin tarafında mı yoğunlaşıyor?
- Stablecoin toplam {data.get('Total_Stable','—')}: piyasaya hazır "barut" var mı?
- Stable.C.D {data.get('STABLE_C_D','—')} ve USDT.D {data.get('USDT_D','—')}: toplam stable parkı ile USDT özel talebi aynı şeyi mi söylüyor?
- Likidite analizi: para kripto'ya mı giriyor, stablecoin'de mi bekliyor?

**🪙 4. ALTCOİN & DOMAİNANCE ANALİZİ**
- BTC dominance {data.get('Dom','—')}, ETH dominance {data.get('ETH_Dom','—')}: dominance trendi yükseliyor mu?
- ETH ({data.get('ETH_C','—')} / 7g: {data.get('ETH_7D','—')}), SOL ({data.get('SOL_C','—')} / 7g: {data.get('SOL_7D','—')}) BTC'ye göre güçlü mü zayıf mı?
- Hangi altcoin rölatif güç gösteriyor? Hangisi zayıf?
- Bu dominance seviyesinde altcoin pozisyonu mantıklı mı?

**📰 5. HABER & KATALİZÖR ANALİZİ**
- Yukarıdaki haberlerin BTC/kripto piyasasına olası etkisini değerlendir.
- Önümüzdeki 1-3 gün için izlenmesi gereken kritik gelişmeler neler?

**🎯 6. GÜNLÜK AKSİYON PLANI (1-3 Gün)**

📗 LONG (Alış) Senaryosu:
  - Giriş seviyesi: (kesin rakam)
  - Stop-Loss: (kesin rakam)
  - Hedef 1 / Hedef 2: (kesin rakamlar)
  - Gerekçe: (hangi koşul sağlanırsa giriş yapılır)

📕 SHORT (Satış) Senaryosu:
  - Giriş seviyesi: (kesin rakam)
  - Stop-Loss: (kesin rakam)
  - Hedef 1 / Hedef 2: (kesin rakamlar)
  - Gerekçe: (hangi koşul sağlanırsa giriş yapılır)

📒 BEKLE Senaryosu:
  - Hangi koşulda beklenmeli?
  - Beklerken izlenecek tetikleyici seviyeler neler?

**⚠️ 7. KRİTİK RİSK & ÖZET**
- Bugünün en kritik riski (tek cümle, rakamsal)
- Genel piyasa pozisyonu özeti (1-2 cümle)
- BTC için en olası senaryo (rakamsal eşiklerle)
"""
