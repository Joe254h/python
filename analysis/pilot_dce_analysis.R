## ===========================================================================
## Pilot DCE analysis — Uasin Gishu childcare study
## Base R only: conditional logit fitted directly, no package dependencies.
## ===========================================================================
options(stringsAsFactors = FALSE, width = 100)
dce  <- read.csv("dce_long.csv")
resp <- read.csv("respondents.csv")

cat("== 1. What was fielded ==\n")
cat("respondents:", length(unique(dce$rid)),
    "| tasks:", nrow(dce)/3,
    "| unique choice sets:", length(unique(dce$design_set)), "\n")
cat("block sizes:", paste(names(table(resp$block)), table(resp$block), sep="=", collapse="  "), "\n\n")

## ---- choice shares --------------------------------------------------------
chosen <- dce[dce$choice == 1, ]
cat("Choice shares over", nrow(chosen), "tasks\n")
print(round(100 * table(chosen$alt) / nrow(chosen), 1))
optout_rate <- mean(chosen$alt == "none")
cat("opt-out rate:", sprintf("%.1f%%", 100*optout_rate), "\n\n")

svc <- chosen[chosen$alt != "none", ]
cat("Among", nrow(svc), "service choices, A was picked",
    sprintf("%.1f%%", 100*mean(svc$alt == "A")), "of the time\n")
bt <- binom.test(sum(svc$alt=="A"), nrow(svc), 0.5)
cat("  binomial test vs 50/50: p =", sprintf("%.3f", bt$p.value),
    " 95% CI", sprintf("[%.1f%%, %.1f%%]", 100*bt$conf.int[1], 100*bt$conf.int[2]), "\n\n")

## ---- THE CONFOUND ---------------------------------------------------------
cat("== 2. Why that number cannot be read as a position effect ==\n")
wide <- reshape(unique(dce[dce$alt != "none", c("design_set","alt","cost_kes")]),
                idvar = "design_set", timevar = "alt", direction = "wide")
wide$A_cheaper <- wide$cost_kes.A < wide$cost_kes.B
cat("Across the", nrow(wide), "fielded cards, A was the cheaper option on",
    sum(wide$A_cheaper), "\n")
cat("  => position A and 'cheaper' agree on",
    sprintf("%.0f%%", 100*mean(wide$A_cheaper)), "of cards.\n")
cheap_chosen <- merge(svc, wide[, c("design_set","A_cheaper")], by="design_set")
picked_cheaper <- with(cheap_chosen, (alt=="A" & A_cheaper) | (alt=="B" & !A_cheaper))
cat("  cheaper option chosen in", sum(picked_cheaper), "of", nrow(cheap_chosen),
    sprintf("(%.1f%%)\n\n", 100*mean(picked_cheaper)))

## ---- conditional logit ----------------------------------------------------
make_X <- function(d, with_position = FALSE, cost_linear = TRUE) {
  f <- function(v, lv) factor(v, levels = lv)
  d$location  <- f(d$location,  c("NONE","Inside market, next to stalls","5-min walk","15-min walk"))
  d$hours     <- f(d$hours,     c("NONE","6:00-19:00","7:00-17:00"))
  d$care      <- f(d$care,      c("NONE","1 trained caregiver per 5 children",
                                  "1 trained caregiver per 10 children",
                                  "1 untrained helper per 10 children"))
  d$food      <- f(d$food,      c("NONE","Porridge & lunch provided","Bring own food"))
  d$operator  <- f(d$operator,  c("NONE","County staff","Private operator",
                                  "Joint County & Private (PPP)","Committee of market traders"))
  d$inclusion <- f(d$inclusion, c("NONE","Physically accessible with staff disability-trained",
                                  "Physically accessible, staff not trained","No special accommodation"))
  svc <- d$optout == 0
  cols <- list(optout = as.numeric(d$optout))
  if (cost_linear) cols$cost <- ifelse(svc, d$cost_kes/100, 0)
  else for (lv in c(60,100,150)) cols[[paste0("cost_",lv)]] <- as.numeric(svc & d$cost_kes==lv)
  add <- function(var, drop1) {
    lv <- levels(d[[var]]); lv <- lv[lv != "NONE" & lv != drop1]
    for (l in lv) cols[[paste0(var,"_",gsub("[^A-Za-z0-9]+","_",l))]] <<- as.numeric(svc & d[[var]]==l)
  }
  add("location","Inside market, next to stalls")
  add("hours","6:00-19:00")
  add("care","1 trained caregiver per 5 children")
  add("food","Porridge & lunch provided")
  add("operator","County staff")
  add("inclusion","Physically accessible with staff disability-trained")
  if (with_position) cols$positionA <- as.numeric(svc & d$alt == "A")
  as.matrix(as.data.frame(cols))
}

