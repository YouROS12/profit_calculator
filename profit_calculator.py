import streamlit as st
import pandas as pd
import math
import datetime
import io # Required for Excel download in memory
import copy # Needed for deep copying scenario data

# --- Constants ---
AVG_DAYS_PER_MONTH = 30  # More precise average days/month

# --- Core Calculation Functions (Unchanged, but will use calculated total fixed cost) ---

def calculate_breakeven(total_fixed_costs, price_per_order, variable_cost_per_order_calculated):
    """Calculates the breakeven point using total fixed costs."""
    if price_per_order is None or variable_cost_per_order_calculated is None or total_fixed_costs is None:
        return None, None
    if price_per_order <= 0 or variable_cost_per_order_calculated < 0 or total_fixed_costs < 0:
         return None, None
    if variable_cost_per_order_calculated >= price_per_order:
        return None, price_per_order - variable_cost_per_order_calculated

    contribution_margin = price_per_order - variable_cost_per_order_calculated
    if contribution_margin == 0:
         return float('inf'), contribution_margin
    if total_fixed_costs == 0:
        return 0, contribution_margin

    breakeven_orders = total_fixed_costs / contribution_margin
    return math.ceil(breakeven_orders), contribution_margin

def calculate_orders_for_profit(total_fixed_costs, price_per_order, variable_cost_per_order_calculated, target_profit):
    """Calculates orders needed for profit using total fixed costs."""
    if any(v is None for v in [total_fixed_costs, price_per_order, variable_cost_per_order_calculated, target_profit]) or target_profit <= 0:
        return None
    if price_per_order <= 0 or variable_cost_per_order_calculated < 0 or total_fixed_costs < 0:
        return None
    if variable_cost_per_order_calculated >= price_per_order:
        return None

    contribution_margin = price_per_order - variable_cost_per_order_calculated
    if contribution_margin == 0:
        return float('inf')

    orders_needed = (total_fixed_costs + target_profit) / contribution_margin
    return math.ceil(orders_needed)

# --- Projection Function (Accepts total fixed costs) ---
def generate_projections(
    total_fixed_costs_monthly, # *** Accepts the calculated total ***
    price_per_order,
    variable_cost_per_order_calculated,
    initial_monthly_orders,
    num_months,
    monthly_growth_rate_pct=0.0
):
    if any(v is None for v in [total_fixed_costs_monthly, price_per_order, variable_cost_per_order_calculated, initial_monthly_orders, num_months]) or initial_monthly_orders < 0:
         if not (initial_monthly_orders == 0 and total_fixed_costs_monthly == 0):
            st.warning("Cannot generate projections with zero/negative initial orders (unless fixed costs are also zero) or other missing inputs.")
            return pd.DataFrame()

    weeks_per_month_avg = 52 / 12
    # Calculate weekly fixed cost based on the total monthly fixed cost
    fixed_costs_weekly = total_fixed_costs_monthly / weeks_per_month_avg if weeks_per_month_avg > 0 else 0
    projection_data = []
    current_monthly_orders = float(initial_monthly_orders)
    global_week_counter = 1
    cumulative_profit_tracker = 0.0

    for month in range(1, num_months + 1):
        if month > 1:
            current_monthly_orders *= (1 + monthly_growth_rate_pct / 100.0)

        num_weeks_this_month = 4 # Simplified 4-week month assumption
        orders_per_week = current_monthly_orders / num_weeks_this_month if num_weeks_this_month > 0 else 0

        for week_in_month_simulated in range(num_weeks_this_month):
            simulated_orders = orders_per_week
            revenue = simulated_orders * price_per_order
            total_variable_costs = simulated_orders * variable_cost_per_order_calculated
            # Use the calculated weekly fixed cost derived from the total monthly
            profit = revenue - total_variable_costs - fixed_costs_weekly
            cumulative_profit_tracker += profit

            projection_data.append({
                "Month": month, "Global_Week": global_week_counter,
                "Projected_Orders_Weekly": round(simulated_orders, 1),
                "Revenue_Weekly": round(revenue, 2),
                "Variable_Costs_Weekly": round(total_variable_costs, 2),
                "Fixed_Costs_Weekly": round(fixed_costs_weekly, 2), # Display the averaged weekly value
                "Profit_Weekly": round(profit, 2),
                "Cumulative_Profit": round(cumulative_profit_tracker, 2)
            })
            global_week_counter += 1

    return pd.DataFrame(projection_data)

