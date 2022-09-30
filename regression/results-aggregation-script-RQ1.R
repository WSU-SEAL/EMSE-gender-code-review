library(lme4)
library(car)
library(Hmisc)
library(fmsb)
library(rms)
library(pROC)
library(epiDisplay)
library(MASS)
library(pscl)
library(DescTools)
library(effects)


get.automated.spearman <- function(dataset, metrics, spearman.threshold, verbose = F){
  
  .get.higher.correlation <- function(index1, index2, metrics, metric.correlations, verbose = F, count){
    metric1 <- metrics[index1]
    metric2 <- metrics[index2]
    if(verbose)
      cat(paste0('Step ', count, ' - {', metric1, ', ', metric2, '} > '))# are correlated with r = ', metric.correlations[metric1, metric2], '\n'))
    metric1.correlation <- mean(metric.correlations[metric1, !metrics %in% c(metric1, metric2)])
    metric2.correlation <- mean(metric.correlations[metric2, !metrics %in% c(metric1, metric2)])
    if(metric1.correlation <= metric2.correlation){
      return(index2)
    } else {
      return(index1)
    }
  }
  
  metric.correlations <- abs(rcorr(as.matrix(dataset[, metrics]), type = 'spearman')$r)
  
  above.threshold <- which((metric.correlations >= spearman.threshold), arr.ind = TRUE)
  row.names(above.threshold) <- NULL
  above.threshold <- as.data.frame(above.threshold, row.names = NULL)
  above.threshold <- above.threshold[above.threshold$row != above.threshold$col, ]
  above.threshold$correlation <- 100
  for(i in 1:nrow(above.threshold)){
    above.threshold$correlation[i] <- metric.correlations[above.threshold$row[i], above.threshold$col[i]]
  }
  above.threshold <- above.threshold[order(-above.threshold$correlation), ]
  
  exclude.metrics <- {}
  count <- 1
  repeat{
    if(nrow(above.threshold) == 0)
      break
    tmp <- above.threshold[1, ]
    exclude.index <- .get.higher.correlation(tmp$row, tmp$col, metrics, metric.correlations, verbose, count)
    exclude.metrics <- c(exclude.metrics, metrics[exclude.index])
    if(verbose){
      cat(paste0(metrics[exclude.index], '\n'))
      count <- count + 1
    }
    above.threshold <- above.threshold[-which((above.threshold$row == exclude.index) | (above.threshold$col == exclude.index)), ]
  }
  selected.metrics <- metrics[!metrics %in% exclude.metrics]
  return(selected.metrics)
}


remove.constant.categorical <-
  function(dataset,
           metrics) {
    # Check constant metrics
    constant <-
      apply(dataset[, metrics], 2, function(x)
        max(x) == min(x))
    constant <- names(constant[constant == TRUE])
    # Remove constant metrics
    if (length(constant) > 0) {
      metrics <- metrics[!metrics %in% constant]
    }
    
    # Check categorical metrics
    category <- sapply(dataset[, metrics], class)
    category <- names(category[category == "character"])
    # Remove categorical metrics from Spearman Analysis
    if (length(category) > 0) {
      metrics <- metrics[!metrics %in% category]
    }
    
    return(metrics)
  }


stepwise.vif <-
  function (dataset,
            metrics,
            vif.threshold = 5,
            verbose = F)
  {
    dataset$dummy <- rnorm(nrow(dataset))
    output <- metrics
    step.count <- 1
    output.results <- list()
    repeat {
      vif.scores <- vif(lm(as.formula(paste0(
        "dummy~", paste0(output,
                         collapse = "+")
      )), data = dataset))
      na.coefficients <- Reduce('|', is.nan(vif.scores))
      if (na.coefficients) {
        stop("NA coefficient in a regression model.")
      }
      output.results[[step.count]] <-
        sort(vif.scores, decreasing = F)
      vif.scores <- vif.scores[vif.scores >= vif.threshold]
      if (length(vif.scores) == 0)
        break
      drop.var <-
        names(vif.scores[vif.scores == max(vif.scores)])[1]
      if (verbose) {
        print(paste0(
          "Step ",
          step.count,
          " - Exclude ",
          drop.var,
          " (VIF = ",
          max(vif.scores),
          ")"
        ))
      }
      step.count <- step.count + 1
      output <- output[!output %in% drop.var]
    }
    names(output.results) <- paste0("Iteration ", 1:step.count)
    names(output.results)[length(output.results)] <- "Final"
    return(output)
  }



