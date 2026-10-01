import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

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
    border: 2px solid #444;
    padding: 8px;
    text-align: center;
    background: #1a1f2e;
    color: #ddd;
    font-size: 13px;
    line-height: 1.6;
    border-radius: 6px;
}
.qimen-cell .palace-name {
    font-size: 15px;
    font-weight: bold;
    margin-bottom: 4px;
}
.qimen-cell .score {
    font-size: 20px;
    font-weight: bold;
    margin: 4px 0;
}
.qimen-cell .level {
    font-size: 12px;
    margin-top: 4px;
}

@media (max-width: 768px) {
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .qimen-cell { padding: 4px; font-size: 10px; }
    .qimen-cell .palace-name { font-size: 12px; }
    .qimen-cell .score { font-size: 16px; }
    .qimen-cell .level { font-size: 10px; }
    h1 { font-size: 22px !important; }
    h2 { font-size: 18px !important; }
    h3 { font-size: 16px !important; }
}
</style>
""", unsafe_allow_html=True)

st.title("🔮 时空能量分析")
st.caption("输入出生时间，查看每年哪个方位最有利")


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


def compute_palace_energy(palace, target_year, birth_year, sizhu):
    """
    乘法联动 + 放大系数
    综合能量 = (方位分 × 流年因子 × 大运因子) × 5.0
    不同宫位曲线形状不同
    """
    # 方位分
    bq = PALACE_BENQI[palace]
    bq_score = WUXING_COEF.get(bq, 0)
    feixing = (target_year - 2026) % 9 + 1
    fs_wx = FEIXING_MAP.get(feixing, "")
    fs_score = WUXING_COEF.get(fs_wx, 0) * 0.3
    palace_score = bq_score + fs_score

    # 大运分
    age = target_year - birth_year + 1
    dy_gan, dy_zhi = get_dayun(age, sizhu)
    dy_score = 0.0
    if TIANGAN_WUXING.get(dy_gan):
        dy_score += WUXING_COEF[TIANGAN_WUXING[dy_gan]] * 0.5
    if DIZHI_WUXING.get(dy_zhi):
        dy_score += WUXING_COEF[DIZHI_WUXING[dy_zhi]] * 0.4

    # 流年分
    y_gan, _ = get_year_ganzhi(target_year)
    y_wx = TIANGAN_WUXING.get(y_gan, "")
    y_score = WUXING_COEF.get(y_wx, 0)

    # 乘法因子
    y_factor = 1.0 + y_score * 0.8
    dy_factor = 1.0 + dy_score * 0.5

    # 乘法 + 放大
    total = palace_score * y_factor * dy_factor * 5.0
    return total


def get_level(score):
    if score > 3.0:
        return "🟢 有利", "#66bb6a"
    elif score > 1.0:
        return "🟡 偏有利", "#ffca28"
    elif score > -1.0:
        return "🟠 偏不利", "#ff9800"
    else:
        return "🔴 不利", "#ef5350"


# ===== 主界面 =====
st.markdown("### 📅 第一步：输入出生信息")

col_y, col_m, col_d, col_h = st.columns(4)
with col_y:
    year = st.number_input("出生年份", min_value=1900, max_value=2100, value=1990, step=1)
with col_m:
    month = st.number_input("出生月份", min_value=1, max_value=12, value=1, step=1)
with col_d:
    day = st.number_input("出生日期", min_value=1, max_value=31, value=1, step=1)
with col_h:
    hour = st.number_input("出生小时（0-23）", min_value=0, max_value=23, value=0, step=1)

st.caption("提示：出生时间用于计算四柱和日主，越准确结果越贴合。")

sizhu = build_sizhu(year, month, day, hour)
daymaster_gan = sizhu["日"][0]
daymaster_wx = TIANGAN_WUXING[daymaster_gan]

st.markdown("---")
st.markdown("### 📊 第二步：查看结果")

st.caption(f"出生：{year}年{month}月{day}日{hour}时　｜　"
           f"四柱：{sizhu['年'][0]}{sizhu['年'][1]} "
           f"{sizhu['月'][0]}{sizhu['月'][1]} "
           f"{sizhu['日'][0]}{sizhu['日'][1]} "
           f"{sizhu['时'][0]}{sizhu['时'][1]}　｜　日主：{daymaster_gan}（{daymaster_wx}）")

current_year = datetime.now().year
target_year = st.slider("查看年份", min_value=year, max_value=year + 60,
                        value=max(current_year, year), step=1)

st.caption("💡 拖动上面的滑块，可以查看不同年份的九宫方位能量。")

st.markdown(f"## 📅 {target_year} 年 · 九宫方位能量")

palace_layout = [
    ("巽", "东南", "#4caf50"), ("离", "正南", "#ff5252"), ("坤", "西南", "#ffc107"),
    ("震", "正东", "#26a69a"), ("中", "中央", "#8d6e63"), ("兑", "正西", "#e8e8e8"),
    ("艮", "东北", "#9e9e9e"), ("坎", "正北", "#2196f3"), ("乾", "西北", "#ffd54f"),
]

energies = {}
for name, _, _ in palace_layout:
    energies[name] = compute_palace_energy(name, target_year, year, sizhu)

html = '<div class="qimen-grid">'
for name, direction, color in palace_layout:
    score = energies[name]
    level_text, level_color = get_level(score)
    html += (
        f'<div class="qimen-cell" style="border-color: {level_color};">'
        f'<div class="palace-name" style="color: {color};">{name}宫 · {direction}</div>'
        f'<div class="score" style="color: {level_color};">{score:+.2f}</div>'
        f'<div class="level" style="color: {level_color};">{level_text}</div>'
        f'</div>'
    )
html += '</div>'
st.html(html)

sorted_palaces = sorted(energies.items(), key=lambda x: x[1], reverse=True)
best_3 = sorted_palaces[:3]
worst_3 = sorted_palaces[-3:]
palace_dir = {name: direction for name, direction, _ in palace_layout}

st.markdown("---")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown(f"### ✅ {target_year} 年有利方位")
    for name, score in best_3:
        level_text, level_color = get_level(score)
        st.markdown(f"- **{palace_dir[name]}（{name}宫）**：{score:+.2f} {level_text}")

with col_b:
    st.markdown(f"### ⚠️ {target_year} 年需注意方位")
    for name, score in worst_3:
        level_text, level_color = get_level(score)
        st.markdown(f"- **{palace_dir[name]}（{name}宫）**：{score:+.2f} {level_text}")

st.caption("仅作能量参考，不构成实际建议。")

st.divider()
st.markdown("## 📈 方位能量随时间变化")

watch_palace = st.selectbox("选择方位", [f"{d}（{n}宫）" for n, d, _ in palace_layout])
watch_name = watch_palace.split("（")[1].replace("宫）", "")

years = list(range(year, year + 60))
trend_scores = [compute_palace_energy(watch_name, y, year, sizhu) for y in years]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=years, y=trend_scores,
    mode="lines+markers",
    line=dict(color="#ffb74d", width=3),
    marker=dict(size=6),
    name="综合能量",
))
fig.add_vline(x=target_year, line_dash="dash", line_color="#42a5f5",
              annotation_text=f"{target_year}年")
fig.add_hline(y=0, line_dash="dot", line_color="#555")
fig.update_layout(
    height=400, template="plotly_dark",
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis_title="年份", yaxis_title="综合能量",
)
st.plotly_chart(fig, use_container_width=True, config={
    'scrollZoom': True,
    'displayModeBar': False,
})

st.divider()
st.markdown("""
**怎么看这个页面**：

1. 顶部先填出生信息
2. 拖动年份滑块，看不同年份的九宫格变化
3. 绿色/黄色方位适合去，橙色/红色建议减少停留
4. 下方曲线看某个方位的 60 年趋势

仅作能量参考，不构成实际建议。
""")
