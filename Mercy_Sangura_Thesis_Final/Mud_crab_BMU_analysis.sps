* ==========================================================================.
* MUD CRAB MARKET STRUCTURE, SOUTH COAST OF KENYA.
* Objective-wise analysis by Beach Management Unit (BMU).
* Reproduces every table and figure reported in Chapter Four.
*.
* HOW TO RUN.
*   1) Open this file in IBM SPSS Statistics, File > Open > Syntax.
*   2) Edit the FILE= path on the GET command below so that it points at
*      your own copy of Mud_crab_BMU_final_corrected.sav.
*   3) Choose Run > All, then save the Viewer output as
*      Appendix_A_SPSS_output.spv.
*.
* HOW THE ANALYSIS IS SET UP.
* - Every CROSSTABS command is run BY actor, so each output table
*   carries all four actor categories: fishers, middlemen, hoteliers and
*   exporters.
* - Fishers and middlemen are tested against BMU separately, because a
*   harvester and a trader do different work and pooling them would
*   confuse site with role.
* - Hoteliers and exporters are described but not tested against BMU:
*   four of the five hoteliers and all four exporters operated outside
*   the four BMU frames, so no site comparison is possible for them.
* - The Other sites group (bmu = 5) is excluded from every BMU test.
* - Msambweni (bmu = 4) has no middleman, so middleman BMU tests use the
*   three sites where traders were sampled.
* - Monte Carlo chi-square with 10,000 resamples is used throughout,
*   because many of these tables are sparse and the asymptotic
*   chi-square approximation would not hold.
* - Every chart plots percentages, never raw counts, so that groups of
*   different size can be read side by side.
* - Respondent R051 carries the corrected medium-crab price of KSh 650
*   per kilogram in this dataset.
* ==========================================================================.

GET FILE='C:\MudCrab\Mud_crab_BMU_final_corrected.sav'.
DATASET NAME crab WINDOW=FRONT.
DATASET ACTIVATE crab.

* If the file is already open in SPSS, comment out the three lines above
* and run this one instead, with the dataset window in front:
* DATASET NAME crab WINDOW=FRONT.

* --------------------------------------------------------------------------.
* SECTION 0 - SAMPLE DESCRIPTION (Table 2, Figure 5).
* --------------------------------------------------------------------------.

* Table 1 is the methods table in section 3.9; it is not an SPSS output.

* Table 2: distribution of respondents by actor category and BMU.
CROSSTABS
  /TABLES=actor BY bmu
  /FORMAT=AVALUE TABLES
  /CELLS=COUNT ROW
  /COUNT ROUND CELL.

FREQUENCIES VARIABLES=actor bmu landing_site
  /ORDER=ANALYSIS.

* Figure 5: composition of the sample by actor category within each BMU.
DATASET DECLARE figdat.
AGGREGATE /OUTFILE=figdat /BREAK=bmu actor /n=N.
DATASET ACTIVATE figdat.
AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /BREAK=bmu /ntot=SUM(n).
COMPUTE pct = 100 * n / ntot.
VARIABLE LABELS pct 'Percentage of respondents within BMU'.
FORMATS pct (F5.1).
EXECUTE.
GRAPH
  /BAR(STACK)=MEAN(pct) BY bmu BY actor
  /TITLE='Composition of the sample by actor category within each BMU'.
DATASET ACTIVATE crab.
DATASET CLOSE figdat.

* --------------------------------------------------------------------------.
* SECTION 1 - OBJECTIVE ONE: PROFILE OF THE ACTORS AND THEIR.
* CHARACTERISTICS (Tables 3 to 16).
* --------------------------------------------------------------------------.

* Table 3: age Group of Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=age_group_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 4: gender of Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=gender_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 5: highest Education Attained by Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=education_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 6: ethnic Group of Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=ethnicity_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 7: marital Status of Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=marital_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 8: years of Experience of Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=experience_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 9: primary Role and Business Ownership of Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=primary_role_0_1 own_manage_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 10: scale of Operation of Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=scale_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 11: monthly Mud Crab Income Band of Fishers, Middlemen, Hoteliers and Exporters by BMU.
CROSSTABS
  /TABLES=income_band_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 13: other Income Activities, Operating Licence and Loan Use by Actor and BMU.
CROSSTABS
  /TABLES=other_activity_0_1 licence_0_1 loans_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 14: main Source of Business Credit by Actor and BMU.
