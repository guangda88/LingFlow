# Methodology

Our study adopts a mixed-methods approach, combining quantitative log analysis with qualitative case study analysis.

**3.1 Data Collection**
We collected a complete dump of LingFamily's internal communication logs from the lingmessage system. The raw corpus consisted of 699 JSON files. We implemented a cleaning pipeline that:
1.  Removed duplicate entries based on content MD5 hashing.
2.  Standardized timestamp formats.
3.  Filtered non-textual artifacts (e.g., binary logs).
The final clean dataset comprises **91 unique interaction logs**, spanning from March 20, 2026, to April 17, 2026.

**3.2 Quantitative Analysis**
We performed a lexical analysis on the cleaned corpus to estimate the distribution of operational states. We defined two keyword sets:
*   **Negative States** (accidents, bugs, failures): `['事故', '错误', '失败', 'fail', 'error', 'bug', 'fix']`
*   **Positive States** (completions, reports): `['完成', '成功', '报告', 'report', 'success', 'done']`
We calculated the frequency of these keywords per log entry to construct a "Community Vitality Index" (ratio of positive to negative mentions).

**3.3 Qualitative Case Study**
To understand the mechanism behind the high frequency of accidents, we selected two P0-level accident reports ("Pipeline Black Hole" and "v0.16 Audit Failure"). We performed close reading and extracted:
*   The **Failure Pattern**: What technical or procedural breakdown occurred?
*   The **Repair Mechanism**: How was the failure resolved?
*   The **Institutionalization**: Did the failure lead to a new rule or cultural norm (e.g., "Counterfactual Reasoning")?