AutoSpearman <-
  function(dataset,
           metrics,
           spearman.threshold = 0.7,
           vif.threshold = 5,
           verbose = F) {
    # Remove constant metrics and categorical metrics
    metrics <- remove.constant.categorical(dataset, metrics)
    
    
    spearman.metrics <-
      get.automated.spearman(dataset, metrics, spearman.threshold, verbose)
    AutoSpearman.metrics <-
      stepwise.vif(dataset, spearman.metrics, vif.threshold, verbose)
    
    return(AutoSpearman.metrics)
  }

get_p_code<- function(pvalue){
  if(length(pvalue) == 0)
     return ("$-$")
  
  p_code =""
  if (pvalue <0.001){
    p_code ="$^{***}$"
  }
  else if (pvalue <0.01){ 
    p_code ="$^{**}$"
  }
  else if (pvalue <0.05){
    p_code ="$^{*}$"
  }
  return (p_code)
}

get_OR_code<- function(or_value){
  if(length(or_value) == 0)
    return ("$-$")
  
  or_code =""
  if (or_value >1){
    or_code =paste("\\biasToWomen{",or_value,"}", sep="")
  }
  else or_code =paste("\\biasToMen{",or_value,"}", sep="")
  
  return (or_code)
}


get_impact_code<- function(impact_value){
  if(length(impact_value) == 0)
    return ("$-$")
  
  impact_code =""
  if (impact_value <1){
    impact_code =paste("\\biasToWomen{",impact_value,"}", sep="")
  }
  else impact_code =paste("\\biasToMen{",impact_value,"}", sep="")
  
  return (impact_code)
}

get_z_code<- function(z_value){
  if(length(z_value) == 0)
    return ("$-$")
  
  z_code =""
  if (z_value <0){
    z_code =paste("\\biasToWomen{",z_value,"}", sep="")
  }
  else z_code =paste("\\biasToMen{",z_value,"}", sep="")
  
  return (z_code)
}

get_z_code_review<- function(z_value){
  if(length(z_value) == 0)
    return ("$-$")
  
  z_code =""
  if (z_value >0){
    z_code =paste("\\biasToWomen{",z_value,"}", sep="")
  }
  else z_code =paste("\\biasToMen{",z_value,"}", sep="")
  
  return (z_code)
}

get_GN_code<- function(or_value){
  if((length(or_value) == 0) ||is.na(or_value))
    return ("$-$")
  
  
  or_code =""
  if (or_value >1){
    or_code =paste("\\biasToGendered{",or_value,"}", sep="")
  }
  else or_code =or_value
  
  return (or_code)
}


projects=c("android" ="Android", 
           "chromiumos" ="Chromium OS", 
           "couchbase"="Couchbase", 
           "go" ="Go", 
           "libreoffice" ="LibreOffice",
           "ovirt" ="oVirt", 
           "qt" ="Qt", 
           "typo3" ="Typo3", 
           "whamcloud" ="Whamcloud", 
           "wikimedia"="Wikimedia", 
           "ghtorrent-small"="Github (S)",
           "ghtorrent-medium"="Github (M)",
           "ghtorrent-large"="Github (L)", 
           "ghtorrent-extra-large"="Github (XL)")

#not including Gender, isBugFix, and isGenderNeutral here, as those are required.
dynamic_vars = c('logRevExp', 'logPatchSize', 'logTotalCommit','numPatch',
                 'tenure', 'ratioNew',
                 'fileCount', 'dirCount', 
                 'cyCmplx','cmtVolume')

RQ1_latex_table_code =""