# --- Time to Breakeven Helper (Unchanged) ---
def find_time_to_positive_profit(projections_df):
    if projections_df.empty or 'Cumulative_Profit' not in projections_df.columns:
        return None, None, None
    positive_profit_rows = projections_df[projections_df['Cumulative_Profit'] >= 0]
    if positive_profit_rows.empty:
        return None, None, "Not Reached"
    first_positive_week_index = positive_profit_rows.index.min()
    first_positive_week_data = projections_df.loc[first_positive_week_index]
    week = first_positive_week_data['Global_Week']
    month = first_positive_week_data['Month']
    return week, month, "Reached"


# --- Streamlit App Structure ---

st.set_page_config(layout="wide", page_title="Advanced Breakeven Calculator")
st.title("📊 Advanced Business Breakeven & Projection Calculator")
st.markdown("""
Analyze profitability with detailed cost inputs. **Use the sidebar for inputs.** Results update live. Save & compare scenarios.
""")

# --- Initialize Session State (Unchanged) ---
if 'saved_scenario' not in st.session_state:
    st.session_state.saved_scenario = None


# --- Sidebar for Inputs ---
st.sidebar.header("⚙️ Input Parameters")

# --- NEW: Fixed Cost Inputs ---
st.sidebar.subheader("Fixed Costs Configuration")
marketer_payment_monthly = st.sidebar.number_input(
    "Monthly Marketer Payment (MAD )", min_value=0.0, value=3000.0, step=50.0, format="%.2f",
    help="Fixed monthly payment to marketing personnel/agency."
)
ads_spend_daily = st.sidebar.number_input(
    "Average Daily Ads Spend (MAD )", min_value=0.0, value=300.0, step=10.0, format="%.2f",
    help="Average amount spent on advertising per day."
)
# --- Calculate Total Monthly Fixed Costs ---
ads_spend_monthly = ads_spend_daily * AVG_DAYS_PER_MONTH
total_fixed_costs_monthly = marketer_payment_monthly + ads_spend_monthly
st.sidebar.info(f"**Total Estimated Monthly Fixed Costs:** MAD {total_fixed_costs_monthly:,.2f}")


# --- Other Core Inputs (Price, Variable Cost) ---
st.sidebar.divider()
st.sidebar.subheader("Revenue & Variable Costs")
price_per_order = st.sidebar.number_input(
    "Avg. Selling Price / Order (MAD )", min_value=0.01, value=450.0, step=0.50, format="%.2f",
    help="Average revenue per single order."
)

vc_input_method = st.sidebar.radio(
    "Variable Cost Input Method:", ('Fixed Amount (MAD )', 'Percentage (%)'), horizontal=True,
    help="Define variable costs as a flat amount or % of selling price."
)

variable_cost_amount = st.sidebar.number_input(
    "Avg. Variable Cost / Order (MAD )", min_value=0.0, value=390.0, step=0.50, format="%.2f",
    help="Direct cost per order (materials, etc.). Used if 'Fixed Amount (MAD )' selected.",
    disabled=(vc_input_method == 'Percentage (%)')
)
variable_cost_percentage = st.sidebar.number_input(
    "Avg. Variable Cost / Order (%)", min_value=0.0, max_value=500.0, value=85.0, step=1.0, format="%.1f",
    help="Variable cost as % of Selling Price. Used if 'Percentage (%)' selected.",
    disabled=(vc_input_method == 'Fixed Amount (MAD )')
)

# Calculate the effective variable cost
variable_cost_per_order_calculated = None
if vc_input_method == 'Fixed Amount (MAD )':
    variable_cost_per_order_calculated = variable_cost_amount
elif vc_input_method == 'Percentage (%)' and price_per_order > 0:
    variable_cost_per_order_calculated = price_per_order * (variable_cost_percentage / 100.0)
elif price_per_order <= 0 and vc_input_method == 'Percentage (%)':
     st.sidebar.warning("Cannot calculate % Variable Cost with MAD 0 Selling Price.")
     variable_cost_per_order_calculated = 0
else:
     variable_cost_per_order_calculated = 0


