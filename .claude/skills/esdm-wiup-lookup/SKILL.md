---
name: esdm-wiup-lookup
description: 인도네시아 ESDM Minerba Geoportal(https://geoportal.esdm.go.id/minerba/)에서 회사명(광구명)으로 검색해 WIUP 정보(광물 종류, 위치, IUP 면적, 허가 종류, 생산 단계 등)를 엑셀로, 광구 경계 좌표(폴리곤)를 QGIS용 GeoJSON으로 저장한다. CLI 스크립트와 누구나 쓸 수 있는 Streamlit 웹앱(app.py) 두 가지 방식 제공. 사용자가 "광구명으로 WIUP 정보/경계 좌표 가져와줘", "이 회사 광구 QGIS에 올리고 싶어" 라고 요청할 때 사용.
user-invocable: true
---

# ESDM Minerba WIUP 조회 스킬

인도네시아 에너지광물자원부(ESDM) 산하 Minerba Geoportal
(https://geoportal.esdm.go.id/minerba/)은 ArcGIS Web AppBuilder로 만들어진
지도 애플리케이션이다. 화면 자체는 JS로 렌더링되는 SPA라 브라우저 스크래핑이
필요해 보이지만, 실제로는 **인증 없이 열려 있는 공개 ArcGIS REST 서비스**가
뒤에서 지도를 그리고 있으므로 이 REST API를 직접 호출하는 것이 훨씬 빠르고
정확하다 (좌표도 검색 결과에 바로 포함되어 나온다).

## 데이터 소스

- 서비스: `WIUP_Publish` (MapServer, 레이어 0 = "WIUP")
- URL: `https://geoportal.esdm.go.id/monaresia/sharing/servers/3b305b4113384b41b7490479e0702093/rest/services/Pusat/WIUP_Publish/MapServer/0/query`
- 인증: 불필요 (토큰 없이 공개 조회 가능. `capabilities: "Map,Query,Data"`)
- 좌표계: WGS84 (EPSG:4326, 위경도) — QGIS에서 바로 쓸 수 있음
- 서버 페이지당 최대 반환 건수: 100 (`maxRecordCount`) — 검색어가 넓으면
  `resultOffset`으로 페이지네이션 필요 (스크립트가 자동 처리함)
- 이 레이어는 "생산 중(아직 유효/active)" 인 WIUP/IUP/IUPK/PKP2B/IPR/KK/WIUPK를
  담고 있음 (서비스 설명: "status kegiatan usaha masih berlaku (aktif)")

이 URL은 웹앱의 `config.json` → 지도 아이템(`itemId`) → 웹맵 JSON
(`.../sharing/rest/content/items/<itemId>/data?f=json`)의 `operationalLayers`를
따라가서 찾아낸 것이다. 만약 나중에 URL이 바뀌거나 접근이 안 되면 아래 절차로
다시 찾을 수 있다:
1. `https://geoportal.esdm.go.id/minerba/config.json` 에서 `map.itemId`와
   `map.portalUrl` 확인
2. `<portalUrl>/sharing/rest/content/items/<itemId>/data?f=json` 요청 →
   `operationalLayers` 배열에서 원하는 레이어(title에 "WIUP", "Wilayah Izin
   Usaha Pertambangan" 등이 포함된 항목)의 `url` 필드 확인
3. 그 MapServer URL에 `?f=json`을 붙여 `capabilities`에 `Query`가 있는지,
   토큰이 필요한지(`Token Required` 에러 여부) 확인

## 필드(속성) 매핑

| API 필드명 | 의미 | 사용자가 물어본 항목과 매칭 |
|---|---|---|
| `nama_usaha` | 회사명(광구를 보유한 사업체명) | 검색 키로 주로 사용 (사실상 "광구명"에 가장 가까움) |
| `komoditas` | 광물 종류 | **광물 종류** |
| `nama_prov`, `nama_kab`, `pulau`, `lokasi` | 주/군/섬/상세 위치 설명 | **위치** |
| `luas_sk` | 면적 (헥타르, Ha) | **IUP 면적** |
| `jenis_izin` | 허가 종류: WIUP/IUP/IUPK/PKP2B/IPR/KK/WIUPK | **WIUP 종류** |
| `kegiatan` | 사업 단계: 예) PENCADANGAN(예비지정)/EKSPLORASI(탐사)/OPERASI PRODUKSI(생산 운영) 등 | **생산 단계** |
| `kode_wiup` | Single ID (전국 고유 식별자) | 참고용 고유 키 |
| `sk_iup` | 허가서(SK) 번호 | 참고 |
| `tgl_berlaku`, `tgl_akhir` | 허가 시작일/만료일 (epoch ms) | 참고 |
| `cnc` | Clean and Clear 상태 | 참고 |
| `badan_usaha` | 사업체 형태 (PT/CV 등) | 참고 |
| `pejabat` | 허가권자 (MENTERI/GUBERNUR/Bupati 등) | 참고 |
| geometry (`rings`) | 광구 경계 폴리곤 좌표 (경위도) | **경계 좌표 → QGIS용** |

주의: 이 레이어에는 "블록명" 같은 별도 명칭 필드가 없다. 인도네시아 IUP는
보통 회사(사업체) 단위로 발급되므로, "광구명"을 물으면 대개 **회사명
(`nama_usaha`)** 을 검색어로 쓰면 된다. 만약 사용자가 말하는 "광구명"이
특정 지정 광업지역(Wilayah Pertambangan)의 블록 이름(예: "Blok Balun-3")을
뜻한다면, 이는 다른 레이어인 `Wilayah_Pertambangan_2025`
(`blok` 필드 보유, URL은 참고: `https://geoportal.esdm.go.id/monaresia/sharing/servers/c1b5104a2502497cbdcaa8a8f2f5e8a7/rest/services/Pusat/Wilayah_Pertambangan_2025/MapServer`)
를 대신 조회해야 한다 — 다만 이 레이어는 생산 단계(`kegiatan`) 등 회사별
허가 상세 정보는 없고 구역 지정 정보 위주다. 사용자에게 어떤 의미인지
모호하면 먼저 물어볼 것.

## 코드 구조

핵심 조회/변환 로직은 프로젝트 루트의 **`wiup_lib.py`** 하나에 모여 있고,
CLI 스크립트와 Streamlit 앱이 이를 공유한다 (단일 진실 공급원):

```
<project_root>/
├── wiup_lib.py              # 공용 라이브러리 (검색, GeoJSON 변환, 엑셀 변환)
├── app.py                   # Streamlit 웹앱 (누구나 브라우저로 사용)
├── requirements.txt         # streamlit, pandas, openpyxl, pydeck
└── .claude/skills/esdm-wiup-lookup/
    ├── SKILL.md
    └── scripts/search_wiup.py   # CLI 스크립트 (wiup_lib.py를 import)
```

### 1) Streamlit 웹앱 (비개발자도 사용 가능)

```bash
streamlit run app.py
```
브라우저에서 `http://localhost:8501` 접속 → 회사명 입력 → 검색 → 결과 표에서
광구 선택 → 지도로 경계 미리보기 → **광구정보 엑셀(.xlsx)** / **경계좌표
GeoJSON(.geojson)** 다운로드 버튼 클릭.

패키지가 없으면 먼저 `pip install -r requirements.txt`.

외부에 공개 URL로 배포하려면(예: Streamlit Community Cloud) 사용자의
GitHub/Streamlit 계정이 필요하므로, 사용자가 명시적으로 요청할 때만 진행할 것
(2026-08-12 기준: 사용자가 "지금은 로컬 테스트만" 선택 — 아직 미배포 상태).

### 2) CLI 스크립트

```bash
# 회사명으로 검색 (부분일치, 대소문자 무시) + 엑셀/GeoJSON 저장
python .claude/skills/esdm-wiup-lookup/scripts/search_wiup.py "BUKIT MAKMUR ISTINDO NIKELTAMA" --xlsx info.xlsx --geojson boundary.geojson

# Single ID로 정확히 검색
python .claude/skills/esdm-wiup-lookup/scripts/search_wiup.py "1473065402022002" --field kode_wiup --exact

# 위치 설명으로 검색
python .claude/skills/esdm-wiup-lookup/scripts/search_wiup.py "Bengkulu Selatan" --field lokasi

# 광물 종류로 검색 (결과가 많을 수 있음 → 자동 페이지네이션)
python .claude/skills/esdm-wiup-lookup/scripts/search_wiup.py "Nikel" --field komoditas --geojson nikel.geojson

# 회사명/위치/Single ID를 한번에 OR로 검색
python .claude/skills/esdm-wiup-lookup/scripts/search_wiup.py "검색어" --field all

# 속성만 빠르게 확인하고 싶을 때 (경계좌표 없이, 응답 가벼움)
python .claude/skills/esdm-wiup-lookup/scripts/search_wiup.py "ANTAM" --no-geometry
```

`--xlsx`는 검색 결과가 여러 건이면 첫 번째 결과만 저장하고 경고를 출력한다
(특정 회사 하나만 원하면 검색어를 더 구체적으로 넣을 것). 엑셀에는 광구
속성 정보만 담는다 — **경계좌표는 GeoJSON에만** 저장한다(사용자 확정 사항).

Python 표준 라이브러리(`urllib`, `json`, `argparse`)만 사용해 조회하므로
CLI 자체는 추가 설치가 필요 없다(엑셀 저장 시에만 `openpyxl` 필요, 이미
설치되어 있음). 이 환경에는 `python` 커맨드(3.13)가 설치되어 있음.

## 동작 방식 요약 (wiup_lib.py)

1. 검색어와 대상 필드로 ArcGIS `WHERE` 절 조립
   (`UPPER(필드) LIKE UPPER('%검색어%')`, 작은따옴표는 이스케이프 처리)
2. `resultOffset`을 늘려가며 `exceededTransferLimit`이 false가 될 때까지
   반복 조회 (서버가 한 번에 최대 100건만 주기 때문)
3. 사용자가 요청한 항목(광물 종류/위치/면적/허가 종류/생산 단계 등)을
   한글 라벨(`FIELD_ORDER`)로 매핑해 표시
4. `xlsx_bytes()`: 광구 속성 정보 1건을 단일 시트 엑셀로 변환 (경계좌표 제외)
5. `geojson_bytes()`: ArcGIS의 `rings` 좌표를 GeoJSON `Polygon.coordinates`
   구조로 변환 (좌표계 EPSG:4326 명시)

## QGIS로 가져오기

생성된 `.geojson` 파일은 QGIS에서 다음 중 아무 방법으로나 바로 열 수 있다:
- 탐색기에서 QGIS 지도 캔버스로 드래그 앤 드롭
- `레이어(Layer) > 레이어 추가(Add Layer) > 벡터 레이어 추가(Add Vector Layer)` →
  파일 선택
- 좌표계는 이미 EPSG:4326(WGS84)로 저장되어 있으므로 별도 좌표계 지정 없이
  바로 정합됨 (필요하면 프로젝트 좌표계에 맞춰 On-the-fly 재투영됨)

## QGIS로 가져오기

생성된 `.geojson` 파일은 QGIS에서 다음 중 아무 방법으로나 바로 열 수 있다:
- 탐색기에서 QGIS 지도 캔버스로 드래그 앤 드롭
- `레이어(Layer) > 레이어 추가(Add Layer) > 벡터 레이어 추가(Add Vector Layer)` →
  파일 선택
- 좌표계는 이미 EPSG:4326(WGS84)로 저장되어 있으므로 별도 좌표계 지정 없이
  바로 정합됨 (필요하면 프로젝트 좌표계에 맞춰 On-the-fly 재투영됨)

## 검증 이력

2026-08-12에 아래를 실제로 호출/실행해 정상 동작을 확인함:
- `WIUP_Publish` MapServer가 토큰 없이 공개 조회 가능함을 확인 (`f=json`,
  `f=geojson` 둘 다 지원)
- `nama_usaha`에 "ANTAM" 부분일치 검색 → 3건, 경계 폴리곤 좌표 포함해 정상 반환
- `komoditas`에 "Nikel" 검색 → 417건, `resultOffset` 페이지네이션으로 전건
  누락 없이 수집됨 (100건 단위로 5회 페이지 호출)
- `jenis_izin` distinct 값 확인: WIUP, IUP, IUPK, PKP2B, IPR, KK, WIUPK
  (사용자가 말한 "WIUP 종류"에 해당하는 실제 값 목록)
- "BUKIT MAKMUR ISTINDO NIKELTAMA" 검색 → 1건 정확히 매칭, 폴리곤 118개
  꼭짓점 정상 반환 (Sulawesi Tengah, Morowali, 니켈, 4778 Ha, 생산 운영 중)
- `wiup_lib.py`로 리팩터링 후 CLI(`--xlsx`+`--geojson` 동시 저장)와
  Streamlit 앱(`app.py`) 양쪽에서 재검증 완료
- `streamlit run app.py` 로 앱을 띄워 `curl localhost:8501` → HTTP 200 확인
  (로컬 실행 정상. 외부 공개 배포는 사용자 요청 시 별도 진행 예정)
