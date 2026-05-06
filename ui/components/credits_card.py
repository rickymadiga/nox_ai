import streamlit as st
import time
import logging
from ui.services import api, state
from ui.config import PRIMARY_GREEN

logger = logging.getLogger(__name__)

def show():
    """Display credits card and recharge section in sidebar"""
    current_credits = api.get_credits()
    st.session_state.credits = current_credits
    st.session_state.last_credit_update = state.get_utc_timestamp()
    
    display_credits_card(current_credits, st.session_state.is_admin)
    
    st.divider()
    
    if st.session_state.is_admin:
        _show_admin_credit_management()
    else:
        _show_user_recharge()
    
    # Credit warning
    if not st.session_state.is_admin and current_credits <= 10:
        st.markdown(f'''
        <div class="credit-warning">
            <strong>⚠️ Low Credit Balance!</strong><br>
            You have only {current_credits} credits left.<br>
            Please recharge to continue building.
        </div>
        ''', unsafe_allow_html=True)


def display_credits_card(current_credits: int, is_admin: bool = False) -> None:
    """Display credit status card"""
    if is_admin:
        st.markdown(f'''
        <div class="credit-card">
            <div style="font-size: 1.2rem; font-weight: 700;">💰 Credits</div>
            <div style="font-size: 2.5rem; color: {PRIMARY_GREEN}; font-weight: 700; margin: 0.5rem 0;">∞ Unlimited</div>
            <div style="font-size: 0.85rem; color: #9ca3af;">Admin Account - No limit</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        # Determine color based on credit level
        if current_credits <= 10:
            color = "#ef4444"  # Red
            status = "🔴 Critical"
        elif current_credits <= 50:
            color = "#f59e0b"  # Orange
            status = "🟡 Low"
        else:
            color = PRIMARY_GREEN
            status = "🟢 Healthy"
        
        st.markdown(f'''
        <div class="credit-card">
            <div style="font-size: 1.2rem; font-weight: 700;">💰 Credits</div>
            <div style="font-size: 2.5rem; color: {color}; font-weight: 700; margin: 0.5rem 0;">{current_credits:,}</div>
            <div style="font-size: 0.85rem; color: #9ca3af;">Status: {status}</div>
        </div>
        ''', unsafe_allow_html=True)


def _show_user_recharge():
    """Show user recharge UI"""
    st.subheader("💳 Recharge Credits")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        amount = st.number_input(
            "Amount (sh)",
            min_value=500,
            max_value=1000000,
            step=500,
            value=5000,
            key="recharge_amount",
            help="Select amount to recharge. Minimum: sh500"
        )
    
    with st.expander("📊 Pricing Info", expanded=False):
        st.markdown("""
        **Credit Packages:**
        - sh500 = 500 credits
        - sh1,000 = 1,000 credits  
        - sh5,000 = 5,000 credits
        - sh10,000 = 10,000 credits
        - sh50,000 = 50,000 credits
        """)
    
    if st.button("💰 Recharge Now", use_container_width=True, key="recharge_btn"):
        if amount > 0:
            _process_recharge(amount)
        else:
            st.warning("⚠️ Amount must be > 0")
    
    st.divider()
    
    # Recharge history
    with st.expander("📜 Recharge History", expanded=False):
        history = api.get_recharge_history()
        if history and history.get("status") == "success":
            recharges = history.get("recharges", [])
            if recharges:
                st.markdown("**Recent Transactions:**")
                for i, r in enumerate(recharges[:10], 1):
                    date = r.get('date', 'Unknown')
                    amount_paid = r.get('amount', 0)
                    credits_got = r.get('credits_received', 0)
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.caption(f"**{i}.** {date}")
                    with col2:
                        st.caption(f"₦{amount_paid:,}")
                    with col3:
                        st.caption(f"+{credits_got:,} 🎁")
                
                if len(recharges) > 10:
                    st.caption(f"... and {len(recharges) - 10} more transactions")
            else:
                st.info("💭 No recharge history yet.")
        else:
            st.error("Failed to load history")


def _process_recharge(amount: int):
    """Process recharge transaction"""
    with st.spinner("🔄 Processing payment..."):
        logger.info(f"[Frontend] Recharge initiated: {amount}sh")
        
        recharge_result = api.recharge(amount)
        
        if not recharge_result:
            return
        
        status = recharge_result.get("status")
        
        # Success
        if status == "success":
            credits_added = recharge_result.get("credits_added", 0)
            new_balance = recharge_result.get("new_balance", 0)
            
            st.markdown(f'''
            <div class="credit-success">
                <div style="font-weight: 700; font-size: 1.1rem;">✅ Recharge Successful!</div>
                <div style="margin-top: 0.5rem;">
                Added: <strong>+{credits_added:,}</strong> credits<br>
                New Balance: <strong>{new_balance:,}</strong> credits
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.session_state.credits = new_balance
            st.balloons()
            time.sleep(1)
            st.rerun()
        
        # Redirect to payment
        elif status == "redirect":
            new_endpoint = recharge_result.get("new_endpoint")
            payload = recharge_result.get("payload", {})
            
            st.warning("🔄 Redirecting to payment gateway...")
            logger.info(f"[Frontend] Redirect → {new_endpoint}")
            
            redirect_result = api.api_post(new_endpoint, payload, auth=True, timeout=30)
            
            if redirect_result:
                payment_url = redirect_result.get("payment_url") or redirect_result.get("authorization_url")
                
                if payment_url:
                    st.markdown(f"""
                    <div class="credit-success">
                        <b>💳 Payment Ready</b><br><br>
                        <a href="{payment_url}" target="_blank">
                            👉 Click here to complete payment
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("❌ Payment initialization failed")
                    with st.expander("🔧 Debug Info"):
                        st.json(redirect_result)
            else:
                st.error("❌ Failed to initialize payment")
        
        # Failure
        else:
            error_msg = recharge_result.get("detail", "Unknown error")
            st.markdown(f'''
            <div class="credit-warning">
                <div style="font-weight: 700;">❌ Recharge Failed</div>
                <div style="margin-top: 0.3rem;">{error_msg}</div>
            </div>
            ''', unsafe_allow_html=True)


def _show_admin_credit_management():
    """Show admin credit management UI"""
    st.subheader("👑 Admin Credit Management")
    
    with st.expander("🎛️ Add Credits to User", expanded=True):
        st.markdown("#### ➕ Distribute Credits")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            target_user = st.text_input(
                "Username",
                placeholder="Enter username",
                key="admin_target_user"
            )
        
        col3, col4 = st.columns([2, 1])
        with col3:
            add_amount = st.number_input(
                "Credits to Add",
                min_value=0,
                max_value=1000000,
                step=1000,
                value=10000,
                key="admin_add_credits"
            )
        
        add_reason = st.text_input(
            "Reason (Optional)",
            placeholder="e.g., Promotion, Bonus, Gift",
            key="admin_add_reason"
        )
        
        if st.button("➕ Add Credits", use_container_width=True, key="admin_add_credits_btn"):
            if target_user and add_amount > 0:
                with st.spinner("🔄 Adding credits..."):
                    result = api.add_admin_credits(target_user, add_amount, add_reason)
                    
                    if result and result.get("status") == "success":
                        new_balance = result.get("new_balance", 0)
                        
                        st.markdown(f'''
                        <div class="credit-success">
                            <div style="font-weight: 700; font-size: 1.1rem;">✅ Credits Added!</div>
                            <div style="margin-top: 0.5rem;">
                                User: <strong>{target_user}</strong><br>
                                Added: <strong>+{add_amount:,}</strong><br>
                                New Balance: <strong>{new_balance:,}</strong>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                        st.balloons()
                    else:
                        error_msg = result.get("detail", "Unknown error") if result else "Failed"
                        st.error(f"❌ Failed: {error_msg}")
            else:
                st.warning("⚠️ Enter username and amount > 0")
        
        st.divider()
        
        # Distribution history
        with st.expander("📊 Distribution History", expanded=False):
            history = api.get_credit_distribution_history()
            
            if history and history.get("status") == "success":
                distributions = history.get("distributions", [])
                
                if distributions:
                    for i, dist in enumerate(distributions[:20], 1):
                        col1, col2, col3, col4 = st.columns([2, 1.5, 1, 1.5])
                        with col1:
                            st.caption(f"**{i}.** {dist.get('date')}")
                        with col2:
                            st.caption(f"👤 {dist.get('user')}")
                        with col3:
                            st.caption(f"+{dist.get('amount'):,}")
                        with col4:
                            st.caption(dist.get('reason'))