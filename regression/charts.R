
library(dplyr) 

library(gmodels)
library(ggplot2)
library(scales)
library(reshape2)
library(RColorBrewer)
library(beanplot)
library(grid)




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
          "ghtorrent-small"="Github(S)",
           "ghtorrent-medium"="Github(M)",
           "ghtorrent-large"="Github(L)", 
           "ghtorrent-extra-large"="Github(XL)")


# Bean plot for H2


merged_df <- data.frame(matrix(ncol = 4, nrow = 0))

#provide column names
colnames(merged_df) <- c('Gender', 'logReviewInterval', "reviewInterval", 'Project')


for (project in names(projects)) {
  #print(project)
  datafile =paste("../dataset/",project,  "-dataset1.csv", sep="")
  print(datafile)
  dataset = read.csv(datafile, header = TRUE)
  dataset$logReviewInterval=log(dataset$reviewInterval+1)
  
  
  df_filter =dataset[, c("Gender", "logReviewInterval", "reviewInterval")]
  df_filter['Project'] = projects[project]
  
  print(nrow(merged_df))
  merged_df =rbind(merged_df, df_filter)
  
  print(nrow(merged_df))

}



chart_df =merged_df[merged_df$reviewInterval>0.5,]

chart_df =chart_df[chart_df$reviewInterval<8760,]



#Review Interval
par(mar=c(6,4,4,1),ps=9, cex=.99)

bplot<-beanplot(reviewInterval
                ~ Gender*Project, data = chart_df, side='both',las=3, 
                col=list('#311FEC','#E86BDE'), border = "black", 
                cutmin = 0,what=c(0,1,1,0), yaxt='n',  
                ylab="Review interval (log)",cex.lab=1.2,
                overallline="median",beanlines="median",bw="nrd0"	)

#par(xpd=TRUE,ps=12)

axis(2,at=c(1,10,144,720,2160,4320,8760),
     labels =c('1 hr','10 hr','1 wk','1 mo','3 mo','6 mo',  '1 yr'), las=1)


legend('bottom', fill=c('#311FEC','#E86BDE'), cex=0.9,
       legend= c('Male', 'Female'), title = "", inset=c(0,0),
       bty='n', horiz = TRUE)



# bar plot for H3

merged_df_review <- data.frame(matrix(ncol = 3, nrow = 0))

#provide column names
colnames(merged_df_review) <- c('Gender', 'avgReviewPerMonth', 'Project')



for (project in names(projects)) {
  #print(project)
  #project="android"
  datafile =paste(project, "-dataset2.csv", sep="")
  print(datafile)
  dataset_review = read.csv(datafile, header = TRUE)
  dataset_review$avgReviewPerMonth=dataset_review$revExp/dataset_review$tenure
  
  
  df_filter =dataset_review[, c("Gender", "avgReviewPerMonth")]
  df_filter['Project'] = projects[project]
  
  print(nrow(merged_df_review))
  merged_df_review =rbind(merged_df_review, df_filter)
  
  print(nrow(merged_df_review))
  
}



chart_df_review =merged_df_review[merged_df_review$avgReviewPerMonth<100,]

chart_df_review$GenderFactor <-factor(chart_df_review$Gender, labels=c("Men","Women"))

ggplot(data =chart_df_review, aes(x=Project, y=avgReviewPerMonth, fill=GenderFactor)) + 
  geom_boxplot(position=position_dodge(width=0.8),width=0.6) +
  #scale_y_continuous(trans='log10')+
  scale_fill_manual(values = c('#311FDC','#EE6BDE'))+ 
  guides(fill=guide_legend(title="Gender ")) +
  ylab("# of reviews") + xlab("") + 
  theme(axis.text.x = element_text(colour = "black", angle = 30, hjust=1),
        axis.text.y = element_text(colour = "black"),
        #legend.title=element_text("Has negative comments?"),
        legend.direction = "horizontal", legend.position = "top",
        legend.text = element_text(size = 11,face="bold"),
        axis.text=element_text(size=10),
        axis.title=element_text(size=12),
        plot.margin = unit(c(0,0,0,0), "cm")) + ylim(0,75)


acceptance_trend_df <- data.frame( project =c("Android", "Chormium OS", "Couchbase",
                                  "Go", "LibreOffice", "oVirt", "Qt",
                                  "Typo3", "Whamcloud", 
                                  "Android", "Chormium OS", "Couchbase",
                                  "Go", "LibreOffice", "oVirt", "Qt",
                                  "Typo3", "Whamcloud"),
                                perc =c(0.0619,   0.0874,  0.0969,0.059,0.0814,
                                        0.0954,   0.031,    0.0377,  0.0785,
                                        0.133,0.167,  0.117,  0.056, 0.091,
                                        0.116,  0.047,  0.048,  0.082
                                ), year =c(2017,2017,2017,2017,2017,
                                                   2017,2017,2017,2017,
                                                   2022,2022,2022,2022,2022,
                                                   2022,2022,2022,2022)  )



acceptance_trend_df$Year <-factor(acceptance_trend_df$year, labels = c("September 2017", "April 2022"))

ggplot(data =acceptance_trend_df, aes(x=project, y=perc, fill=Year)) + 
  geom_bar(stat="identity", position = "dodge") +
  scale_y_continuous(labels=scales::percent) +
  #scale_fill_manual(values = c('#311FDC','#EE6BDE'))+ 
  guides(fill=guide_legend(title="Year ")) +
  ylab("Ratio of women") + xlab("") + 
  theme(axis.text.x = element_text(colour = "black", angle = 30, hjust=1),
        axis.text.y = element_text(colour = "black"),
        #legend.title=element_text("Has negative comments?"),
        legend.direction = "horizontal", legend.position = "top",
        legend.text = element_text(size = 11,face="bold"),
        axis.text=element_text(size=10),
        axis.title=element_text(size=12),
        plot.margin = unit(c(0,0,0,0), "cm"))
