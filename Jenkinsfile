@Library('jenkins-shared-library@v0.6') _

def pod = libraryResource 'io/milvus/pod/tekton.yaml'

pipeline {
    options {
        skipDefaultCheckout true
    }
    agent {
        kubernetes {
            cloud '4am'
            yaml pod
        }
    }
    stages {
        stage('build-and-push') {
            steps {
                container('kubectl') {
                    script {
                        isPr = env.CHANGE_ID != null
                        gitMode = isPr ? 'merge' : 'fetch'
                        gitBaseRef = isPr ? "$env.CHANGE_TARGET" : "$env.BRANCH_NAME"

                        job_name = tekton.buildConanfiles arch: 'amd64',
                                              isPr: isPr,
                                              gitMode: gitMode ,
                                              gitBaseRef: gitBaseRef,
                                              pullRequestNumber: "$env.CHANGE_ID"
                    }
                }

                container('tkn') {
                    script {
                        try {
                            tekton.print_log(job_name)
                        } catch (Exception e) {
                            println e
                        }

                        tekton.check_result(job_name)
                    }
                }
            }
            post {
                // always sure to stop the tekton job
                always {
                    container('tkn') {
                        script {
                          try {
                              tekton.cancel(job_name)
                          } catch (Exception e) {
                          }
                        }
                    }
                }
            }
        }
    }
}

