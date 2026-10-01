import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(page_title="时空能量分析", layout="wide")

st.markdown("""
<style>
/* ===== 桌面端 ===== */
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

/* ===== 手机端适配（屏幕宽度小于 768px）===== */
@media (max-width: 768px) {
    /* 列堆叠：左右两栏变成上下排列 */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    /* 九宫格缩小 */
    .qimen-cell {
        padding: 4px;
        font-size: 10px;
        line-height: 1.4;
    }
    .qimen-cell .palace-name {
        font-size: 12px;
        margin-bottom: 2px;
    }
    /* 标题缩小 */
    h1 {
        font-size: 22px !important;
    }
    h2 {
        font-size: 18px !important;
    }
    h3 {
        font-size: 16px !important;
    }
    /* 侧边栏输入框高度适配 */
    .stNumberInput input {
        font-size: 16px !important;
    }
    /* 隐藏 Plotly 工具栏（手机上没必要显示） */
    .modebar {
        display: none !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.title("🔮 时空能量分析")
st.caption("输入出生时间，查看方位能量与八字流年趋势")

with st.sidebar:
    st.header("📅 出生信息")
    year = st.number_input("出生年份", min_value=1900, max_value=2100, value=1990, step=1)
    month = st.number_input("出生月份", min_value=1, max_value=12, value=1, step=1)
    day = st.number_input("出生日期", min_value=1, max_value=31, value=1, step=1)
    hour = st.number_input("出生小时（0-23）", min_value=0, max_value=23, value=0, step=1)


# ===== 干支基础 =====
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

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

WUXING_COEF = {"火": 1.0, "木": 0.8, "土": -0.6, "金": -0.4, "水": -1.0}

PALACE_BENQI = {"巽": "木", "离": "火", "坤": "土", "震": "木", "中": "土",
                "兑": "金", "艮": "土", "坎": "水", "乾": "金"}

FEIXING_MAP = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土",
               6: "金", 7: "金", 8: "土", 9: "火"}


def get_year_ganzhi(year):
    gan = TIANGAN[(year - 1984) % 10]
    zhi = DIZHI[(year - 1984) % 12]
    return gan, zhi


def get_month_zhi_by_jieqi(month, day):
    jieqi_days = {1: 6, 2: 4, 3: 6, 4: 5, 5: 6, 6: 6,
                  7: 7, 8: 8, 9: 8, 10: 8, 11: 7, 12: 7}
    if day >= jieqi_days[month]:
        month_zhi_idx = month % 12
    else:
        month_zhi_idx = (month - 1) % 12
    return DIZHI[month_zhi_idx]


def get_day_ganzhi(year, month, day):
    dt = datetime(year, month, day)
    base = datetime(1900, 1, 1)
    delta = (dt - base).days
    gan = TIANGAN[(delta + 10) % 10]
    zhi = DIZHI[(delta + 10) % 12]
    return gan, zhi


def get_hour_ganzhi(day_gan, hour):
    day_gan_idx = TIANGAN.index(day_gan)
    hour_zhi_idx = ((hour + 1) // 2) % 12
    hour_gan_idx = (day_gan_idx * 2 + hour_zhi_idx) % 10
    return TIANGAN[hour_gan_idx], DIZHI[hour_zhi_idx]


def build_sizhu(year, month, day, hour):
    year_gan, year_zhi = get_year_ganzhi(year)
    month_zhi = get_month_zhi_by_jieqi(month, day)
    month_zhi_idx = DIZHI.index(month_zhi)
    year_gan_idx = TIANGAN.index(year_gan)
    month_gan_idx = (year_gan_idx * 2 + month_zhi_idx) % 10
    month_gan = TIANGAN[month_gan_idx]

    day_gan, day_zhi = get_day_ganzhi(year, month, day)
    hour_gan, hour_zhi = get_hour_ganzhi(day_gan, hour)

    return {
        "年": (year_gan, year_zhi),
        "月": (month_gan, month_zhi),
        "日": (day_gan, day_zhi),
        "时": (hour_gan, hour_zhi),
    }


def compute_daymaster_strength(sizhu):
    score = {"火": 0.0, "木": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}
    for zhu_name, (gan, zhi) in sizhu.items():
        if gan in TIANGAN_WUXING:
            if zhu_name != "日":
                score[TIANGAN_WUXING[gan]] += 1.0
        if zhi in DIZHI_CANGGAN:
            for cg, w in DIZHI_CANGGAN[zhi].items():
                score[TIANGAN_WUXING[cg]] += w
    return score


def compute_palace_score(palace, year):
    bq = PALACE_BENQI[palace]
    bq_score = WUXING_COEF.get(bq, 0)

    feixing = (year - 2026) % 9 + 1
    fs_wx = FEIXING_MAP.get(feixing, "")
    fs_score = WUXING_COEF.get(fs_wx, 0) * 0.3

    return bq_score + fs_score


def get_dayun_list(sizhu):
    month_gan, month_zhi = sizhu["月"]
    mg_idx = TIANGAN.index(month_gan)
    mz_idx = DIZHI.index(month_zhi)
    dayun = []
    for i in range(8):
        g = TIANGAN[(mg_idx - 1 - i) % 10]
        z = DIZHI[(mz_idx - 1 - i) % 12]
        dayun.append((g, z))
    return dayun


def get_dayun(age, sizhu):
    dayun = get_dayun_list(sizhu)
    idx = min((age - 1) // 10, len(dayun) - 1)
    return dayun[idx]


# ===== 主界面 =====
sizhu = build_sizhu(year, month, day, hour)
daymaster_gan = sizhu["日"][0]
daymaster_wx = TIANGAN_WUXING[daymaster_gan]

st.caption(f"出生：{year}年{month}月{day}日{hour}时　｜　"
           f"四柱：{sizhu['年'][0]}{sizhu['年'][1]} "
           f"{sizhu['月'][0]}{sizhu['月'][1]} "
           f"{sizhu['日'][0]}{sizhu['日'][1]} "
           f"{sizhu['时'][0]}{sizhu['时'][1]}　｜　日主：{daymaster_gan}（{daymaster_wx}）")

strength = compute_daymaster_strength(sizhu)
st.caption(f"日主强弱：火 {strength['火']:.2f} ｜ 木 {strength['木']:.2f} ｜ "
           f"土 {strength['土']:.2f} ｜ 金 {strength['金']:.2f} ｜ 水 {strength['水']:.2f}")

col1, col2 = st.columns([3, 4])

with col1:
    st.subheader("🧭 空间维度 · 方位能量")

    st.markdown("**九宫格（基于出生年的方位分）**")

    palace_layout = [
        ("巽", "东南", "#4caf50"), ("离", "正南", "#ff5252"), ("坤", "西南", "#ffc107"),
        ("震", "正东", "#26a69a"), ("中", "中央", "#8d6e63"), ("兑", "正西", "#e8e8e8"),
        ("艮", "东北", "#9e9e9e"), ("坎", "正北", "#2196f3"), ("乾", "西北", "#ffd54f"),
    ]

    html = '<div class="qimen-grid">'
    for name, direction, color in palace_layout:
        bq = PALACE_BENQI[name]
        score = compute_palace_score(name, year)
        html += (
            f'<div class="qimen-cell" style="border-color: {color};">'
            f'<div class="palace-name" style="color: {color};">{name}宫</div>'
            f'<div style="font-size:11px;color:#888;">{direction}</div>'
            f'<div style="font-size:12px;color:#ddd;">本气：{bq}</div>'
            f'<div style="font-size:12px;color:#ffb74d;">{year}年分：{score:+.2f}</div>'
            f'</div>'
        )
    html += '</div>'
    st.html(html)

    st.caption("方位分 = 宫位本气分 + 流年飞星分，每年变化。")

with col2:
    st.subheader("📈 宫位 60 年趋势")

    palace_options = ["巽宫（东南·木）", "离宫（正南·火）", "坤宫（西南·土）",
                      "震宫（正东·木）", "中宫（中央·土）", "兑宫（正西·金）",
                      "艮宫（东北·土）", "坎宫（正北·水）", "乾宫（西北·金）"]
    selected = st.selectbox("选择宫位", palace_options)
    palace_names = ["巽", "离", "坤", "震", "中", "兑", "艮", "坎", "乾"]
    selected_palace = palace_names[palace_options.index(selected)]

    years = list(range(year, year + 60))
    flow_scores = []
    palace_scores = []
    dayun_scores = []

    for yi, y in enumerate(years):
        y_gan, y_zhi = get_year_ganzhi(y)
        age = y - year + 1

        p_score = compute_palace_score(selected_palace, y)
        palace_scores.append(p_score)

        dy_gan, dy_zhi = get_dayun(age, sizhu)
        dy_score = 0.0
        if TIANGAN_WUXING.get(dy_gan):
            dy_score += WUXING_COEF[TIANGAN_WUXING[dy_gan]] * 1.0
        if DIZHI_WUXING.get(dy_zhi):
            dy_score += WUXING_COEF[DIZHI_WUXING[dy_zhi]] * 0.8
        dayun_scores.append(dy_score)

        y_wx = TIANGAN_WUXING.get(y_gan, "")
        y_score = WUXING_COEF.get(y_wx, 0) * 0.5

        y_factor = 1.0 + y_score * 0.8
        dy_factor = 1.0 + dy_score * 0.5
        total = p_score * y_factor * dy_factor
        flow_scores.append(total)

    st.markdown(f"**当前方位分（{year}年）**：{compute_palace_score(selected_palace, year):+.2f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=flow_scores,
        mode="lines", line=dict(color="#ffb74d", width=2.5),
        name="综合能量",
    ))
    fig.add_trace(go.Scatter(
        x=years, y=palace_scores,
        mode="lines", line=dict(color="#66bb6a", width=1, dash="dot"),
        name="方位分（随流年）",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#555")
    fig.update_layout(
        height=400, template="plotly_dark",
        margin=dict(l=60, r=20, t=30, b=40),
        xaxis_title="年份", yaxis_title="综合能量",
    )
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True,
        'displayModeBar': False,
    })

    st.caption("橙线=综合能量（方位分 × 流年因子 × 大运因子）｜ 绿点线=方位分")

st.divider()
st.markdown("""
**联动逻辑**：

- **方位分**：从奇门盘算，宫位本气 × 五行权重 + 流年飞星
- **流年因子**：1 + 流年天干五行权重 × 0.8
- **大运因子**：1 + 大运干支五行权重 × 0.5
- **综合能量** = 方位分 × 流年因子 × 大运因子

不同宫位，因为方位分不同，曲线形状会不同。仅作能量起伏演示，不构成预测。
""")
