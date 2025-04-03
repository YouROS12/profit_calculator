import streamlit as st
import math

# --- App Configuration ---
st.set_page_config(layout="wide", page_title="Graduation Dress Profit Calculator")

# --- Helper Function ---
def format_currency(value):
    """Formats a number as MAD currency."""
    return f"{value:,.2f} MAD"

# --- Sidebar for Inputs ---
st.sidebar.header("📊 Input Parameters")

st.sidebar.subheader("🎯 Profit Goal")
target_profit = st.sidebar.number_input("Overall Profit Target (MAD)", min_value=1, value=30000, step=1000)

st.sidebar.divider()

st.sidebar.subheader("👗 Dress Details")
dress_cost = st.sidebar.number_input("Purchase Cost per Dress (MAD)", min_value=1.0, value=115.0, step=1.0)
dress_selling_price = st.sidebar.number_input("Selling Price After Rentals (MAD)", min_value=0.0, value=180.0, step=5.0, help="The price you sell the dress for after it has been rented.")

st.sidebar.subheader("렌탈 (Rental) Details")
average_rental_price = st.sidebar.slider("Average Rental Price per Hire (MAD)", min_value=0.0, max_value=100.0, value=45.0, step=1.0)
average_rentals_per_dress = st.sidebar.slider("Average Rentals Before Selling", min_value=0.0, max_value=5.0, value=1.5, step=0.1)

st.sidebar.divider()

st.sidebar.subheader("🎀 Add-ons (Personalization)")
gap_price = st.sidebar.number_input("Personalized Gap Selling Price (MAD)", min_value=0.0, value=15.0, step=0.5)
gap_cost = st.sidebar.number_input("Personalized Gap Cost (MAD)", min_value=0.0, value=10.0, step=0.5)

scarf_price = st.sidebar.number_input("Personalized Scarf Selling Price (MAD)", min_value=0.0, value=25.0, step=0.5)
scarf_cost = st.sidebar.number_input("Personalized Scarf Cost (MAD)", min_value=0.0, value=10.0, step=0.5)

# --- MODIFIED: Percentage Input for Personalization ---
percent_personalized_sales = st.sidebar.slider(
    "% of Dress Sales Including Personalization",
    min_value=0,
    max_value=100,
    value=75, # Default to 75%
    step=5,
    help="What percentage of your dress sales also include both the personalized Gap and Scarf?"
)
# --- REMOVED: addon_method radio button and independent counts ---

# --- Calculations ---

# 1. Dress Profits (Lifecycle: Rentals + Final Sale)
profit_from_sale_raw = dress_selling_price - dress_cost
rental_profit_per_dress_raw = average_rental_price * average_rentals_per_dress
base_total_profit_per_dress_raw = profit_from_sale_raw + rental_profit_per_dress_raw # Profit from dress cycle ONLY

# Calculate Overall Dress Cycle Margin (remains the same logic)
total_revenue_per_dress_cycle = (average_rental_price * average_rentals_per_dress) + dress_selling_price
overall_profit_margin_percent = 0.0
calculation_issue_margin = ""
if total_revenue_per_dress_cycle <= 0:
     overall_profit_margin_percent = 0.0
     calculation_issue_margin = " (Cannot calculate margin: No revenue)"
else:
    overall_profit_margin_percent = (base_total_profit_per_dress_raw / total_revenue_per_dress_cycle) * 100.0


# 2. Add-on Profits (per set)
profit_per_gap_raw = gap_price - gap_cost
profit_per_scarf_raw = scarf_price - scarf_cost
total_profit_per_addon_set_raw = profit_per_gap_raw + profit_per_scarf_raw

# 3. --- MODIFIED: Calculate Average Profit Per Sale (Weighted Average) ---
profit_per_simple_sale_raw = base_total_profit_per_dress_raw
profit_per_personalized_sale_raw = base_total_profit_per_dress_raw + total_profit_per_addon_set_raw

# Calculate the weighted average profit based on the percentage
personalized_fraction = percent_personalized_sales / 100.0
simple_fraction = 1.0 - personalized_fraction

