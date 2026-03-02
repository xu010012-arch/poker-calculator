import streamlit as st
import random
import pandas as pd
from treys import Card, Evaluator

# --- 核心计算引擎 (已修复 KeyError) ---
def calculate_poker_stats(hole_cards, board_cards, num_opp, sims=5000):
    evaluator = Evaluator()
    ranks, suits = '23456789TJQKA', 'shdc'
    deck = [r+s for r in ranks for s in suits]
    
    wins, ties = 0, 0
    # 牌型统计字典：1(同花顺) 到 9(高牌)
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
        
        # 评估我的成牌
        my_score = evaluator.evaluate(final_board, my_hand)
        my_class = evaluator.get_rank_class(my_score)
        hand_counts[my_class] += 1
        
        # 评估对手最强牌
        opp_scores = [evaluator.evaluate(final_board, [Card.new(opp_cards[i*2]), Card.new(opp_cards[i*2+1])]) for i in range(num_opp)]
        best_opp = min(opp_scores)
        
        if my_score < best_opp: wins += 1
        elif my_score == best_opp: ties += 1
            
    win_rate = (wins + ties / 2.0) / sims
    hand_probs = {k: (v / sims) for k, v in hand_counts.items()}
    return win_rate, hand_probs

# 牌型显示名称
CLASS_MAP = {1:"同花顺/皇家同花顺", 2:"四条", 3:"葫芦", 4:"同花", 5:"顺子", 6:"三条", 7:"两对", 8:"一对", 9:"高牌"}

# --- UI 页面配置 ---
st.set_page_config(page_title="德州助手", page_icon="🃏", layout="centered")

# CSS 注入：优化按钮高度和手机端间距
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 10px; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    .stPills [data-testid="stBaseButton-secondary"] { padding: 4px 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🃏 德州扑克实战助手")

# 侧边栏：配置区
with st.sidebar:
    st.header("⚙️ 模拟参数")
    num_opp = st.select_slider("对手人数", options=list(range(1, 9)), value=1)
    sims = st.segmented_control("计算精度", options=[1000, 5000, 10000], default=5000)
    st.divider()
    st.caption("基于蒙特卡洛随机模拟算法，模拟结果随次数增加而趋于稳定。")

# 常量定义
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

# --- 2. 公共牌 (使用 Tabs 节省空间) ---
st.write("### 2. 公共牌面")
f_tab, t_tab, r_tab = st.tabs(["翻牌 (Flop)", "转牌 (Turn)", "河牌 (River)"])

with f_tab:
    fc1, fc2, fc3 = st.columns(3)
    fr1 = fc1.pills("F1R", ["-"]+r_opts, key="fr1"); fs1 = fc1.pills("F1S", s_opts, key="fs1")
    fr2 = fc2.pills("F2R", ["-"]+r_opts, key="fr2"); fs2 = fc2.pills("F2S", s_opts, key="fs2")
    fr3 = fc3.pills("F3R", ["-"]+r_opts, key="fr3"); fs3 = fc3.pills("F3S", s_opts, key="fs3")

with t_tab:
    tr = st.pills("TR", ["-"]+r_opts, key="tr"); ts = st.pills("TS", s_opts, key="ts")

with r_tab:
    rr = st.pills("RR", ["-"]+r_opts, key="rr"); rs = st.pills("RS", s_opts, key="rs")

# --- 3. 筹码数据 ---
st.write("### 3. 底池决策数据")
p_c1, p_c2 = st.columns(2)
pot_size = p_c1.number_input("当前底池总额 ($)", min_value=1, value=100)
call_amt = p_c2.number_input("需要跟注金额 ($)", min_value=0, value=20)

st.divider()

# --- 4. 分析引擎 ---
if st.button("🚀 开始全深度决策分析", type="primary", use_container_width=True):
    if not all([h1r, h1s, h2r, h2s]):
        st.error("⚠️ 请先点选你的两张底牌！")
    else:
        h = [r_map[h1r]+s_map[h1s], r_map[h2r]+s_map[h2s]]
        b = []
        for rv, sv in [(fr1, fs1), (fr2, fs2), (fr3, fs3), (tr, ts), (rr, rs)]:
            if rv and rv != "-": b.append(r_map[rv]+s_map[sv])
        
        if len(set(h+b)) != len(h+b):
            st.error("⚠️ 卡牌输入重复，请检查牌面！")
        else:
            with st.spinner('正在模拟数万种发牌组合...'):
                win_rate, hand_probs = calculate_poker_stats(h, b, num_opp, sims)
                
                # 计算期望值 (EV)
                pot_odds = call_amt / (pot_size + call_amt) if (pot_size + call_amt) > 0 else 0
                ev = (win_rate * pot_size) - ((1 - win_rate) * call_amt)
                
                # 核心指标看板
                m1, m2, m3 = st.columns(3)
                m1.metric("预期胜率", f"{win_rate*100:.1f}%")
                m2.metric("赔率门槛", f"{pot_odds*100:.1f}%")
                m3.metric("预估 EV", f"${ev:.1f}", delta=f"{ev:.1f}" if ev > 0 else f"{ev:.1f}")

                # 详细战术建议
                st.write("#### 💡 实战建议")
                if win_rate > pot_odds:
                    adv = (win_rate - pot_odds) * 100
                    st.success(f"**✅ 建议：跟注 (EV+)**")
                    st.markdown(f"""
                    * **战术理由**：你的胜率领先赔率门槛 **{adv:.1f}%**。从概率学角度看，这次投入的性价比极高。
                    * **操作策略**：如果对手表现出软弱，可以考虑加注。
                    """)
                else:
                    disadv = (pot_odds - win_rate) * 100
                    st.warning(f"**❌ 建议：弃牌 (EV-)**")
                    st.markdown(f"""
                    * **战术理由**：你的胜率落后赔率门槛 **{disadv:.1f}%**。除非有极大的隐含赔率，否则不建议入池。
                    * **操作策略**：保护好你的筹码，寻找下一个更有利的入场时机。
                    """)

                # 成牌概率表格
                with st.expander("📊 查看最终成牌概率统计"):
                    st.write("至河牌圈时，你最终成牌的结构分布如下：")
                    df = pd.DataFrame([{"牌型": CLASS_MAP[k], "概率": f"{v*100:.1f}%"} for k, v in hand_probs.items() if v > 0])
                    st.table(df)

if st.button("🔄 重置所有选项"):
    st.rerun()