CROSSTABS
  /TABLES=loan_source_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 15: knowledge Acquisition and Formal Training by Actor and BMU.
CROSSTABS
  /TABLES=knowledge_source_0_1 training_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 16: cooperative Membership, Self-Help Group Participation and Primary Market Supplied by Actor and BMU.
CROSSTABS
  /TABLES=cooperative_0_1 self_help_0_1 market_supply_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Objective 1 tested against BMU - FISHERS only, four BMUs.
TEMPORARY.
SELECT IF (actor = 1 AND bmu <= 4).
CROSSTABS
  /TABLES=age_group_0_1 gender_0_1 education_0_1 ethnicity_0_1
          marital_0_1 experience_0_1 primary_role_0_1 own_manage_0_1
          scale_0_1 income_band_0_1 other_activity_0_1 licence_0_1
          loans_0_1 loan_source_0_1 knowledge_source_0_1 training_0_1
          cooperative_0_1 self_help_0_1 market_supply_0_1
          BY bmu
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Objective 1 tested against BMU - MIDDLEMEN only, three BMUs.
TEMPORARY.
SELECT IF (actor = 2 AND bmu <= 3).
CROSSTABS
  /TABLES=age_group_0_1 gender_0_1 education_0_1 ethnicity_0_1
          marital_0_1 experience_0_1 primary_role_0_1 own_manage_0_1
          scale_0_1 income_band_0_1 other_activity_0_1 licence_0_1
          loans_0_1 loan_source_0_1 knowledge_source_0_1 training_0_1
          cooperative_0_1 self_help_0_1 market_supply_0_1
          BY bmu
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Hoteliers and exporters: description only, no BMU test is possible.
TEMPORARY.
SELECT IF (actor >= 3).
CROSSTABS
  /TABLES=age_group_0_1 gender_0_1 education_0_1 ethnicity_0_1
          marital_0_1 experience_0_1 primary_role_0_1 own_manage_0_1
          scale_0_1 income_band_0_1 other_activity_0_1 licence_0_1
          loans_0_1 loan_source_0_1 knowledge_source_0_1 training_0_1
          cooperative_0_1 self_help_0_1 market_supply_0_1
          BY actor
  /FORMAT=AVALUE TABLES
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL.

* --------------------------------------------------------------------------.
* SECTION 2 - OBJECTIVE TWO: FUNCTIONS PERFORMED AT EACH MARKET NODE.
* (Tables 17 to 44).
* --------------------------------------------------------------------------.

* Table 17: how Mud Crabs Are Acquired and Source of Crabs for Sale by Actor and BMU.
CROSSTABS
  /TABLES=acquisition_0_2 source_trade_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 18: fishing or Collection Gear Used by Actor and BMU.
CROSSTABS
  /TABLES=gear_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 19: daily Mud Crab Catch Reported by Actor and BMU.
CROSSTABS
  /TABLES=catch_daily_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 20: proportion of Catch Sold and Travel Time from Fishing Grounds to Market by Actor and BMU.
CROSSTABS
  /TABLES=proportion_sold_0_2 time_market_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 21: main Buyer Category by Actor and BMU.
CROSSTABS
  /TABLES=buyer_category_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 22: primary Market Channel and Contact With Final Consumers by Actor and BMU.
CROSSTABS
  /TABLES=market_channel_0_2 consumer_contact_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 23: number of Buyers, State of Crabs Sold and Regularity of the Main Buyer by Actor and BMU.
CROSSTABS
  /TABLES=buyer_count_0_2 product_state_0_2 buyer_regular_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 24: location of Sale and Knowledge of the Onward Sale by Actor and BMU.
CROSSTABS
  /TABLES=location_sale_0_2 sell_to_next_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 25: first Buyer Location Reported by Fishers by BMU.
CROSSTABS
  /TABLES=buyer1_location_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 26: second Buyer Location Reported by Fishers by BMU.
CROSSTABS
  /TABLES=buyer2_location_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 27: preparation of Mud Crabs for Market and Preservation by Actor and BMU.
CROSSTABS
  /TABLES=preparation_0_2 preserve_process_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 28: packaging Used for Transporting Mud Crabs by Actor and BMU.
CROSSTABS
  /TABLES=packaging_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 29: mode of Transporting Mud Crabs to Market by Actor and BMU.
CROSSTABS
  /TABLES=transport_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 30: grading Practice and Criteria Used to Determine Grade by Actor and BMU.