clogit <- function(X, y, group) {
  k <- ncol(X)
  nll <- function(b) {
    v  <- as.vector(X %*% b)
    mx <- ave(v, group, FUN = max)
    lse <- log(ave(exp(v - mx), group, FUN = sum)) + mx
    -sum(v[y == 1] - lse[y == 1])
  }
  fit <- optim(rep(0, k), nll, method = "BFGS", hessian = TRUE,
               control = list(maxit = 2000, reltol = 1e-12))
  se <- tryCatch(sqrt(diag(solve(fit$hessian))), error = function(e) rep(NA_real_, k))
  out <- data.frame(term = colnames(X), est = fit$par, se = se,
                    z = fit$par/se, p = 2*pnorm(-abs(fit$par/se)),
                    row.names = NULL)
  attr(out, "LL") <- -fit$value
  attr(out, "converged") <- fit$convergence == 0
  out
}
fitc <- clogit

grp <- paste(dce$rid, dce$task)
cat("== 3. Can the fielded design identify the model? ==\n")
X0 <- make_X(dce, with_position = FALSE, cost_linear = FALSE)
cat("parameters in the full dummy-coded model:", ncol(X0), "\n")
cat("unique choice sets fielded:", length(unique(dce$design_set)), "\n")
cat("design-matrix rank:", qr(X0)$rank, "of", ncol(X0), "columns\n")
cat("\nThe matrix has full column rank, so the model IS estimable - the common\n",
    "rule of thumb 'at least as many choice sets as parameters' is a conservative\n",
    "guard, not a mathematical identification condition. What 12 sets cannot give\n",
    "is PRECISION: there is very little independent variation for 15 parameters,\n",
    "which is why almost every standard error below is large.\n\n", sep="")

cat("== 4. Cost coefficient, with and without a position term ==\n")
m1 <- fitc(make_X(dce, FALSE, TRUE), dce$choice, grp)
m2 <- fitc(make_X(dce, TRUE,  TRUE), dce$choice, grp)
show <- function(m, keep) {
  s <- m[m$term %in% keep, ]
  print(data.frame(term = s$term, estimate = round(s$est,3), se = round(s$se,3),
                   z = round(s$z,2), p = round(s$p,3)), row.names = FALSE)
}
cat("\nModel 1 — attributes only\n");            show(m1, c("cost","optout"))
cat("  log-likelihood:", round(attr(m1,"LL"),2), "\n")
cat("\nModel 2 — attributes + position A\n");    show(m2, c("cost","optout","positionA"))
cat("  log-likelihood:", round(attr(m2,"LL"),2), "\n")
lr <- 2*(attr(m2,"LL") - attr(m1,"LL"))
cat("\nLikelihood-ratio test for the position term: chi2 =", round(lr,2),
    " df = 1  p =", sprintf("%.4f", pchisq(lr, 1, lower.tail = FALSE)), "\n")
cat("cost coefficient:", sprintf("%.3f without position, %.3f with position\n",
    m1$est[m1$term=="cost"], m2$est[m2$term=="cost"]))

cat("\n== 5. Full attribute model (read with the identification caveat above) ==\n")
print(data.frame(term = m2$term, estimate = round(m2$est,3), se = round(m2$se,3),
                 z = round(m2$z,2), p = round(m2$p,3)), row.names = FALSE)

saveRDS(list(m1=m1, m2=m2), "pilot_models.rds")

## ---- fit quality -----------------------------------------------------------
cat("\n== 6. How well does the model fit? ==\n")
ll_null <- nrow(dce)/3 * log(1/3)
for (nm in c("m1","m2")) {
  m <- get(nm); ll <- attr(m, "LL")
  cat(sprintf("  %s: LL = %8.2f   McFadden R2 = %.3f   converged = %s\n",
              nm, ll, 1 - ll/ll_null, attr(m, "converged")))
}
cat("  null (equal probability) LL =", round(ll_null,2), "\n")
cat("  Only the position term reaches significance. No service feature does.\n\n")

