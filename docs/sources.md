# Sources for every number in the deck

| Number used | Source |
|---|---|
| No commercial CMM mitigation project in India; Moonidih pilot proved feasibility | Ember (2026), *Understanding India's coal mine methane landscape*, https://ember-energy.org/latest-insights/understanding-indias-coal-mine-methane-landscape/ |
| 810 kt CH4 reported for 2019 (BUR); >1.6 Mt by end of decade unabated; 68% of fugitive fossil methane from coal; $980 mn import savings; underground ≈3.5% of coal but ≈15% of methane; IEA 2,759 kt vs GMI 894 kt vs GEM 1,023.8 kt; $13.3 bn for ~31 bcm imported gas FY2023-24 | Ember (2026), same report |
| 2019 rules: Degree-III enterprises to prepare CMM reduction plans; net-zero commitments by end-2025 | Ember (2025), *Subnational coal mine methane mitigation*, https://ember-energy.org/latest-updates/subnational-coal-mine-methane-mitigation/ |
| Degree-III > 10 m3/t; 35% reduction by 2029 = 586 kt CH4 | Ember (2025), *Coal mine methane's critical moment in India*, https://ember-energy.org/latest-insights/coal-mine-methanes-critical-moment-in-india/ |
| 2.2 Mt CH4 from India's coal mines in 2025 (2.0 Mt in 2024) | IEA Global Methane Tracker 2026, reported by KNN India, https://knnindia.co.in/news/newsdetails/sectors/energy/indias-coal-mine-methane-emissions-hit-22-mn-tonnes-in-2025-among-top-global-emitters-iea-report |
| 5-15% explosive range; ≥30% (2 × UEL) good-practice minimum; national minimums 25-40%; air ingress can drop drainage gas below 30%; seam gas 80-95% CH4 | UNECE (2016), *Best Practice Guidance for Effective Methane Drainage and Use in Coal Mines*, 2nd ed., ECE/ENERGY/105 |
| India CMM/CBM Clearinghouse at CMPDI, 2008, US EPA support | Global Methane Initiative, https://globalmethane.org/challenge/cbm.html |
| 260 / 71 / 7 underground mines in Degree I / II / III (2015); degree thresholds | Sadavarte et al., arXiv:2107.10317, citing MoLE (2017) |
| SCCL seams described as Degree-I gassiness (Shanthikhani, KK mines) | SCCL expressions of interest, scclmines.com |
| MH-440D: 0-100 %vol, UART + 0.4-2.0 V, T90 < 30 s, 3 min warm-up | Winsen product page, https://www.winsen-sensor.com/sensors/combustible-sensor/mh440d.html |
| Explosive triangle on the routing chart | Coward & Jones, US Bureau of Mines Bulletin 503 (approximate vertices) |
| Judging criteria, themes, timeline | https://www.vishwakarma-awards.org/ |

## Our own calculations (reproducible)

| Number | Script |
|---|---|
| 432 Nm3/day, 24.8 tCO2e/day, 1,504 kWh/day for one borehole at 0.3 m3/min CH4 | `analysis/gas_calcs.py` (assumptions in file) |
| 14.4% flow under-read without density correction at 60% CH4 | `analysis/gas_calcs.py` |
| Bracket FoS 1.87 (rev A) and 3.87 (rev B) | `analysis/bracket_fea.py` |
| Leak model: 28.5% minimum with throttling, isolation at 331 s, 17.0% unmanaged | `analysis/leak_sim.py` |
| $612.5 per t CH4, $190/day per borehole, payback < 2 days on parts | `docs/research_figures.py` → `analysis/unit_economics.json` |
| ₹68,670 build, ₹21,660 per node | `electronics/bom.py` (pre-order estimates) |
