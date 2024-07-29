pipeline {
    agent {
        kubernetes {
            yaml '''
spec:
  hostAliases:
  - ip: 10.100.35.150
    hostnames:
    - jfrog.milvus.io
  containers:
  - name: conan
    image: harbor.milvus.io/milvusdb/conan:1.62.0
    command:
    - cat
    tty: true
'''
        }
    }

    stages {
        stage('add conan remote') {
            steps {
                container('conan') {
                    sh '''
                 conan remote add artifactory https://jfrog.milvus.io/artifactory/api/conan/conan-local
                  '''
                }
            }
        }

        stage('conan user login') {
            steps {
                container('conan') {
                    withCredentials([usernamePassword(credentialsId: 'conan-publisher', usernameVariable: 'CI_CONAN_USERNAME', passwordVariable: 'CI_CONAN_PASSWORD')]) {
                        sh '''
                       conan user -r artifactory ${CI_CONAN_USERNAME} -p ${CI_CONAN_PASSWORD}
                         '''
                    }
                }
            }
        }

        stage('Build') {
            steps {
                container('conan') {
                    echo 'Building..'
                    sh '''
                 python3 build.py
                   '''
                }
            }
        }
        stage('Test') {
            steps {
                echo 'Testing..'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying....'
            }
        }
    }
}