## ---- respondent-level choice patterns --------------------------------------
cat("== 7. How did individuals answer? ==\n")
pat <- merge(chosen[chosen$alt != "none", c("rid","design_set","alt")],
             wide[, c("design_set","A_cheaper")], by = "design_set")
per <- aggregate(cbind(nA = alt == "A",
                       n_cheap = (alt=="A" & A_cheaper) | (alt=="B" & !A_cheaper)) ~ rid,
                 data = pat, FUN = sum)
per$n <- as.vector(table(pat$rid)[as.character(per$rid)])
cat("respondents choosing A on all 6 tasks      :", sum(per$nA == per$n), "of", nrow(per), "\n")
cat("respondents choosing B on all 6 tasks      :", sum(per$nA == 0),     "of", nrow(per), "\n")
cat("respondents choosing the cheaper every time:", sum(per$n_cheap == per$n), "\n")
cat("respondents never choosing the cheaper     :", sum(per$n_cheap == 0), "\n")
cat("\ndistribution of 'times A chosen' (0-6):\n"); print(table(factor(per$nA, levels=0:6)))
cat("\nIf traders were answering on price, 'times cheaper chosen' would cluster high.\n")
print(table(factor(per$n_cheap, levels=0:6)))

## ---- interview duration ----------------------------------------------------
cat("\n== 8. Interview duration ==\n")
dur <- suppressWarnings(as.numeric(resp$duration_min))
dur <- dur[!is.na(dur)]
cat("n =", length(dur), " median =", round(median(dur),1), "min  IQR",
    paste(round(quantile(dur, c(.25,.75)),1), collapse=" to "),
    " range", paste(round(range(dur),1), collapse=" to "), "\n")
cat("interviews over 3 hours (form left open?):", sum(dur > 180), "\n")

## ---- reliability -----------------------------------------------------------
cat("\n== 9. Reliability of the two multi-item scales ==\n")
num <- function(x) suppressWarnings(as.numeric(sub("^\\s*(\\d+).*$", "\\1", as.character(x))))
alpha_tbl <- function(df, label) {
  M <- as.data.frame(lapply(df, num)); M <- M[complete.cases(M), , drop = FALSE]
  k <- ncol(M); n <- nrow(M)
  a <- (k/(k-1)) * (1 - sum(apply(M,2,var))/var(rowSums(M)))
  cat(sprintf("\n%s: %d items, %d complete cases, Cronbach alpha = %.3f\n", label, k, n, a))
  out <- data.frame(item = names(M),
                    mean = round(colMeans(M),2), sd = round(apply(M,2,sd),2),
                    item_total_r = NA_real_, alpha_if_dropped = NA_real_)
  for (j in seq_len(k)) {
    rest <- rowSums(M[,-j,drop=FALSE])
    out$item_total_r[j] <- round(cor(M[,j], rest), 3)
    Mj <- M[,-j,drop=FALSE]; kj <- ncol(Mj)
    out$alpha_if_dropped[j] <- round((kj/(kj-1))*(1 - sum(apply(Mj,2,var))/var(rowSums(Mj))), 3)
  }
  print(out, row.names = FALSE)
  invisible(a)
}
E1 <- resp[, grep("^E1[a-l]$", names(resp))]
E6 <- resp[, grep("^E6[a-g]$", names(resp))]
a1 <- alpha_tbl(E1, "E1 service-attribute importance")
a6 <- alpha_tbl(E6, "E6 norms and perceptions")

cat("\nFloor/ceiling check on E1 (a scale everyone answers at the top cannot discriminate)\n")
E1n <- as.data.frame(lapply(E1, num))
cat("  share of all E1 responses at the maximum (4):",
    sprintf("%.1f%%\n", 100*mean(unlist(E1n) == 4, na.rm = TRUE)))
cat("  share at 3 or 4:", sprintf("%.1f%%\n", 100*mean(unlist(E1n) >= 3, na.rm = TRUE)))
cat("  items with zero variance:", sum(apply(E1n, 2, function(x) var(x, na.rm=TRUE)) == 0), "\n")