CROSSTABS
  /TABLES=grading_0_2 grade_basis_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 31: quality Measures Before Market and Use of Formal Quality Control by Actor and BMU.
CROSSTABS
  /TABLES=quality_before_0_2 quality_control_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 32: size Label and Grade Assignment for Large Crabs by Actor and BMU.
CROSSTABS
  /TABLES=size_large_0_2 grade_large_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 33: size Label and Grade Assignment for Medium Crabs by Actor and BMU.
CROSSTABS
  /TABLES=size_medium_0_2 grade_medium_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 34: size Label and Grade Assignment for Small Crabs by Actor and BMU.
CROSSTABS
  /TABLES=size_small_0_2 grade_small_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 35: reported Daily Mortality by Actor and BMU.
CROSSTABS
  /TABLES=mortality_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 36: reported Loss Through Spoilage by Actor and BMU.
CROSSTABS
  /TABLES=spoilage_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 37: mode of Payment by Actor and BMU.
CROSSTABS
  /TABLES=payment_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 38: pricing Mechanism and How Prices Are Set by Actor and BMU.
CROSSTABS
  /TABLES=price_standard_0_2 price_setting_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 39: factors Influencing Price Fluctuations by Actor and BMU.
CROSSTABS
  /TABLES=price_factors_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 40: tied Depot Owners and Arrangements With Tied Fishers and Traders by Actor and BMU.
CROSSTABS
  /TABLES=depot_tied_0_2 fisher_arrangement_0_2 trader_arrangement_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 41: arrangements Used With Tied Depot Owners by Actor and BMU.
CROSSTABS
  /TABLES=depot_arrangement_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 42: tied Fishers, Tied Traders and Trading Agreements by Actor and BMU.
CROSSTABS
  /TABLES=fishers_tied_0_2 traders_tied_0_2 formal_agreement_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 43: role of Intermediaries and Negotiation Terms by Actor and BMU.
CROSSTABS
  /TABLES=intermediary_role_0_2 negotiation_terms_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 44: technology Adoption and Market Research by Actor and BMU.
CROSSTABS
  /TABLES=technology_0_2 market_research_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Objective 2 tested against BMU - FISHERS only, four BMUs.
TEMPORARY.
SELECT IF (actor = 1 AND bmu <= 4).
CROSSTABS
  /TABLES=acquisition_0_2 source_trade_0_2 gear_0_2 catch_daily_0_2
          proportion_sold_0_2 time_market_0_2 buyer_category_0_2
          market_channel_0_2 consumer_contact_0_2 buyer_count_0_2
          product_state_0_2 buyer_regular_0_2 location_sale_0_2
          sell_to_next_0_2 buyer1_location_0_2 buyer2_location_0_2
          preparation_0_2 preserve_process_0_2 packaging_0_2
          transport_0_2 grading_0_2 grade_basis_0_2 quality_before_0_2
          quality_control_0_2 size_large_0_2 grade_large_0_2
          size_medium_0_2 grade_medium_0_2 size_small_0_2
          grade_small_0_2 mortality_0_2 spoilage_0_2 payment_0_2
          price_standard_0_2 price_setting_0_2 price_factors_0_2
          depot_tied_0_2 fisher_arrangement_0_2 trader_arrangement_0_2
          depot_arrangement_0_2 fishers_tied_0_2 traders_tied_0_2
          formal_agreement_0_2 intermediary_role_0_2
          negotiation_terms_0_2 technology_0_2 market_research_0_2
          BY bmu
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Objective 2 tested against BMU - MIDDLEMEN only, three BMUs.
TEMPORARY.
SELECT IF (actor = 2 AND bmu <= 3).
CROSSTABS
  /TABLES=acquisition_0_2 source_trade_0_2 gear_0_2 catch_daily_0_2
          proportion_sold_0_2 time_market_0_2 buyer_category_0_2
          market_channel_0_2 consumer_contact_0_2 buyer_count_0_2
          product_state_0_2 buyer_regular_0_2 location_sale_0_2
          sell_to_next_0_2 buyer1_location_0_2 buyer2_location_0_2
          preparation_0_2 preserve_process_0_2 packaging_0_2
          transport_0_2 grading_0_2 grade_basis_0_2 quality_before_0_2
          quality_control_0_2 size_large_0_2 grade_large_0_2
          size_medium_0_2 grade_medium_0_2 size_small_0_2
          grade_small_0_2 mortality_0_2 spoilage_0_2 payment_0_2
          price_standard_0_2 price_setting_0_2 price_factors_0_2
          depot_tied_0_2 fisher_arrangement_0_2 trader_arrangement_0_2
          depot_arrangement_0_2 fishers_tied_0_2 traders_tied_0_2
          formal_agreement_0_2 intermediary_role_0_2
          negotiation_terms_0_2 technology_0_2 market_research_0_2
          BY bmu
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Hoteliers and exporters: description only, no BMU test is possible.
TEMPORARY.
SELECT IF (actor >= 3).
CROSSTABS
  /TABLES=acquisition_0_2 source_trade_0_2 gear_0_2 catch_daily_0_2
          proportion_sold_0_2 time_market_0_2 buyer_category_0_2
          market_channel_0_2 consumer_contact_0_2 buyer_count_0_2
          product_state_0_2 buyer_regular_0_2 location_sale_0_2
          sell_to_next_0_2 buyer1_location_0_2 buyer2_location_0_2
          preparation_0_2 preserve_process_0_2 packaging_0_2
          transport_0_2 grading_0_2 grade_basis_0_2 quality_before_0_2
          quality_control_0_2 size_large_0_2 grade_large_0_2
          size_medium_0_2 grade_medium_0_2 size_small_0_2
          grade_small_0_2 mortality_0_2 spoilage_0_2 payment_0_2
          price_standard_0_2 price_setting_0_2 price_factors_0_2
          depot_tied_0_2 fisher_arrangement_0_2 trader_arrangement_0_2
          depot_arrangement_0_2 fishers_tied_0_2 traders_tied_0_2
          formal_agreement_0_2 intermediary_role_0_2
          negotiation_terms_0_2 technology_0_2 market_research_0_2
          BY actor
  /FORMAT=AVALUE TABLES
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL.

