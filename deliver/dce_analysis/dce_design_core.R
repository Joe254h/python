## ---------------------------------------------------------------------------
## D-efficient design for the Uasin Gishu childcare choice experiment.
## Base R only — no packages, nothing to install, nothing to break between
## versions. Sourced by dce_design.Rmd, and runnable on its own.
## ---------------------------------------------------------------------------

## ---- attributes: levels listed best-first where the attribute has an order --
dce_attributes <- function() {
  list(
    cost = list(
      label = "Cost",
      levels = c("KES 30/day", "KES 60/day", "KES 100/day", "KES 150/day"),
      ordered = TRUE),
    location = list(
      label = "Location",
      levels = c("Inside the market, next to the stalls", "5-minute walk",
                 "15-minute walk"),
      ordered = TRUE),
    hours = list(
      label = "Opening hours",
      levels = c("6:00-19:00", "7:00-17:00"),
      ordered = TRUE),
    care = list(
      label = "Caregiver ratio & training",
      levels = c("1 trained caregiver per 5 children",
                 "1 trained caregiver per 10 children",
                 "1 untrained helper per 10 children"),
      ordered = TRUE),
    food = list(
      label = "Food",
      levels = c("Porridge and lunch provided", "You bring the child's food"),
      ordered = TRUE),
    operator = list(
      label = "Who runs it",
      levels = c("County staff; complaints go to the county office",
                 paste("Private operator paying rent; operator sets fees;",
                       "complaints go to the operator"),
                 paste("County and private operator jointly agree on fees;",
                       "complaints go to a joint office"),
                 "Committee of market traders; complaints go to the committee"),
      ordered = FALSE),
    inclusion = list(
      label = "Inclusiveness of facilities",
      levels = c(paste("Physically accessible with staff trained to support",
                       "children with disabilities"),
                 paste("Physically accessible (ramp, adapted toilet),",
                       "staff not disability-trained"),
                 "No special accommodation for children with disabilities"),
      ordered = TRUE)
  )
}

## ---- dummy coding ----------------------------------------------------------
## Attribute j with L levels uses L-1 columns. Level 1 is the reference (all
## zeros); level k puts a 1 in column k-1. Column 1 of the design is the
## constant carried by the opt-out alternative.
.make_coder <- function(lvls) {
  offsets <- c(0, cumsum(lvls - 1))
  k <- sum(lvls - 1) + 1
  function(alt) {
    x <- numeric(k)
    for (j in seq_along(alt)) if (alt[j] > 1) x[1 + offsets[j] + alt[j] - 1] <- 1
    x
  }
}

## ---- constraints -----------------------------------------------------------
## A card is useless if the two options are identical, and almost useless if one
## is weakly better on every ordered attribute with the management model held
## equal — the respondent makes no trade-off at all.
.dominated <- function(a, b, ordered_idx, unordered_idx) {
  for (pair in list(list(a, b), list(b, a))) {
    x <- pair[[1]]; y <- pair[[2]]
    if (length(unordered_idx) && any(x[unordered_idx] != y[unordered_idx])) next
    if (all(x[ordered_idx] <= y[ordered_idx]) &&
        any(x[ordered_idx] <  y[ordered_idx])) return(TRUE)
  }
  FALSE
}

## ---- D-error ---------------------------------------------------------------
## Priors are zero, so every alternative has probability 1/J and the MNL
## information matrix is exact: I = sum_s X_s' (diag(p) - p p') X_s.
.d_error <- function(design, coder, k, n_alts) {
  p <- rep(1 / n_alts, n_alts)
  W <- diag(p) - tcrossprod(p)
  optout <- numeric(k); optout[1] <- 1
  I <- matrix(0, k, k)
  for (s in seq_along(design)) {
    X <- rbind(coder(design[[s]]$A), coder(design[[s]]$B), optout)
    I <- I + t(X) %*% W %*% X
  }
  d <- determinant(I, logarithm = TRUE)
  if (d$sign <= 0) return(Inf)
  exp(-as.numeric(d$modulus) / k)
}

## ---- level balance ---------------------------------------------------------
## D-optimality alone can leave a level appearing 10 times and another 8. That
## makes exact per-block balance arithmetically impossible later, so a small
## penalty is added to the objective: D-efficiency still decides, but ties break
## toward an even design.
.balance <- function(design, lvls) {
  tot <- 0
  for (j in seq_along(lvls)) {
    counts <- tabulate(unlist(lapply(design, function(s) c(s$A[j], s$B[j]))),
                       nbins = lvls[j])
    tot <- tot + sum(abs(counts - mean(counts)))
  }
  tot
}

