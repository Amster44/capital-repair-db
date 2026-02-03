#!/usr/bin/env python3
"""
collapse_ozhf_houses.py

Схлопывает CSV "Сведения по ОЖФ" (где строки размножены по помещениям/комнатам)
до уровня "1 строка = 1 дом".

Оставляет только:
- GUID дома по ФИАС
- адрес дома
- ОКТМО
- способ управления
- ОГРН управляющей организации
- КПП управляющей организации
- наименование управляющей организации

Пример:
python collapse_ozhf_houses.py --ozhf_dir "data/ojf_data" --out "data/ozhf_houses_collapsed.csv"
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, List

import pandas as pd


def sniff_csv(path: str, sample_bytes: int = 1024 * 256) -> Tuple[str, str]:
    """Угадываем разделитель и кодировку"""
    p = Path(path)
    raw = p.read_bytes()[:sample_bytes]

    # encoding guess
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            raw.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    else:
        encoding = "utf-8"

    text = raw.decode(encoding, errors="ignore")
    try:
        dialect = csv.Sniffer().sniff(text, delimiters=[",", ";", "\t", "|"])
        sep = dialect.delimiter
    except Exception:
        lines = [ln for ln in text.splitlines() if ln.strip()][:5]
        candidates = [",", ";", "\t", "|"]
        best = (",", 0)
        for cand in candidates:
            cols = max((len(ln.split(cand)) for ln in lines), default=0)
            if cols > best[1]:
                best = (cand, cols)
        sep = best[0]

    return sep, encoding


def norm_header(s: str) -> str:
    s = str(s).strip().lower().replace("\ufeff", "")
    s = re.sub(r"\s+", " ", s)
    return s


def find_col(cols: List[str], *needles: str, strict: bool = False) -> Optional[str]:
    """Ищем колонку по подстрокам"""
    cols_norm = [(c, norm_header(c)) for c in cols]
    n = [norm_header(x) for x in needles]
    for orig, cn in cols_norm:
        if strict:
            if all(x in cn for x in n):
                return orig
        else:
            if any(x in cn for x in n):
                return orig
    return None


def clean_guid(x) -> Optional[str]:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if not s:
        return None
    return s.lower()


def clean_digits(x) -> Optional[str]:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = re.sub(r"\D+", "", str(x))
    return s if s else None


def best_row_score(
    mgmt_method: Optional[str],
    ogrn: Optional[str],
    uo_name: Optional[str],
    address: Optional[str],
) -> int:
    """Чем выше score, тем лучше строка"""
    score = 0
    if ogrn:
        score += 100
    if mgmt_method:
        score += 30
        mm = norm_header(mgmt_method)
        if "не выбран" not in mm and "не выбран способ" not in mm:
            score += 20
    if uo_name:
        score += 10
    if address:
        score += 5
    return score


def update_best_from_chunk(
    chunk: pd.DataFrame,
    best: Dict[str, Tuple[int, int, dict]],
    col_guid_house_fias: str,
    col_addr: Optional[str],
    col_oktmo: Optional[str],
    col_mgmt: Optional[str],
    col_ogrn: Optional[str],
    col_kpp: Optional[str],
    col_uo_name: Optional[str],
) -> None:
    chunk[col_guid_house_fias] = chunk[col_guid_house_fias].map(clean_guid)
    if col_ogrn:
        chunk[col_ogrn] = chunk[col_ogrn].map(clean_digits)
    if col_kpp:
        chunk[col_kpp] = chunk[col_kpp].map(clean_digits)
    if col_oktmo:
        chunk[col_oktmo] = chunk[col_oktmo].map(clean_digits)

    for _, r in chunk.iterrows():
        guid = r.get(col_guid_house_fias)
        if not guid:
            continue

        addr = (r.get(col_addr) or "").strip() if col_addr else ""
        oktmo = r.get(col_oktmo) if col_oktmo else None
        mgmt = (r.get(col_mgmt) or "").strip() if col_mgmt else ""
        ogrn = r.get(col_ogrn) if col_ogrn else None
        kpp = r.get(col_kpp) if col_kpp else None
        uo_name = (r.get(col_uo_name) or "").strip() if col_uo_name else ""

        score = best_row_score(mgmt, ogrn, uo_name, addr)
        addr_len = len(addr)

        rowdict = {
            "guid_house_fias": guid,
            "address": addr or None,
            "oktmo": oktmo,
            "mgmt_method": mgmt or None,
            "ogrn_uo": ogrn,
            "kpp_uo": kpp,
            "uo_name": uo_name or None,
        }

        cur = best.get(guid)
        if cur is None:
            best[guid] = (score, addr_len, rowdict)
        else:
            cur_score, cur_len, _ = cur
            if score > cur_score or (score == cur_score and addr_len > cur_len):
                best[guid] = (score, addr_len, rowdict)


def collapse_ozhf_files_to_houses(ozhf_files: List[str], chunksize: int = 500_000) -> pd.DataFrame:
    if not ozhf_files:
        raise ValueError("Не переданы файлы ОЖФ")

    first = ozhf_files[0]
    sep, enc = sniff_csv(first)
    head = pd.read_csv(first, sep=sep, encoding=enc, nrows=0)
    cols = list(head.columns)

    col_guid_house_fias = find_col(cols, "глобальный уникальный идентификатор дома по фиас")
    if not col_guid_house_fias:
        raise ValueError("ОЖФ: не найдена колонка 'Глобальный уникальный идентификатор дома по ФИАС'")

    col_addr = find_col(cols, "адрес ожф") or find_col(cols, "адрес")
    col_oktmo = find_col(cols, "код октмо")
    col_mgmt = find_col(cols, "способ управления")

    # ОГРН/КПП организации, осуществляющей управление домом
    col_ogrn = find_col(cols, "огрн организации", "управлен", strict=False)
    col_kpp = find_col(cols, "кпп организации", "управлен", strict=False)
    col_uo_name = find_col(cols, "наименование организации", "управлен", strict=False)

    usecols = [c for c in [col_guid_house_fias, col_addr, col_oktmo, col_mgmt, col_ogrn, col_kpp, col_uo_name] if c]

    best: Dict[str, Tuple[int, int, dict]] = {}

    for fp in ozhf_files:
        sep, enc = sniff_csv(fp)
        print(f"Читаю ОЖФ: {fp}")
        for chunk in pd.read_csv(
            fp,
            sep=sep,
            encoding=enc,
            usecols=usecols,
            dtype=str,
            chunksize=chunksize,
            low_memory=False,
        ):
            update_best_from_chunk(
                chunk,
                best,
                col_guid_house_fias=col_guid_house_fias,
                col_addr=col_addr,
                col_oktmo=col_oktmo,
                col_mgmt=col_mgmt,
                col_ogrn=col_ogrn,
                col_kpp=col_kpp,
                col_uo_name=col_uo_name,
            )

    df = pd.DataFrame([v[2] for v in best.values()])

    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].replace({"": None})

    order = ["guid_house_fias", "address", "oktmo", "mgmt_method", "ogrn_uo", "kpp_uo", "uo_name"]
    df = df[[c for c in order if c in df.columns]]

    return df


def collect_files(args_ozhf: List[str], ozhf_dir: Optional[str]) -> List[str]:
    files: List[str] = []
    if args_ozhf:
        files.extend(args_ozhf)
    if ozhf_dir:
        p = Path(ozhf_dir)
        if not p.exists():
            raise ValueError(f"--ozhf_dir не существует: {ozhf_dir}")
        files.extend([str(x) for x in sorted(p.glob("*.csv"))])

    files = list(dict.fromkeys(files))
    if not files:
        raise ValueError("Не передано ни одного ОЖФ файла")
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ozhf", action="append", default=[], help="Путь к ОЖФ CSV")
    ap.add_argument("--ozhf_dir", default=None, help="Папка с ОЖФ CSV")
    ap.add_argument("--out", required=True, help="Выходной CSV")
    ap.add_argument("--chunksize", type=int, default=500_000)
    args = ap.parse_args()

    ozhf_files = collect_files(args.ozhf, args.ozhf_dir)
    print(f"ОЖФ файлов: {len(ozhf_files)}")

    houses = collapse_ozhf_files_to_houses(ozhf_files, chunksize=args.chunksize)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    houses.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("Готово.")
    print(f"Дома (строк): {len(houses):,}")
    if "ogrn_uo" in houses.columns:
        share = houses["ogrn_uo"].notna().mean()
        print(f"Доля домов с ОГРН: {share:.2%}")


if __name__ == "__main__":
    main()