* --------------------------------------------------------------------------.
* SECTION 3 - OBJECTIVE THREE: CONSTRAINTS AND OPPORTUNITIES (Tables 50 to.
* 60).
* --------------------------------------------------------------------------.

* Table 50: main Operational or Marketing Constraint by Actor and BMU.
CROSSTABS
  /TABLES=main_constraint_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 51: main Infrastructure or Logistics Constraint and Need for Improvement by Actor and BMU.
CROSSTABS
  /TABLES=infrastructure_0_3 infra_improvement_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 52: barriers to Market Access and Operational Challenges by Actor and BMU.
CROSSTABS
  /TABLES=market_barriers_0_3 experienced_challenges_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 53: risk Management Method by Actor and BMU.
CROSSTABS
  /TABLES=risk_management_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 54: innovation, Changes in Marketing Strategy and Adaptation by Actor and BMU.
CROSSTABS
  /TABLES=innovation_0_3 market_changes_0_3 adaptation_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 55: regulation, Management-Plan Awareness and Sources of Industry Information by Actor and BMU.
CROSSTABS
  /TABLES=regulation_0_3 management_plan_0_3 persons_interest_0_3
          industry_updates_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 56: perception That the Mud Crab Market Is Well Structured by Actor and BMU.
CROSSTABS
  /TABLES=well_structured_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 57: perception That Mud Crab Marketing Is Integrated With Other Fisheries by Actor and BMU.
CROSSTABS
  /TABLES=species_integrated_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 58: awareness of a Policy Framework for Crab Markets by Actor and BMU.
CROSSTABS
  /TABLES=policy_framework_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 59: priority Opportunity and Recommended Market-System Enhancement by Actor and BMU.
CROSSTABS
  /TABLES=opportunity_0_3 system_enhancement_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Table 60: reported Youth Involvement and Perceived Diversification Potential by Actor and BMU.
CROSSTABS
  /TABLES=youth_0_3 diversification_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Objective 3 tested against BMU - FISHERS only, four BMUs.
