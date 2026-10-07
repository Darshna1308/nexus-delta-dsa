/* NEXUS DELTA — SAS mirror of the key analytical steps (Team DSA, Build for Bharat 2.0 Round 2)
   STATUS: translation of the Python/Colab pipeline for SAS Viya / SAS OnDemand for Academics.
   NOT executed in the authoring environment — treat as a template and re-run before quoting any SAS-side number.
   Numbers quoted in the Approach Note come from the executed Colab notebooks (01-06). */
libname nd "/home/&sysuserid/nexus_delta";   /* put the organiser files + exported out/analytics_clean.csv here */

proc import datafile="/home/&sysuserid/nexus_delta/JDS_Skill_Traits.xlsx" out=nd.jds dbms=xlsx replace; run;
proc import datafile="/home/&sysuserid/nexus_delta/out/analytics_clean.csv" out=nd.analytics dbms=csv replace; guessingrows=max; run;

/* 1. Internal evidence: Wilcoxon / Mann-Whitney U for each skill (high vs low hike) */
proc npar1way data=nd.jds wilcoxon;
  class salary_hike_high_or_low;
  var big_data_skills maths_stats_skills coding_skills ai_and_ml_skills dashboard_and_storytelling_skills;
  ods output WilcoxonTest=nd.wilcoxon_out;
run;
/* Cliff's delta = 2U/(n1*n2) - 1 ; Holm adjustment */
proc multtest inpvalues=nd.wilcoxon_out holm out=nd.holm_out; run;

/* 2. T1: L2-style (ridge-like) logistic on standardised skills + ROC */
proc stdize data=nd.jds out=nd.jds_z method=std; var big_data_skills--dashboard_and_storytelling_skills; run;
proc logistic data=nd.jds_z plots(only)=roc;
  model salary_hike_high_or_low(event='1') = big_data_skills maths_stats_skills coding_skills ai_and_ml_skills dashboard_and_storytelling_skills / ctable;
run;

/* 3. Market: cumulative-logit (ordinal) model of salary band; ODDS RATIOS = exp(beta) for higher band */
proc logistic data=nd.analytics(where=(is_ds_p=1));
  class seniority(ref='mid') loc_tier(ref='Tier1') role_family(ref='other') / param=ref;
  model salary_ord(order=internal) = big_data_p maths_stats_p coding_p ai_ml_p story_p exp_min seniority loc_tier role_family exp_span jobtype_missing trunc_skills / link=clogit;
  ods output OddsRatios=nd.market_or;
run;

/* 4. Career ladder: paired senior vs junior pay, Wilcoxon signed-rank (create wide table senior/junior per company first) */
/* proc univariate data=nd.ladder_wide; var diff; run;   -> signed-rank test in the Tests for Location output */