## ---- E6 direction check -----------------------------------------------------
cat("\n== 10. E6 mixes item directions ==\n")
cat("Scale is 1 = strongly agree ... 4 = strongly disagree.\n")
cat("E6a and E6b are worded so that AGREEING is the traditional view;\n")
cat("E6c to E6g are worded so that AGREEING is the supportive view.\n")
cat("Summing them without reversing measures nothing coherent.\n\n")
E6n <- as.data.frame(lapply(E6, num)); E6n <- E6n[complete.cases(E6n), ]
alpha_of <- function(M) { k <- ncol(M)
  (k/(k-1))*(1 - sum(apply(M,2,var))/var(rowSums(M))) }
cat(sprintf("  alpha as collected                      : %.3f\n", alpha_of(E6n)))
E6r <- E6n; E6r$E6a <- 5 - E6r$E6a; E6r$E6b <- 5 - E6r$E6b
cat(sprintf("  alpha with E6a and E6b reverse-coded    : %.3f\n", alpha_of(E6r)))
cat(sprintf("  alpha on the 5 supportive items only    : %.3f\n",
            alpha_of(E6n[, c("E6c","E6d","E6e","E6f","E6g")])))
cat("\nitem-total correlations after reverse-coding:\n")
it <- sapply(seq_len(ncol(E6r)), function(j) round(cor(E6r[,j], rowSums(E6r[,-j,drop=FALSE])),3))
print(setNames(it, names(E6r)))

## ---- sample size from the regenerated design's information matrix -----------
cat("\n== 11. Sample size for the full study ==\n")
cards <- read.csv("../output/r/choice_cards.csv")
lv <- list(
  cost      = c("KES 30/day","KES 60/day","KES 100/day","KES 150/day"),
  location  = c("Inside the market, next to the stalls","5-minute walk","15-minute walk"),
  hours     = c("6:00-19:00","7:00-17:00"),
  care      = c("1 trained caregiver per 5 children","1 trained caregiver per 10 children",
                "1 untrained helper per 10 children"),
  food      = c("Porridge and lunch provided","You bring the child's food"),
  operator  = c("County staff; complaints go to the county office",
                "Private operator paying rent; operator sets fees; complaints go to the operator",
                "County and private operator jointly agree on fees; complaints go to a joint office",
                "Committee of market traders; complaints go to the committee"),
  inclusion = c("Physically accessible with staff trained to support children with disabilities",
                "Physically accessible (ramp, adapted toilet), staff not disability-trained",
                "No special accommodation for children with disabilities"))
lvls <- lengths(lv); K <- sum(lvls - 1) + 1
code <- function(r) { x <- numeric(K); off <- c(0, cumsum(lvls - 1))
  for (j in seq_along(lv)) { i <- match(r[[names(lv)[j]]], lv[[j]])
    if (i > 1) x[1 + off[j] + i - 1] <- 1 }
  x }
p <- rep(1/3, 3); W <- diag(p) - tcrossprod(p)
optout <- c(1, numeric(K-1))
I_tot <- matrix(0, K, K)
for (b in unique(cards$block)) for (cc in unique(cards$card_in_block[cards$block==b])) {
  rs <- cards[cards$block==b & cards$card_in_block==cc, ]
  X <- rbind(code(rs[rs$alt=="A",]), code(rs[rs$alt=="B",]), optout)
  I_tot <- I_tot + t(X) %*% W %*% X
}
nm <- c("opt-out", unlist(lapply(names(lv), function(j) paste0(j,": ",lv[[j]][-1]))))
cat("Design: 18 cards in 3 blocks, 6 per respondent.\n")
cat("With N respondents split evenly across blocks, total information = (N/3) * I.\n\n")
se_at <- function(N) sqrt(diag(solve((N/3) * I_tot)))
Ns <- c(100,150,200,250,300,400,500)
tab <- sapply(Ns, function(N) round(se_at(N), 3))
dimnames(tab) <- list(nm, paste0("N=", Ns))
cat("Projected standard errors (zero priors, main effects):\n"); print(tab)

cat("\nSmallest coefficient detectable with 80% power (needs |b|/SE >= 2.80):\n")
det <- sapply(Ns, function(N) round(2.80 * se_at(N), 2))
dimnames(det) <- list(nm, paste0("N=", Ns)); print(det)

