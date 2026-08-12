# -*- coding: utf-8 -*-
"""
ESDM Minerba Geoportal WIUP 조회 웹앱 (Streamlit).

입력: 회사명(또는 위치/Single ID 등)
출력: 1) 광구정보 엑셀(.xlsx)  2) 광구 경계좌표 GeoJSON(.geojson, QGIS 바로 로드 가능)

실행:
    streamlit run app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import pydeck as pdk
import streamlit as st

import wiup_lib as wl

st.set_page_config(page_title="ESDM Minerba 조회", page_icon="⛏️", layout="wide")

st.markdown(
    """
    <style>
    .st-key-detail_select_box div[data-baseweb="select"] > div {
        background-color: #d6f0ff !important;
        border-color: #4fb3e8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⛏️ 인도네시아 ESDM Minerba 조회")
st.caption(
    "인도네시아 에너지광물자원부(ESDM) Minerba Geoportal의 공개 데이터를 실시간으로 조회합니다. "
    "회사명을 입력하면 광구(WIUP/IUP 등) 정보와 경계 좌표를 확인하고 파일로 내려받을 수 있습니다."
)

with st.form("search_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        term = st.text_input(
            "검색어",
            placeholder="예: BUKIT MAKMUR ISTINDO NIKELTAMA",
            help="기본은 회사명 검색입니다. 오른쪽에서 다른 항목으로 바꿀 수 있습니다.",
        )
    with col2:
        field_options = list(wl.SEARCHABLE_FIELDS.keys()) + ["all"]
        field_labels = {**wl.SEARCHABLE_FIELDS, "all": "전체(회사명+위치+Single ID)"}
        field = st.selectbox(
            "검색 대상",
            options=field_options,
            index=0,
            format_func=lambda k: field_labels[k],
        )
    exact = st.checkbox("정확히 일치하는 것만 검색", value=False)
    submitted = st.form_submit_button("🔍 검색", use_container_width=True)

with st.expander("💡 검색 대상별 검색어 예시"):
    st.markdown("**광물 종류** — 원본 데이터가 인도네시아어라 아래처럼 인도네시아어 표기로 입력 (대소문자 무관)")
    mineral_cols = st.columns(3)
    for i, (kr, term_ex) in enumerate(wl.MINERAL_SEARCH_EXAMPLES):
        with mineral_cols[i % 3]:
            st.markdown(f"- **{kr}**: `{term_ex}`")

    st.markdown("---")
    st.markdown("**허가 종류** — 아래 7가지 값 중 하나를 그대로 입력")
    permit_cols = st.columns(3)
    for i, (kr, term_ex) in enumerate(wl.PERMIT_TYPE_EXAMPLES):
        with permit_cols[i % 3]:
            st.markdown(f"- {kr}: `{term_ex}`")

    st.markdown("---")
    st.markdown("**생산단계** — 아래 7가지 값 중 하나를 그대로 입력")
    stage_cols = st.columns(3)
    for i, (kr, term_ex) in enumerate(wl.PRODUCTION_STAGE_EXAMPLES):
        with stage_cols[i % 3]:
            st.markdown(f"- **{kr}**: `{term_ex}`")

if submitted:
    term_clean = term.strip()
    if not term_clean:
        st.warning("검색어를 입력해주세요.")
        st.session_state.pop("features", None)
    else:
        with st.spinner("ESDM Minerba Geoportal 조회 중..."):
            try:
                features = wl.search(term_clean, field=field, exact=exact, geometry=True)
                st.session_state["features"] = features
                st.session_state["searched_term"] = term_clean
            except wl.WiupApiError as e:
                st.error(f"조회 중 오류가 발생했습니다: {e}")
                st.session_state.pop("features", None)

features = st.session_state.get("features")

if features is not None:
    if not features:
        st.info("검색 결과가 없습니다. 검색어나 검색 대상을 확인해주세요.")
    else:
        st.success(f"'{st.session_state.get('searched_term')}' 검색 결과: 총 {len(features)}건")

        rows = []
        for f in features:
            a = f.get("attributes", {})
            rows.append(
                {
                    "회사명": a.get("nama_usaha"),
                    "허가종류": a.get("jenis_izin"),
                    "광물종류": a.get("komoditas"),
                    "주": a.get("nama_prov"),
                    "군/시": a.get("nama_kab"),
                    "면적(Ha)": a.get("luas_sk"),
                    "생산단계": a.get("kegiatan"),
                    "Single ID": a.get("kode_wiup"),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        option_labels = []
        for i, f in enumerate(features):
            a = f.get("attributes", {})
            option_labels.append(f"{a.get('nama_usaha')}  |  {a.get('kode_wiup')}  |  {a.get('nama_kab')}")
        idx = 0
        if len(features) > 1:
            with st.container(key="detail_select_box"):
                selected = st.selectbox(
                    "🔎 상세 정보를 볼 광구를 선택하세요",
                    options=range(len(features)),
                    format_func=lambda i: option_labels[i],
                )
            idx = selected

        feat = features[idx]
        attrs = feat.get("attributes", {})

        st.subheader(f"📋 {attrs.get('nama_usaha')} — 광구 상세 정보")
        info_rows = [(label, attrs.get(key)) for key, label in wl.FIELD_ORDER]
        info_rows.append(("허가 시작일", wl.epoch_ms_to_date(attrs.get("tgl_berlaku"))))
        info_rows.append(("허가 만료일", wl.epoch_ms_to_date(attrs.get("tgl_akhir"))))
        st.table(pd.DataFrame(info_rows, columns=["항목", "값"]).set_index("항목"))

        geom = feat.get("geometry")
        rings = geom.get("rings") if geom else None
        if rings:
            ring = rings[0]
            polygon_coords = [[pt[0], pt[1]] for pt in ring]
            centroid_lon = sum(p[0] for p in polygon_coords) / len(polygon_coords)
            centroid_lat = sum(p[1] for p in polygon_coords) / len(polygon_coords)

            layer = pdk.Layer(
                "PolygonLayer",
                data=[{"polygon": polygon_coords}],
                get_polygon="polygon",
                get_fill_color=[255, 140, 0, 90],
                get_line_color=[230, 80, 0],
                line_width_min_pixels=2,
                pickable=True,
                stroked=True,
                filled=True,
            )
            view_state = pdk.ViewState(longitude=centroid_lon, latitude=centroid_lat, zoom=11)
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
        else:
            st.warning("이 레코드에는 경계 좌표(geometry)가 없습니다.")

        safe_name = wl.safe_filename(attrs.get("nama_usaha") or attrs.get("kode_wiup"))

        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button(
                "📊 광구정보 엑셀(.xlsx) 다운로드",
                data=wl.xlsx_bytes(attrs),
                file_name=f"{safe_name}_WIUP.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_b:
            st.download_button(
                "🗺️ 경계좌표 GeoJSON 다운로드",
                data=wl.geojson_bytes([feat]),
                file_name=f"{safe_name}.geojson",
                mime="application/geo+json",
                use_container_width=True,
                disabled=not rings,
            )

        st.markdown("&nbsp;")
        st.markdown(f"**📦 검색 결과 전체 일괄 다운로드** ({len(features)}건)")
        safe_term = wl.safe_filename(st.session_state.get("searched_term"))
        col_c, col_d = st.columns(2)
        with col_c:
            st.download_button(
                f"📊 전체 {len(features)}건 엑셀(.xlsx) 다운로드",
                data=wl.xlsx_bytes_multi(features),
                file_name=f"{safe_term}_WIUP_전체{len(features)}건.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_d:
            st.download_button(
                f"🗺️ 전체 {len(features)}건 GeoJSON 다운로드",
                data=wl.geojson_bytes(features),
                file_name=f"{safe_term}_전체{len(features)}건.geojson",
                mime="application/geo+json",
                use_container_width=True,
            )

st.divider()
st.caption(
    "데이터 출처: ESDM Minerba Geoportal · Ditjen Mineral dan Batubara — WIUP_Publish "
    "(공개 ArcGIS REST 서비스, 매 검색마다 실시간 조회, 별도 로그인/토큰 불필요)"
)
