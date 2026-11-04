During the exploratory phase of our research project, before narrowing our focus to fourth-down decisions, we considered several topic
proposals. One such idea was to model the outcomes of run or pass plays during the first three downs. We achieve this by building two
separate multinomial logistic regression models  for pass and run plays. This allows us to forecast the entire distribution of outcomes
as opposed to predicting a single average gain. Both regression models have the same dependent variable and same predictors and only 
differ in data samples - one model uses pass plays and the other run plays. In each model, the dependent variable is a categorical
variable with 17 categories for no gain or a loss, single-yard gains from 1 to 10, wider bins for longer gains (11–14, 15–19, 20–29 and
30+), a touchdown, and a turnover. The predictors in the models, on the other hand, capture the situational context for each play - field
position in 10-yard zones, down, yards to go in groups, and whether the previous play of the drive gained yards and the strength of the
two teams. Team strength enters as offense and defense scores standardized against the previous season's league distribution. 
From the predicted category probabilities, we derive expected yards, first-down probabilities, and probabilities of touchdowns, turnovers,
and no gain. 
The models are trained on a specific range of seasons (2000-2021) and evaluated out-of-sample on later seasons (2022-2025). Overall,
the modest show marginal improvement in predictive accuracy over historical outcome frequencies, reflecting the inherent randomness
of individual plays. Comparing the run and pass predictions for the same situation and matchup reveals where each play type tends
to perform better. Finally, adding estimation uncertainty can enable every prediction and play decision (run vs pass) comparison
to carry a confidence interval and a probability that one option is better.