average_profit_per_sale_raw = (personalized_fraction * profit_per_personalized_sale_raw) + \
                              (simple_fraction * profit_per_simple_sale_raw)

# 4. Calculate Number of Sales Needed
dresses_needed = 0
calculation_possible = True
error_message = ""

if average_profit_per_sale_raw <= 0:
    if target_profit > 0:
        calculation_possible = False
        error_message = f"Cannot reach target: The calculated average profit per sale ({format_currency(average_profit_per_sale_raw)}) is zero or negative based on the current costs, prices, and personalization rate."
    else:
        # Target is 0 or negative, so 0 sales needed even if avg profit is non-positive
        dresses_needed = 0
elif target_profit <= 0:
     # Target is 0 or negative, and avg profit is positive
     dresses_needed = 0
else:
    # Target is positive, avg profit is positive
    dresses_needed = math.ceil(target_profit / average_profit_per_sale_raw)


# --- Main Area for Results ---
st.title("🎓 Graduation Dress Business Profit Calculator")
st.markdown("Adjust parameters in the sidebar. The calculator assumes a percentage of dress sales include personalization (Gap + Scarf).")
st.divider()

# Display Intermediate Calculations
st.subheader("📈 Calculated Profits & Margin per Item/Cycle")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Profit from Dress Final Sale", format_currency(profit_from_sale_raw), help=f"{format_currency(dress_selling_price)} Selling Price - {format_currency(dress_cost)} Cost")
    st.metric("Avg. Rental Profit / Dress", format_currency(rental_profit_per_dress_raw), help=f"{average_rentals_per_dress} rentals @ {format_currency(average_rental_price)} avg.")
    st.metric("➡️ Base Profit / Dress Cycle", format_currency(base_total_profit_per_dress_raw), help="Profit from rentals + final sale, BEFORE add-ons.")

with col2:
     st.metric("Profit / Personalized Gap", format_currency(profit_per_gap_raw))
     st.metric("Profit / Personalized Scarf", format_currency(profit_per_scarf_raw))
     st.metric("➡️ Profit / Add-on Set", format_currency(total_profit_per_addon_set_raw), help="Combined profit from one Gap + one Scarf.")

with col3:
     st.metric("📊 Overall Profit Margin / Dress Cycle", f"{overall_profit_margin_percent:.1f}%", help=f"Base Dress Profit / Total Dress Revenue {calculation_issue_margin}")
     st.metric("Avg. Profit / Simple Sale", format_currency(profit_per_simple_sale_raw), help="Profit from dress cycle only.")
     st.metric("Avg. Profit / Personalized Sale", format_currency(profit_per_personalized_sale_raw), help="Profit from dress cycle + add-on set.")


st.divider()

# --- MODIFIED: Display Average Profit Calculation ---
st.subheader("📊 Weighted Average Profit per Sale")
st.info(f"Based on **{percent_personalized_sales}%** of sales including personalization (Gap + Scarf):")
st.metric(
    "Calculated Average Profit per Dress Sale",
    format_currency(average_profit_per_sale_raw),
    help=f"({percent_personalized_sales}% * {format_currency(profit_per_personalized_sale_raw)}) + ({100-percent_personalized_sales}% * {format_currency(profit_per_simple_sale_raw)})"
)

st.divider()

# Display Final Result
st.subheader("🎯 Sales Target")

if not calculation_possible:
    st.error(error_message)
elif target_profit <= 0 :
     st.success(f"🎉 Your profit target is {format_currency(target_profit)} or less. **0 dress sales** are needed.")
else:
    st.metric(
        label=f"Number of Dress Sales Needed to Reach {format_currency(target_profit)} Profit",
        value=f"{int(dresses_needed)} dresses"
        )
    st.info(f"This calculation uses the **average profit per sale of {format_currency(average_profit_per_sale_raw)}**, considering the specified mix of simple and personalized sales.")


# --- How to Run ---
st.sidebar.divider()
st.sidebar.caption("How to run this app:")
st.sidebar.code("""
1. Save code as profit_calculator.py
2. Open terminal/command prompt
3. Navigate to directory
4. Run: streamlit run profit_calculator.py
""")
st.sidebar.caption("Requires Python & Streamlit (`pip install streamlit`)")