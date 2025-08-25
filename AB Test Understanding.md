---
layout: page
title: "Understanding of A/B Testing"
---

# Understanding of A/B Testing

AB Testing is probably one of the most important basic of data scientist knowledge. There are some concept that need to be known before we can initiate the experimentation. In this analysis I will share at least two areas of AB testing that need to be covered. 

The first one is about the experimentation design and the second one is about the business setup.

## (1) Experiment Design. 

Based on my understanding, experiment design is the planning before we can run the experimentation. There are few steps inside the experiment design. The first one is (a) Hypothesis testing (b) Understanding of success metrics (c) control variables (d) randomisation strategy (e) sample size and duration.

### A. Hypothesis Testing.
Hypothesis testing is setting up what is the null hypothesis and what is the alternate hypothesis. 
- Null hypothesis is the status quo.
- Alternate Hypothesis is the new feature that we are trying to prove.

Eg. We are planning to create an experiment to change the colour of the button from blue to right. 

- H0: The red colour has the same conversion rate as the blue button colour.
- H1: New red button colour has the different conversion than the old button.

### B. Understanding the success metrics
Defining what kind of metrics that we want to see impacted because of the experimentation (Primary Metrics), what is the secondary metrics, and what is the guadrail metrics.

- Primary Metrics: Conversion Rate
- Secondary Metrics: GMV, Number of Orders, etc.
- Guadrail metrics: The number of complaint, page load time, etc.

### C. Control Variable
Control variable is making sure that there is only one attributes that tested during experimentation and make sure other than that keeping the same. Eg. Experimentation about the colour button only changed the colour and keep the text font, size, and other the same.


### D.Randomisation Strategy
Randomisation strategy is really matters when it comes to the experimentation. Deciding which users that need to be included and excluded. There are two methods at least available: standard randomisation and stratified randomisation. Standard randomisation take the coinflip for every sample where stratified randomisation making sure it is divided into different group (for example: location) and then the randomisation for each of the group proportionally.

### E. Sample Size and Duration.
The sample size of the ab-testing probably not only technically complex but it require good understanding of business as well. At least four things that need to be considered (a) statistical significant (b) power (c) minimum detectable effect (mde) (d) baseline of the success metrics

- Baseline of the success metrics: what is the baseline of the original conversion in history.
- Statistical Significant: The mathematical confident the change is real not only due to random chance. The number of Statistical Significant usually used by business is 5%.
- Power (1-beta): The probability of catching the real effect. Where beta is the probability of failing rejecting the null hypothesis. Those two numbers beta and power comes together. Where beta usually 20% and the power 80% for the business standard.
- Minimum detectable Effect (MDE): MDE usually decided by the project or product owner. It measure the relative improvement from the baseline. 
    - It can be decided by for example the investment in the product is around 50k pound and better this product can give return around 50k a year.
    - Competitor benchmark: Most of the experimentation could generate around 5-15% of additional relative conversion. The page re-design require higher investment and expecting higher return as well. Changing the button probably only affect 1-3% of additional relative conversion.
    - The practical recommendation would be expecting ~20% of increment.


Here is the good experimentation design for an experimentation:

1. Hypothesis testing: H1: Changing button colour to green will enhance affect customers to purchase item faster. H0: Changing button colour to green does not have positive impact to the conversion or have same conversion as the previous button colour.
2. Primary metric: CTR, secondary metric: gmv, number of order, number of user converted.
3. Control variable: making sure the button attribute except colour will not changed 
4. The randomisation will make sure stratisfied based on the devide type
5. Sample size: 10.000 each of the group will running around 2 weeks 