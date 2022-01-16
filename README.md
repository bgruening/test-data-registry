# test-data-registry
List, collect and reference good test datasets for tool and workflow testing

This repo is will investigate a meta-data collection of test data. The idea is that we list test-data useful work tool and workflow testing and share them across
communities, e.g. Galaxy, Snakemake or Nextflow.

### The idea in a nutshell:

* test data can be stored anywhere, __not__ in this repo
* this is a registry, so we annotate test data here and provide a link to the real data; [example](https://github.com/bgruening/test-data-registry/blob/main/registry/fasta.yaml)
* we need to find a way to create unified identifier for each test dataset, this could be a simple hashtable, created/updated automatically by CI
* the tools that want to use the test data, specifying the UUID - the hash - this is the weakest point imho, as this is not super transparent for a tool dev (Bjoern hopes that tooling might help here)
* the community can iterate over this github repo and collect the test data to create a backup - simple store with the hash maybe
* tool tests using UUID, will be crawling the hashmap in this repo to find the URI - download test data, run the tests
* a fancy website could be created to search for similar tools, similar datasets to guide users to find cool test data

### Notes for Galaxy:

* We keep all tool repos as they are
* We iterate over the repos and the git history and extract all "good" datasets
* The datasets are then added to this registry here (the download URL is the github URL), automatically
* Planemo needs the following updates:
  * Download test data via URL
  * the value in `<param name="inp_ped" value="pedin.21" />` should accept 1) a URI or a data-registry-hash (we can replace `value` by `uri` or `tr_hash` ...)
  * if the test speciefies a tr_hash the hash is resolved to a URI, the URI is passed from planemo to Galaxy
* We can then migrate a few tools to use the new hash-identified, or URI based download of test data
* We can backup the test-data-registry to depot.galaxyproject.org on a regular basis similar to what we do with cargo-port
* If we are happy with this model, we could even pruify our tool repos and remove test data
* Later if we have backups of all those files, we could rewrit our repos and get rid of those test files (if needed).
* This system can work also for huge data and real worklow tests, like IWC. 