# --- Profit Goal & Projections (Unchanged Input Widgets) ---
st.sidebar.divider()
st.sidebar.subheader("Optional: Profit Goal")
target_profit_monthly = st.sidebar.number_input(
    "Target Monthly Profit (MAD )", min_value=0.0, value=1000.0, step=100.0, format="%.2f",
    help="Set a desired monthly profit."
)

st.sidebar.divider()
st.sidebar.subheader("Projection Settings")
num_months = st.sidebar.slider(
    "Months to Project", min_value=1, max_value=60, value=12, step=1,
    help="Duration for financial simulation."
)
monthly_growth_rate = st.sidebar.number_input(
    "Monthly Order Growth Rate (%)", min_value=-100.0, value=2.0, step=0.5, format="%.1f",
    help="Expected monthly percentage change in order volume."
)

# --- Scenario Management (Needs update to save new fixed cost inputs) ---
st.sidebar.divider()
st.sidebar.subheader("Scenario Management")
if st.sidebar.button("💾 Save Current as Scenario 1"):
    # *** Store NEW fixed cost inputs, remove the old one ***
    st.session_state.saved_scenario = {
        'inputs': {
            'marketer_payment_monthly': marketer_payment_monthly, # NEW
            'ads_spend_daily': ads_spend_daily,                   # NEW
            'price_per_order': price_per_order,
            'vc_input_method': vc_input_method,
            'variable_cost_amount': variable_cost_amount,
            'variable_cost_percentage': variable_cost_percentage,
            'target_profit_monthly': target_profit_monthly,
            'num_months': num_months,
            'monthly_growth_rate': monthly_growth_rate,
        },
        'calculated': {
             'total_fixed_costs_monthly': total_fixed_costs_monthly, # Store calculated total
             'variable_cost_per_order_calculated': variable_cost_per_order_calculated,
        }
        # Results will be added after calculations run
    }
    st.sidebar.success("Scenario 1 Saved!")

if st.session_state.saved_scenario:
    if st.sidebar.button("❌ Clear Saved Scenario"):
        st.session_state.saved_scenario = None
        st.sidebar.info("Saved scenario cleared.")
        st.experimental_rerun()


# --- Main Panel for Results ---

st.header("📈 Core Calculations")

# Use the calculated total_fixed_costs_monthly from now on
st.info(f"Using **Total Monthly Fixed Costs: MAD {total_fixed_costs_monthly:,.2f}** (Marketer: MAD {marketer_payment_monthly:,.2f}, Ads: ~MAD {ads_spend_monthly:,.2f})")
st.info(f"Using **Calculated Variable Cost per Order: MAD {variable_cost_per_order_calculated:.2f}** (Based on '{vc_input_method}')")

# 1. Calculate Breakeven and Contribution Margin (using calculated total fixed cost)
breakeven_orders_monthly, contribution_margin = calculate_breakeven(total_fixed_costs_monthly, price_per_order, variable_cost_per_order_calculated)

if variable_cost_per_order_calculated is None or contribution_margin is None:
    st.error(f"❌ Error: Cannot calculate with invalid inputs (e.g., Price MAD {price_per_order:.2f} <= Calculated Variable Cost MAD {variable_cost_per_order_calculated:.2f}). Correct inputs.")
    if st.session_state.saved_scenario and 'results' not in st.session_state.saved_scenario:
         st.session_state.saved_scenario['results'] = {'error': 'Invalid input for calculation'}
    st.stop()

st.metric(label="💰 Contribution Margin per Order", value=f"MAD {contribution_margin:.2f}",
          help="Profit per order before fixed costs. (Price - Calculated Variable Cost)")


# 2. Display Breakeven Point
st.subheader("🎯 Breakeven Point")
col1, col2 = st.columns(2)
breakeven_revenue = None
with col1:
    if breakeven_orders_monthly == float('inf'):
        st.metric(label="Orders per Month to Break Even", value="Infinite ♾️", help="Contribution margin is zero or negative.")
    elif breakeven_orders_monthly is not None:
        st.metric(label="Orders per Month to Break Even", value=f"{breakeven_orders_monthly:,.0f}")
        breakeven_revenue = breakeven_orders_monthly * price_per_order
    else:
        st.metric(label="Orders per Month to Break Even", value="N/A")

