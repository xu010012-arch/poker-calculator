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
    # 初始化 1-9 种牌型的统计字典
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
        
        # 评估我的牌力
        my_score = evaluator.evaluate(final_board, my_hand)
        my_class = evaluator.get_rank_class(my_score)
        hand_counts[my_class] = hand_counts.get(my_class, 0) + 1
        
        # 评估对手最强牌
        opp_scores = [evaluator.evaluate(final_board, [Card.new(opp_cards[i*2]), Card.new(opp_cards[i*2+1])]) for i in range(num_opp)]
        best_opp = min(opp_scores)
        
        if my_score < best_opp: wins += 1
        elif my_score == best_opp: ties += 1
            
    win_rate = (wins + ties / 2.0) / sims
    hand_probs = {k: (v / sims) for k, v in hand_counts.items()}
    return win_rate, hand_probs

# 牌型名称映射表
CLASS_MAP = {1:"同花顺", 2:"四条", 3:"葫芦", 4:"同花", 5:"顺子", 6:"三条", 7:"两对", 8:"一对", 9:"高牌"}

# --- UI 页面配置 ---
st.set_page_config(page_title="德州助手 Pro", page_icon="🃏", layout="centered")

# CSS 强制微调：隐藏下拉框焦点，美化移动端间距
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🃏 德州助手")

# 侧边栏：环境设置
with st.sidebar:
    st.header("⚙️ 模拟参数")
    num_opp = st.select_slider("对手人数", options=list(range(1, 9)), value=1)
    sims = st.segmented_control("精度 (Simulations)", options=[1000, 5000, 10000], default=5000)
    st.divider()
    st.caption("这其实是一套基于蒙特卡洛算法的预测系统，逻辑上和你处理复杂数据预测（如降雨预测）的思路非常接近。")

# 数据字典
r_opts = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
r_vals = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
s_opts = ['♠', '♥', '♦', '♣']
s_vals = ['s', 'h', 'd', 'c']
r_map, s_map = dict(zip(r_opts, r_vals)), dict(zip(s_opts, s_vals))

# --- 1. 我的底牌 (使用 Pills 彻底防跳键盘) ---
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

# --- 2. 公共牌 (Tabs 标签页切换) ---
st.write("### 2. 公共牌面")
f_tab, t_tab, r_tab = st.tabs(["翻牌 (Flop)", "转牌 (Turn)", "河牌 (River)"])

with f_tab:
    fc1, fc2, fc3 = st.columns(3)
    fr1 = fc1.pills("F1R", ["-"]+r_opts, key="fr1"); fs1 = fc1.pills("F1S", s_opts, key="fs1")
    fr2 = fc2.pills("F2R", ["-"]+r_opts, key="fr2"); fs2 = fc2.pills("F2S", s_opts, key="fs2")
    fr3 = fc3.pills("F3R", ["-"]+r_opts, key="fr3"); fs3 = fc3.pills("F3S", s_opts, key="fs3")

with t_tab:
    tr = st.pills("TR", ["-"]+r_opts, key="tr")
    ts = st.pills("TS", s_opts, key="ts")

with r_tab:
    rr = st.pills("RR", ["-"]+r_opts, key="rr")
    rs = st.pills("RS", s_opts, key="rs")

# --- 3. 筹码数据 ---
st.write("### 3. 底池决策数据")
p_c1, p_c2 = st.columns(2)
pot_size = p_c1.number_input("当前总底池 ($)", min_value=0, value=100, step=10)
call_amt = p_c2.number_input("需跟注金额 ($)", min_value=0, value=20, step=5)

st.divider()

# --- 4. 计算与分析逻辑 ---
if st.button("🚀 开始全深度决策分析", type="primary", use_container_width=True):
    if not all([h1r, h1s, h2r, h2s]):
        st.error("⚠️ 请先点选你的两张底牌！")
    else:
        # 构建卡牌序列
        h = [r_map[h1r]+s_map[h1s], r_map[h2r]+s_map[h2s]]
        b = []
        for rv, sv in [(fr1, fs1), (fr2, fs2), (fr3, fs3), (tr, ts), (rr, rs)]:
            if rv and rv != "-": b.append(r_map[rv]+s_map[sv])
        
        # 查重校验
        if len(set(h+b)) != len(h+b):
            st.error("⚠️ 卡牌输入重复，请检查牌面！")
        else:
            with st.spinner('AI 正在模拟数万种发牌组合...'):
                win_rate, hand_probs = calculate_poker_stats(h, b, num_opp, sims)
                
                # 计算期望值 (EV)
                # EV = (Win% * Pot_to_win) - (Loss% * Amount_to_call)
                pot_odds = call_amt / (pot_size + call_amt) if (pot_size + call_amt) > 0 else 0
                ev = (win_rate * pot_size) - ((1 - win_rate) * call_amt)
                
                # --- 结果展示 ---
                m1, m2, m3 = st.columns(3)
                m1.metric("预期胜率", f"{win_rate*100:.1f}%")
                m2.metric("赔率门槛", f"{pot_odds*100:.1f}%")
                m3.metric("单次 EV", f"${ev:.1f}", delta=f"{ev:.1f}" if ev > 0 else f"{ev:.1f}")

                st.write("#### 💡 实战策略建议")
                if win_rate > pot_odds:
                    advantage = (win_rate - pot_odds) * 100
                    st.success(f"**建议：跟注 (Positive EV)**")
                    st.markdown(f"你的胜率领先赔率要求 **{advantage:.1f}%**。这是一个长线盈利的决策。如果对手看起来比较弱，甚至可以考虑加注。")
                else:
                    disadvantage = (pot_odds - win_rate) * 100
                    st.warning(f"**建议：弃牌 (Negative EV)**")
                    st.markdown(f"你的胜率落后赔率要求 **{disadvantage:.1f}%**。除非你确信后续有巨大的隐含赔率，否则不建议入池。")

                # 牌型统计
                [Image of Texas Hold'em hand rankings chart]
                with st.expander("📊 查看成牌概率详情"):
                    st.write("至河牌圈时，你最终成牌的结构分布：")
                    df = pd.DataFrame([{"牌型": CLASS_MAP[k], "概率": f"{v*100:.1f}%"} for k, v in hand_probs.items() if v > 0])
                    st.table(df)

if st.button("🔄 重置所有选项"):
    st.session_state.clear()
    st.rerun()