for (project in names(projects)) {
  p_name =projects[project]
  datafile =paste("../dataset/", project, "-dataset1.csv", sep="")
  print(datafile)
  dataset = read.csv(datafile, header = TRUE)
  #dataset$Gender <-factor(dataset$Gender)
 
  dataset$ratioNew= dataset$numNewFiles / dataset$fileCount
  dataset$logReviewInterval=log(dataset$reviewInterval+1)
  dataset$logPatchSize=log(dataset$patchSize+1)
  dataset$logTotalCommit=log(dataset$totalCommit+1)
  dataset$logRevExp=log(dataset$revExp+1)
  survived_vars = AutoSpearman(dataset = dataset, metrics = dynamic_vars,verbose = T)
  print(survived_vars)
  
  formula_string ="isAccepted ~ isBugFix +  isGenderNeutral + Gender"
  formula_string_factored = "isAccepted ~ isBugFix  +NeutralFactor * GenderFactor "
  
  
  for (variable in survived_vars){
    if(project=="qt")
    {
      
      formula_string =paste(formula_string, "+ ", variable,  sep=" ")  
    }  else {
      formula_string =paste(formula_string, "+ rcs(", variable, ",4)" , sep=" ")
      formula_string_factored =paste(formula_string_factored, "+ rcs(", variable, ",4)" , sep=" ")  
    }
    
    
  }
  
  print (formula_string)
  #print (formula_string_factored)
  
  fit_glm_acceptance <- glm(as.formula(formula_string) , data=dataset,  x=T, y=T, 
                            family = binomial)
  
  model_summary =coef(summary(fit_glm_acceptance))
  
  nagelR2 =round(PseudoR2(fit_glm_acceptance,which = "Nagelkerke"),3)
  mcfadden=round(PseudoR2(fit_glm_acceptance,which = "McFadden"),3)
  coxsnell=round(PseudoR2(fit_glm_acceptance,which = "CoxSnell"),3)
  veal=round(PseudoR2(fit_glm_acceptance,which = "VeallZimmermann"),3)
  model_performance =round(with(summary(fit_glm_acceptance), 1 - deviance/null.deviance),3)
  
  model_coefficients <- coef(fit_glm_acceptance)
  
  gender_odds_ratio =round(exp(model_coefficients["Gender"]),3)
  gender_pvalue =round(model_summary[grepl("^Gender$",row.names(model_summary)), 4],4)
  
  
  if (project=="libreoffice" |project =="qt" | project =="wikimedia" |project=="whamcloud")
  {
    RQ1_latex_table_code =paste(RQ1_latex_table_code, p_name, "&", 
                                veal, "&",
                                get_OR_code(gender_odds_ratio), "",
                                get_p_code(gender_pvalue), "& ",
                                "$-$", "& ", "$-$", "& ", "$-$", " &", "$-$", "",
                                #get_p_code(gender_and_neutral_pvalue), 
                                " \\\\ \\hline \n", sep = " ")
    
  } else {
   dataset$GenderFactor <-factor(dataset$Gender, labels=c("M","F"))
   dataset$NeutralFactor <-factor(dataset$isGenderNeutral,  labels=c("N","Y"))

    gender_neutral_odds_ratio = round(exp(model_coefficients["isGenderNeutral"] ),2)
    gender_neutral_pvalue =round(model_summary[grepl("isGenderNeutral$",row.names(model_summary)), 4],4)
  
    print (formula_string_factored)
    
    fit_glm_acceptance2 <- glm(as.formula(formula_string_factored) , data=dataset,  x=T, y=T, 
                              family = binomial)
    
    model_coefficients2 <- coef(fit_glm_acceptance2)
    model_summary2 =coef(summary(fit_glm_acceptance2))
    
    veal2=round(PseudoR2(fit_glm_acceptance2,which = "VeallZimmermann"),3)
    
    print(paste("First", veal, " Second: ", veal2))
    
    WomanGendered =round(exp(model_coefficients2["GenderFactorF"]),2)
    wg_pvalue =round(model_summary2[grepl("^GenderFactorF$",row.names(model_summary2)), 4],4)
    
    ManNeutral =round(exp(model_coefficients2["NeutralFactorY"]),2)
    mn_pvalue =round(model_summary2[grepl("^NeutralFactorY$",row.names(model_summary2)), 4],4)
    
    WomanNeutral =round(exp(model_coefficients2["NeutralFactorY:GenderFactorF"]),2)
    wn_pvalue =round(model_summary2[grepl("^NeutralFactorY:GenderFactorF$",row.names(model_summary2)), 4],4)

    RQ1_latex_table_code =paste(RQ1_latex_table_code, p_name, " & ", 
                                veal, " & ",
                                get_OR_code(gender_odds_ratio), "",
                                get_p_code(gender_pvalue), " & ",
                                get_GN_code(gender_neutral_odds_ratio), "",
                                get_p_code(gender_neutral_pvalue), " & ",
                                WomanGendered, "",
                                get_p_code(wg_pvalue), " & ",
                                ManNeutral, "",
                                get_p_code(mn_pvalue), " & ",
                               WomanNeutral, "",
                                get_p_code(wn_pvalue), " ",
                                
                                #get_p_code(gender_and_neutral_pvalue), 
                                " \\\\ \\hline \n", sep = "")
  
    }
  
}

#This line prints the tabular form
cat(RQ1_latex_table_code)








