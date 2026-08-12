# ESDM Minerba WIUP 조회

인도네시아 에너지광물자원부(ESDM) Minerba Geoportal(https://geoportal.esdm.go.id/minerba/)의
공개 ArcGIS REST 데이터를 실시간으로 조회하는 Streamlit 웹앱입니다.

회사명(광구명)을 입력하면:
- **광구 정보**: 광물 종류, 위치, 면적(Ha), 허가 종류(WIUP/IUP/IUPK/PKP2B/IPR/KK), 생산 단계 등을 조회해 **엑셀(.xlsx)**로 다운로드
- **광구 경계 좌표**(폴리곤)를 **GeoJSON**으로 다운로드 → QGIS 등 GIS 툴에 바로 로드 가능
- 검색 결과가 여러 건이면 개별 다운로드뿐 아니라 **전체 결과 일괄 다운로드**(엑셀/GeoJSON)도 가능
- 지도에서 선택한 광구의 경계를 바로 미리보기

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속.

## 배포 (Streamlit Community Cloud)

1. 이 저장소를 GitHub(공개 또는 비공개)에 push
2. https://share.streamlit.io 에서 GitHub 계정으로 로그인 → "New app"
3. 저장소/브랜치 선택, Main file path에 `app.py` 지정 → Deploy
4. 몇 분 뒤 `https://<앱이름>.streamlit.app` 형태의 공개 URL 발급
   → 이 링크만 있으면 로그인 없이 누구나 접속해 사용 가능
5. 이후 GitHub에 push할 때마다 앱이 자동으로 재배포됨

## 코드 구조

```
wiup_lib.py    # 검색 / GeoJSON 변환 / 엑셀 변환 공용 라이브러리
app.py         # Streamlit 웹앱 (배포 대상)
requirements.txt
.claude/skills/esdm-wiup-lookup/
  ├── SKILL.md               # Claude Code 스킬 문서
  └── scripts/search_wiup.py # CLI 버전 (동일 라이브러리 사용)
```

## 데이터 출처

ESDM Minerba Geoportal의 `WIUP_Publish` ArcGIS MapServer(공개, 토큰 불필요)를
매 검색마다 실시간으로 호출합니다. 별도로 데이터를 수집/저장하지 않습니다.