worst <- which.max(se_at(300))
cat("\nAt N = 300 the least precisely estimated parameter is:", nm[worst],
    sprintf("(SE %.3f, detects |b| >= %.2f)\n", se_at(300)[worst], 2.8*se_at(300)[worst]))
cat("\nRule-of-thumb cross-check (Johnson & Orme): n >= 500*c/(t*a) with c =",
    max(lvls), "levels, t = 6 tasks, a = 2 service alternatives\n")
cat("  => n >=", ceiling(500*max(lvls)/(6*2)), "for main effects.\n")
cat("  A subgroup you want to model separately needs that many ON ITS OWN.\n")

## ---- robustness: are four respondents driving the position effect? ----------
cat("\n== 12. Robustness of the position finding ==\n")
allA <- per$rid[per$nA == per$n]
cat("dropping the", length(allA), "respondents who chose A on every task\n")
d2 <- dce[!(dce$rid %in% allA), ]
g2 <- paste(d2$rid, d2$task)
m2b <- clogit(make_X(d2, TRUE, TRUE), d2$choice, g2)
s <- m2b[m2b$term %in% c("cost","optout","positionA"), ]
print(data.frame(term=s$term, estimate=round(s$est,3), se=round(s$se,3),
                 z=round(s$z,2), p=round(s$p,3)), row.names=FALSE)
cat("  n respondents now:", length(unique(d2$rid)), "\n")

## ---- can willingness to pay be computed? -----------------------------------
cat("\n== 13. Willingness to pay ==\n")
bc1 <- m1$est[m1$term=="cost"]; bc2 <- m2$est[m2$term=="cost"]
cat(sprintf("cost coefficient: %+.3f (p=%.3f) without position; %+.3f (p=%.3f) with position\n",
            bc1, m1$p[m1$term=="cost"], bc2, m2$p[m2$term=="cost"]))
cat("WTP = -b_attribute / b_cost. That ratio is only meaningful when b_cost is\n")
cat("negative and precisely estimated. Here it is neither: not significant in\n")
cat("either model, and it changes sign depending on whether position is included.\n")
cat("=> No monetary willingness-to-pay figure can be reported from this pilot.\n")

## ---- export for the report --------------------------------------------------
res <- list(
  n_resp = length(unique(dce$rid)), n_tasks = nrow(dce)/3,
  n_sets_fielded = length(unique(dce$design_set)),
  share_A = round(100*mean(svc$alt=="A"),1), p_A = round(bt$p.value,4),
  ci_A = round(100*bt$conf.int,1),
  optout_rate = round(100*optout_rate,1),
  A_cheaper_cards = sum(wide$A_cheaper), n_cards = nrow(wide),
  cheaper_chosen = sum(picked_cheaper), cheaper_n = nrow(cheap_chosen),
  cheaper_pct = round(100*mean(picked_cheaper),1),
  cost_no_pos = round(bc1,3), cost_with_pos = round(bc2,3),
  pos_est = round(m2$est[m2$term=="positionA"],3),
  pos_se = round(m2$se[m2$term=="positionA"],3),
  pos_p = round(m2$p[m2$term=="positionA"],4),
  lr_chi2 = round(lr,2), lr_p = round(pchisq(lr,1,lower.tail=FALSE),4),
  alpha_E1 = round(a1,3), alpha_E6_raw = round(alpha_of(E6n),3),
  alpha_E6_rev = round(alpha_of(E6r),3),
  E1_zero_var = names(E1n)[apply(E1n,2,function(x) var(x,na.rm=TRUE))==0],
  dur_median = round(median(dur),1), dur_max = round(max(dur),1),
  dur_over3h = sum(dur>180),
  allA_n = length(allA),
  se300 = round(se_at(300),3), se200 = round(se_at(200),3), se150 = round(se_at(150),3),
  jo_min = ceiling(500*max(lvls)/(6*2)),
  param_names = nm)
jsonlite_ok <- requireNamespace("jsonlite", quietly = TRUE)
if (jsonlite_ok) {
  writeLines(jsonlite::toJSON(res, auto_unbox = TRUE, pretty = TRUE), "pilot_results.json")
} else {
  dput(res, file = "pilot_results.R")
}
cat("\nresults exported (", if (jsonlite_ok) "pilot_results.json" else "pilot_results.R", ")\n")