TEMPORARY.
SELECT IF (actor = 1 AND bmu <= 4).
CROSSTABS
  /TABLES=main_constraint_0_3 infrastructure_0_3 infra_improvement_0_3
          market_barriers_0_3 experienced_challenges_0_3
          risk_management_0_3 innovation_0_3 market_changes_0_3
          adaptation_0_3 regulation_0_3 management_plan_0_3
          persons_interest_0_3 industry_updates_0_3 well_structured_0_3
          species_integrated_0_3 policy_framework_0_3 opportunity_0_3
          system_enhancement_0_3 youth_0_3 diversification_0_3
          BY bmu
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Objective 3 tested against BMU - MIDDLEMEN only, three BMUs.
TEMPORARY.
SELECT IF (actor = 2 AND bmu <= 3).
CROSSTABS
  /TABLES=main_constraint_0_3 infrastructure_0_3 infra_improvement_0_3
          market_barriers_0_3 experienced_challenges_0_3
          risk_management_0_3 innovation_0_3 market_changes_0_3
          adaptation_0_3 regulation_0_3 management_plan_0_3
          persons_interest_0_3 industry_updates_0_3 well_structured_0_3
          species_integrated_0_3 policy_framework_0_3 opportunity_0_3
          system_enhancement_0_3 youth_0_3 diversification_0_3
          BY bmu
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL
  /METHOD=MC CIN(99) SAMPLES(10000).

* Hoteliers and exporters: description only, no BMU test is possible.
TEMPORARY.
SELECT IF (actor >= 3).
CROSSTABS
  /TABLES=main_constraint_0_3 infrastructure_0_3 infra_improvement_0_3
          market_barriers_0_3 experienced_challenges_0_3
          risk_management_0_3 innovation_0_3 market_changes_0_3
          adaptation_0_3 regulation_0_3 management_plan_0_3
          persons_interest_0_3 industry_updates_0_3 well_structured_0_3
          species_integrated_0_3 policy_framework_0_3 opportunity_0_3
          system_enhancement_0_3 youth_0_3 diversification_0_3
          BY actor
  /FORMAT=AVALUE TABLES
  /CELLS=COUNT COLUMN
  /COUNT ROUND CELL.

* --------------------------------------------------------------------------.
* SECTION 4 - CONTINUOUS MEASURES (Tables 12 and 45).
* --------------------------------------------------------------------------.

* Table 12: reported monthly mud crab income and age of respondents.
EXAMINE VARIABLES=income_ksh_0_1 age_0_1 BY actor
  /PLOT NONE
  /STATISTICS DESCRIPTIVES
  /PERCENTILES(25,50,75) HAVERAGE
  /MISSING LISTWISE.

* Table 45: reported mud crab prices by actor category and size grade.
EXAMINE VARIABLES=price_large_0_2 price_medium_0_2 price_small_0_2 BY actor
  /PLOT NONE
  /STATISTICS DESCRIPTIVES
  /PERCENTILES(25,50,75) HAVERAGE
  /MISSING PAIRWISE.

* Table 48: mean price by actor category, BMU and size grade.
MEANS TABLES=price_large_0_2 price_medium_0_2 price_small_0_2 BY actor BY bmu
  /CELLS=MEAN COUNT STDDEV.

* --------------------------------------------------------------------------.
* SECTION 5 - KRUSKAL-WALLIS PRICE COMPARISONS (Table 46).
* --------------------------------------------------------------------------.

* Prices are ordinal and heavily tied, and the four actor groups are of
* very unequal size, so price is compared with the Kruskal-Wallis H test
* rather than one-way ANOVA.

* Price compared across the four actor categories.
NPAR TESTS
  /K-W=price_large_0_2 price_medium_0_2 price_small_0_2 BY actor(1 4)
  /MISSING ANALYSIS.

* Fisher price compared across the four BMUs.
TEMPORARY.
SELECT IF (actor = 1 AND bmu <= 4).
NPAR TESTS
  /K-W=price_large_0_2 price_medium_0_2 price_small_0_2 BY bmu(1 4)
  /MISSING ANALYSIS.

* Middleman price compared across the three BMUs where traders were sampled.
TEMPORARY.
SELECT IF (actor = 2 AND bmu <= 3).
NPAR TESTS
  /K-W=price_large_0_2 price_medium_0_2 BY bmu(1 3)
  /MISSING ANALYSIS.

* Small crabs are priced by fishers only, so no across-actor comparison
* is possible for Grade C; the row is left blank in Table 46.

* --------------------------------------------------------------------------.
* SECTION 6 - MARKETING MARGINS AND THE DISTRIBUTION OF VALUE (Tables 47.
* and 49, Figures 26 to 28).
* --------------------------------------------------------------------------.

