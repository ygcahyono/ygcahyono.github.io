1. What is XGBoost

XGBoost is the combination of the weak tree learners altogether where 
the model will learn sequentially 

XGBoost is the combination of weak sequential tree learner. Where the following tree will 
fix the previous mistakes. XGBoost is ensemble tree model same as Random Forest. But the key difference is that RF uses combination of strong tree learner where XGBoost is exactly the opposite.

In general, XGBoost perform better compared to Random Forest because each tree will focus to fix only the mistakes from the previous tree.

Some of the important hyperparameter

1. learning rate or eta
2. sub-sample: (0,1] percentage, the ratio of sampling instance. setting it to 0.5 means that XGBoost would randomly sample half of the training sample, reducing the risk of overfitting.
3. colsample_bytree (0,1] percentage, the sub-sample ratio of columns that used during the training phase. 
4. min-child weight: The minimum number of samples required to make a split (?)


Learn about interpretable machine learning by xgboost as well. https://medium.com/data-science/interpretable-machine-learning-with-xgboost-9ec80d148d27