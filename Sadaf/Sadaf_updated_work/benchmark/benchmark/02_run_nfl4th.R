# Run in terminal: Rscript benchmark/02_run_nfl4th.R
# Install nfl4th once if needed: install.packages('nfl4th', repos='https://cloud.r-project.org')
if (!requireNamespace('nfl4th', quietly = TRUE)) {
  stop("Please install nfl4th in R first: install.packages('nfl4th')")
}

input <- 'benchmark/benchmark_scenarios_2025.csv'
output <- 'benchmark/nfl4th_results_2025.csv'
if (!file.exists(input)) stop('Missing input: ', input)
x <- read.csv(input, stringsAsFactors = FALSE, check.names = FALSE)
need <- c('game_id', 'play_id', 'home_team', 'away_team', 'posteam',
          'type', 'season', 'qtr', 'quarter_seconds_remaining',
          'ydstogo', 'yardline_100', 'score_differential',
          'home_opening_kickoff', 'posteam_timeouts_remaining',
          'defteam_timeouts_remaining')
missing <- setdiff(need, names(x))
if (length(missing)) stop('Missing columns: ', paste(missing, collapse=', '))
if (nrow(x) == 0) stop('No scenarios to evaluate')

chunk_size <- 10L
chunks <- split(seq_len(nrow(x)), ceiling(seq_len(nrow(x))/chunk_size))
results <- list()
for (i in seq_along(chunks)) {
  ids <- chunks[[i]]
  cat(sprintf('Running nfl4th batch %d/%d (%d plays)...\n', i, length(chunks), length(ids)))
  one <- x[ids, , drop=FALSE]
  # add_4th_probs uses actual teams and season to find game-specific context.
  val <- tryCatch(nfl4th::add_4th_probs(one), error = function(e) {
    message('Batch error: ', conditionMessage(e), ' — retrying rows separately')
    NULL
  })
  if (!is.null(val)) {
    results[[length(results)+1L]] <- as.data.frame(val)
  } else {
    for (j in seq_len(nrow(one))) {
      row <- one[j, , drop=FALSE]
      r <- tryCatch(as.data.frame(nfl4th::add_4th_probs(row)),
                    error = function(e) {
                      message('Skipping ', row$game_id, ' ', row$play_id, ': ', conditionMessage(e))
                      NULL
                    })
      if (!is.null(r)) results[[length(results)+1L]] <- r
    }
  }
}
if (!length(results)) stop('No nfl4th outputs produced. Check R errors above.')
res <- do.call(rbind, results)
keep <- c('game_id', 'play_id', 'go_wp', 'fg_wp', 'punt_wp',
          'go_boost', 'first_down_prob', 'fg_make_prob')
missing <- setdiff(keep, names(res))
if (length(missing)) stop('nfl4th result omitted expected columns: ', paste(missing, collapse=', '))
res <- res[, keep, drop=FALSE]
write.csv(res, output, row.names=FALSE, na='')
cat('Saved ', nrow(res), ' nfl4th rows to ', output, '\n', sep='')
cat('Complete 3-action cases: ', sum(complete.cases(res[c('go_wp','fg_wp','punt_wp')])), '\n', sep='')
