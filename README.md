# test-data-registry
List, collect and reference good test datasets for tool and workflow testing

This repo is will investigate a meta-data collection of test data. The idea is that we list test-data useful work tool and workflow testing and share them across
communities, e.g. Galaxy, Snakemake or Nextflow.

The idea in a nutshell:

* test data can be stored anywhere, __not__ in this repo
* this is a registry, so we annotate test data here and provide a link to the real data; [example](https://github.com/bgruening/test-data-registry/blob/main/registry/fasta.yaml)
* we need to find a way to create unified identifier for each test dataset, this could be a simple hashtable, created/updated automatically by CI
* the tools that want to use the test data, specifying the unique ID - the hash - this is the weakest point imho, as this is not super transparent for a tool dev (Bjoern hopes that tooling might help here)
* the community can iterate over this github repo and collect the test data to create a backup - simple store with the hash maybe
* tool tests using UUID, will be crawling the hashmap in this repo to find the URI - download test data, run the tests
* a fancy website could be created to search for similar tools, similar datasets to guide users to find cool test data

Notes:

* The Galaxy community could keep all repos as they are and map all test data burried in the repos and git history to this repo. Automatically. Later if we have backups of all those files, we could rewrit our repos and get rid of those test files (if needed).
* This system can work also for huge data and real worklow tests 
