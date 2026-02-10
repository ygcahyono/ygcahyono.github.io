# This is All You Need to Know to Setup an Experimentation

*August 25, 2025 · Statistics and Probability*

## Understanding of A/B Testing

A/B Testing is probably one of the most important fundamental of data scientist knowledge. There are basic understanding that we need to have before we can launch the a/b testing. In this blogsplot, I will cover the experimental design to help having the right screw driver to design the experimentation

## (1) Experiment Design.

Experiment design is like all the planing material before we can run the experimentation. There are few steps inside it. The first one is (a) Hypothesis testing (b) Set-up the metrics (c) Choosing the randomisation unit strategy (d) control variables (e) sample size and duration.

### A. Hypothesis Testing.

We have two types of hypothesis testing, building statistical or business hypothesis.

1. Business Hypothesis we can easily define using rule of: If -> Then -> Because.

If a Product Manager about to start a discount experimentation, giving 10% discount to customers during non-peak hour. The hypothesis testing should be like this: "**If** we give 10% discount to customers **then** the completed rides will increased by 5% **because** price sensitive users will more likely to use our platform instead of others."

2. Statistical hypothesis testing version:

There are two types of statistical hypothesis, null hypothesis and alternate hypothesis.
- Null hypothesis is the status quo or current condition.
- Alternate Hypothesis is the new feature that we are trying to prove.

- H0: 10% discount during non-peak hours will not increase the completion rides.
- H1: 10% discount will increase the completion rate during non-peak hours, because price sensitive users will likely to use our platform more.

### B. Understanding the success metrics
Defining what kind of metrics that we want to see impacted because of the experimentation (Primary Metrics), what is the secondary metrics, and what is the guadrail metrics.

- Primary Metrics   : Rides Completion.
- Secondary Metrics : Number of login users, number of attempt orders.
- Guadrail metrics  : Number of cancellation orders, cancellation rate.

### C. Control Variable
Control variable is making sure that there is only one attributes that tested during experimentation and make sure other than that keeping the same. Eg. Experimentation about the colour button only changed the colour and keep the text font, size, and other the same.

### D.Randomisation Strategy
Randomisation strategy is really matters when it comes to the experimentation. Deciding which users that need to be included and excluded. There are some randomisation unit that usually commercial use:

1. Standard user randomisation      : Takes the coinflip for every sample on user level
2. Standard session randomisation   : Takes coinflip for every session randomly suitable for non-login users
3. Stratified randomisation         : For each different group, coinflip the sample randomly.

### E. Sample Size and Duration.
The **sample size** of the ab-testing probably not only technically complex but it require good understanding of business as well. At least four things that need to be considered (1) Statistical Significant (2) Power or Beta (c) Minimum Detectable Effect (MDE) (d) baseline of the success metrics

1. Statistical Significant          : The mathematical confident the change is real not only due to random chance. The number of Statistical Significant usually used inside the corporate setting is 0.05.
2. Power (1-beta)                   : The probability of catching the real effect. Where beta is the probability of failing rejecting the null hypothesis. Those two numbers beta and power comes together. Where beta usually 20% and the power 80% for the business standard.
3. Baseline of the success metrics  : Pre-experimentation key-metrics number
4. Minimum Detectable Effect (MDE)  : MDE usually decided by the project or product owner. It measure the relative improvement from the baseline.
    - Business Call         :It can be decided by for example the investment in the campaign is around $50k and better this product can have positive (+ROI).
    - Competitor benchmark  : Most of the experimentation could generate around 5-15% of additional relative conversion. The page re-design require higher investment and expecting higher return as well. Changing the button probably only affect 1-3% of additional relative conversion. In the past similar campaign could bring ~5pp MDE over the control group for example.
    - The practical recommendation would be expecting ~20% of increment.

**Duration** usually considers the full cycle of customers interaction to the platform. For customer based application usually we run at least a week to see the full week effect such as weekend and weekday, where usually customers behave differently.

Here are the remaining points of the experimentation cycle that left:
(F) Check the tracker of the metrics (G) Run The Experimentation -> (H) Analyse -> (I) Interpret and Deliver the Result.
