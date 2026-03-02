import streamlit as st
import random
import pandas as pd
from treys import Card, Evaluator

# --- 核心计算引擎 (增加牌型记录) ---
def calculate_poker_stats(hole_cards, board_cards, num_opp, sims=5000):
    evaluator = Evaluator()
    ranks, suits = '23456789TJQKA', 'shdc'
    deck = [r+s for r in ranks for s in suits]
    
    wins, ties = 0, 0
    # 用于记录各种牌型出现的次数
    hand_counts = {i: 0 for i in range(1, 10)} 
    
    my_hand = [Card.new(c) for c in hole_cards]
    board = [Card.new(c) for c in board_cards]
    used = hole_cards + board_cards
    
    for _ in range(sims):
        rem = [c for c in deck if c not in used]
        # 补齐 5 张公共牌
        final_board_strs = board_cards + random.sample(rem, 5 - len(board))
        final_board = [Card.new(c) for c in final_board_strs]
        
        # 重新计算剩余牌堆，给对手发牌
        rem_after_board = [c for c in deck if c not in (hole_cards + final_board_strs)]
        opp_cards = random.sample(rem_after_board, num_opp * 2)
        
        # 我的表现
        my_score = evaluator.evaluate(final_board, my_hand)
        my_class = evaluator.get_rank_class(my_score)
        hand_counts[my_class] += 1
        
        # 对手表现
        opp_scores = [evaluator.evaluate(final_board, [Card.new(opp_cards[i*2]), Card.new(opp_cards[i*2+1])]) for i in range(num_opp)]
        best_opp = min(opp_scores)
        
        if my_score < best_opp: wins += 1
        elif my_score == best_opp: ties += 1
            
    win_rate = (wins + ties / 2.0) / sims
    # 转换为百分比
    hand_probs = {k: (v / sims) for k, v in hand_counts.items()}
    return win_rate, hand_probs

# --- 映射表 ---
CLASS_MAP = {
    1: "皇家同花顺/同花顺",
    2: "四条 (Quads)",
    3: "葫芦 (Full House)",
    4: "同花 (Flush)",
    5: "顺子 (Straight)",
    6: "三条 (Set/Trips)",
    7: "两对 (Two Pair)",
    8: "一对 (One Pair)",
    9: "高牌 (High Card)"
}

# --- UI 设置 ---
st.set_page_config(page_title="德州助手 Pro+", page_icon="🃏", layout="centered")
st.title("🃏 德州助手 Pro+ (牌型统计版)")

with st.sidebar:
    st.header("⚙️ 模拟设置")
    num_opp = st.slider("对手人数", 1, 8, 1)
    sims = st.selectbox("模拟精度", [1000, 5000, 10000], index=1)
    st.divider()
    st.caption("注：牌型概率为您在河牌圈最终成牌的预期。")

# 1. 牌面输入
st.write("### 1. 牌面输入")
r_opts = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
r_vals = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
s_opts = ['♠', '♥', '♦', '♣']
s_vals = ['s', 'h', 'd', 'c']
r_map, s_map = dict(zip(r_opts, r_vals)), dict(zip(s_opts, s_vals))

c1, c2 = st.columns(2)
with col1:
    st.caption("我的底牌")
    h_c1, h_c2 = st.columns(2)
    h1r = h_c1.selectbox("P1", r_opts, key="h1r", label_visibility="collapsed")
    h1s = h_c2.selectbox("S1", s_opts, key="h1s", label_visibility="collapsed")
    h2r = h_c1.selectbox("P2", r_opts, index=1, key="h2r", label_visibility="collapsed")
    h2s = h_c2.selectbox("S2", s_opts, index=1, key="h2s", label_visibility="collapsed")
with col2:
    st.caption("公共牌 (未发选 -)")
    f1, f2, f3, t, r = st.columns(5)
    fr1 = f1.selectbox("F1", ["-"]+r_opts); fs1 = f1.selectbox("S1", s_opts, key="fs1", label_visibility="collapsed")
    fr2 = f2.selectbox("F2", ["-"]+r_opts); fs2 = f2.selectbox("S2", s_opts, key="fs2", label_visibility="collapsed")
    fr3 = f3.selectbox("F3", ["-"]+r_opts); fs3 = f3.selectbox("S3", s_opts, key="fs3", label_visibility="collapsed")
    tr = t.selectbox("T", ["-"]+r_opts); ts = t.selectbox("TS", s_opts, key="ts", label_visibility="collapsed")
    rr = r.selectbox("R", ["-"]+r_opts); rs = r.selectbox("RS", s_opts, key="rs", label_visibility="collapsed")

# 2. 筹码数据
st.write("### 2. 底池与赔率")
p_col1, p_col2 = st.columns(2)
pot_size = p_col1.number_input("当前总底池 ($)", min_value=0, value=100)
call_amount = p_col2.number_input("需跟注金额 ($)", min_value=0, value=20)

st.divider()

# 3. 计算展示
if st.button("🚀 开始全深度分析", type="primary", use_container_width=True):
    h = [r_map[h1r]+s_map[h1s], r_map[h2r]+s_map[h2s]]
    b = []
    for r, s in [(fr1, fs1), (fr2, fs2), (fr3, fs3), (tr, ts), (rr, rs)]:
        if r != "-": b.append(r_map[r]+s_map[s])
    
    if len(set(h+b)) != len(h+b):
        st.error("卡牌重复！")
    else:
        with st.spinner('AI 正在模拟数万种发牌可能...'):
            win_rate, hand_probs = calculate_poker_stats(h, b, num_opp, sims)
            
            # 顶部核心指标
            pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 0
            
            m1, m2 = st.columns(2)
            m1.metric("预期胜率", f"{win_rate*100:.2f}%")
            m2.metric("跟注保本胜率", f"{pot_odds*100:.2f}%")
            
            if win_rate > pot_odds:
                st.success("✅ **数学领先 (EV+)**: 长期看，此举盈利。")
            else:
                st.warning("❌ **数学落后 (EV-)**: 长期看，此举亏损。")
            
            # 牌型概率表
            st.write("#### 📊 最终成牌概率统计")
            prob_data = [{"牌型": CLASS_MAP[k], "概率": f"{v*100:.1f}%"} for k, v in hand_probs.items() if v > 0]
            st.table(pd.DataFrame(prob_data))

if st.button("🔄 重置状态"):
    st.rerun()
