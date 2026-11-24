We evaluate each fourth-down option (going for it, punting, or attempting a field goal) based on expected points (EP), which represent the next score in the half from the offense's perspective. To build the model, we use nflverse play-by-play data for the 2021-2025 NFL seasons, which encompasses 1,424 regular-season and playoff games, with 139,408 plays included in the estimates. Field position is valued with nflverse's own EP estimates. The value of a first down at each yard line is determined by the mean EP of first-down plays from that spot, smoothed with a centered five-yard moving average. Each outcome of a fourth-down decision is expressed as a resulting field position, valued with this curve. When the opponent takes possession, the value is the negative of their first-down value at that spot.
The value of going for it is calculated by weighing the two outcomes by an estimated conversion probability. This probability is estimated as the share of third- and fourth-down runs and passes at the same distance that gained the required yards without a turnover, constrained so it doesn't rise with distance. The idea is that longer distances should remain harder to convert.

$$
\begin{equation}
  p(d) = \min_{k \le d} \, c(k)
  \label{eq:pconv}
\end{equation}
$$

where $d$ is the yards to go ($d = 1, \dots, 15$, with distances of 15 yards or more pooled into $d = 15$) and $c(k)$ is the share of third- and fourth-down runs and passes with $k$ yards to go that gained the required distance without a turnover. Taking the minimum over shorter distances keeps $p(d)$, the conversion probability, from increasing with distance.
 
The value of converting is calculated by taking the average field-position value after replaying every observed conversion gain at a given distance from the current yard line. Touchdowns are counted as 7 points. 
 
$$
\begin{equation}
  S(y, d) = \frac{1}{|G_d|} \sum_{g \in G_d}
  \begin{cases}
    7, & g \ge y,\\
    V(y - g), & g < y,
  \end{cases}
  \label{eq:success}
\end{equation}
$$
 
where $S(y, d)$ is the expected points after a successful conversion, $y$ is the distance in yards from the opponent's end zone ($1 \le y \le 99$), $G_d$ is the set of yards gained on all successful conversions with $d$ yards to go, and $|G_d|$ corresponds to their number. The first-down value $V(y)$ is the mean nflverse EP of first-down plays from yard line $y$, smoothed with a centered five-yard moving average. A gain $g \ge y$ reaches the end zone and counts as a touchdown worth 7 points; on fourth-and-goal, $S(y, d) = 7$.
 
A failed attempt gives the opponent the ball at the same spot. A punt is valued at the average post-punt EP observed from that yard line, which includes returns, touchbacks, and blocks, and is defined only where at least 20 punts occurred. A field goal weighs 3 points, with a make probability that depends on kick distance and is constrained to fall as distance grows, against the opponent's field position after a miss. The recommended option is the one with the highest EP.

$$
\begin{equation}
  \mathrm{EP}_{\mathrm{go}}(y, d) = p(d)\, S(y, d) + \bigl(1 - p(d)\bigr)\, F(y),
  \qquad F(y) = -V(100 - y)
  \label{eq:go}
\end{equation}
$$

where $\mathrm{EP}_{\mathrm{go}}(y, d)$ is the expected points of going for it on fourth-and-$d$ at yard line $y$, and $F(y)$ is the value to the offense of a failed attempt. After a failure the opponent takes over at the same spot, which is yard line $100 - y$ from its side, so the offense's value is the negative of the opponent's first-down value there.
 
Two late-game rules adjust these values: on the last play of a half, only points scored on that play count, and in the fourth quarter, a trailing team that could not get the ball back late in the fourth quarter or overtime, a trailing team that could not get the ball back gets the same value from punting, or from a field goal that cannot tie or win, as from a failed attempt. 
 
To measure the uncertainty associated with estimating these values from a finite sample, we use a nonparametric bootstrap that resamples whole games rather than individual plays, as plays in the same game share teams, conditions, and game script. In each of 1,000 replications, we draw 1,424 games with replacement and rebuild every lookup table with the same procedure, including the smoothing, minimum-count rules, and monotonicity constraints. The 95% interval is calculated from the 2.5th to the 97.5th percentile of the 1,000 bootstrap estimates. We also report how often each option ranks first and an interval for the recommended option's margin over the runner-up, computed within each replication. For example, on fourth-and-4 at the opponent's 35 in a tied third quarter, a field goal is worth 1.67 EP [1.50, 1.77] and going for it 1.22 EP [1.11, 1.31]. The field goal leads by 0.45 [0.25, 0.59] and ranks first in all 1,000 replications. Resampling individual plays instead resulted in intervals only 0-4% narrower.
These intervals capture sampling uncertainty in league-wide estimates, rather than the full uncertainty of a particular decision. Because the model pools attempts across all teams and field positions, the intervals are narrow. The fourth-and-1 conversion probability, for instance, is 69% [68%, 70%], reflecting the league-average rate rather than a specific team's chances on a specific play. The intervals also take nflverse's EP estimates as given, and they do not reflect the model's simplifications, including a conversion probability that depends only on yards to go, and time and score entering only through the two late-game rules.


