#!/usr/bin/groovy

@Library('github.com/rguareschi/mcd-meetup-api-library@master')

def chartDir = ''
def commitHash = ''
def containerName = ''
def dryRun = ''
def gitBranch = ''
def imageAppName = ''
def imageRepository = ''
def imageTag = ''
def name = ''
def namespace = ''
def pipelineConfig = ''
def scmConfig = ''
def set = []
def testResult = ''

def pipelineLibrary = new com.lookup8.Pipeline()

/*
    Pipeline
*/
podTemplate(label: 'jenkins-pipeline', containers: [
    containerTemplate(
        name: 'jnlp',
        image: 'jenkinsci/jnlp-slave',
        args: '${computer.jnlpmac} ${computer.name}',
        workingDir: '/home/jenkins'
    ),
    containerTemplate(
        name: 'docker',
        image: 'docker:1.13.1',
        command: 'tail -f /dev/null',
        ttyEnabled: true
    ),
    containerTemplate(
        name: 'helm',
        image: 'lachlanevenson/k8s-helm:v2.8.0',
        command: 'tail -f /dev/null',
        ttyEnabled: true
    ),
    containerTemplate(
        name: 'kubectl',
        image: 'lachlanevenson/k8s-kubectl:v1.10.0',
        command: 'tail -f /dev/null',
        ttyEnabled: true
    )
],
volumes:[
    hostPathVolume(mountPath: '/var/run/docker.sock', hostPath: '/var/run/docker.sock'),
]){

    node ('jenkins-pipeline') {

        /*
            Preparing workspace with source code, sanity checks, setting global properties, creating namespaces if required
        */
        stage('Prepare Workspace') {

            scmConfig = checkout scm
            pipelineConfig = readJSON file:'Jenkinsfile.json'
            pipelineSecrets = readJSON file:'Jenkinsfile.secrets'

            gitBranch = scmConfig.GIT_BRANCH
            commitHash = scmConfig.GIT_COMMIT
    
            namespace = pipelineLibrary.setNamespace(gitBranch)

            if (pipelineConfig.pipeline.sanityChecks) {
                pipelineLibrary.sanityCheck('docker', "docker version") // check if docker is available
                pipelineLibrary.sanityCheck('helm', "helm init --client-only") // check if helm is available
                pipelineLibrary.sanityCheck('kubectl', "kubectl get nodes") // check if kubectl is available and can communicate with the api
            } else {
                println "Skipping Sanity Checks!"
            }
        
        }

        /*
            Building and publishing application container image
        */
        stage('Build Image') {
            container('docker') {
                withCredentials([[ $class: 'UsernamePasswordMultiBinding', credentialsId: 'dockerhub', usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_PASSWORD' ]]) 
                {
                    sh "docker login -u $DOCKERHUB_USERNAME -p $DOCKERHUB_PASSWORD"
                    
                    try {
                        sh "docker build -t ${pipelineConfig.application.imageName}:${commitHash} -f ${WORKSPACE}/api/Dockerfile.dist ${WORKSPACE}/api"                       
                    } catch (e) {
                        println "Build Failed!"
                        currentBuild.result = 'FAILURE'
                        return                        
                    }

                }
            }
        }

        /*
            Running tests against application container
        */
        stage('Test Image') {
            container('docker') {

                try {

                    pipelineLibrary.removeTestContainer('docker', 'mysql')
                    pipelineLibrary.removeTestContainer('docker', 'api')

                    sh """
                        docker run -d \
                            --name mysql \
                            -e MYSQL_ROOT_PASSWORD=weakpassword \
                            -e MYSQL_DATABASE=api \
                            mysql:5.7
                    """

                    sh """
                        docker run -d \
                            --name api \
                            --link=mysql \
                            -e DATABASE_HOST=mysql \
                            -e DATABASE_PORT=3306 \
                            -e DATABASE_USER=root \
                            -e DATABASE_PASS=weakpassword \
                            -e DATABASE_NAME=api \
                            -p 8000:8000 \
                            ${pipelineConfig.application.imageName}:${commitHash}
                    """

                    try {
                        retry(12) {
                    
                            script {
                                testResult = sh ( 
                                    script: "docker exec -i api bash -c 'curl --write-out %{http_code} --silent --output /dev/null http://localhost:8000'", 
                                    returnStdout: true
                                )
                            }

                            if (testResult == "200") {
                            
                                println "Tests Passed!"
                                
                                pipelineLibrary.removeTestContainer('docker', 'mysql')
                                pipelineLibrary.removeTestContainer('docker', 'api')
                            
                            }
                            
                            println "Waiting 5s and retry our test"
                            sleep 5

                        }
                    } catch (e) {
                        println "Tests Failed!"
                        pipelineLibrary.removeTestContainer('docker', 'mysql')
                        pipelineLibrary.removeTestContainer('docker', 'api')
                        currentBuild.result = 'FAILURE'
                        return
                    }
                } catch (e) {
                    pipelineLibrary.removeTestContainer('docker', 'mysql')
                    pipelineLibrary.removeTestContainer('docker', 'api')
                    currentBuild.result = 'FAILURE'
                    return
                }
            }
        }

        /*
            Publish Container Image
        */
        stage ('Publish Image') {
            container('docker') {
                sh "docker tag ${pipelineConfig.application.imageName}:${commitHash} ${pipelineConfig.application.imageRepository}/${pipelineConfig.application.imageName}:${commitHash}"
                sh "docker push ${pipelineConfig.application.imageRepository}/${pipelineConfig.application.imageName}:${commitHash}"
            }
        }

        /*
            Testing Helm Deployment
        */
        stage ('Test Helm Deployment') {
            container('helm') {

                pipelineLibrary.helmLint(pipelineConfig.helm.chartDir)

                pipelineLibrary.helmDeploy(
                    dryRun          : true,
                    name            : "${pipelineConfig.application.name}-${namespace}",
                    namespace       : namespace,
                    chartDir        : pipelineConfig.helm.chartDir,
                    servicePort     : "8000",
                    containerPort   : "8000",
                    set             : [
                        "imageName"     : "${pipelineConfig.application.imageRepository}/${pipelineConfig.application.imageName}",
                        "commitHash"    : commitHash,
                        "replicas"      : pipelineConfig.application.replicas,
                        "cpu"           : pipelineConfig.application.cpu,
                        "memory"        : pipelineConfig.application.memory,
                        "databaseHost"  : pipelineSecrets.develop.databaseHost,
                        "databasePort"  : pipelineSecrets.develop.databasePort,
                        "databaseUser"  : pipelineSecrets.develop.databaseUser,
                        "databasePass"  : pipelineSecrets.develop.databasePass,
                        "databaseName"  : pipelineSecrets.develop.databaseName                        
                    ]
                )
            }
        }

        /*
            Deploy to k8s
        */
        if (gitBranch == "develop") {
            stage ('Deploy to k8s') {
                container('helm') {
                    
                    pipelineLibrary.helmLint(pipelineConfig.helm.chartDir)
                    
                    pipelineLibrary.helmDeploy(
                        dryRun          : false,
                        name            : "${pipelineConfig.application.name}-${namespace}",
                        namespace       : namespace,
                        chartDir        : pipelineConfig.helm.chartDir,
                        set             : [
                            "imageName"     : "${pipelineConfig.application.imageRepository}/${pipelineConfig.application.imageName}",
                            "commitHash"    : commitHash,
                            "replicas"      : pipelineConfig.application.replicas,
                            "cpu"           : pipelineConfig.application.cpu,
                            "memory"        : pipelineConfig.application.memory,
                            "serviceType"   : pipelineConfig.application.serviceType,
                            "servicePort"   : pipelineConfig.application.servicePort,
                            "containerPort" : pipelineConfig.application.containerPort,
                            "databaseHost"  : pipelineSecrets.develop.databaseHost,
                            "databasePort"  : pipelineSecrets.develop.databasePort,
                            "databaseUser"  : pipelineSecrets.develop.databaseUser,
                            "databasePass"  : pipelineSecrets.develop.databasePass,
                            "databaseName"  : pipelineSecrets.develop.databaseName   
                        ]
                    )
                    
                    currentBuild.result = 'SUCCESS'
                }
            }
        } else if (gitBranch =~ "PR-*") {
            stage ('Deploy to k8s') {
                container('helm') {
                    
                    pipelineLibrary.helmLint(pipelineConfig.helm.chartDir)
                    
                    pipelineLibrary.helmDeploy(
                        dryRun          : pipelineConfig.pipeline.pullRequests.dryRun, // set to true so we can skip an actual deployment on k8s
                        name            : "${pipelineConfig.application.name}-${namespace}",
                        namespace       : namespace,
                        chartDir        : pipelineConfig.helm.chartDir,
                        serviceType     : pipelineConfig.application.serviceType,
                        servicePort     : pipelineConfig.application.servicePort,
                        containerPort   : pipelineConfig.application.containerPort,               
                        set             : [
                            "imageName"     : "${pipelineConfig.application.imageRepository}/${pipelineConfig.application.imageName}",
                            "commitHash"    : commitHash,
                            "replicas"      : pipelineConfig.application.replicas,
                            "cpu"           : pipelineConfig.application.cpu,
                            "memory"        : pipelineConfig.application.memory,
                            "serviceType"   : pipelineConfig.application.serviceType,
                            "servicePort"   : pipelineConfig.application.servicePort,
                            "containerPort" : pipelineConfig.application.containerPort,
                            "databaseHost"  : pipelineSecrets.production.databaseHost,
                            "databasePort"  : pipelineSecrets.production.databasePort,
                            "databaseUser"  : pipelineSecrets.production.databaseUser,
                            "databasePass"  : pipelineSecrets.production.databasePass,
                            "databaseName"  : pipelineSecrets.production.databaseName   
                        ]
                    )

                    
                    if (!pipelineConfig.pipeline.pullRequests.dryRun) {
                        // cleanup PRs namespaces
                        pipelineLibrary.helmDelete("${pipelineConfig.application.name}-${namespace}")
                        pipelineLibrary.deleteNamespace(namespace)
                    }

                    currentBuild.result = 'SUCCESS'
                    
                }
            }       
        } else if ( gitBranch == "master" ) {
            stage ('Deploy to k8s') {
                container('helm') {
                    
                    pipelineLibrary.helmLint(pipelineConfig.helm.chartDir)
                    
                    pipelineLibrary.helmDeploy(
                        dryRun          : false,
                        name            : "${pipelineConfig.application.name}-${namespace}",
                        namespace       : namespace,
                        chartDir        : pipelineConfig.helm.chartDir,
                        serviceType     : pipelineConfig.application.serviceType,
                        servicePort     : pipelineConfig.application.servicePort,
                        containerPort   : pipelineConfig.application.containerPort,               
                        set             : [
                            "imageName"     : "${pipelineConfig.application.imageRepository}/${pipelineConfig.application.imageName}",
                            "commitHash"    : commitHash,
                            "replicas"      : pipelineConfig.application.replicas,
                            "cpu"           : pipelineConfig.application.cpu,
                            "memory"        : pipelineConfig.application.memory,
                            "serviceType"   : pipelineConfig.application.serviceType,
                            "servicePort"   : pipelineConfig.application.servicePort,
                            "containerPort" : pipelineConfig.application.containerPort,
                            "databaseHost"  : pipelineSecrets.production.databaseHost,
                            "databasePort"  : pipelineSecrets.production.databasePort,
                            "databaseUser"  : pipelineSecrets.production.databaseUser,
                            "databasePass"  : pipelineSecrets.production.databasePass,
                            "databaseName"  : pipelineSecrets.production.databaseName   
                        ]
                    )
                    
                    currentBuild.result = 'SUCCESS'
                }
            }       
        } else {
            println "No Branch to Deploy!"
            currentBuild.result = 'SUCCESS'
        }
    }
}