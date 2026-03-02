import streamlit as st
import random
from treys import Card, Evaluator


# --- 核心计算逻辑 ---
def calculate_win_rate(hole_cards_str, community_cards_str, num_opponents=1, simulations=5000):
    evaluator = Evaluator()
    ranks = '23456789TJQKA'
    suits = 'shdc'
    all_cards_str = [r + s for r in ranks for s in suits]

    wins = 0
    ties = 0

    my_hand = [Card.new(c) for c in hole_cards_str]
    board = [Card.new(c) for c in community_cards_str]
    known_cards_str = hole_cards_str + community_cards_str

    for _ in range(simulations):
        remaining_cards_str = [c for c in all_cards_str if c not in known_cards_str]

        needed_community = 5 - len(board)
        drawn_for_board_str = random.sample(remaining_cards_str, needed_community)
        current_board = board + [Card.new(c) for c in drawn_for_board_str]

        remaining_cards_str = [c for c in remaining_cards_str if c not in drawn_for_board_str]
        drawn_for_opponents_str = random.sample(remaining_cards_str, num_opponents * 2)

        my_score = evaluator.evaluate(current_board, my_hand)

        opponents_scores = []
        for i in range(num_opponents):
            opp_hand_str = drawn_for_opponents_str[i * 2: i * 2 + 2]
            opp_hand = [Card.new(c) for c in opp_hand_str]
            opp_score = evaluator.evaluate(current_board, opp_hand)
            opponents_scores.append(opp_score)

        best_opp_score = min(opponents_scores)

        if my_score < best_opp_score:
            wins += 1
        elif my_score == best_opp_score:
            ties += 1

    return (wins + ties / 2.0) / simulations


# --- 下注建议逻辑 ---
def get_betting_advice(win_rate, num_opponents):
    # 计算你在当前人数下的"平均公平胜率"
    fair_share = 1.0 / (num_opponents + 1)

    # 计算你的优势倍数
    advantage_ratio = win_rate / fair_share

    if advantage_ratio >= 1.5:
        return "🔥 **绝对优势 (Strong)**", "你的牌力远超平均水平。建议：**激进下注 (Value Bet) 或 加注 (Raise)**。建立底池，争取最大化收益。"
    elif 1.1 <= advantage_ratio < 1.5:
        return "👍 **略微优势 (Marginal)**", "你拥有一定的胜率优势。建议：**试探性下注 (Bet) 或 跟注 (Call)**。控制底池大小，观察对手反应。"
    elif 0.8 <= advantage_ratio < 1.1:
        return "⚖️ **势均力敌 (Draw/Weak)**", "胜率接近平均水平，可能在听牌或中等牌力。建议：**过牌 (Check) 免费看牌，或在赔率合适时跟注 (Call)**。避免主动造大底池。"
    else:
        return "🧊 **处于劣势 (Disadvantage)**", "胜率明显落后。建议：如果对手下注，果断 **弃牌 (Fold)**；如果无人下注，可以选择 **过牌 (Check)**。除非你有极好的诈唬时机，否则不要往底池投入筹码。"


# --- 网页 UI 设计 ---
st.set_page_config(page_title="德州扑克胜率计算器", page_icon="🃏", layout="centered")
st.title("🃏 德州扑克胜率计算器")

# 定义点数和花色的映射
ranks_display = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
ranks_value = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
rank_map = dict(zip(ranks_display, ranks_value))

suits_display = ['♠ 黑桃', '♥ 红桃', '♦ 方块', '♣ 梅花']
suits_value = ['s', 'h', 'd', 'c']
suit_map = dict(zip(suits_display, suits_value))

# --- 侧边栏：设置 ---
with st.sidebar:
    st.header("⚙️ 牌局设置")
    num_opponents = st.slider("对手数量", min_value=1, max_value=8, value=1)
    simulations = st.select_slider("模拟精度", options=[1000, 5000, 10000, 20000], value=5000)

# ==========================================
# 主界面：选牌区
# ==========================================

st.subheader("1. 选择你的底牌")
col1, col2, col3, col4 = st.columns(4)
with col1:
    h1_r = st.selectbox("底牌 1 点数", ranks_display, index=0, key="h1_r")
