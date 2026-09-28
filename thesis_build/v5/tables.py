# -*- coding: utf-8 -*-
"""Every Chapter Four table, in the actor-by-BMU layout, across all three objectives."""
import sys, json
sys.path.insert(0, 'v5')
from engine import (DF, VL, LBL, ACT, BMU, ACTORS, SITES, NA, table, HEADERS, WIDTHS,
                    vals, valid_n, sampled, categories, _MC, fmt_p)

AGE   = ['Under 18', '18-35', '36-49', '50-60', 'Over 60']
EDU   = ['No formal education', 'Primary', 'Secondary', 'Certificate', 'Diploma', 'Undergraduate']
ETH   = ['Digo', 'Duruma', 'Vumba', 'Swahili', 'Kikuyu', 'Chinese']
MAR   = ['Single', 'Married', 'Separated / divorced', 'Widowed']
EXP   = ['Less than 5 years', '5-10 years', '11-20 years', 'Over 20 years']
SCALE = ['Small-scale', 'Medium-scale', 'Large-scale']
INC   = ['Below KSh 13,900', 'KSh 13,900-69,500', 'KSh 69,501-139,000']
YN    = ['Yes', 'No']
CATCH = ['2-3 kg', '4-5 kg', '5-10 kg', 'Above 10 kg']
MORT  = ['Frozen / no mortality', '0.5-1 kg', '4-5 kg', 'Above 10 kg']
SPOIL = ['1 kg', '3 kg', '5 kg', 'Above 10 kg']
LIK   = ['Strongly disagree', 'Disagree', 'Neutral', 'Agree']
YOUTH = ['Very low', 'Low', 'Neutral']
DIV   = ['Negative', 'Not explored yet', 'Neutral', 'Positive']
CONS  = ['Price fluctuations', 'Mortality', 'Market seasonality',
         'High freight, flight delays and supply risk']
INFRA = ['Poor road infrastructure', 'Lack of aggregation facilities', 'Limited transport',
         'Market seasonality', 'High freight, flight delays and mortality']

