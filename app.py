import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Tuple

# Configuration
st.set_page_config(
    page_title="Gilt Ladder Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class GiltLadderCalculator:
    def __init__(self):
        self.personal_allowance = 12570  # 2024/25 tax year
        self.basic_rate_threshold = 50270
        self.higher_rate_threshold = 125140
        
    def calculate_yield_to_maturity(self, price: float, face_value: float, 
                                  coupon_rate: float, years_to_maturity: float) -> float:
        """Calculate Yield to Maturity using approximation formula"""
        annual_coupon = face_value * (coupon_rate / 100)
        capital_gain = (face_value - price) / years_to_maturity
        average_price = (face_value + price) / 2
        ytm = (annual_coupon + capital_gain) / average_price * 100
        return ytm
    
    def calculate_tax_liability(self, income: float, pension_income: float = 0) -> Dict:
        """Calculate tax liability based on total income"""
        total_income = income + pension_income
        
        if total_income <= self.personal_allowance:
            tax = 0
        elif total_income <= self.basic_rate_threshold:
            tax = (total_income - self.personal_allowance) * 0.20
        elif total_income <= self.higher_rate_threshold:
            basic_tax = (self.basic_rate_threshold - self.personal_allowance) * 0.20
            higher_tax = (total_income - self.basic_rate_threshold) * 0.40
            tax = basic_tax + higher_tax
        else:
            basic_tax = (self.basic_rate_threshold - self.personal_allowance) * 0.20
            higher_tax = (self.higher_rate_threshold - self.basic_rate_threshold) * 0.40
            additional_tax = (total_income - self.higher_rate_threshold) * 0.45
            tax = basic_tax + higher_tax + additional_tax
            
        return {
            'gross_income': total_income,
            'tax_liability': tax,
            'net_income': total_income - tax,
            'effective_rate': (tax / total_income * 100) if total_income > 0 else 0
        }
    
    def create_bond_ladder(self, total_investment: float, ladder_years: int, 
                          target_yield: float) -> pd.DataFrame:
        """Create a bond ladder allocation"""
        allocation_per_year = total_investment / ladder_years
        
        ladder_data = []
        for year in range(1, ladder_years + 1):
            maturity_year = datetime.now().year + year
            estimated_yield = target_yield + (year - 1) * 0.1  # Yield curve slope
            annual_income = allocation_per_year * (estimated_yield / 100)
            
            ladder_data.append({
                'Maturity_Year': maturity_year,
                'Allocation': allocation_per_year,
                'Target_Yield': estimated_yield,
                'Annual_Income': annual_income,
                'Allocation_Percentage': (allocation_per_year / total_investment) * 100
            })
            
        return pd.DataFrame(ladder_data)

def main():
    st.title("🏦 Gilt Ladder Calculator")
    st.markdown("**Build and analyze your UK gilt ladder investment strategy**")
    
    calc = GiltLadderCalculator()
    
    # Sidebar inputs
    st.sidebar.header("📊 Investment Parameters")
    
    # Portfolio inputs
    sipp_value = st.sidebar.number_input(
        "SIPP Value (£)", 
        min_value=0, 
        value=565000, 
        step=1000,
        help="Current value of your Self-Invested Personal Pension"
    )
    
    isa_value = st.sidebar.number_input(
        "ISA Value (£)", 
        min_value=0, 
        value=92000, 
        step=1000,
        help="Current value of your Individual Savings Account"
    )
    
    # Income targets
    target_income = st.sidebar.number_input(
        "Target Annual Income (£)", 
        min_value=0, 
        value=40000, 
        step=1000,
        help="Desired annual income from your bond ladder"
    )
    
    pension_income = st.sidebar.number_input(
        "Other Pension Income (£)", 
        min_value=0, 
        value=13000, 
        step=500,
        help="Income from defined benefit pensions or state pension"
    )
    
    # Ladder parameters
    ladder_years = st.sidebar.slider(
        "Ladder Duration (Years)", 
        min_value=3, 
        max_value=10, 
        value=5,
        help="Number of years in your bond ladder"
    )
    
    target_yield = st.sidebar.slider(
        "Target Average Yield (%)", 
        min_value=2.0, 
        max_value=8.0, 
        value=4.5, 
        step=0.1,
        help="Expected average yield across your gilt portfolio"
    )
    
    # Advanced options
    with st.sidebar.expander("⚙️ Advanced Options"):
        isa_yield_premium = st.slider(
            "ISA Yield Premium (%)", 
            min_value=0.0, 
            max_value=2.0, 
            value=0.5, 
            step=0.1,
            help="Additional yield for ISA investments (corporate bonds vs gilts)"
        )
        
        cash_buffer_percent = st.slider(
            "Cash Buffer (%)", 
            min_value=0, 
            max_value=20, 
            value=5,
            help="Percentage to keep in cash for flexibility"
        )
    
    # Main calculation area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📈 Bond Ladder Analysis")
        
        # Calculate cash buffers
        sipp_cash = sipp_value * (cash_buffer_percent / 100)
        isa_cash = isa_value * (cash_buffer_percent / 100)
        sipp_invested = sipp_value - sipp_cash
        isa_invested = isa_value - isa_cash
        
        # Create ladders
        sipp_ladder = calc.create_bond_ladder(sipp_invested, ladder_years, target_yield)
        isa_ladder = calc.create_bond_ladder(isa_invested, ladder_years, target_yield + isa_yield_premium)
        
        # Display ladders
        st.subheader("SIPP Bond Ladder")
        st.dataframe(
            sipp_ladder.style.format({
                'Allocation': '£{:,.0f}',
                'Target_Yield': '{:.1f}%',
                'Annual_Income': '£{:,.0f}',
                'Allocation_Percentage': '{:.1f}%'
            }),
            use_container_width=True
        )
        
        st.subheader("ISA Bond Ladder")
        st.dataframe(
            isa_ladder.style.format({
                'Allocation': '£{:,.0f}',
                'Target_Yield': '{:.1f}%',
                'Annual_Income': '£{:,.0f}',
                'Allocation_Percentage': '{:.1f}%'
            }),
            use_container_width=True
        )
        
        # Income projection chart
        total_ladder_income = sipp_ladder['Annual_Income'].sum() + isa_ladder['Annual_Income'].sum()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=sipp_ladder['Maturity_Year'],
            y=sipp_ladder['Annual_Income'],
            name='SIPP Income',
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            x=isa_ladder['Maturity_Year'],
            y=isa_ladder['Annual_Income'],
            name='ISA Income',
            marker_color='lightgreen'
        ))
        
        fig.update_layout(
            title='Annual Income by Maturity Year',
            xaxis_title='Maturity Year',
            yaxis_title='Annual Income (£)',
            barmode='stack',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.header("💰 Income Summary")
        
        # Calculate total income
        total_bond_income = total_ladder_income
        total_income = total_bond_income + pension_income
        
        # Tax calculation
        tax_calc = calc.calculate_tax_liability(total_bond_income, pension_income)
        
        # Display summary
        st.metric("Total Bond Income", f"£{total_bond_income:,.0f}")
        st.metric("Other Pension Income", f"£{pension_income:,.0f}")
        st.metric("Gross Total Income", f"£{tax_calc['gross_income']:,.0f}")
        st.metric("Tax Liability", f"£{tax_calc['tax_liability']:,.0f}")
        st.metric("Net Income", f"£{tax_calc['net_income']:,.0f}")
        st.metric("Effective Tax Rate", f"{tax_calc['effective_rate']:.1f}%")
        
        # Target comparison
        income_vs_target = (tax_calc['net_income'] / target_income - 1) * 100
        st.metric(
            "vs Target Income", 
            f"{income_vs_target:+.1f}%",
            delta=f"£{tax_calc['net_income'] - target_income:,.0f}"
        )
        
        st.header("🎯 Portfolio Allocation")
        
        # Portfolio pie chart
        allocation_data = {
            'SIPP Bonds': sipp_invested,
            'ISA Bonds': isa_invested,
            'SIPP Cash': sipp_cash,
            'ISA Cash': isa_cash
        }
        
        fig_pie = px.pie(
            values=list(allocation_data.values()),
            names=list(allocation_data.keys()),
            title="Portfolio Allocation"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Cash buffer info
        st.info(f"""
        **Cash Buffers:**
        - SIPP: £{sipp_cash:,.0f}
        - ISA: £{isa_cash:,.0f}
        - Total: £{sipp_cash + isa_cash:,.0f}
        """)
    
    # Additional analysis section
    st.header("📋 Implementation Guidance")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🎯 Recommended Gilt Selection")
        
        # Sample gilt recommendations based on maturity years
        gilt_recommendations = []
        for _, row in sipp_ladder.iterrows():
            year = row['Maturity_Year']
            if year == 2028:
                gilt_recommendations.append(("UK Treasury 1.625% 2028", "GB00BFWFPP71"))
            elif year == 2029:
                gilt_recommendations.append(("UK Treasury 0.875% 2029", "GB00BJMHB534"))
            elif year == 2030:
                gilt_recommendations.append(("UK Treasury 0.375% 2030", "GB00BKPWFW93"))
            elif year == 2031:
                gilt_recommendations.append(("UK Treasury 0.25% 2031", "GB00BN65R313"))
            elif year == 2032:
                gilt_recommendations.append(("UK Treasury 4.25% 2032", "GB00004893086"))
            else:
                gilt_recommendations.append((f"UK Treasury Gilt {year}", "TBD"))
        
        for gilt_name, isin in gilt_recommendations:
            st.write(f"**{gilt_name}**")
            st.write(f"ISIN: {isin}")
            st.write("---")
    
    with col4:
        st.subheader("⚠️ Key Considerations")
        
        st.write("""
        **Before Implementation:**
        - ✅ Open Interactive Investor SIPP and ISA accounts
        - ✅ Research current gilt prices and yields
        - ✅ Consider staggering purchases over 3-6 months
        - ✅ Set up drawdown arrangements
        
        **Ongoing Management:**
        - 🔄 Reinvest matured bonds in new 5-year issues
        - 📊 Review annually for income target adjustments
        - 💰 Monitor inflation impact on purchasing power
        - 🎯 Maintain ladder structure consistently
        """)
        
        # Risk warning
        st.warning("""
        **Risk Warning:** This calculator provides estimates based on current assumptions. 
        Actual returns may vary due to interest rate changes, inflation, and market conditions. 
        Consider seeking professional financial advice before implementing any strategy.
        """)

if __name__ == "__main__":
    main()