with col2:
    h1_s = st.selectbox("底牌 1 花色", suits_display, index=0, key="h1_s")
with col3:
    h2_r = st.selectbox("底牌 2 点数", ranks_display, index=1, key="h2_r")
with col4:
    h2_s = st.selectbox("底牌 2 花色", suits_display, index=1, key="h2_s")

st.divider()

st.subheader("2. 选择公共牌")

# 翻牌区
st.markdown("##### 翻牌 (Flop)")
f_col1, f_col2, f_col3 = st.columns(3)
with f_col1:
    f1_r = st.selectbox("第 1 张", ["(未发)"] + ranks_display, index=0, key="f1_r")
    f1_s = st.selectbox("花色 1", suits_display, label_visibility="collapsed", key="f1_s")
with f_col2:
    f2_r = st.selectbox("第 2 张", ["(未发)"] + ranks_display, index=0, key="f2_r")
    f2_s = st.selectbox("花色 2", suits_display, label_visibility="collapsed", key="f2_s")
with f_col3:
    f3_r = st.selectbox("第 3 张", ["(未发)"] + ranks_display, index=0, key="f3_r")
    f3_s = st.selectbox("花色 3", suits_display, label_visibility="collapsed", key="f3_s")

# 转牌与河牌区
st.markdown("##### 转牌 & 河牌 (Turn & River)")
tr_col1, tr_col2, _ = st.columns([1, 1, 1])
with tr_col1:
    t_r = st.selectbox("转牌 (第 4 张)", ["(未发)"] + ranks_display, index=0, key="t_r")
    t_s = st.selectbox("转牌花色", suits_display, label_visibility="collapsed", key="t_s")
with tr_col2:
    r_r = st.selectbox("河牌 (第 5 张)", ["(未发)"] + ranks_display, index=0, key="r_r")
    r_s = st.selectbox("河牌花色", suits_display, label_visibility="collapsed", key="r_s")

# ==========================================
# 按钮交互区
# ==========================================
st.write("---")
btn_col1, btn_col2 = st.columns([3, 1])  # 让计算按钮更宽，重置按钮稍窄
with btn_col1:
    calc_btn = st.button("🚀 计算胜率并获取建议", type="primary", use_container_width=True)
with btn_col2:
    reset_btn = st.button("🔄 一键清空", use_container_width=True)

# 处理重置逻辑
if reset_btn:
    # 清空 Streamlit 的 session state 来重置所有输入框
    st.session_state.clear()
    st.rerun()

# 处理计算逻辑
if calc_btn:
    hole1 = rank_map[h1_r] + suit_map[h1_s]
    hole2 = rank_map[h2_r] + suit_map[h2_s]

    community_cards = []
    selections = [(f1_r, f1_s), (f2_r, f2_s), (f3_r, f3_s), (t_r, t_s), (r_r, r_s)]
    for r_val, s_val in selections:
        if r_val != "(未发)":
            community_cards.append(rank_map[r_val] + suit_map[s_val])

    all_selected = [hole1, hole2] + community_cards

    if hole1 == hole2:
        st.error("⚠️ 两张底牌不能是同一张牌！")
    elif len(all_selected) != len(set(all_selected)):
        st.error("⚠️ 你选出的牌中有重复的牌，请仔细检查！")
    else:
        with st.spinner('正在进行蒙特卡洛模拟，请稍候...'):
            win_rate = calculate_win_rate([hole1, hole2], community_cards, num_opponents, simulations)

            # 分割线隔离结果区
            st.divider()

            # 显示胜率
            st.metric(label=f"📊 对抗 {num_opponents} 名随机手牌对手的预期胜率", value=f"{win_rate * 100:.2f}%")

            # 获取并显示下注建议
            status_title, advice_text = get_betting_advice(win_rate, num_opponents)

            st.markdown(f"### 💡 当前牌力评级: {status_title}")
            st.info(advice_text)

            # 增加免责声明
            st.caption(
                "⚠️ **免责声明**：此建议仅基于对抗“随机手牌”的纯数学胜率计算得出。实战中，请务必结合对手的打法风格（松/紧）、位置、筹码深度以及底池赔率（Pot Odds）综合判断。")