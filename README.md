# mcd-meetup-api

## NOTE

Avoid using **:latest** tags

## Images

### build the base image
```shell
docker build -t lookup8/mcd-meetup-api-base:latest -f "$(pwd)/api/Dockerfile.build" "$(pwd)/api/"
```

### build the distribution image (also available during pipeline execution)
```shell
docker build -t lookup8/mcd-meetup-api:latest -f "$(pwd)/api/Dockerfile.dist" "$(pwd)/api/"
```

## Pipeline Configuration

Some pipeline parameters can be defined in the *Jenkinsfile.json* file

## Pipeline Library

A separate repository holds the [Libraries](https://github.com/rguareschi/mcd-meetup-api-library.git) required during pipeline execution.

## Pipeline Secrests

**For the sake of simplicity**, pipeline secrets are defined in the *Jenkinsfile.secrets* file. 

**NOTE: we recommend using Hashicorp Vault**
