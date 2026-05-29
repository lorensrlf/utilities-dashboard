#!/usr/bin/env python3
"""
extract_data.py
───────────────
Lê o arquivo Database_Formatted v3.zip (ou .xlsx) e gera
data/dashboard_data.json pronto para o dashboard.

Uso:
    python scripts/extract_data.py
    python scripts/extract_data.py "D:/investment cycles/Database_Formatted v3.zip"
"""

import zipfile, openpyxl, json, io, sys, os
from datetime import datetime, date

# ── Configuração ─────────────────────────────────────────────────────────────
DEFAULT_SOURCE = r"D:\investment cycles\Database_Formatted v3.zip"
OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'dashboard_data.json')

# ── Helpers ──────────────────────────────────────────────────────────────────

def safe_float(v, default=None):
    try:
        if v is None:
            return default
        if isinstance(v, str) and v.startswith('#'):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default

def fmt_date(v):
    if isinstance(v, datetime):
        return v.strftime('%Y-%m-%d')
    if isinstance(v, date):
        return v.strftime('%Y-%m-%d')
    return None

def load_wb(path):
    if path.lower().endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.endswith('.xlsx')]
            if not names:
                raise FileNotFoundError("Nenhum .xlsx encontrado no zip")
            raw = z.read(names[0])
        return openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    return openpyxl.load_workbook(path, read_only=True, data_only=True)

# ── Extractors ────────────────────────────────────────────────────────────────

def extract_summary(ws):
    """KPIs da aba Summary: PLD médio, máximo, floor%, spreads."""
    rows = list(ws.iter_rows(values_only=True))
    def r(row_idx, col_idx):
        try:
            return safe_float(rows[row_idx][col_idx])
        except IndexError:
            return None

    kpis = {
        "pld_avg_se":      r(1, 1),
        "pld_avg_se_prev": r(1, 2),
        "pld_avg_se_wow":  r(1, 3),
        "pld_max":         r(2, 1),
        "pld_floor_pct":   r(3, 1),
        "spread_se_s":     r(4, 1),
        "spread_se_n":     r(5, 1),
        "spread_se_ne":    r(6, 1),
        "spread_s_ne":     r(7, 1),
    }
    # Arredondar
    for k, v in kpis.items():
        if v is not None:
            kpis[k] = round(v, 4)
    return kpis


def extract_dcide(ws):
    """
    Preços forward Dcide (CONV): 2Q26, 2026, 2027, 2028, 2029, 2030.
    Seção GRAPH começa na coluna 40 (índice).
    Col 42 = preço atual (mai/26), col 57 = semana anterior (mai/11).
    """
    rows = list(ws.iter_rows(values_only=True))

    # Datas históricas (row 2, cols 42-53 = 12 meses mensais)
    date_row = rows[1]
    dates = []
    for j in range(42, 54):
        dates.append(fmt_date(date_row[j]))

    conv_data = []
    for i in range(2, 8):       # linhas 3-8: 2Q26, 2026, 2027, 2028, 2029, 2030
        r = rows[i]
        label = r[41]
        if label is None or (isinstance(label, str) and label in ('INCENT', 'SPREAD')):
            break
        current   = safe_float(r[42])
        prev_week = safe_float(r[56]) if len(r) > 56 else None   # coluna May-11
        history   = [safe_float(r[j]) for j in range(42, 54)]

        wow_pct = None
        if current is not None and prev_week is not None and prev_week != 0:
            wow_pct = round((current - prev_week) / prev_week * 100, 1)

        conv_data.append({
            "label":     str(label),
            "current":   round(current, 1) if current is not None else None,
            "prev_week": round(prev_week, 1) if prev_week is not None else None,
            "wow_pct":   wow_pct,
            "history":   [round(v, 1) if v is not None else None for v in history],
        })

    return {"dates": dates, "conv": conv_data}


def extract_pld_history(ws):
    """PLD diário SE/CO histórico (aba PLD_SE_Histórico)."""
    rows = list(ws.iter_rows(values_only=True))
    result = []
    for r in rows[2:]:
        if not isinstance(r[1], datetime):
            continue
        val = safe_float(r[2])
        if val is None:
            continue
        result.append({"date": r[1].strftime('%Y-%m-%d'), "pld": round(val, 2)})
    return result


