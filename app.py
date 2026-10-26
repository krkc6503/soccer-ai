        use_container_width=True
    )

# ==========================================
# 市場価値 TOP10 グラフ
# ==========================================

    st.divider()
    st.header("📊 市場価値 TOP10")

    top10 = (
        tm.sort_values(
            "market_value_in_eur",
            ascending=False
        )
        .head(10)
        .copy()
    )

    top10["市場価値(M€)"] = (
        top10["market_value_in_eur"] / 1_000_000
    )

    chart = top10.set_index("name")["市場価値(M€)"]

    st.bar_chart(chart)
if page == "データ閲覧":
# ==========================================
# Transfermarkt 基本情報
# ==========================================

    st.divider()
    st.subheader("🌍 Transfermarktデータ")

    st.metric(
        "登録選手数",
        len(tm)
    )

    st.metric(
        "EAFC27登録選手数",
        len(ea)
    )
# ==========================================
# CSV閲覧
# ==========================================

    st.divider()
    st.header("📄 データ閲覧")

    with st.expander("EAFC27 データを見る"):
        st.dataframe(
            ea,
            use_container_width=True
        )

    with st.expander("Transfermarkt データを見る"):
        st.dataframe(
            tm,
            use_container_width=True
        )
if page == "データ閲覧":
# ==========================================
# CSVダウンロード
# ==========================================

    st.divider()
    st.header("📥 CSVダウンロード")

    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            label="EAFC27 CSV",
            data=ea.to_csv(index=False).encode("utf-8-sig"),
            file_name="EAFC27_export.csv",
            mime="text/csv"
        )

    with col2:

        st.download_button(
            label="Transfermarkt CSV",
            data=tm.to_csv(index=False).encode("utf-8-sig"),
            file_name="Transfermarkt_export.csv",
            mime="text/csv"
        )

# ==========================================
# データ件数
# ==========================================

    st.divider()
    st.header("📊 データ件数")

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "EAFC26選手数",
            len(ea)
        )

    with c2:
        st.metric(
            "Transfermarkt選手数",
            len(tm)
        )

# ==========================================
# 列名確認（デバッグ用）
# ==========================================

    with st.expander("🛠 デバッグ情報"):

        st.write("EAFC27 Columns")
        st.write(list(ea.columns))

        st.write("Transfermarkt Columns")
        st.write(list(tm.columns))

# ==========================================
# フッター
# ==========================================

st.divider()