* Mean price at each node. The margins in Table 47 are the differences
* between these means; they are GROSS margins, because the survey did not
* collect the handling, transport and mortality costs that a net margin
* would require.
MEANS TABLES=price_large_0_2 price_medium_0_2 BY actor
  /CELLS=MEAN COUNT STDDEV.

* Table 49: first-sale spread between fishers and middlemen within each BMU.
TEMPORARY.
SELECT IF (actor <= 2 AND bmu <= 4).
MEANS TABLES=price_large_0_2 price_medium_0_2 BY bmu BY actor
  /CELLS=MEAN COUNT.

* Figure 27: mean large-crab price by actor category and BMU.
GRAPH
  /BAR(GROUPED)=MEAN(price_large_0_2) BY bmu BY actor
  /TITLE='Mean large-crab price by actor category and BMU'.

* --------------------------------------------------------------------------.
* SECTION 7 - THE REMAINING CHAPTER FOUR FIGURES.
* --------------------------------------------------------------------------.

* Each figure below plots percentages within the grouping variable. The
* figures printed in the thesis were drawn to APA 7 from these same
* percentages, so the numbers match cell for cell.

* Figures plotted within actor category:
*   Figure 6: age Distribution Within Each Actor Category.
*   Figure 8: highest Education Attained Within Each Actor Category.
*   Figure 9: scale of Operation Within Each Actor Category.
*   Figure 10: monthly Mud Crab Income Band Within Each Actor Category.
*   Figure 11: licensing, Credit, Training and Collective Membership by Actor Category.
*   Figure 12: source of Crabs for Sale Within Each Actor Category.
*   Figure 16: main Buyer Category Within Each Actor Category.
*   Figure 17: preparation of Mud Crabs for Market by Actor Category.
*   Figure 18: packaging Used for Transporting Mud Crabs by Actor Category.
*   Figure 19: mode of Transporting Mud Crabs to Market by Actor Category.
*   Figure 20: criteria Used to Determine Crab Grade by Actor Category.
*   Figure 22: reported Daily Mortality by Actor Category.
*   Figure 23: mode of Payment by Actor Category.
*   Figure 24: how Mud Crab Prices Are Set, by Actor Category.
*   Figure 27: mean Large-Crab Price by Actor Category and BMU.
*   Figure 29: main Operational or Marketing Constraint by Actor Category.
*   Figure 31: main Infrastructure or Logistics Constraint by Actor Category.
*   Figure 33: perception That the Mud Crab Market Is Well Structured, by Actor Category.
*   Figure 34: priority Opportunity for Improving Mud Crab Marketing by Actor Category.
*   Figure 35: recommended Market-System Enhancement by Actor Category.
*   Figure 36: reported Involvement of Youth by Actor Category.
*   Figure 37: perceived Potential for Product or Market Diversification by Actor Category.
*
* Figures plotted within BMU:
*   Figure 5: composition of the Sample by Actor Category Within Each BMU.
*   Figure 7: age Distribution of Fishers Within Each BMU.
*   Figure 13: fishing or Collection Gear Used by Fishers Within Each BMU.
*   Figure 14: daily Mud Crab Catch Reported by Fishers Within Each BMU.
*   Figure 15: travel Time from Fishing Grounds to Market, Fishers by BMU.
*   Figure 21: large-Crab Size Label Reported by Fishers Within Each BMU.
*   Figure 28: fisher Price as a Percentage of the Middleman Price Within Each BMU.
*   Figure 30: main Constraint Reported by Middlemen Within Each BMU.
*   Figure 32: awareness of the Crab Fishery Management Plan Among Fishers, by BMU.

* Template for a figure plotted within actor category. Replace VARNAME
* with the variable named in the table that the figure accompanies.
DATASET DECLARE figdat.
AGGREGATE /OUTFILE=figdat /BREAK=actor age_group_0_1 /n=N.
DATASET ACTIVATE figdat.
AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /BREAK=actor /ntot=SUM(n).
COMPUTE pct = 100 * n / ntot.
VARIABLE LABELS pct 'Percentage within actor category'.
FORMATS pct (F5.1).
EXECUTE.
GRAPH
  /BAR(GROUPED)=MEAN(pct) BY actor BY age_group_0_1
  /TITLE='Age distribution within each actor category'.
DATASET ACTIVATE crab.
DATASET CLOSE figdat.

