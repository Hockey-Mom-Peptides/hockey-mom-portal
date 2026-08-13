import streamlit as st

def render_peptide_kit_listing():
    st.title("🔥 Hot Hockey Mom Peptides")
    st.subheader("Ultimate Research Start Up Kit")
    
    # Left: Image display & Kit Inclusions
    col_left, col_right = st.columns([1.2, 1])
    
    with col_left:
        # Displaying the finalized listing photo
        st.image("start up kit.png", caption="Ultimate Start Up Kit Components")
        
        st.markdown("""
        ### 📦 What's Included:
        * **(1)** Bonus vial storage case
        * **(1)** Mini sharps container
        * **(1)** Reusable injector pen
        * **(25)** Disposable needle tips
        * **(3)** Prefilled 100-unit Vials *(Customized by selection)*
        * **(2)** 200-Unit vial Vit. B-complex
        * Dosage/Injection Guide & QR Code
        
        > **Storage Note:** GLP vials must be kept in the refrigerator. Vitamin B Complex is stored in a room temperature, dark, dry place.
        """)

    # Right: Configuration & Pricing
    with col_right:
        st.markdown("### 🛒 Select Your Research Cycle")
        
        # Mapping your specific pricing structures
        kit_options = {
            "Trizepatide: 3-Month Starter Dose (2.5mg/wk)": 135.00,
            "Retatrutide: 3-Month Starter Dose (2mg/wk)": 195.00,
            "KLOW: 8-Week Cycle": 220.00,
            "KLOW: 12-Week Cycle": 285.00
        }
        
        selected_option = st.selectbox(
            "Choose your package:",
            options=list(kit_options.keys())
        )
        
        final_price = kit_options[selected_option]
        
        st.markdown("---")
        st.metric(label="Total Package Cost", value=f"${final_price:.2f}")
        
        if st.button("Add Kit to Cart", type="primary"):
            st.success(f"Added {selected_option} to your cart! Total: ${final_price:.2f}")

def main():
    st.set_page_config(page_title="Hot Hockey Mom Peptides", page_icon="🔥", layout="wide")
    render_peptide_kit_listing()

if __name__ == "__main__":
    main()
