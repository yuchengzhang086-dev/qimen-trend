import streamlit as st
import plotly.graph_objects as go
import numpy as np
import re
from kinqimen import kinqimen

st.set_page_config(page_title="时空能量分析", layout="wide")

st.markdown("""
<style>
.qimen-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
    max-width: 100%;
}
.qimen-cell {
    border: 1px solid #444;
    padding: 8px;
    text-align: center;
    background: #1a1f2e;
    color: #ddd;
    font-size: 13px;
    line-height: 1.6;
    border-radius: 4px;
}
.qimen-cell .palace-name {
    font-size: 15px;
    font-weight: bold;
    margin-bottom: 4px;
}
.qimen-cell .door { color: #4caf50; }
.qimen-cell .star { color: #ff5252; }
.qimen-cell .god { color: #42a5f5; }
</style>
""", unsafe_allow_html=True)

st.title("🔮 时空能量分析")
st.caption("奇门定方位，八字定时间，两者通过五行联动")

with st.sidebar:
    st.header("📅 出生信息")
    year = st.number_input("出生年份", min_value=1900, max_value=2100, value=1990, step=1)
    month = st.number_input("出生月份", min_value=1, max_value=12, value=1, step=1)
    day = st.number_input("出生日期", min_value=1, max_value=31, value=1, step=1)
    hour = st.number_input("出生小时（0-23）", min_value=0, max_value=23, value=0, step=1)


def get_qimen_pan(year, month, day, hour):
    try:
        qimen = kinqimen.Qimen(year, month, day, hour)
        return qimen.pan()
    except Exception as e:
        return {"error": str(e)}


# ===== 基础对照 =====
TIANGAN_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火",
                  "戊": "土", "己": "土", "庚": "金", "辛": "金",
                  "壬": "水", "癸": "水"}

DIZHI_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木",
                "辰": "土", "巳": "火", "午": "火", "未": "土",
                "申": "金", "酉": "金", "戌": "土", "亥": "水"}

DIZHI_CANGGAN = {
    "子": {"癸": 1.0}, "丑": {"己": 0.6, "癸": 0.3, "辛": 0.1},
    "寅": {"甲": 0.6, "丙": 0.3, "戊": 0.1}, "卯": {"乙": 1.0},
    "辰": {"戊": 0.6, "乙": 0.3, "癸": 0.1}, "巳": {"丙": 0.6, "庚": 0.3, "戊": 0.1},
    "午": {"丁": 0.7, "己": 0.3}, "未": {"己": 0.6, "丁": 0.3, "乙": 0.1},
    "申": {"庚": 0.6, "壬": 0.3, "戊": 0.1}, "酉": {"辛": 1.0},
    "戌": {"戊": 0.6, "辛": 0.3, "丁": 0.1}, "亥": {"壬": 0.7, "甲": 0.3},
}

WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

MONTH_STRENGTH = {
    "寅": {"火": 0.75, "木": 1.0, "土": 0.2, "金": 0.35, "水": 0.5},
    "卯": {"火": 0.75, "木": 1.0, "土": 0.2, "金": 0.35, "水": 0.5},
    "辰": {"火": 0.5, "木": 0.35, "土": 1.0, "金": 0.75, "水": 0.2},
    "巳": {"火": 1.0, "木": 0.5, "土": 0.75, "金": 0.2, "水": 0.35},
    "午": {"火": 1.0, "木": 0.5, "土": 0.75, "金": 0.2, "水": 0.35},
    "未": {"火": 0.5, "木": 0.35, "土": 1.0, "金": 0.75, "水": 0.2},
    "申": {"火": 0.35, "木": 0.2, "土": 0.5, "金": 1.0, "水": 0.75},
    "酉": {"火": 0.35, "木": 0.2, "土": 0.5, "金": 1.0, "水": 0.75},
    "戌": {"火": 0.5, "木": 0.35, "土": 1.0, "金": 0.75, "水": 0.2},
    "亥": {"火": 0.2, "木": 0.75, "土": 0.35, "金": 0.5, "水": 1.0},
    "子": {"火": 0.2, "木": 0.75, "土": 0.35, "金": 0.5, "水": 1.0},
    "丑": {"火": 0.5, "木": 0.35, "土": 1.0, "金": 0.75, "水": 0.2},
}

ZHI_SEQ = ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"]
GAN_SEQ = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

WUXING_COEF = {"火": 1.0, "木": 0.8, "土": -0.6, "金": -0.4, "水": -1.0}

PALACE_BENQI = {"巽": "木", "离": "火", "坤": "土", "震": "木", "中": "土",
                "兑": "金", "艮": "土", "坎": "水", "乾": "金"}


def extract_sizhu(ganzhi_str):
    ganzhi_str = ganzhi_str.replace(" ", "").replace("\u3000", "")
    GAN = "甲乙丙丁戊己庚辛壬癸"
    ZHI = "子丑寅卯辰巳午未申酉戌亥"
    pattern = f'([{GAN}])([{ZHI}])'
    matches = re.findall(pattern, ganzhi_str)
    if len(matches) >= 4:
        return {"年": matches[0], "月": matches[1], "日": matches[2], "时": matches[3]}
    return None


