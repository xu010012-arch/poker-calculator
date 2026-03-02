import streamlit as st
import random
import pandas as pd
from treys import Card, Evaluator

# --- 核心计算引擎 ---
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
        sampled_board = random.sample(rem, 5 - len(board))
        final_board_strs = board_cards + sampled_board
        final_board = [Card.new(c) for c in final_board_strs]
        
        rem_after_board = [c for c in rem if c not in sampled_board]
        opp_cards = random.sample(rem_after_board, num_opp * 2)
        
        my_score = evaluator.evaluate(final_board, my_hand)
        my_class = evaluator.get_rank_class(my_score)
        hand_counts[my_class] = hand_counts.get(my_class, 0) + 1
        
        opp_scores = [evaluator.evaluate(final_board, [Card.new(opp_cards[i*2]), Card.new(opp_cards[i*2+1])]) for i in range(num_opp)]
        best_opp = min(opp_scores)
        
        if my_score < best_opp: wins += 1
        elif my_score == best_opp: ties += 1
            
    win_rate = (wins + ties / 2.0) / sims
    hand_probs = {k: (v / sims) for k, v in hand_counts.items()}
    return win_rate, hand_probs

CLASS_MAP = {1:"同花顺", 2:"四条", 3:"葫芦", 4:"同花", 5:"顺子", 6:"三条", 7:"两对", 8:"一对", 9:"高牌"}

# --- UI 界面 ---
st.set_page_config(page_title="德州助手 Pro+", page_icon="🃏", layout="centered")

st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 10px; font-weight: bold; height: 3rem; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

st.title("🃏 德州扑克实战助手")

# 侧边栏：调高上限
with st.sidebar:
    st.header("⚙️ 模拟参数")
    num_opp = st.select_slider("对手人数", options=list(range(1, 9)), value=1)
    # 将上限调高至 50,000 次
    sims = st.selectbox("计算精度 (次数越多越准，高精度需等待)", 
                        options=[1000, 5000, 10000, 20000, 50000], 
                        index=1)
    st.warning("⚠️ 注意：50,000 次模拟在手机端可能需要 5-10 秒计算时间。")

r_opts = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
r_vals = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
s_opts = ['♠', '♥', '♦', '♣']
s_vals = ['s', 'h', 'd', 'c']
r_map, s_map = dict(zip(r_opts, r_vals)), dict(zip(s_opts, s_vals))

# 1. 我的底牌
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

# 2. 公共牌面
st.write("### 2. 公共牌面")
f_tab, t_tab, r_tab = st.tabs(["翻牌", "转牌", "河牌"])
with f_tab:
    fc1, fc2, fc3 = st.columns(3)
    fr1 = fc1.pills("F1R", ["-"]+r_opts, key="fr1"); fs1 = fc1.pills("F1S", s_opts, key="fs1")
    fr2 = fc2.pills("F2R", ["-"]+r_opts, key="fr2"); fs2 = fc2.pills("F2S", s_opts, key="fs2")
    fr3 = fc3.pills("F3R", ["-"]+r_opts, key="fr3"); fs3 = fc3.pills("F3S", s_opts, key="fs3")
with t_tab:
    tr = st.pills("TR", ["-"]+r_opts, key="tr"); ts = st.pills("TS", s_opts, key="ts")
with r_tab:
    rr = st.pills("RR", ["-"]+r_opts, key="rr"); rs = st.pills("RS", s_opts, key="rs")

# 3. 筹码数据
st.write("### 3. 底池决策")
p_c1, p_c2 = st.columns(2)
pot_size = p_c1.number_input("底池总额 ($)", min_value=1, value=100)
call_amt = p_c2.number_input("需跟注额 ($)", min_value=0, value=20)

st.divider()

if st.button("🚀 开始深度分析", type="primary", use_container_width=True):
    if not all([h1r, h1s, h2r, h2s]):
        st.error("请选好底牌！")
    else:
        h = [r_map[h1r]+s_map[h1s], r_map[h2r]+s_map[h2s]]
        b = []
        for rv, sv in [(fr1, fs1), (fr2, fs2), (fr3, fs3), (tr, ts), (rr, rs)]:
            if rv and rv != "-": b.append(r_map[rv]+s_map[sv])
        
        if len(set(h+b)) != len(h+b):
            st.error("卡牌重复！")
        else:
            with st.spinner(f'AI 正在进行 {sims} 次模拟...'):
                win_rate, hand_probs = calculate_poker_stats(h, b, num_opp, sims)
                pot_odds = call_amt / (pot_size + call_amt) if (pot_size + call_amt) > 0 else 0
                
                m1, m2 = st.columns(2)
                # 胜率显示保留两位小数
                m1.metric("预期胜率", f"{win_rate*100:.2f}%")
                m2.metric("赔率门槛", f"{pot_odds*100:.2f}%")
                
                if win_rate > pot_odds:
                    st.success("✅ 建议：跟注 (EV+)")
                else:
                    st.warning("❌ 建议：弃牌 (EV-)")

                with st.expander("📊 查看详细牌型分布"):
                    # 关键修改：保留 3 位小数，以便显示微小概率
                    prob_list = []
                    for k, v in hand_probs.items():
                        if v > 0:
                            hand_name = CLASS_MAP.get(k, f"其他({k})")
                            prob_list.append({"牌型": hand_name, "概率": f"{v*100:.3f}%"})
                    
                    if prob_list:
                        st.table(pd.DataFrame(prob_list))

if st.button("🔄 重置"):
    st.rerun()