## ---- generate --------------------------------------------------------------
dce_generate <- function(attrs = dce_attributes(), n_sets = 18,
                         sets_per_respondent = 6, min_diff = NULL,
                         n_start = 20, max_pass = 30, seed = 20260918,
                         balance_weight = 0.01, verbose = TRUE) {
  set.seed(seed)
  lvls <- vapply(attrs, function(a) length(a$levels), 1L)
  n_attr <- length(attrs)
  if (is.null(min_diff)) min_diff <- n_attr          # demand a full trade-off
  ordered_idx   <- which(vapply(attrs, function(a) a$ordered, TRUE))
  unordered_idx <- which(!vapply(attrs, function(a) a$ordered, TRUE))
  coder <- .make_coder(lvls)
  k <- sum(lvls - 1) + 1
  n_alts <- 3

  if (n_sets < k)
    stop(sprintf(paste("Model is unidentified: %d choice sets for %d parameters.",
                       "Raise n_sets to at least %d."), n_sets, k, k))

  valid <- function(a, b) {
    if (sum(a != b) < min_diff) return(FALSE)
    !.dominated(a, b, ordered_idx, unordered_idx)
  }
  random_set <- function() {
    repeat {
      a <- vapply(lvls, function(L) sample.int(L, 1), 1L)
      b <- vapply(lvls, function(L) sample.int(L, 1), 1L)
      if (valid(a, b)) return(list(A = a, B = b))
    }
  }

  objective <- function(design)
    .d_error(design, coder, k, n_alts) * (1 + balance_weight * .balance(design, lvls))

  best <- NULL; best_err <- Inf
  for (start in seq_len(n_start)) {
    design <- replicate(n_sets, random_set(), simplify = FALSE)
    err <- objective(design)
    for (pass in seq_len(max_pass)) {
      improved <- FALSE
      for (s in seq_len(n_sets)) {
        for (alt in c("A", "B")) {
          for (j in seq_len(n_attr)) {
            cur <- design[[s]][[alt]][j]
            for (lv in seq_len(lvls[j])) {
              if (lv == cur) next
              design[[s]][[alt]][j] <- lv
              if (!valid(design[[s]]$A, design[[s]]$B)) {
                design[[s]][[alt]][j] <- cur; next
              }
              e <- objective(design)
              if (e < err - 1e-12) { err <- e; cur <- lv; improved <- TRUE }
              else design[[s]][[alt]][j] <- cur
            }
          }
        }
      }
      if (!improved) break
    }
    if (err < best_err) { best <- design; best_err <- err }
    if (verbose) cat(sprintf("  start %2d of %d: objective %.6f (D-error %.6f)\n",
                             start, n_start, err,
                             .d_error(design, coder, k, n_alts)))
  }

  ## ---- blocking: split so level frequencies are as even as possible --------
  n_blocks <- n_sets / sets_per_respondent
  stopifnot(n_blocks %% 1 == 0)
  imbalance <- function(assign) {
    tot <- 0
    for (j in seq_len(n_attr)) {
      counts <- matrix(0, n_blocks, lvls[j])
      for (s in seq_len(n_sets)) for (alt in c("A", "B"))
        counts[assign[s], best[[s]][[alt]][j]] <- counts[assign[s], best[[s]][[alt]][j]] + 1
      w <- if (identical(names(attrs)[j], "operator")) 4 else 1
      tot <- tot + w * sum(abs(sweep(counts, 2, colMeans(counts))))
    }
    tot
  }
  base_assign <- rep(seq_len(n_blocks), each = sets_per_respondent)
  block <- base_assign; best_imb <- imbalance(base_assign)
  for (i in seq_len(2000)) {                       # random restarts
    a <- sample(base_assign)
    v <- imbalance(a)
    if (v < best_imb) { block <- a; best_imb <- v }
  }
  repeat {                                         # then swap until no gain
    improved <- FALSE
    for (s1 in seq_len(n_sets - 1)) for (s2 in (s1 + 1):n_sets) {
      if (block[s1] == block[s2]) next
      cand <- block
      cand[c(s1, s2)] <- cand[c(s2, s1)]
      v <- imbalance(cand)
      if (v < best_imb - 1e-9) { block <- cand; best_imb <- v; improved <- TRUE }
    }
    if (!improved) break
  }

  structure(list(design = best,
                 d_error = .d_error(best, coder, k, n_alts),
                 objective = best_err,
                 balance = .balance(best, lvls), block = block,
                 imbalance = best_imb, attrs = attrs, lvls = lvls,
                 n_sets = n_sets, n_blocks = n_blocks,
                 sets_per_respondent = sets_per_respondent,
                 n_par = k, ordered_idx = ordered_idx,
                 unordered_idx = unordered_idx),
            class = "dce_design")
}

