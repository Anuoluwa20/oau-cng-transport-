# Statistical findings

Dataset: combined transport observation data used as supplied for the analytics and visualization exercise.

## Key findings

- The highest mean completed wait among stop-direction/time-block groups was 20.51 minutes at NEW MARKET -> ACADEMICS during AM (n=298; median 22.00).
- The largest average hourly queue was 48.90 people at BUS STOP -> CAMPUS GATE around 15:00 (n=30).
- The lowest completed-case boarding share within 10 minutes was 50.2% at NEW MARKET -> ACADEMICS (n=546).
- Queue size vs waiting time: p=<0.0001 (reject at 0.05; Spearman rho 0.679).
- CNG bus vs Keke completed waiting time: p=<0.0001 (reject at 0.05; rank-biserial correlation 0.264).
- Block vs boarded within 10 minutes: p=<0.0001 (reject at 0.05; Cramer's V 0.207).
- NEW MARKET morning vs rest-of-day wait: p=<0.0001 (reject at 0.05; rank-biserial correlation 0.501).
- HALL morning vs rest-of-day wait: p=<0.0001 (reject at 0.05; rank-biserial correlation 0.489).

## Q1. Where and when are the longest waiting times?

The table below ranks stop-direction/time-block groups by mean completed wait; the confidence intervals are bootstrap intervals from the computed summary table.

- NEW MARKET -> ACADEMICS, AM: n=298, mean=20.51 min, median=22.00 min, 90th percentile=34.00 min, mean 95% CI 19.19–21.77.
- BUS STOP -> CAMPUS GATE, PM: n=1318, mean=10.52 min, median=11.00 min, 90th percentile=17.00 min, mean 95% CI 10.22–10.79.
- CAMPUS GATE -> BUS STOP, AM: n=1037, mean=10.51 min, median=11.00 min, 90th percentile=19.00 min, mean 95% CI 10.15–10.90.
- NEW MARKET -> CAMPUS GATE, MD: n=405, mean=7.43 min, median=2.00 min, 90th percentile=22.00 min, mean 95% CI 6.62–8.30.
- SUB -> HALL, AM: n=75, mean=7.28 min, median=4.00 min, 90th percentile=18.60 min, mean 95% CI 5.67–9.12.

**Chart:** `S04_wait_by_stop_direction.png` and `S05_wait_by_block.png`.

## Q2. How likely is a passenger to board within 5, 10 and 15 minutes?

- BUS STOP -> ACADEMICS, within 5 min: 88.7% (n=441; 95% CI 85.4–91.3%; 391 completed waits within threshold).
- BUS STOP -> ACADEMICS, within 10 min: 97.7% (n=441; 95% CI 95.9–98.8%; 431 completed waits within threshold).
- BUS STOP -> ACADEMICS, within 15 min: 98.9% (n=441; 95% CI 97.4–99.5%; 436 completed waits within threshold).
- BUS STOP -> CAMPUS GATE, within 5 min: 37.6% (n=2546; 95% CI 35.8–39.5%; 958 completed waits within threshold).
- BUS STOP -> CAMPUS GATE, within 10 min: 63.1% (n=2546; 95% CI 61.2–64.9%; 1606 completed waits within threshold).
- BUS STOP -> CAMPUS GATE, within 15 min: 87.7% (n=2546; 95% CI 86.4–89.0%; 2234 completed waits within threshold).
- CAMPUS GATE -> ACADEMICS, within 5 min: 83.6% (n=269; 95% CI 78.8–87.6%; 225 completed waits within threshold).
- CAMPUS GATE -> ACADEMICS, within 10 min: 98.1% (n=269; 95% CI 95.7–99.2%; 264 completed waits within threshold).
- CAMPUS GATE -> ACADEMICS, within 15 min: 99.3% (n=269; 95% CI 97.3–99.8%; 267 completed waits within threshold).
- CAMPUS GATE -> BUS STOP, within 5 min: 60.4% (n=2084; 95% CI 58.2–62.4%; 1258 completed waits within threshold).
- CAMPUS GATE -> BUS STOP, within 10 min: 74.9% (n=2084; 95% CI 72.9–76.7%; 1560 completed waits within threshold).
- CAMPUS GATE -> BUS STOP, within 15 min: 88.5% (n=2084; 95% CI 87.1–89.8%; 1845 completed waits within threshold).
- CAMPUS GATE -> HALL, within 5 min: 93.7% (n=605; 95% CI 91.5–95.4%; 567 completed waits within threshold).
- CAMPUS GATE -> HALL, within 10 min: 97.5% (n=605; 95% CI 95.9–98.5%; 590 completed waits within threshold).
- CAMPUS GATE -> HALL, within 15 min: 99.5% (n=605; 95% CI 98.6–99.8%; 602 completed waits within threshold).
- CAMPUS GATE -> NEW MARKET, within 5 min: 65.0% (n=591; 95% CI 61.0–68.7%; 384 completed waits within threshold).
- CAMPUS GATE -> NEW MARKET, within 10 min: 83.4% (n=591; 95% CI 80.2–86.2%; 493 completed waits within threshold).
- CAMPUS GATE -> NEW MARKET, within 15 min: 93.6% (n=591; 95% CI 91.3–95.3%; 553 completed waits within threshold).
- HALL -> CAMPUS GATE, within 5 min: 90.2% (n=571; 95% CI 87.5–92.4%; 515 completed waits within threshold).
- HALL -> CAMPUS GATE, within 10 min: 96.7% (n=571; 95% CI 94.9–97.9%; 552 completed waits within threshold).
- HALL -> CAMPUS GATE, within 15 min: 98.4% (n=571; 95% CI 97.0–99.2%; 562 completed waits within threshold).
- NEW MARKET -> ACADEMICS, within 5 min: 37.5% (n=546; 95% CI 33.6–41.7%; 205 completed waits within threshold).
- NEW MARKET -> ACADEMICS, within 10 min: 50.2% (n=546; 95% CI 46.0–54.4%; 274 completed waits within threshold).
- NEW MARKET -> ACADEMICS, within 15 min: 61.7% (n=546; 95% CI 57.6–65.7%; 337 completed waits within threshold).
- NEW MARKET -> CAMPUS GATE, within 5 min: 64.2% (n=908; 95% CI 61.0–67.3%; 583 completed waits within threshold).
- NEW MARKET -> CAMPUS GATE, within 10 min: 75.1% (n=908; 95% CI 72.2–77.8%; 682 completed waits within threshold).
- NEW MARKET -> CAMPUS GATE, within 15 min: 82.5% (n=908; 95% CI 79.9–84.8%; 749 completed waits within threshold).
- SUB -> HALL, within 5 min: 67.5% (n=520; 95% CI 63.4–71.4%; 351 completed waits within threshold).
- SUB -> HALL, within 10 min: 86.0% (n=520; 95% CI 82.7–88.7%; 447 completed waits within threshold).
- SUB -> HALL, within 15 min: 94.4% (n=520; 95% CI 92.1–96.1%; 491 completed waits within threshold).
- SUB -> NEW MARKET, within 5 min: 67.8% (n=609; 95% CI 64.0–71.4%; 413 completed waits within threshold).
- SUB -> NEW MARKET, within 10 min: 86.7% (n=609; 95% CI 83.8–89.2%; 528 completed waits within threshold).
- SUB -> NEW MARKET, within 15 min: 96.9% (n=609; 95% CI 95.2–98.0%; 590 completed waits within threshold).

**Method:** completed-case proportions with Wilson confidence intervals.
**Chart:** `S07_boarding_probability.png`.

## Q3. When are the peak queue periods at each stop-direction, and how big are they?

- BUS STOP -> CAMPUS GATE: 15:00, mean queue 48.90 people (n=30 snapshots; maximum snapshot 102 people).
- SUB -> CAMPUS GATE: 16:00, mean queue 44.33 people (n=6 snapshots; maximum snapshot 60 people).
- CAMPUS GATE -> BUS STOP: 10:00, mean queue 31.21 people (n=42 snapshots; maximum snapshot 60 people).
- NEW MARKET -> CAMPUS GATE: 18:00, mean queue 30.00 people (n=7 snapshots; maximum snapshot 60 people).
- NEW MARKET -> ACADEMICS: 09:00, mean queue 20.67 people (n=42 snapshots; maximum snapshot 40 people).
- SUB -> NEW MARKET: 18:00, mean queue 3.71 people (n=7 snapshots; maximum snapshot 9 people).
- SUB -> HALL: 17:00, mean queue 3.19 people (n=42 snapshots; maximum snapshot 19 people).
- CAMPUS GATE -> NEW MARKET: 09:00, mean queue 2.69 people (n=42 snapshots; maximum snapshot 10 people).
- HALL -> CAMPUS GATE: 08:00, mean queue 2.52 people (n=42 snapshots; maximum snapshot 15 people).
- CAMPUS GATE -> HALL: 08:00, mean queue 1.43 people (n=42 snapshots; maximum snapshot 7 people).
- BUS STOP -> ACADEMICS: 10:00, mean queue 1.36 people (n=42 snapshots; maximum snapshot 10 people).
- CAMPUS GATE -> ACADEMICS: 18:00, mean queue 0.57 people (n=7 snapshots; maximum snapshot 2 people).

**Method:** maximum mean queue from the computed stop-direction/hour table.
**Chart:** `01_queue_by_hour.png` and `02_queue_heatmap.png`.

## Q4. Is the Campus Gate to Bus Stop morning queue comparable to the Bus Stop to Campus Gate evening queue?

- **CAMPUS GATE -> BUS STOP, 08:00-10:30 vs BUS STOP -> CAMPUS GATE, 15:00-18:00:** **Method:** Mann–Whitney U. **Groups and descriptive statistics:** CAMPUS GATE -> BUS STOP, 08:00-10:30: n=112, mean=29.00, median=28.00, mean 95% CI 25.20–33.13; BUS STOP -> CAMPUS GATE, 15:00-18:00: n=117, mean=40.73, median=36.00, mean 95% CI 35.72–45.66. **Test:** statistic=5,158.500, p=0.0054, rank-biserial correlation=-0.213; effect 95% CI -0.360–-0.066. **Decision:** reject at 0.05.
- **Answer:** The evening median queue was 36.00 versus 28.00 in the morning. The Mann–Whitney result indicates a distribution difference, but it does not establish equivalence; the groups should not be called comparable based on this test alone.

**Chart:** `S10_gate_morning_vs_bus_stop_evening.png`.

## Q5. Do waiting times at New Market and Hall increase in the morning compared with the rest of the day?

- **NEW MARKET, 08:00–10:30 vs NEW MARKET, rest of day:** **Method:** Mann–Whitney U. **Groups and descriptive statistics:** NEW MARKET, 08:00-10:30: n=385, mean=16.10, median=15.00, mean 95% CI 14.84–17.32; NEW MARKET, rest of day: n=1069, mean=6.18, median=2.00, mean 95% CI 5.71–6.66. **Test:** statistic=308,786.500, p=<0.0001, rank-biserial correlation=0.501; effect 95% CI 0.442–0.559. **Decision:** reject at 0.05.
- **HALL, 08:00–10:30 vs HALL, rest of day:** **Method:** Mann–Whitney U. **Groups and descriptive statistics:** HALL, 08:00-10:30: n=145, mean=4.52, median=2.00, mean 95% CI 3.66–5.48; HALL, rest of day: n=426, mean=0.59, median=0.00, mean 95% CI 0.46–0.71. **Test:** statistic=45,995.500, p=<0.0001, rank-biserial correlation=0.489; effect 95% CI 0.396–0.583. **Decision:** reject at 0.05.
- **Answer:** New Market morning median wait was higher than the rest of the day (statistically significant); Hall morning median wait was higher than the rest of the day (statistically significant).

**Chart:** `S15_new_market_morning_vs_rest_of_day.png` and `S16_hall_morning_vs_rest_of_day.png`.

## Q6. Do queues at New Market and Hall rise on Fridays between 13:00 and 14:30 compared with other weekdays?

- **Friday vs Other weekdays:** **Method:** Mann–Whitney U. **Groups and descriptive statistics:** Friday: n=20, mean=41.90, median=18.50, 95% CI not reported for n < 30; Other weekdays: n=80, mean=0.56, median=0.00, mean 95% CI 0.30–0.88. **Test:** statistic=1,467.000, p=<0.0001, rank-biserial correlation=0.834. **Decision:** reject at 0.05.
- **Friday vs Other weekdays:** **Method:** Mann–Whitney U. **Groups and descriptive statistics:** Friday: n=10, mean=1.20, median=0.00, 95% CI not reported for n < 30; Other weekdays: n=40, mean=0.00, median=0.00, mean 95% CI 0.00–0.00. **Test:** statistic=280.000, p=<0.0001, rank-biserial correlation=0.400. **Decision:** reject at 0.05.
- **Answer:** New Market Friday median queue was higher than other weekdays (statistically significant); Hall Friday median queue was the same as other weekdays (statistically significant).

**Chart:** `S11_friday_new_market.png` and `S12_friday_hall.png`.

## Q7. Is demand different on weekdays and weekends?

- **Weekday vs Weekend:** **Method:** Mann–Whitney U. **Groups and descriptive statistics:** Weekday hourly demand: n=603, mean=41.08, median=26.00, mean 95% CI 37.35–45.06; Weekend hourly demand: n=240, mean=20.85, median=13.00, mean 95% CI 17.99–23.94. **Test:** statistic=101,455.500, p=<0.0001, rank-biserial correlation=0.402; effect 95% CI 0.324–0.480. **Decision:** reject at 0.05.
- **Answer:** Mean hourly arrivals were higher on weekdays than weekends; the distribution comparison was significantly different.

**Chart:** `S13_weekday_vs_weekend.png`.

## Q8. Is there a difference in waiting time between CNG buses and keke?

- **CNG bus vs Keke:** **Method:** Mann–Whitney U. **Groups and descriptive statistics:** CNG bus: n=4967, mean=6.93, median=6.00, mean 95% CI 6.75–7.11; Keke: n=4723, mean=4.65, median=1.00, mean 95% CI 4.45–4.86. **Test:** statistic=14,825,006.500, p=<0.0001, rank-biserial correlation=0.264; effect 95% CI 0.242–0.286. **Decision:** reject at 0.05.
- **Answer:** CNG bus median wait was higher than Keke; the test was significant.

**Chart:** `S14_cng_bus_vs_keke.png`.

## Q9. Is the share of passengers who board within 10 minutes related to the time block?

- **AM/MD/PM vs Yes/No:** **Method:** Chi-square. **Groups and descriptive statistics:** Block AM: share within 10 min=0.650, n=2697 (95% Wilson CI 0.632–0.668); Block MD: share within 10 min=0.872, n=3363 (95% Wilson CI 0.860–0.882); Block PM: share within 10 min=0.756, n=3630 (95% Wilson CI 0.741–0.769). **Test:** statistic=414.255, p=<0.0001, Cramer's V=0.207. **Decision:** reject at 0.05.
- **Answer:** The share boarding within 10 minutes varies by time block in the chi-square test.

**Chart:** `S07_boarding_probability.png`.

## Q10. Is queue size related to waiting time, and is hour of day related to queue size?

- **Queue size vs waiting time:** **Method:** Spearman. **Groups and descriptive statistics:** Group means/medians are not applicable to this test.. **Test:** statistic=0.679, p=<0.0001, Spearman rho=0.679; effect 95% CI 0.668–0.689. **Decision:** reject at 0.05.
- **Hour of day vs queue size:** **Method:** Spearman. **Groups and descriptive statistics:** Group means/medians are not applicable to this test.. **Test:** statistic=-0.091, p=<0.0001, Spearman rho=-0.091; effect 95% CI -0.119–-0.062. **Decision:** reject at 0.05.
- **Answer:** Spearman associations were Queue size vs waiting time rho=0.679; Hour of day vs queue size rho=-0.091.

**Chart:** `S17_spearman_correlation.png` and `S18_queue_vs_wait_regression.png`.

## Q11. How efficient is the service?

- BUS STOP -> CAMPUS GATE: n=935 vehicle records; load factor=82.27%; left-behind rate=70.96%; mean headway=5.21 min; mean demand/capacity=1.005; over-capacity hours=4.
- CAMPUS GATE -> BUS STOP: n=1,331 vehicle records; load factor=59.19%; left-behind rate=56.87%; mean headway=3.47 min; mean demand/capacity=0.596; over-capacity hours=0.
- NEW MARKET -> ACADEMICS: n=588 vehicle records; load factor=56.60%; left-behind rate=63.80%; mean headway=7.09 min; mean demand/capacity=0.549; over-capacity hours=2.
- SUB -> NEW MARKET: n=550 vehicle records; load factor=41.80%; left-behind rate=15.18%; mean headway=8.19 min; mean demand/capacity=0.518; over-capacity hours=1.
- CAMPUS GATE -> NEW MARKET: n=558 vehicle records; load factor=51.29%; left-behind rate=18.20%; mean headway=7.72 min; mean demand/capacity=0.513; over-capacity hours=0.
- NEW MARKET -> CAMPUS GATE: n=835 vehicle records; load factor=41.85%; left-behind rate=64.01%; mean headway=5.32 min; mean demand/capacity=0.434; over-capacity hours=0.
- BUS STOP -> ACADEMICS: n=691 vehicle records; load factor=38.44%; left-behind rate=4.73%; mean headway=6.08 min; mean demand/capacity=0.387; over-capacity hours=0.
- SUB -> HALL: n=510 vehicle records; load factor=39.41%; left-behind rate=15.47%; mean headway=8.45 min; mean demand/capacity=0.372; over-capacity hours=0.
- HALL -> CAMPUS GATE: n=1,100 vehicle records; load factor=20.93%; left-behind rate=6.19%; mean headway=4.06 min; mean demand/capacity=0.282; over-capacity hours=0.
- CAMPUS GATE -> ACADEMICS: n=587 vehicle records; load factor=27.46%; left-behind rate=0.74%; mean headway=7.09 min; mean demand/capacity=0.272; over-capacity hours=0.
- CAMPUS GATE -> HALL: n=1,083 vehicle records; load factor=22.89%; left-behind rate=2.51%; mean headway=4.25 min; mean demand/capacity=0.271; over-capacity hours=0.
- BUS STOP -> Unknown destination: n=7 vehicle records; load factor=96.70%; left-behind rate=48.54%; mean headway=3.29 min; mean demand/capacity=not computed; over-capacity hours=0.
- CAMPUS GATE -> CAMPUS GATE: n=6 vehicle records; load factor=29.49%; left-behind rate=0.00%; mean headway=11.40 min; mean demand/capacity=not computed; over-capacity hours=0.
- HALL -> HALL: n=1 vehicle records; load factor=76.92%; left-behind rate=0.00%; mean headway=not computed min; mean demand/capacity=not computed; over-capacity hours=0.
- NEW MARKET -> BUS STOP: n=1 vehicle records; load factor=38.46%; left-behind rate=0.00%; mean headway=not computed min; mean demand/capacity=not computed; over-capacity hours=0.
- **Over capacity:** BUS STOP -> CAMPUS GATE, NEW MARKET -> ACADEMICS, SUB -> NEW MARKET
- Fleet availability: not computed because the fleet table has no records.

**Charts:** `06_headway_by_hour.png`, `07_load_factor_by_stop_direction.png`, `09_demand_capacity_heatmap.png`, and `10_fleet_availability.png`.

## Q12. How do students' survey answers compare with the observed waiting times?

- BUS STOP: reported mean=15.50 min (survey n=2); observed mean=7.18 min (observed n=2,987). Confidence intervals and a significance test are not available in the computed comparison table.
- CAMPUS GATE: reported mean=11.87 min (survey n=19); observed mean=4.55 min (observed n=3,549). Confidence intervals and a significance test are not available in the computed comparison table.
- HALL: reported mean=11.75 min (survey n=4); observed mean=1.59 min (observed n=571). Confidence intervals and a significance test are not available in the computed comparison table.
- NEW MARKET: reported mean=9.95 min (survey n=10); observed mean=8.81 min (observed n=1,454). Confidence intervals and a significance test are not available in the computed comparison table.
- OTHER: reported mean=16.17 min (survey n=3); observed mean=not computed min (observed n=not computed). Confidence intervals and a significance test are not available in the computed comparison table.
- ROAD 7: reported mean=23.00 min (survey n=2); observed mean=not computed min (observed n=not computed). Confidence intervals and a significance test are not available in the computed comparison table.
- SUB: reported mean=15.78 min (survey n=9); observed mean=4.47 min (observed n=1,129). Confidence intervals and a significance test are not available in the computed comparison table.
- **Answer:** Reported mean waits were higher than observed means at 5 of 5 stops with both summaries; survey sample sizes are small and the comparison is descriptive.

**Chart:** `S19_survey_vs_observed_wait.png`.

## Q13. Can waiting time be predicted better than a simple baseline?

Model MAE=2.00 min on n=1 validation records; the median-by-stop-direction-and-block baseline was not computable. No validation rows match a training stop-direction/block baseline. It cannot be determined whether the model beats the baseline.

**Charts:** `S20_prediction_vs_observed.png`, `S21_prediction_residuals.png`, and `S22_prediction_residuals_by_hour.png`.

## Limitations

- Small samples with n < 30 are marked in the relevant charts; confidence intervals are omitted for those groups.
- Unfinished waits have no recorded elapsed censor duration, so Kaplan–Meier curves cannot be estimated.
- Mann–Whitney U tests compare distributions and do not establish equivalence; observations may not be independent.
- Confidence intervals for wait summaries are bootstrap intervals; boarding-probability intervals are Wilson intervals.
- Spearman intervals, where shown, use the Fisher z approximation; chi-square effect-size intervals were not computed.
- Survey-reported waiting-time intervals are compared descriptively with observed waits; the samples are independent and reported intervals may omit open-ended categories.
- Demand-to-capacity calculations depend on matching demand and recorded vehicle capacity by date, route, and hour; missing values are not imputed.
- The supplied fleet table has no availability records; prediction validation has very few complete rows and no matching training route/block for the median baseline.
