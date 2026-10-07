/* NEXUS DELTA - SAS mirror of the key analytical steps (Team DSA, Build For Bharat 2.0)
   STATUS: translation of the Python pipeline for SAS Viya / SAS VFL /
   SAS OnDemand for Academics.
   Not executed in the authoring environment: re-run in SAS before quoting
   any SAS-side number.
   Numbers in the Approach Note come from the executed Python notebooks 01-08. */
options validvarname=v7;            /* 'maths-stats_skills' -> maths_stats_skills */
/* folder holding the organiser files and the exported out/analytics_clean.csv */
libname nd "/home/&sysuserid/nexus_delta";

proc import datafile="/home/&sysuserid/nexus_delta/JDS_Skill_Traits.xlsx"
            out=nd.jds dbms=xlsx replace; run;
proc import datafile="/home/&sysuserid/nexus_delta/out/analytics_clean.csv"
            out=nd.analytics_raw dbms=csv replace;
  guessingrows=max; run;

/* three flags are exported as the text True/False; capability flags are already 0/1 */
data nd.analytics;
  set nd.analytics_raw;
  array t{*} $ is_ds_p jobtype_missing trunc_skills;
  array n{*} is_ds_p_n jobtype_missing_n trunc_skills_n;
  do i = 1 to dim(t); n{i} = (strip(t{i}) = 'True'); end;
  drop i;
run;

/* 1. Internal evidence: Mann-Whitney U (Wilcoxon rank-sum) per skill, high vs low hike */
%let skills = big_data_skills maths_stats_skills coding_skills ai_and_ml_skills
              dashboard_and_storytelling_skills;
proc npar1way data=nd.jds wilcoxon;
  class salary_hike_high_or_low;
  var &skills;
  ods output WilcoxonTest=nd.wtest WilcoxonScores=nd.wscores;
run;
/* two-sided p-values -> Holm adjustment (multtest needs a variable named raw_p) */
data nd.pvals;
  set nd.wtest; where Name1 = 'P2_WIL';   /* normal approx., continuity-corrected */
  raw_p = nValue1; keep Variable raw_p;
run;
proc multtest inpvalues=nd.pvals holm out=nd.holm_out; run;
/* Cliff's delta = 2U/(n1*n0) - 1, with U = rank sum of the high group - n1(n1+1)/2 */
proc sort data=nd.wscores; by Variable; run;
data nd.cliffs;
  merge nd.wscores(where=(Class='1') rename=(N=n1 SumOfScores=S1))
        nd.wscores(where=(Class='0') keep=Variable Class N rename=(N=n0));
  by Variable;
  U = S1 - n1*(n1+1)/2;  cliffs_delta = 2*U/(n1*n0) - 1;
run;

/* 2. T1: logistic model on standardised skills + ROC */
proc stdize data=nd.jds out=nd.jds_z method=std; var &skills; run;
proc logistic data=nd.jds_z plots(only)=roc;
  model salary_hike_high_or_low(event='1') = &skills / ctable;
run;

/* 3. Market: cumulative-logit (proportional-odds) model of the 6 salary bands.
      DESCENDING models P(Y >= j), so exp(beta) > 1 means higher bands. The score test
      for the proportional-odds assumption is printed by default. */
proc logistic data=nd.analytics(where=(is_ds_p_n=1)) descending;
  class seniority(ref='mid') loc_tier(ref='Tier1') role_family(ref='other') / param=ref;
  model salary_ord = big_data_p maths_stats_p coding_p ai_ml_p story_p
                     exp_min exp_span jobtype_missing_n trunc_skills_n
                     seniority loc_tier role_family / link=clogit;
  ods output OddsRatios=nd.market_or;
run;

/* 4. Career ladder: paired senior vs junior median pay per company.
      Build nd.ladder_wide first; the Wilcoxon signed-rank test appears
      under Tests for Location. */
/* proc univariate data=nd.ladder_wide; var diff; run; */
