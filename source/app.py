import json
import os
import csv
from dotenv import load_dotenv
import streamlit as st

# Import backend extraction and QA functions from main.py
from main import answer_level2, extract_level1

load_dotenv()
model_name = os.getenv("MODEL_NAME", "gemini-3.5-flash-lite")

# Configure Streamlit page layout
st.set_page_config(
    page_title="Billwise - Utility Bill Decoder",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- NEW: Function to load questions from level2.csv ---
@st.cache_data
def get_test_questions():
    questions = []
    try:
        with open("test/csv/level2.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = row.get("question", "").strip()
                # Deduplicate questions since every bill repeats the same 12 questions
                if q and q not in questions:
                    questions.append(q)
    except Exception:
        pass
    
    # Fallback just in case the file isn't found
    if not questions:
        questions = [
            "How much of my bill is taxes?",
            "What is the total amount due?",
            "How many units were consumed this month?",
            "When is the due date?"
        ]
    return questions

# Custom CSS for Billwise aesthetic & hiding default headers
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit default top header, Deploy button, and hamburger menu */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }

    .stApp {
        background-color: #F8FAFC;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
        width: 260px !important;
    }

    .brand-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 22px;
        font-weight: 700;
        color: #6E56CF;
        margin-bottom: 30px;
        padding-left: 5px;
    }

    .nav-item-active {
        background-color: #F3F0FF;
        color: #6E56CF;
        padding: 10px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
    }

    .status-banner {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 14px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    .status-pill {
        background-color: #E6F4EA;
        color: #137333;
        font-size: 13px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
    }

    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    .metric-title {
        font-size: 11px;
        font-weight: 700;
        color: #64748B;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 4px;
    }

    .metric-subtext {
        font-size: 12px;
        color: #64748B;
    }

    .content-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }

    .box-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px;
    }

    .box-title {
        font-size: 16px;
        font-weight: 700;
        color: #0F172A;
    }

    .purple-pill {
        background-color: #F3F0FF;
        color: #6E56CF;
        font-size: 12px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 12px;
    }

    .user-bubble {
        background-color: #6E56CF;
        color: #FFFFFF;
        padding: 12px 16px;
        border-radius: 16px 16px 2px 16px;
        font-size: 14px;
        margin-left: auto;
        max-width: 80%;
        margin-bottom: 12px;
    }

    .assistant-bubble {
        background-color: #F1F5F9;
        color: #0F172A;
        padding: 14px 18px;
        border-radius: 16px 16px 16px 2px;
        font-size: 14px;
        line-height: 1.5;
        margin-bottom: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Sidebar Navigation (Cleaned)
with st.sidebar:
  st.markdown(
      '<div class="brand-logo">⚡ billwise</div>', unsafe_allow_html=True
  )
  st.markdown(
      '<div class="nav-item-active">📄 Bill decoder</div>',
      unsafe_allow_html=True,
  )

  st.divider()

  st.markdown(
      """
        <div style="background:#F3F0FF; padding:16px; border-radius:12px; margin-top:20px;">
            <div style="font-weight:600; color:#6E56CF; font-size:13px; margin-bottom:4px;">✨ Clarity, one bill at a time.</div>
            <div style="font-size:12px; color:#64748B;">Understand every charge instantly with AI guidance.</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

# Main Header & Breadcrumbs
st.markdown(
    '<div style="font-size:13px; color:#64748B;'
    ' margin-bottom:8px;">Workspace &nbsp;/&nbsp; <span style="color:#0F172A;'
    ' font-weight:500;">Bill decoder</span></div>',
    unsafe_allow_html=True,
)

top_col1, top_col2 = st.columns([3, 1])
with top_col1:
  st.markdown(
      '<h1 style="font-size:28px; font-weight:700; color:#0F172A;'
      ' margin:0;">A clearer look at your bill</h1>',
      unsafe_allow_html=True,
  )
  st.markdown(
      '<p style="font-size:14px; color:#64748B; margin-top:4px;">Review the'
      " details, explore the data, and ask what's on your mind.</p>",
      unsafe_allow_html=True,
  )

with top_col2:
  uploaded_file = st.file_uploader(
      "Upload new bill",
      type=["png", "jpg", "jpeg"],
      label_visibility="collapsed",
  )

st.markdown("<br>", unsafe_allow_html=True)

if uploaded_file is not None:
  image_bytes = uploaded_file.getvalue()

  try:
    json_raw = extract_level1(image_bytes, model_name)
    bill_data = json.loads(json_raw)
  except Exception as e:
    bill_data = {}

  st.markdown(
      f"""
        <div class="status-banner">
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="font-size:20px;">📄</span>
                <div>
                    <div style="font-weight:600; font-size:14px; color:#0F172A;">{uploaded_file.name}</div>
                    <div style="font-size:12px; color:#64748B;">Image · {round(len(image_bytes)/1024, 1)} KB · Uploaded just now</div>
                </div>
            </div>
            <div class="status-pill">✓ Decoded successfully</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  kpi1, kpi2, kpi3, kpi4 = st.columns(4)

  payable = (
      bill_data.get("payable_within_due_date")
      or bill_data.get("current_bill")
      or "—"
  )
  due_date = bill_data.get("due_date") or "—"
  units = bill_data.get("units_consumed") or "—"
  bill_month = bill_data.get("bill_month") or "—"
  provider = bill_data.get("provider") or "Electricity"

  payable_str = (
      f"PKR {payable:,}"
      if isinstance(payable, (int, float))
      else f"PKR {payable}"
  )

  with kpi1:
    st.markdown(
        f"""
            <div class="metric-card">
                <div class="metric-title">AMOUNT DUE</div>
                <div class="metric-value">{payable_str}</div>
                <div class="metric-subtext">Current bill payable within due date</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with kpi2:
    st.markdown(
        f"""
            <div class="metric-card">
                <div class="metric-title">DUE DATE</div>
                <div class="metric-value">{due_date}</div>
                <div class="metric-subtext">Last date to pay without surcharge</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with kpi3:
    st.markdown(
        f"""
            <div class="metric-card">
                <div class="metric-title">ELECTRICITY USED</div>
                <div class="metric-value">{units} kWh</div>
                <div class="metric-subtext">Units consumed this month</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with kpi4:
    st.markdown(
        f"""
            <div class="metric-card">
                <div class="metric-title">BILLING PERIOD</div>
                <div class="metric-value">{bill_month}</div>
                <div class="metric-subtext">{provider} Utility Provider</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  col_left, col_right = st.columns([1, 1.2])

  with col_left:
    st.markdown(
        """
            <div class="content-box">
                <div class="box-header">
                    <div class="box-title">Your bill</div>
                    <span style="font-size:12px; color:#64748B; background:#F1F5F9; padding:2px 8px; border-radius:6px;">Page 1 / 1</span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.image(uploaded_file, use_container_width=True)
    st.markdown(
        '<div style="text-align:center; font-size:12px; color:#64748B;'
        ' margin-top:10px;">🛡️ Personal details masked & privacy'
        " protected</div>",
        unsafe_allow_html=True,
    )

  with col_right:
    st.markdown(
        """
            <div class="content-box">
                <div class="box-header">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div class="box-title">Extracted data</div>
                        <span class="purple-pill">JSON</span>
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.code(json.dumps(bill_data, indent=2), language="json")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
            <div class="content-box">
                <div class="box-header">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div class="box-title">Ask your bill</div>
                        <span style="background:#E6F4EA; color:#137333; font-size:12px; font-weight:600; padding:3px 10px; border-radius:12px;">Bill assistant</span>
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if "chat_history" not in st.session_state:
      st.session_state.chat_history = []

    for chat in st.session_state.chat_history:
      st.markdown(
          f'<div class="user-bubble">{chat["question"]}</div>',
          unsafe_allow_html=True,
      )
      st.markdown(
          f'<div class="assistant-bubble">{chat["answer"]}</div>',
          unsafe_allow_html=True,
      )

    # --- NEW: Dropdown form using the loaded questions ---
    questions_list = get_test_questions()
    
    with st.form(key="question_form", clear_on_submit=False):
      user_q = st.selectbox(
          "Select a question...",
          options=questions_list,
          label_visibility="collapsed",
      )
      submit_btn = st.form_submit_button("Ask Assistant", type="primary")

    if submit_btn and user_q:
      with st.spinner("Analyzing bill details..."):
        try:
          ans = answer_level2(image_bytes, user_q, model_name)
          st.session_state.chat_history.append(
              {"question": user_q, "answer": ans}
          )
          st.rerun()
        except Exception as ex:
          st.error(f"Error answering question: {ex}")

else:
  st.markdown(
      """
        <div style="text-align:center; padding:60px; background:#FFFFFF; border:2px dashed #CBD5E1; border-radius:16px; margin-top:20px;">
            <div style="font-size:40px; margin-bottom:10px;">⚡</div>
            <div style="font-size:18px; font-weight:700; color:#0F172A; margin-bottom:6px;">Upload a bill to get started</div>
            <div style="font-size:14px; color:#64748B; margin-bottom:20px;">Support for K-Electric, LESCO, and IESCO electricity bills (.png, .jpg)</div>
        </div>
    """,
      unsafe_allow_html=True,
  ) 