with col2:
    if breakeven_revenue == float('inf') or breakeven_revenue is None and breakeven_orders_monthly == float('inf'):
         st.metric(label="Revenue per Month to Break Even", value="Infinite ♾️")
    elif breakeven_revenue is not None:
        st.metric(label="Revenue per Month to Break Even", value=f"MAD {breakeven_revenue:,.2f}")
    else:
         st.metric(label="Revenue per Month to Break Even", value="N/A")

# 3. Calculate and Display Profit Goal (using calculated total fixed cost)
orders_for_profit = None
profit_goal_revenue = None
if target_profit_monthly > 0:
    st.subheader(f"💸 Target Profit: MAD {target_profit_monthly:,.2f}/Month")
    orders_for_profit = calculate_orders_for_profit(total_fixed_costs_monthly, price_per_order, variable_cost_per_order_calculated, target_profit_monthly)
    col3, col4 = st.columns(2)
    with col3:
        if orders_for_profit == float('inf'):
             st.metric(label="Orders Needed for Target Profit", value="Infinite ♾️")
        elif orders_for_profit is not None:
            st.metric(label="Orders Needed for Target Profit", value=f"{orders_for_profit:,.0f}")
            profit_goal_revenue = orders_for_profit * price_per_order
        else:
            st.metric(label="Orders Needed for Target Profit", value="N/A", help="Check if Price > Variable Cost.")

    with col4:
         if profit_goal_revenue == float('inf') or profit_goal_revenue is None and orders_for_profit == float('inf'):
              st.metric(label="Revenue Needed for Target Profit", value="Infinite ♾️")
         elif profit_goal_revenue is not None:
            st.metric(label="Revenue Needed for Target Profit", value=f"MAD {profit_goal_revenue:,.2f}")
         else:
            st.metric(label="Revenue Needed for Target Profit", value="N/A")
else:
    st.markdown("_No monthly profit target set (or target is MAD 0)._")


# --- Projection Section (uses calculated total fixed cost) ---
st.divider()
st.header("🗓️ Financial Projections")

projection_start_orders = 0
projection_basis = "Invalid Inputs"
if orders_for_profit is not None and orders_for_profit != float('inf') and orders_for_profit > 0:
    projection_start_orders = orders_for_profit
    projection_basis = f"Target Profit ({orders_for_profit:,.0f} orders/month)"
elif breakeven_orders_monthly is not None and breakeven_orders_monthly != float('inf') and breakeven_orders_monthly >= 0:
    projection_start_orders = breakeven_orders_monthly
    projection_basis = f"Breakeven Point ({breakeven_orders_monthly:,.0f} orders/month)"
else:
    projection_start_orders = None
    projection_basis = "Cannot determine valid starting point"

st.info(f"ℹ️ Projections starting based on: **{projection_basis}**. Growth Rate: **{monthly_growth_rate:.1f}%** per month.")

final_cumulative_profit = None
projections_df = pd.DataFrame()
monthly_summary = pd.DataFrame()

