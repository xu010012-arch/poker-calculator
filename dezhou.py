import streamlit as st
import random
import pandas as pd
from treys import Card, Evaluator

# --- 核心计算引擎 (带防御性统计) ---
def calculate_poker_stats(hole_cards, board_cards, num_opp, sims=5000):
    evaluator = Evaluator()
    ranks, suits = '23456789TJQKA', 'shdc'
    deck = [r+s for r in ranks for s in suits]
    
    wins, ties = 0, 0
    # 初始化统计字典，确保 1-9 的 key 都存在
    hand_counts = {i: 0 for i in range(1, 10)} 
    
    my_hand = [Card.new(c) for c in hole_cards]
    board = [Card.new(c) for c in board_cards]
    used = hole_cards + board_cards
    
    for _ in range(sims):
        rem = [c for c in deck if c not in used]
        # 补齐 5 张公共牌
        sampled_board = random.sample(rem, 5 - len(board))
        final_board_strs = board_cards + sampled_board
        final_board = [Card.new(c) for c in final_board_strs]
        
        # 给对手发牌
        rem_after_board = [c for c in rem if c not in sampled_board]
        opp_cards = random.sample(rem_after_board, num_opp * 2)
        
        # 我的成牌评估
        my_score = evaluator.evaluate(final_board, my_hand)
        my_class = evaluator.get_rank_class(my_score)
        hand_counts[my_class] = hand_counts.get(my_class, 0) + 1
        
        # 对手最强成牌评估
        opp_scores = [evaluator.evaluate(final_board, [Card.new(opp_cards[i*2]), Card.new(opp_cards[i*2+1])]) for i in range(num_opp)]
        best_opp = min(opp_scores)
        
        if my_score < best_opp: wins += 1
        elif my_score == best_opp: ties += 1
            
    win_rate = (wins + ties / 2.0) / sims
    hand_probs = {k: (v / sims) for k, v in hand_counts.items()}
    return win_rate, hand_probs

CLASS_MAP = {1:"同花顺", 2:"四条", 3:"葫芦", 4:"同花", 5:"顺子", 6:"三条", 7:"两对", 8:"一对", 9:"高牌"}

# --- UI 界面设置 ---
st.set_page_config(page_title="德州助手 Pro", page_icon="🃏", layout="centered")

# CSS 强制微调，防止移动端布局溢出
st.markdown("<style>button[kind='secondary'] { padding: 0.2rem 0.5rem; }</style>", unsafe_allow_html=True)

st.title("🃏 德州扑克助手 (手机优化版)")

with st.sidebar:
    st.header("⚙️ 设置")
    num_opp = st.slider("对手人数", 1, 8, 1)
    sims = st.segmented_control("精度", options=[1000, 5000, 10000], default=5000)
    st.info("这其实也是一种‘预测’，原理和你研究的降雨预测模型（蒙特卡洛模拟）有些异曲同工之处。")

r_opts = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
r_vals = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
s_opts = ['♠', '♥', '♦', '♣']
s_vals = ['s', 'h', 'd', 'c']
r_map, s_map = dict(zip(r_opts, r_vals)), dict(zip(s_opts, s_vals))

# --- 1. 我的底牌 ---
st.write("### 1. 我的底牌")
c1, c2 = st.columns(2)
with c1:
    st.caption("第一张")
    h1r = st.pills("点1", r_opts, key="h1r", label_visibility="collapsed")
    h1s = st.pills("花1", s_opts, key="h1s", label_visibility="collapsed")
with c2:
    st.caption("第二张")
    h2r = st.pills("点2", r_opts, key="h2r", label_visibility="collapsed")
    h2s = st.pills("花2", s_opts, key="h2s", label_visibility="collapsed")

# --- 2. 公共牌 (使用 Tabs 节省垂直空间) ---
st.write("### 2. 公共牌")
f_tab, t_tab, r_tab = st.tabs(["翻牌(Flop)", "转牌(Turn)", "河牌(River)"])

with f_tab:
    fc1, fc2, fc3 = st.columns(3)
    fr1 = fc1.pills("F1R", ["-"]+r_opts, key="fr1"); fs1 = fc1.pills("F1S", s_opts, key="fs1")
    fr2 = fc2.pills("F2R", ["-"]+r_opts, key="fr2"); fs2 = fc2.pills("F2S", s_opts, key="fs2")
    fr3 = fc3.pills("F3R", ["-"]+r_opts, key="fr3"); fs3 = fc3.pills("F3S", s_opts, key="fs3")

with t_tab:
    tr = st.pills("TR", ["-"]+r_opts, key="tr"); ts = st.pills("TS", s_opts, key="ts")

with r_tab:
    rr = st.pills("RR", ["-"]+r_opts, key="rr"); rs = st.pills("RS", s_opts, key="rs")

# --- 3. 分析与决策 ---
st.write("### 3. 底池赔率")
p_c1, p_c2 = st.columns(2)
# 这里的数字输入由于需要精确，手机上难免唤起键盘，
# 建议通过加减号操作，或者改成 slider
pot_size = p_c1.number_input("总底池 ($)", min_value=0, value=100, step=10)
call_amt = p_c2.number_input("需跟注 ($)", min_value=0, value=20, step=5)

st.divider()

if st.button("🚀 开始全深度分析", type="primary", use_container_width=True):
    if not all([h1r, h1s, h2r, h2s]):
        st.error("请先选好底牌！")
    else:
        h = [r_map[h1r]+s_map[h1s], r_map[h2r]+s_map[h2s]]
        b = []
        for rv, sv in [(fr1, fs1), (fr2, fs2), (fr3, fs3), (tr, ts), (rr, rs)]:
            if rv and rv != "-": b.append(r_map[rv]+s_map[sv])
        
        if len(set(h+b)) != len(h+b):
            st.error("卡牌重复，请检查！")
        else:
            with st.spinner('模拟中...'):
                wr, probs = calculate_poker_stats(h, b, num_opp, sims)
                pot_odds = call_amt / (pot_size + call_amt) if (pot_size + call_amt) > 0 else 0
                
                m1, m2 = st.columns(2)
                m1.metric("你的胜率", f"{wr*100:.1f}%")
                m2.metric("赔率门槛", f"{pot_odds*100:.1f}%")
                
                if wr > pot_odds:
                    st.success("✅ **建议：跟注 (EV+)**")
                else:
                    st.warning("❌ **建议：弃牌 (EV-)**")
                
                with st.expander("📊 查看成牌概率详情"):
                    df = pd.DataFrame([{"牌型": CLASS_MAP[k], "概率": f"{v*100:.1f}%"} for k, v in probs.items() if v > 0])
                    st.table(df)

if st.button("🔄 重置"):
    st.rerun()
