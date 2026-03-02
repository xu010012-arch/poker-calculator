import streamlit as st
import random
import pandas as pd
from treys import Card, Evaluator

# --- 核心计算引擎 (保持不变) ---
def calculate_poker_stats(hole_cards, board_cards, num_opp, sims=5000):
    evaluator = Evaluator()
    ranks, suits = '23456789TJQKA', 'shdc'
    deck = [r+s for r in ranks for s in suits]
    wins, ties = 0, 0
    hand_counts = {i: 0 for i in range(1, 10)} 
    my_hand = [Card.new(c) for c in hole_cards]
    board = [Card.new(c) for c in board_cards]
    used = hole_cards + board_cards
    for _ in range(sims):
        rem = [c for c in deck if c not in used]
        final_board_strs = board_cards + random.sample(rem, 5 - len(board))
        final_board = [Card.new(c) for c in final_board_strs]
        rem_after_board = [c for c in deck if c not in (hole_cards + final_board_strs)]
        opp_cards = random.sample(rem_after_board, num_opp * 2)
        my_score = evaluator.evaluate(final_board, my_hand)
        my_class = evaluator.get_rank_class(my_score)
        hand_counts[my_class] += 1
        opp_scores = [evaluator.evaluate(final_board, [Card.new(opp_cards[i*2]), Card.new(opp_cards[i*2+1])]) for i in range(num_opp)]
        best_opp = min(opp_scores)
        if my_score < best_opp: wins += 1
        elif my_score == best_opp: ties += 1
    win_rate = (wins + ties / 2.0) / sims
    hand_probs = {k: (v / sims) for k, v in hand_counts.items()}
    return win_rate, hand_probs

CLASS_MAP = {1:"同花顺", 2:"四条", 3:"葫芦", 4:"同花", 5:"顺子", 6:"三条", 7:"两对", 8:"一对", 9:"高牌"}

# --- UI 界面设置 ---
st.set_page_config(page_title="德州助手", page_icon="🃏", layout="centered")

# 使用 CSS 隐藏可能的输入焦点，并美化平铺按钮
st.markdown("""
    <style>
    div[data-baseweb="select"] { display: none; } /* 彻底隐藏下拉框 */
    .stButton button { width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🃏 德州扑克专业助手")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")
    num_opp = st.select_slider("对手人数", options=list(range(1, 9)), value=1)
    sims = st.segmented_control("精度", options=[1000, 5000, 10000], default=5000)

r_opts = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
r_vals = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
s_opts = ['♠', '♥', '♦', '♣']
s_vals = ['s', 'h', 'd', 'c']
r_map, s_map = dict(zip(r_opts, r_vals)), dict(zip(s_opts, s_vals))

# --- 1. 我的底牌 (使用 st.pills 避免键盘) ---
st.write("### 1. 我的底牌")
col1, col2 = st.columns(2)
with col1:
    st.caption("第一张")
    h1r = st.pills("点数", r_opts, key="h1r", label_visibility="collapsed")
    h1s = st.pills("花色线", s_opts, key="h1s", label_visibility="collapsed")
with col2:
    st.caption("第二张")
    h2r = st.pills("点数2", r_opts, key="h2r", label_visibility="collapsed")
    h2s = st.pills("花色2", s_opts, key="h2s", label_visibility="collapsed")

# --- 2. 公共牌 (使用更加紧凑的布局) ---
st.write("### 2. 公共牌")
f_tab, t_tab, r_tab = st.tabs(["翻牌 (Flop)", "转牌 (Turn)", "河牌 (River)"])

with f_tab:
    fc1, fc2, fc3 = st.columns(3)
    fr1 = fc1.pills("F1-R", ["-"] + r_opts, key="fr1"); fs1 = fc1.pills("F1-S", s_opts, key="fs1")
    fr2 = fc2.pills("F2-R", ["-"] + r_opts, key="fr2"); fs2 = fc2.pills("F2-S", s_opts, key="fs2")
    fr3 = fc3.pills("F3-R", ["-"] + r_opts, key="fr3"); fs3 = fc3.pills("F3-S", s_opts, key="fs3")

with t_tab:
    tr = st.pills("转牌点数", ["-"] + r_opts, key="tr")
    ts = st.pills("转牌花色", s_opts, key="ts")

with r_tab:
    rr = st.pills("河牌点数", ["-"] + r_opts, key="rr")
    rs = st.pills("河牌花色", s_opts, key="rs")

# --- 3. 筹码与计算 ---
st.write("### 3. 分析决策")
pot_col, call_col = st.columns(2)
pot_size = pot_col.number_input("底池 ($)", min_value=0, value=100)
call_amt = call_col.number_input("跟注 ($)", min_value=0, value=20)

if st.button("🚀 开始分析 (EV+)", type="primary"):
    if not all([h1r, h1s, h2r, h2s]):
        st.error("请选好你的两张底牌！")
    else:
        h = [r_map[h1r]+s_map[h1s], r_map[h2r]+s_map[h2s]]
        b = []
        for r_v, s_v in [(fr1, fs1), (fr2, fs2), (fr3, fs3), (tr, ts), (rr, rs)]:
            if r_v and r_v != "-": b.append(r_map[r_v]+s_map[s_v])
        
        if len(set(h+b)) != len(h+b):
            st.error("卡牌重复，请检查输入！")
        else:
            win_rate, hand_probs = calculate_poker_stats(h, b, num_opp, sims)
            pot_odds = call_amt / (pot_size + call_amt) if (pot_size + call_amt) > 0 else 0
            
            st.divider()
            c_a, c_b = st.columns(2)
            c_a.metric("预期胜率", f"{win_rate*100:.1f}%")
            c_b.metric("赔率要求", f"{pot_odds*100:.1f}%")
            
            if win_rate > pot_odds:
                st.success("✅ **建议：跟注 (EV+)**")
            else:
                st.warning("❌ **建议：弃牌 (EV-)**")
            
            with st.expander("查看成牌概率"):
                df = pd.DataFrame([{"牌型": CLASS_MAP[k], "概率": f"{v*100:.1f}%"} for k, v in hand_probs.items() if v > 0])
                st.table(df)

if st.button("🔄 重置"):
    st.rerun()