def get_year_ganzhi(year):
    gan = GAN_SEQ[(year - 1984) % 10]
    zhi_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    zhi = zhi_list[(year - 1984) % 12]
    return gan, zhi


def compute_palace_fixed_score(pan, palace):
    tian_gan = pan.get("天盤", {}).get(palace, "")
    di_gan = pan.get("地盤", {}).get(palace, "")
    bq_wx = PALACE_BENQI.get(palace, "")

    tian_wx = TIANGAN_WUXING.get(tian_gan, "")
    di_wx = TIANGAN_WUXING.get(di_gan, "")

    score = 0.0
    if tian_wx:
        score += WUXING_COEF.get(tian_wx, 0) * 1.0
    if di_wx:
        score += WUXING_COEF.get(di_wx, 0) * 1.0
    if bq_wx:
        score += WUXING_COEF.get(bq_wx, 0) * 1.5

    return score, tian_wx, di_wx, bq_wx


def get_dayun(age, sizhu):
    month_gan, month_zhi = sizhu["月"]
    month_gan_idx = GAN_SEQ.index(month_gan) if month_gan in GAN_SEQ else 0
    month_zhi_idx = ZHI_SEQ.index(month_zhi) if month_zhi in ZHI_SEQ else 0

    dayun_list = []
    for i in range(8):
        g = GAN_SEQ[(month_gan_idx - 1 - i) % 10]
        z = ZHI_SEQ[(month_zhi_idx - 1 - i) % 12]
        dayun_list.append((g, z))

    idx = min((age - 1) // 10, len(dayun_list) - 1)
    return dayun_list[idx]


def compute_palace_60year(palace, pan, daymaster_gan, sizhu, start_year):
    years = list(range(start_year, start_year + 60))
    palace_score, _, _, _ = compute_palace_fixed_score(pan, palace)

    flow_scores = []
    dayun_scores = []
    for y in years:
        year_gan, year_zhi = get_year_ganzhi(y)
        age = y - start_year + 1

        dayun_gan, dayun_zhi = get_dayun(age, sizhu)
        dayun_wx_gan = TIANGAN_WUXING.get(dayun_gan, "")
        dayun_wx_zhi = DIZHI_WUXING.get(dayun_zhi, "")
        dayun_score = 0.0
        if dayun_wx_gan:
            dayun_score += WUXING_COEF[dayun_wx_gan] * 1.0
        if dayun_wx_zhi:
            dayun_score += WUXING_COEF[dayun_wx_zhi] * 0.8
        dayun_scores.append(dayun_score)

        year_wx = TIANGAN_WUXING.get(year_gan, "")
        year_score = WUXING_COEF.get(year_wx, 0) * 0.5

        total = palace_score + dayun_score + year_score
        flow_scores.append(total)

    return years, flow_scores, palace_score, dayun_scores


# ===== 主界面 =====
pan = get_qimen_pan(year, month, day, hour)

if "error" in pan:
    st.error(f"排盘失败：{pan['error']}")
    st.stop()

ganzhi_str = pan.get("干支", "")
sizhu = extract_sizhu(ganzhi_str)

if not sizhu:
    st.error(f"无法提取四柱八字。原始干支：`{ganzhi_str}`")
    st.stop()

daymaster_gan = sizhu["日"][0]

st.caption(f"当前输入：{year}年{month}月{day}日{hour}时　｜　四柱：{ganzhi_str}　｜　日主：{daymaster_gan}")

col1, col2 = st.columns([3, 4])

with col1:
    st.subheader("🧭 空间维度 · 奇门九宫")

    st.markdown(f"**节气**：{pan.get('節氣', '—')}")
    st.markdown(f"**格局**：{pan.get('排局', '—')}")

    st.markdown("---")
    st.markdown("**九宫格**")

    palace_layout = [
        ("巽", "东南", "#4caf50"), ("離", "正南", "#ff5252"), ("坤", "西南", "#ffc107"),
        ("震", "正东", "#26a69a"), ("中", "中央", "#8d6e63"), ("兌", "正西", "#e8e8e8"),
        ("艮", "东北", "#9e9e9e"), ("坎", "正北", "#2196f3"), ("乾", "西北", "#ffd54f"),
    ]

    html = '<div class="qimen-grid">'
    for name, direction, color in palace_layout:
        door = pan.get("門", {}).get(name, "—")
        star = pan.get("星", {}).get(name, "—")
        god = pan.get("神", {}).get(name, "—")
        tianpan_val = pan.get("天盤", {}).get(name, "—")
        dipan_val = pan.get("地盤", {}).get(name, "—")
        score, twx, dwx, bw = compute_palace_fixed_score(pan, name)
        html += (
            f'<div class="qimen-cell" style="border-color: {color};">'
            f'<div class="palace-name" style="color: {color};">{name}宫'
            f'<br><span style="font-size:10px;color:#888">{direction}</span></div>'
            f'<div class="god">能量：{god}</div>'
            f'<div class="star">星象：{star}</div>'
            f'<div class="door">出口：{door}</div>'
            f'<div style="font-size:12px;color:#aaa;margin-top:4px;">'
            f'天{twx or "—"} 地{dwx or "—"} 本{bw}</div>'
            f'<div style="font-size:12px;color:#ffb74d;margin-top:2px;">'
            f'方位分：{score:+.2f}</div>'
            f'</div>'
        )
    html += '</div>'
    st.html(html)

    st.markdown("---")
    st.markdown("### 🧭 方位能量排序")

    palace_energy = []
    for name in ["巽", "離", "坤", "震", "中", "兌", "艮", "坎", "乾"]:
        score, twx, dwx, bw = compute_palace_fixed_score(pan, name)
        palace_energy.append({
            "name": name,
            "direction": {"巽": "东南", "離": "正南", "坤": "西南", "震": "正东",
                          "中": "中央", "兌": "正西", "艮": "东北", "坎": "正北", "乾": "西北"}[name],
            "wuxing": f"天{twx or '—'} 地{dwx or '—'} 本{bw}",
            "score": score,
        })

    sorted_palaces = sorted(palace_energy, key=lambda x: x["score"], reverse=True)

    cols_energy = st.columns(3)
    for i, p in enumerate(sorted_palaces):
        with cols_energy[i % 3]:
            if p["score"] > 1.0:
                tag, tag_color = "🟢 有利", "#66bb6a"
            elif p["score"] > 0:
                tag, tag_color = "🟡 偏有利", "#ffca28"
            elif p["score"] > -1.0:
                tag, tag_color = "🟠 偏不利", "#ff9800"
            else:
                tag, tag_color = "🔴 不利", "#ef5350"

            st.markdown(
                f"""<div style="border:1px solid #555; border-radius:6px;
                padding:10px; margin:4px 0; background:#1a1f2e;">
                <div style="font-size:15px;font-weight:bold;color:#ddd;">
                {p['direction']}（{p['name']}宫）</div>
                <div style="color:#aaa;font-size:12px;">{p['wuxing']}</div>
                <div style="color:#ffb74d;font-size:12px;">分数：{p['score']:+.2f}</div>
                <div style="color:{tag_color};font-size:13px;margin-top:4px;">{tag}</div>
                </div>""",
                unsafe_allow_html=True,
            )

with col2:
    st.subheader("📈 宫位趋势 · 时空联动")
    st.caption("每个宫位的 60 年趋势 = 方位分（固定）+ 大运分（10年一变）+ 流年分（每年变）")

    palace_options = ["巽宫（东南·木）", "离宫（正南·火）", "坤宫（西南·土）",
                      "震宫（正东·木）", "中宫（中央·土）", "兑宫（正西·金）",
                      "艮宫（东北·土）", "坎宫（正北·水）", "乾宫（西北·金）"]
    selected = st.selectbox("选择宫位", palace_options)
    palace_names = ["巽", "離", "坤", "震", "中", "兌", "艮", "坎", "乾"]
    palace_index = palace_options.index(selected)
    selected_palace = palace_names[palace_index]

    years_list, flow_scores, palace_score, dayun_scores = compute_palace_60year(
        selected_palace, pan, daymaster_gan, sizhu, year
    )

    st.markdown(f"**该宫方位分（固定）**：{palace_score:+.2f}")

    fig_flow = go.Figure()
    fig_flow.add_trace(go.Scatter(
        x=years_list, y=flow_scores,
        mode="lines", line=dict(color="#ffb74d", width=2.5),
        name="综合能量",
    ))
    fig_flow.add_trace(go.Scatter(
        x=years_list, y=[palace_score + d for d in dayun_scores],
        mode="lines", line=dict(color="#42a5f5", width=1.5, dash="dash"),
        name="方位+大运基线",
    ))
    fig_flow.add_hline(y=palace_score, line_dash="dot", line_color="#888",
                       annotation_text=f"方位分 {palace_score:+.2f}")
    fig_flow.add_hline(y=0, line_dash="dot", line_color="#555")
    fig_flow.update_layout(
        height=400, template="plotly_dark",
        margin=dict(l=60, r=20, t=30, b=40),
        xaxis_title="年份", yaxis_title="综合能量",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_flow, use_container_width=True)

    st.caption("橙线 = 综合能量（方位 + 大运 + 流年）｜ 蓝虚线 = 方位 + 大运基线 ｜ 灰点线 = 方位分")

st.divider()
st.markdown("""
**联动逻辑**：

- **方位分（固定）**：从奇门盘算，天盘干×1 + 地盘干×1 + 本气×1.5
- **大运分（10年一变）**：从八字大运算，大运天干×1 + 大运地支×0.8
- **流年分（每年变）**：从八字流年算，流年天干×0.5

**综合能量 = 方位分 + 大运分 + 流年分**

同一个流年，落在不同宫位上，因为方位分不同，结果不同。
""")