def extract_pld_hourly_week(ws):
    """PLD horário da última semana, subsistema SUDESTE."""
    rows = list(ws.iter_rows(values_only=True))
    header = rows[2]
    dates = [fmt_date(header[j]) for j in range(4, 11)]

    se_by_hour = []
    for r in rows[3:]:
        if len(r) < 11:
            continue
        if r[3] == 'SUDESTE':
            vals = [safe_float(r[j]) for j in range(4, 11)]
            se_by_hour.append(vals)
        if len(se_by_hour) == 24:
            break

    return {"dates": dates, "se": se_by_hour}


def extract_cmo(ws):
    """CMO semanal por subsistema (aba CMO), últimas 52 semanas."""
    rows = list(ws.iter_rows(values_only=True))
    date_row = rows[2]

    # Última coluna com data válida
    last_j = None
    for j, v in enumerate(date_row):
        if isinstance(v, datetime):
            last_j = j

    if last_j is None:
        return {}

    start_j = max(3, last_j - 51)
    dates = [fmt_date(date_row[j]) for j in range(start_j, last_j + 1)]

    labels   = ['se_co', 'south', 'northeast', 'north', 'avg']
    row_idxs = [4, 5, 6, 7, 8]
    series   = {}
    for label, ri in zip(labels, row_idxs):
        series[label] = [safe_float(rows[ri][j]) for j in range(start_j, last_j + 1)]

    current = {
        "date":      dates[-1] if dates else None,
        "se_co":     safe_float(rows[4][last_j]),
        "south":     safe_float(rows[5][last_j]),
        "northeast": safe_float(rows[6][last_j]),
        "north":     safe_float(rows[7][last_j]),
        "avg":       safe_float(rows[8][last_j]),
    }

    return {"dates": dates, "series": series, "current": current}


def extract_ena_demand(ws):
    """ENA por subsistema e histórico de demanda mensal (aba Carga & ENA)."""
    rows = list(ws.iter_rows(values_only=True))

    # ENA: rows 20-23 (índices 19-22)
    ena_map = [
        ("North",     19, 2, 3, 5, 6),
        ("Northeast", 20, 2, 3, 5, 6),
        ("South",     21, 2, 3, 5, 6),
        ("SE / CO",   22, 2, 3, 5, 6),
    ]
    ena = []
    for name, idx, c_ena, c_lta, c_max, c_wow in ena_map:
        try:
            r = rows[idx]
            ena.append({
                "name":    name,
                "ena":     safe_float(r[c_ena]),
                "lta":     safe_float(r[c_lta]),
                "max_cap": safe_float(r[c_max]),
                "wow":     safe_float(r[c_wow]),
            })
        except IndexError:
            pass

    # Demanda mensal histórica: cols 12, 13, 14 a partir da row 16 (índice 15)
    demand = []
    for r in rows[15:]:
        if len(r) < 15:
            continue
        dt  = fmt_date(r[12])
        gw  = safe_float(r[13])
        yoy = safe_float(r[14])
        if dt and gw:
            demand.append({"date": dt, "gw": round(gw, 2), "yoy": yoy})

    return {"ena": ena, "demand_history": demand}


def extract_sim(ws):
    """Níveis dos reservatórios Sabesp SIM (aba SIM), mensal desde 2014."""
    rows = list(ws.iter_rows(values_only=True))
    result = []
    for r in rows[2:]:
        if len(r) < 10:
            continue
        dt = fmt_date(r[1])
        if not dt:
            continue
        sim_val = safe_float(r[9])
        if sim_val is None:
            continue   # pula linhas sem dados
        result.append({
            "date":         dt,
            "cantareira":   safe_float(r[2]),
            "alto_tiete":   safe_float(r[3]),
            "guarapiranga": safe_float(r[4]),
            "alto_cotia":   safe_float(r[5]),
            "rio_grande":   safe_float(r[6]),
            "rio_claro":    safe_float(r[7]),
            "sao_lourenco": safe_float(r[8]),
            "sim":          sim_val,
        })
    return result


def extract_ntnb(ws):
    """NTN-B 2035: yield diário histórico (aba NTNB)."""
    rows = list(ws.iter_rows(values_only=True))
    result = []
    for r in rows[2:]:
        if not isinstance(r[0], datetime):
            continue
        y = safe_float(r[9])   # coluna J = NTN-B 2035 Yield
        if y is None:
            continue
        result.append({
            "date":  r[0].strftime('%Y-%m-%d'),
            "yield": round(y * 100, 3),  # em %
        })
    return {
        "history": result,
        "latest":  result[-1] if result else None,
    }