SPEC = [
 # ---- Objective One -------------------------------------------------------
 ('Age Group of Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('age_group_0_1', AGE)]),
 ('Gender of Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('gender_0_1', ['Male', 'Female'])]),
 ('Highest Education Attained by Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('education_0_1', EDU)]),
 ('Ethnic Group of Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('ethnicity_0_1', ETH)]),
 ('Marital Status of Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('marital_0_1', MAR)]),
 ('Years of Experience of Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('experience_0_1', EXP)]),
 ('Primary Role and Business Ownership of Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('primary_role_0_1', None), ('own_manage_0_1', ['Yes'])]),
 ('Scale of Operation of Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('scale_0_1', SCALE)]),
 ('Monthly Mud Crab Income Band of Fishers, Middlemen, Hoteliers and Exporters by BMU',
  [('income_band_0_1', INC)]),
 ('Other Income Activities and Operating Licence by Actor and BMU',
  [('other_activity_0_1', YN), ('licence_0_1', YN)]),
 ('Use of Loans to Facilitate Business by Actor and BMU',
  [('loans_0_1', YN)]),
 ('Main Source of Business Credit by Actor and BMU',
  [('loan_source_0_1', None)]),
 ('Knowledge Acquisition and Formal Training by Actor and BMU',
  [('knowledge_source_0_1', None), ('training_0_1', YN)]),
 ('Cooperative Membership, Self-Help Group Participation and Primary Market Supplied by Actor and BMU',
  [('cooperative_0_1', ['No']), ('self_help_0_1', ['No']),
   ('market_supply_0_1', ['Local markets', 'Export markets'])]),
 # ---- Objective Two -------------------------------------------------------
 ('How Mud Crabs Are Acquired and Source of Crabs for Sale by Actor and BMU',
  [('acquisition_0_2', ['Catching', 'Purchasing']), ('source_trade_0_2', None)]),
 ('Fishing or Collection Gear Used by Actor and BMU',
  [('gear_0_2', None)]),
 ('Daily Mud Crab Catch Reported by Actor and BMU',
  [('catch_daily_0_2', CATCH)]),
 ('Proportion of Catch Sold and Travel Time from Fishing Grounds to Market by Actor and BMU',
  [('proportion_sold_0_2', ['Whole catch', 'Three-quarters']), ('time_market_0_2', None)]),
 ('Main Buyer Category by Actor and BMU',
  [('buyer_category_0_2', None)]),
 ('Primary Market Channel and Contact With Final Consumers by Actor and BMU',
  [('market_channel_0_2', None),
   ('consumer_contact_0_2', ['Through intermediaries', 'Direct contact'])]),
 ('Preparation of Mud Crabs for Market and Preservation by Actor and BMU',
  [('preparation_0_2', None), ('preserve_process_0_2', ['Yes / frozen', 'No'])]),
 ('Packaging Used for Transporting Mud Crabs by Actor and BMU',
  [('packaging_0_2', None)]),
 ('Mode of Transporting Mud Crabs to Market by Actor and BMU',
  [('transport_0_2', None)]),
 ('Grading Practice and Criteria Used to Determine Grade by Actor and BMU',
  [('grading_0_2', ['Yes']), ('grade_basis_0_2', None)]),
 ('Quality Measures Before Market and Use of Formal Quality Control by Actor and BMU',
  [('quality_before_0_2', None), ('quality_control_0_2', YN)]),
 ('Size Label and Grade Assignment for Large Crabs by Actor and BMU',
  [('size_large_0_2', ['Large', 'All sizes / mixed']),
   ('grade_large_0_2', ['Grade A', 'Mixed grade'])]),
 ('Size Label and Grade Assignment for Medium Crabs by Actor and BMU',
  [('size_medium_0_2', ['Medium', 'Mixed size']),
   ('grade_medium_0_2', ['Grade B', 'Mixed grade'])]),
 ('Size Label and Grade Assignment for Small Crabs by Actor and BMU',
  [('size_small_0_2', ['Small', 'Mixed size']),
   ('grade_small_0_2', ['Grade C', 'Mixed grade'])]),
 ('Reported Daily Mortality by Actor and BMU',
  [('mortality_0_2', MORT)]),
 ('Reported Loss Through Spoilage by Actor and BMU',
  [('spoilage_0_2', SPOIL)]),
 ('Mode of Payment by Actor and BMU',
  [('payment_0_2', None)]),
 ('Pricing Mechanism and How Prices Are Set by Actor and BMU',
  [('price_standard_0_2', ['No']), ('price_setting_0_2', None)]),
 ('Factors Influencing Price Fluctuations by Actor and BMU',
  [('price_factors_0_2', None)]),
 ('Number of Buyers, State of Crabs Sold and Regularity of the Main Buyer by Actor and BMU',
  [('buyer_count_0_2', ['One buyer', 'Two buyers'], 'Number of buyers reported'),
   ('product_state_0_2', ['Live']), ('buyer_regular_0_2', ['Yes'])]),
 ('Location of Sale and Knowledge of the Onward Sale by Actor and BMU',
  [('location_sale_0_2', None), ('sell_to_next_0_2', ['No'])]),
 ('First Buyer Location Reported by Fishers by BMU',
  [('buyer1_location_0_2', None)]),
 ('Second Buyer Location Reported by Fishers by BMU',
  [('buyer2_location_0_2', None)]),
 ('Tied Depot Owners and Arrangements With Tied Fishers and Traders by Actor and BMU',
  [('depot_tied_0_2', YN), ('fisher_arrangement_0_2', None),
   ('trader_arrangement_0_2', None)]),
 ('Arrangements Used With Tied Depot Owners by Actor and BMU',
  [('depot_arrangement_0_2', None)]),

 ('Tied Fishers, Tied Traders and Trading Agreements by Actor and BMU',
  [('fishers_tied_0_2', YN), ('traders_tied_0_2', YN), ('formal_agreement_0_2', YN)]),
 ('Role of Intermediaries and Negotiation Terms by Actor and BMU',
  [('intermediary_role_0_2', None), ('negotiation_terms_0_2', None)]),
 ('Technology Adoption and Market Research by Actor and BMU',
  [('technology_0_2', ['No']), ('market_research_0_2', ['No'])]),
 # ---- Objective Three -----------------------------------------------------
 ('Main Operational or Marketing Constraint by Actor and BMU',
  [('main_constraint_0_3', CONS)]),
 ('Main Infrastructure or Logistics Constraint and Need for Improvement by Actor and BMU',
  [('infrastructure_0_3', INFRA), ('infra_improvement_0_3', ['Yes'])]),
 ('Barriers to Market Access and Operational Challenges by Actor and BMU',
  [('market_barriers_0_3', YN), ('experienced_challenges_0_3', YN)]),
 ('Risk Management Method by Actor and BMU',
  [('risk_management_0_3', None)]),
 ('Innovation, Changes in Marketing Strategy and Adaptation by Actor and BMU',
  [('innovation_0_3', ['No']), ('market_changes_0_3', YN), ('adaptation_0_3', None)]),
 ('Regulation and Management-Plan Awareness by Actor and BMU',
  [('regulation_0_3', YN), ('management_plan_0_3', YN)]),
 ('Knowledge of Interested Organisations and Sources of Industry Information by Actor and BMU',
  [('persons_interest_0_3', ['Yes']), ('industry_updates_0_3', ['Networking'])]),
 ('Perception That the Mud Crab Market Is Well Structured by Actor and BMU',
  [('well_structured_0_3', LIK)]),
 ('Perception That Mud Crab Marketing Is Integrated With Other Fisheries by Actor and BMU',
  [('species_integrated_0_3', LIK)]),
 ('Awareness of a Policy Framework for Crab Markets by Actor and BMU',
  [('policy_framework_0_3', LIK)]),
 ('Priority Opportunity for Improving Mud Crab Marketing by Actor and BMU',
  [('opportunity_0_3', None)]),
 ('Recommended Market-System Enhancement by Actor and BMU',
  [('system_enhancement_0_3', None)]),
 ('Reported Involvement of Youth by Actor and BMU',
  [('youth_0_3', YOUTH)]),
 ('Perceived Potential for Product or Market Diversification by Actor and BMU',
  [('diversification_0_3', DIV)]),
]

T = []
for i, (title, specs) in enumerate(SPEC, start=2):   # Table 1 is the sample distribution
    T.append(table(i, title, specs))
json.dump(T, open('v5/tables_cat.json', 'w'), indent=1)
for t in T:
    print(f"T{t['num']:>2} | {len(t['rows']):>3} rows | {t['title'][:78]}")
print('\ntotal categorical tables:', len(T))
print('longest:', max(len(t['rows']) for t in T), 'rows')