if projection_start_orders is not None:
    # *** Pass the calculated total fixed cost to the projection function ***
    projections_df = generate_projections(
        total_fixed_costs_monthly, # USE THE CALCULATED TOTAL
        price_per_order,
        variable_cost_per_order_calculated,
        projection_start_orders,
        num_months,
        monthly_growth_rate
    )

    if not projections_df.empty:
        breakeven_week, breakeven_month, status = find_time_to_positive_profit(projections_df)
        if status == "Reached":
             st.success(f"📈 **Est. Time to Positive Cumulative Profit:** Global Week {breakeven_week} (Month {breakeven_month})")
        elif status == "Not Reached":
             st.warning(f"📉 **Positive Cumulative Profit Not Reached** within the {num_months}-month projection period.")
        final_cumulative_profit = projections_df['Cumulative_Profit'].iloc[-1]

        with st.expander("📊 View Detailed Weekly Projections", expanded=False):
            st.dataframe(projections_df.style.format({
                "Projected_Orders_Weekly": "{:,.1f}", "Revenue_Weekly": "MAD {:,.2f}",
                "Variable_Costs_Weekly": "MAD {:,.2f}", "Fixed_Costs_Weekly": "MAD {:,.2f}", # Shows average weekly FC portion
                "Profit_Weekly": "MAD {:,.2f}", "Cumulative_Profit": "MAD {:,.2f}",
            }))

        st.subheader("📅 Monthly Summary")
        monthly_summary = projections_df.groupby('Month').agg(
            Total_Orders=('Projected_Orders_Weekly', 'sum'), Total_Revenue=('Revenue_Weekly', 'sum'),
            Total_Variable_Costs=('Variable_Costs_Weekly', 'sum'),
            # Summing the averaged weekly fixed costs gives back approx monthly total
            Total_Fixed_Costs=('Fixed_Costs_Weekly', 'sum'),
            Total_Profit=('Profit_Weekly', 'sum'), End_Cumulative_Profit=('Cumulative_Profit', 'last')
        ).reset_index()

        st.dataframe(monthly_summary.style.format({
            "Month": "{:,.0f}", "Total_Orders": "{:,.1f}", "Total_Revenue": "MAD {:,.2f}",
            "Total_Variable_Costs": "MAD {:,.2f}", "Total_Fixed_Costs": "MAD {:,.2f}",
            "Total_Profit": "MAD {:,.2f}", "End_Cumulative_Profit": "MAD {:,.2f}",
        }).hide(axis="index"))

        st.subheader("Visualizations") # Visualizations
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            st.markdown("**Monthly Profit Trend**")
            chart_data_profit = monthly_summary.set_index('Month')['Total_Profit']
            st.bar_chart(chart_data_profit)
        with viz_col2:
            st.markdown("**Monthly Revenue Breakdown**")
            cost_breakdown_df = monthly_summary[['Month','Total_Variable_Costs', 'Total_Fixed_Costs', 'Total_Profit']].copy()
            cost_breakdown_df.rename(columns={
                'Total_Variable_Costs': 'Variable Costs', 'Total_Fixed_Costs': 'Fixed Costs', 'Total_Profit': 'Profit'
            }, inplace=True)
            cost_breakdown_df = cost_breakdown_df.set_index('Month')
            # Filter out potential NaN/Inf before charting
            cost_breakdown_df.replace([float('inf'), -float('inf')], 0, inplace=True) # Replace Inf with 0 for charting
            cost_breakdown_df.dropna(inplace=True) # Drop rows with NaN if any persist
            if not cost_breakdown_df.empty:
                 st.bar_chart(cost_breakdown_df)
                 st.caption("_(Total bar height approximates Total Revenue)_")
            else:
                 st.caption("_(Cannot display breakdown chart due to invalid data)_")


        st.subheader("📥 Download Projections")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            projections_df.to_excel(writer, index=False, sheet_name='Weekly_Projections')
            monthly_summary.to_excel(writer, index=False, sheet_name='Monthly_Summary')
        output.seek(0)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"business_projections_{timestamp}.xlsx"
        st.download_button(
            label="📄 Download Weekly & Monthly Report (Excel)", data=output,
            file_name=excel_filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Projections could not be generated.")
else:
     st.error("❌ Cannot generate projections: Valid starting point not determined.")


# --- Populate Results for Saved Scenario ---
if st.session_state.saved_scenario and 'results' not in st.session_state.saved_scenario:
    st.session_state.saved_scenario['results'] = {
        'contribution_margin': contribution_margin,
        'breakeven_orders_monthly': breakeven_orders_monthly,
        'breakeven_revenue': breakeven_revenue,
        'orders_for_profit': orders_for_profit,
        'profit_goal_revenue': profit_goal_revenue,
        'projection_basis': projection_basis,
        'projection_start_orders': projection_start_orders,
        'final_cumulative_profit': final_cumulative_profit,
        # Add more key results if needed
    }
    st.session_state.saved_scenario = copy.deepcopy(st.session_state.saved_scenario)


# --- Scenario Comparison Section (Needs update for new fixed cost inputs) ---
st.divider()
st.header("🔄 Scenario Comparison")

if st.session_state.saved_scenario:
    saved = st.session_state.saved_scenario
    saved_results = saved.get('results', {})
    saved_inputs = saved.get('inputs', {})
    # *** Get saved individual fixed cost inputs ***
    saved_marketer_payment = saved_inputs.get('marketer_payment_monthly', 0)
    saved_ads_daily = saved_inputs.get('ads_spend_daily', 0)
    saved_total_fixed = saved.get('calculated', {}).get('total_fixed_costs_monthly', 0) # Get calculated total from saved data

    st.subheader("Comparing Current Settings vs. Saved Scenario 1")
    comp_col1, comp_col2 = st.columns(2)

    # Helper function remains the same
    def display_comparison(col, title, current_val, saved_val, format_func=lambda x: f"{x}"):
         col.markdown(f"**{title}**")
         current_display = "N/A"
         if current_val is not None and current_val != float('inf'):
             try: current_display = format_func(current_val)
             except: current_display = str(current_val)
         elif current_val == float('inf'): current_display = "Infinite ♾️"

         saved_display = "N/A"
         if 'error' in saved_results: saved_display = "Error in Calc"
         elif saved_val is not None and saved_val != float('inf'):
             try: saved_display = format_func(saved_val)
             except: saved_display = str(saved_val)
         elif saved_val == float('inf'): saved_display = "Infinite ♾️"

         col.markdown(f" Current: `{current_display}` | Saved: `{saved_display}`")


    with comp_col1:
        st.markdown("#### Current Scenario Inputs")
        # *** Display current individual fixed cost inputs ***
        st.markdown(f"**Marketer Pay:** `MAD {marketer_payment_monthly:,.2f}` /mo")
        st.markdown(f"**Daily Ads:** `MAD {ads_spend_daily:,.2f}` /day")
        st.markdown(f"**Total Fixed:** `MAD {total_fixed_costs_monthly:,.2f}` /mo")
        st.markdown(f"**Price:** `MAD {price_per_order:,.2f}`")
        st.markdown(f"**Var. Cost ({vc_input_method}):** `MAD {variable_cost_per_order_calculated:.2f}`")
        st.markdown(f"**Profit Goal:** `MAD {target_profit_monthly:,.2f}`")
        st.markdown(f"**Growth:** `{monthly_growth_rate:.1f}%`")


    with comp_col2:
        st.markdown("#### Saved Scenario 1 Inputs")
         # *** Display saved individual fixed cost inputs ***
        st.markdown(f"**Marketer Pay:** `MAD {saved_marketer_payment:,.2f}` /mo")
        st.markdown(f"**Daily Ads:** `MAD {saved_ads_daily:,.2f}` /day")
        st.markdown(f"**Total Fixed:** `MAD {saved_total_fixed:,.2f}` /mo") # Show saved calculated total
        st.markdown(f"**Price:** `MAD {saved_inputs.get('price_per_order', 0):,.2f}`")
        saved_vc_method = saved_inputs.get('vc_input_method', 'N/A')
        saved_vc_calculated = saved.get('calculated', {}).get('variable_cost_per_order_calculated', 0)
        st.markdown(f"**Var. Cost ({saved_vc_method}):** `MAD {saved_vc_calculated:.2f}`")
        st.markdown(f"**Profit Goal:** `MAD {saved_inputs.get('target_profit_monthly', 0):,.2f}`")
        st.markdown(f"**Growth:** `{saved_inputs.get('monthly_growth_rate', 0):.1f}%`")


    st.markdown("---")
    st.markdown("#### Results Comparison")
    res_col1, res_col2 = st.columns(2) # Use columns for results comparison too
    with res_col1:
        display_comparison(st, "Breakeven Orders", breakeven_orders_monthly, saved_results.get('breakeven_orders_monthly'), format_func=lambda x: f"{x:,.0f}")
        display_comparison(st, "Orders for Profit", orders_for_profit, saved_results.get('orders_for_profit'), format_func=lambda x: f"{x:,.0f}")

    with res_col2:
        display_comparison(st, "Breakeven Revenue", breakeven_revenue, saved_results.get('breakeven_revenue'), format_func=lambda x: f"MAD {x:,.2f}")
        display_comparison(st, "Final Cum. Profit", final_cumulative_profit, saved_results.get('final_cumulative_profit'), format_func=lambda x: f"MAD {x:,.2f}")

else:
    st.info("Click 'Save Current as Scenario 1' in the sidebar to store the current inputs and results for comparison.")


st.markdown("---")
st.caption("Fixed costs now based on Marketer Payment & Daily Ads Spend.")