* Template for a figure plotted within BMU, fishers only.
DATASET DECLARE figdat.
USE ALL.
COMPUTE keep = (actor = 1 AND bmu <= 4).
EXECUTE.
FILTER BY keep.
AGGREGATE /OUTFILE=figdat /BREAK=bmu age_group_0_1 /n=N.
FILTER OFF.
DATASET ACTIVATE figdat.
AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /BREAK=bmu /ntot=SUM(n).
COMPUTE pct = 100 * n / ntot.
VARIABLE LABELS pct 'Percentage within BMU'.
FORMATS pct (F5.1).
EXECUTE.
GRAPH
  /BAR(GROUPED)=MEAN(pct) BY bmu BY age_group_0_1
  /TITLE='Age distribution of fishers within each BMU'.
DATASET ACTIVATE crab.
DATASET CLOSE figdat.

* --------------------------------------------------------------------------.
* SECTION 8 - INDEX: WHICH COMMAND PRODUCES WHICH THESIS TABLE.
* --------------------------------------------------------------------------.

* Table  2: actor BY bmu.
* Table  3: age_group_0_1.
* Table  4: gender_0_1.
* Table  5: education_0_1.
* Table  6: ethnicity_0_1.
* Table  7: marital_0_1.
* Table  8: experience_0_1.
* Table  9: primary_role_0_1, own_manage_0_1.
* Table 10: scale_0_1.
* Table 11: income_band_0_1.
* Table 12: EXAMINE income_ksh_0_1 age_0_1.
* Table 13: other_activity_0_1, licence_0_1, loans_0_1.
* Table 14: loan_source_0_1.
* Table 15: knowledge_source_0_1, training_0_1.
* Table 16: cooperative_0_1, self_help_0_1, market_supply_0_1.
* Table 17: acquisition_0_2, source_trade_0_2.
* Table 18: gear_0_2.
* Table 19: catch_daily_0_2.
* Table 20: proportion_sold_0_2, time_market_0_2.
* Table 21: buyer_category_0_2.
* Table 22: market_channel_0_2, consumer_contact_0_2.
* Table 23: buyer_count_0_2, product_state_0_2, buyer_regular_0_2.
* Table 24: location_sale_0_2, sell_to_next_0_2.
* Table 25: buyer1_location_0_2.
* Table 26: buyer2_location_0_2.
* Table 27: preparation_0_2, preserve_process_0_2.
* Table 28: packaging_0_2.
* Table 29: transport_0_2.
* Table 30: grading_0_2, grade_basis_0_2.
* Table 31: quality_before_0_2, quality_control_0_2.
* Table 32: size_large_0_2, grade_large_0_2.
* Table 33: size_medium_0_2, grade_medium_0_2.
* Table 34: size_small_0_2, grade_small_0_2.
* Table 35: mortality_0_2.
* Table 36: spoilage_0_2.
* Table 37: payment_0_2.
* Table 38: price_standard_0_2, price_setting_0_2.
* Table 39: price_factors_0_2.
* Table 40: depot_tied_0_2, fisher_arrangement_0_2,.
*   trader_arrangement_0_2.
* Table 41: depot_arrangement_0_2.
* Table 42: fishers_tied_0_2, traders_tied_0_2, formal_agreement_0_2.
* Table 43: intermediary_role_0_2, negotiation_terms_0_2.
* Table 44: technology_0_2, market_research_0_2.
* Table 45: EXAMINE price_large_0_2 price_medium_0_2 price_small_0_2.
* Table 46: NPAR TESTS /K-W.
* Table 47: MEANS price_* BY actor (gross margins).
* Table 48: MEANS price_* BY actor BY bmu.
* Table 49: MEANS price_* BY bmu BY actor.
* Table 50: main_constraint_0_3.
* Table 51: infrastructure_0_3, infra_improvement_0_3.
* Table 52: market_barriers_0_3, experienced_challenges_0_3.
* Table 53: risk_management_0_3.
* Table 54: innovation_0_3, market_changes_0_3, adaptation_0_3.
* Table 55: regulation_0_3, management_plan_0_3, persons_interest_0_3,.
*   industry_updates_0_3.
* Table 56: well_structured_0_3.
* Table 57: species_integrated_0_3.
* Table 58: policy_framework_0_3.
* Table 59: opportunity_0_3, system_enhancement_0_3.
* Table 60: youth_0_3, diversification_0_3.
* Table 61: the significant Monte Carlo chi-square results above.

* End of syntax.