## ---- verification ----------------------------------------------------------
dce_check <- function(d) {
  attrs <- d$attrs; n_attr <- length(attrs)
  cat("D-error                :", sprintf("%.6f", d$d_error), " (lower is better)\n")
  cat("Parameters estimated   :", d$n_par, "\n")
  cat("Choice sets            :", d$n_sets, "in", d$n_blocks, "blocks of",
      d$sets_per_respondent, "\n\n")

  ident <- sum(vapply(d$design, function(s) all(s$A == s$B), TRUE))
  dom   <- sum(vapply(d$design, function(s)
    .dominated(s$A, s$B, d$ordered_idx, d$unordered_idx), TRUE))
  diffs <- vapply(d$design, function(s) sum(s$A != s$B), 1L)
  cat("Identical A/B pairs    :", ident, " (must be 0)\n")
  cat("Dominated pairs        :", dom,   " (must be 0)\n")
  cat("Attributes differing   : min", min(diffs), "max", max(diffs),
      "of", n_attr, "\n\n")

  cat("Level counts across all", 2 * d$n_sets, "alternatives\n")
  for (j in seq_len(n_attr)) {
    counts <- tabulate(unlist(lapply(d$design, function(s) c(s$A[j], s$B[j]))),
                       nbins = d$lvls[j])
    cat(sprintf("  %-28s %s   (even = %.1f)\n", names(attrs)[j],
                paste(counts, collapse = " "), 2 * d$n_sets / d$lvls[j]))
  }
  cat("\nManagement model by block (should be equal within each block)\n")
  j <- which(names(attrs) == "operator")
  for (b in seq_len(d$n_blocks)) {
    idx <- which(d$block == b)
    counts <- tabulate(unlist(lapply(d$design[idx], function(s) c(s$A[j], s$B[j]))),
                       nbins = d$lvls[j])
    cat("  Block", b, ":", paste(counts, collapse = " "), "\n")
  }
  invisible(list(identical = ident, dominated = dom, min_diff = min(diffs)))
}

## ---- readable output --------------------------------------------------------
dce_cards <- function(d) {
  rows <- list(); i <- 1
  for (b in seq_len(d$n_blocks)) {
    sets <- which(d$block == b)
    for (n in seq_along(sets)) {
      s <- sets[n]
      for (alt in c("A", "B")) {
        lv <- d$design[[s]][[alt]]
        rows[[i]] <- data.frame(
          block = b, card_in_block = n, design_set = s, alt = alt,
          as.list(setNames(
            lapply(seq_along(d$attrs), function(j) d$attrs[[j]]$levels[lv[j]]),
            names(d$attrs))),
          stringsAsFactors = FALSE)
        i <- i + 1
      }
    }
  }
  do.call(rbind, rows)
}

dce_print_cards <- function(d, markdown = FALSE) {
  cards <- dce_cards(d)
  labs <- vapply(d$attrs, function(a) a$label, "")
  for (b in sort(unique(cards$block))) {
    cat("\n\n### Block ", b, "\n", sep = "")
    cb <- cards[cards$block == b, ]
    for (n in sort(unique(cb$card_in_block))) {
      A <- cb[cb$card_in_block == n & cb$alt == "A", ]
      B <- cb[cb$card_in_block == n & cb$alt == "B", ]
      cat("\n\n**F", n, ".  Set ", n, " of ", d$sets_per_respondent,
          "**  (design set ", A$design_set, ")\n\n", sep = "")
      tab <- data.frame(Attribute = labs,
                        `Alternative A` = unlist(A[names(d$attrs)]),
                        `Alternative B` = unlist(B[names(d$attrs)]),
                        check.names = FALSE, row.names = NULL)
      if (markdown && requireNamespace("knitr", quietly = TRUE)) {
        print(knitr::kable(tab))
      } else {
        print(tab, right = FALSE)
      }
      cat("\nWhich would you choose?   [ ] A   [ ] B   ",
          "[ ] Neither - I'd keep my current arrangement\n", sep = "")
    }
  }
  invisible(cards)
}