def extract_tirs(ws, ntnb_yield_pct):
    """IRR real por empresa (aba TIRs). Retorna ticker, IRR atual e spread vs NTN-B."""
    rows = list(ws.iter_rows(values_only=True))
    companies = []
    for r in rows[2:]:
        if r[0] is None:
            break
        ticker = str(r[1]).strip() if r[1] else None
        if not ticker or ticker == 'Real IRR - ':
            break
        irr = safe_float(r[2])
        if irr is None:
            continue
        # Histórico últimos 6 meses (cols 2-7)
        hist = [safe_float(r[j]) for j in range(2, 8)]
        spread = None
        if ntnb_yield_pct is not None:
            spread = round(irr * 100 - ntnb_yield_pct, 2)
        companies.append({
            "ticker":  ticker,
            "irr":     round(irr * 100, 2),
            "spread":  spread,
            "history": [round(v * 100, 2) if v is not None else None for v in hist],
        })
    return companies


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE

    if not os.path.exists(src):
        print(f"ERRO: arquivo não encontrado: {src}")
        print("Uso: python scripts/extract_data.py <caminho_para_zip_ou_xlsx>")
        sys.exit(1)

    print(f"[INFO] Lendo: {src}")
    wb = load_wb(src)

    print("  -> Summary (KPIs)...")
    kpis = extract_summary(wb['Summary'])

    print("  -> DCIDE Semanal (precos forward)...")
    dcide = extract_dcide(wb['DCIDE Semanal'])

    pld_hist_sheet = [s for s in wb.sheetnames if 'SE' in s and 'ist' in s][0]
    print(f"  -> {pld_hist_sheet}...")
    pld_hist = extract_pld_history(wb[pld_hist_sheet])

    pld_hrly_sheet = [s for s in wb.sheetnames if 'or' in s.lower() and 'Plot' in s][0]
    print(f"  -> {pld_hrly_sheet}...")
    pld_hourly = extract_pld_hourly_week(wb[pld_hrly_sheet])

    print("  -> CMO...")
    cmo = extract_cmo(wb['CMO'])

    print("  -> Carga & ENA...")
    carga = extract_ena_demand(wb['Carga & ENA'])

    print("  -> SIM (Sabesp)...")
    sim = extract_sim(wb['SIM'])

    print("  -> NTNB 2035...")
    ntnb = extract_ntnb(wb['NTNB'])

    print("  -> TIRs...")
    ntnb_latest_pct = ntnb['latest']['yield'] if ntnb['latest'] else None
    tirs = extract_tirs(wb['TIRs'], ntnb_latest_pct)

    output = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "source_file":  os.path.basename(src),
        },
        "kpis":            kpis,
        "dcide":           dcide,
        "pld_history":     pld_hist,
        "pld_hourly_week": pld_hourly,
        "cmo":             cmo,
        "ena":             carga["ena"],
        "demand_history":  carga["demand_history"],
        "sim":             sim,
        "ntnb":            ntnb,
        "tirs":            tirs,
    }

    out_path = os.path.abspath(OUTPUT)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Gerado: {out_path}")
    print(f"   KPIs:          pld_avg={kpis.get('pld_avg_se'):.2f} | pld_max={kpis.get('pld_max')}")
    print(f"   DCIDE:         {len(dcide['conv'])} contratos")
    print(f"   PLD historico: {len(pld_hist)} dias")
    print(f"   PLD horario:   {len(pld_hourly.get('se', []))} horas x {len(pld_hourly.get('dates', []))} dias")
    print(f"   CMO:           {len(cmo.get('dates', []))} semanas")
    print(f"   ENA:           {len(carga['ena'])} subsistemas")
    print(f"   Demanda:       {len(carga['demand_history'])} meses")
    print(f"   SIM:           {len(sim)} meses")
    ntnb_str = f"{ntnb_latest_pct:.3f}%" if ntnb_latest_pct else "N/A"
    print(f"   NTN-B atual:   {ntnb_str}")
    print(f"   TIRs:          {len(tirs)} empresas")

if __name__ == '__main__':
    main()
