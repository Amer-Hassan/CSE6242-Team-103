# Failure-based Disappointment Adjusted Model 

Required Files: Disappointment.ipynb

## Overview

This file build's off of Amer's 4th-down EP model and adds a failure-based disappointment modifier that is inspired by the work of Bell (1985) that we referenced in the literature survey. Bell compares two lotteries: one in which the maximum winnings is $10k, and another in which maximum winnings is $1 million. Thus, winning $10k can result in two vastly different emotional outcomes associated with disappointment. Bell's work did not encompass NFL football or 4th-down decision making, so this adjusted model uses an algorithm inspired by his calculations to 1) see if we can compile recommendations that are more closely aligned with historically conservative NFL coaching decisions & 2) later use this algorithm to create a movable bar in the visualization tool for users to adjust disappointment on a scale of 0-1 to see how levels of failure-based disappointment change recommendations. We would note that the scale should be closer to 0 when this tool is utilized to align with the results of Amer's model and provide the best possible recommendation. 

## Methodology/Results

Based on Amer's Expected Points calculations, this adjusted-model uses $V(i) = EP(i) - (d * DIS(i))$ as the base algorithm inspired by Bell (1985) to find disappointment-adjusted values wherein: 

- V(i) is the disappointment-adjusted EP value for each decision
- EP(i) is the original expected points from Amer's model for each decision
- d is a sensitivity coefficient
- DIS(i) is the disappointment-induced penalty.

The disappointment-induced penalty, DIS(i) is formulated via a probability-based calculation: $DIS(i) = p * (1 - p) *(g - b)$ wherein: 

- p is the probability of a good result (4th-down conversion, made field goal, good punt) 
- g is the EP of a good result 
- b is the EP of a bad result

*Note that to figure out what a "good punt" is, since there are no fixed outcomes as in converting a 4th-down or making/missing a field goal, the mean EP for historical punts was calculated at each field position, and then the individual punts that occurred at those field positions were assessed against those means to see how much worse they were from the means, to then be included in the DIS(i) calculation.* 

The model is trained on 2021-2024 aggregated data from nflverse to get the EP. The optimal sensitivity coefficient was tested on 2024 historical coaching data in intervals of .1 from 0-1, resulting in an optimal value of 0.6 when comparing the closeness of the recommendations to actual 2024 coaching decisions. The disappointment-adjusted model with the d coefficient of 0.6 was then tested on 2025 coaching decisions and compared with Amer's original model and resulted in a 11.53% increase in closeness to actual coaching decisions. 

### 2025: Comparison of Models tested against 2025 4th Down Decisions ###
- Original Model: 72.68 %
- Disappointment-Adjusted (d modifier = 0.6): 84.21 %
