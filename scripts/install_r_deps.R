if (!requireNamespace("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager", repos = "https://cloud.r-project.org")
}

BiocManager::install(c("SingleR", "celldex"), update = FALSE, ask = FALSE)

# ScType has no package release; it is sourced directly from its GitHub repo.
# Vendor the two script files it needs into R/sctype/ and source them at call time:
#   source("R/sctype/gene_sets_prepare.R")
#   source("R/sctype/sctype_score_.R")
# See https://github.com/IanevskiAleksandr/sc-type for the current script locations.
