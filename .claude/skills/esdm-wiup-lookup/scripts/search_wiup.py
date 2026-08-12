#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ESDM Minerba Geoportal(https://geoportal.esdm.go.id/minerba/)의
WIUP_Publish ArcGIS 레이어에서 광구(회사명/위치/Single ID 등)를 검색하고,
속성 정보를 콘솔에 출력하며 필요 시 1) 광구정보 엑셀(.xlsx)과
2) 경계좌표 GeoJSON(.geojson)으로 저장한다.

실제 조회/변환 로직은 프로젝트 루트의 wiup_lib.py를 공유한다
(Streamlit 앱 app.py도 동일 모듈을 사용).

사용 예:
  python search_wiup.py "BUKIT MAKMUR ISTINDO NIKELTAMA" --geojson out.geojson --xlsx out.xlsx
  python search_wiup.py "ANTAM" --field nama_usaha
  python search_wiup.py "1473065402022002" --field kode_wiup --exact
"""
import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# 프로젝트 루트(wiup_lib.py 위치)를 import 경로에 추가
# .../<project_root>/.claude/skills/esdm-wiup-lookup/scripts/search_wiup.py
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_PROJECT_ROOT))

try:
    import wiup_lib as wl
except ImportError:
    sys.exit(
        f"[오류] wiup_lib.py를 찾을 수 없습니다. 프로젝트 루트({_PROJECT_ROOT})에 "
        "wiup_lib.py가 있는지 확인하세요."
    )


def print_summary(features):
    if not features:
        print("검색 결과가 없습니다.")
        return

    print(f"총 {len(features)}건 검색됨\n")
    for i, f in enumerate(features, 1):
        a = f.get("attributes", {})
        print(f"[{i}] {a.get('nama_usaha', '-')}  (Single ID: {a.get('kode_wiup', '-')})")
        print(f"    허가 종류      : {a.get('jenis_izin', '-')} / {a.get('badan_usaha', '-')}")
        print(f"    광물 종류      : {a.get('komoditas', '-')}")
        print(
            "    위치          : "
            f"{a.get('nama_prov', '-')} / {a.get('nama_kab', '-')} / {a.get('pulau', '-')}"
        )
        print(f"    상세 위치     : {a.get('lokasi', '-')}")
        print(f"    면적(Ha)      : {a.get('luas_sk')}")
        print(f"    생산 단계     : {a.get('kegiatan', '-')}")
        print(f"    C&C 상태      : {a.get('cnc', '-')}")
        print(f"    SK 번호       : {a.get('sk_iup', '-')}")
        print(f"    허가권자      : {a.get('pejabat', '-')}")
        geom = f.get("geometry")
        ring_count = len(geom.get("rings", [])) if geom else 0
        print(f"    경계 좌표     : {ring_count}개 폴리곤 링 포함")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="ESDM Minerba Geoportal WIUP 레이어 검색 + 엑셀/GeoJSON 추출"
    )
    parser.add_argument("term", help="검색어 (예: 회사명, 위치, Single ID 등)")
    parser.add_argument(
        "--field",
        default="nama_usaha",
        choices=list(wl.SEARCHABLE_FIELDS.keys()) + ["all"],
        help="검색 대상 필드 (기본값: nama_usaha=회사명). 'all'은 회사명/위치/Single ID를 동시 검색",
    )
    parser.add_argument("--exact", action="store_true", help="부분일치 대신 완전일치 검색")
    parser.add_argument(
        "--geojson",
        default=None,
        help="경계좌표를 저장할 GeoJSON 파일 경로 (검색 결과 전체를 하나의 FeatureCollection으로 저장)",
    )
    parser.add_argument(
        "--xlsx",
        default=None,
        help="광구정보를 저장할 엑셀 파일 경로 (검색 결과가 1건일 때만 지원)",
    )
    parser.add_argument(
        "--no-geometry", action="store_true", help="경계 좌표 없이 속성 정보만 조회 (--geojson과 함께 쓸 수 없음)"
    )
    args = parser.parse_args()

    if args.no_geometry and args.geojson:
        parser.error("--no-geometry 와 --geojson은 함께 사용할 수 없습니다.")

    try:
        features = wl.search(args.term, field=args.field, exact=args.exact, geometry=not args.no_geometry)
    except wl.WiupApiError as e:
        sys.exit(f"[오류] {e}")

    print_summary(features)

    if args.geojson and features:
        data = wl.geojson_bytes(features)
        Path(args.geojson).write_bytes(data)
        print(f"GeoJSON 저장 완료: {args.geojson}")
        print("QGIS에서: 레이어 > 레이어 추가 > 벡터 레이어 추가로 이 파일을 불러오면 됩니다.")

    if args.xlsx and features:
        if len(features) > 1:
            print(
                f"[안내] 검색 결과가 {len(features)}건이라 --xlsx는 첫 번째 결과"
                f"({features[0]['attributes'].get('nama_usaha')})만 저장합니다. "
                "특정 회사만 원하면 검색어를 더 구체적으로 입력하세요.",
                file=sys.stderr,
            )
        data = wl.xlsx_bytes(features[0]["attributes"])
        Path(args.xlsx).write_bytes(data)
        print(f"엑셀 저장 완료: {args.xlsx}")


if __name__ == "__main__":
    main()
