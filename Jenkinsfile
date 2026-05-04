pipeline {
    agent any

    environment {
        APP_URL    = "http://65.0.74.194:3000"
        IMAGE_NAME = "shopease-selenium-tests"
        APP_IMAGE  = "shopease-app"
    }

    triggers {
        githubPush()
    }

    stages {

        stage('Checkout Test Repo') {
            steps {
                echo "Checking out Selenium test repo..."
                checkout scm
            }
        }

        stage('Build Test Docker Image') {
            steps {
                echo "Building test Docker image..."
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} ."
            }
        }

        stage('Prepare App Source') {
            steps {
                echo "Cloning application repo..."
                sh """
                    rm -rf shopease
                    git clone https://github.com/salehayasir/shopease.git
                """
            }
        }

        stage('Build App Docker Image') {
            steps {
                echo "Building app image..."
                sh """
                    cd shopease
                    docker build -t ${APP_IMAGE}:${BUILD_NUMBER} .
                """
            }
        }

        stage('Run App Container') {
            steps {
                echo "Starting app container..."
                sh """
                    docker stop shopease-app || true
                    docker rm shopease-app || true
                    docker run -d \
                        -p 3000:3000 \
                        --name shopease-app \
                        ${APP_IMAGE}:${BUILD_NUMBER}
                """
            }
        }

        stage('Wait for App') {
            steps {
                echo "Waiting for app to become ready..."
                sh """
                    for i in \$(seq 1 25); do
                        curl -f http://65.0.74.194:3000 && echo "App is up!" && exit 0
                        echo "Waiting..."
                        sleep 3
                    done
                    echo "App failed to start"
                    exit 1
                """
            }
        }

        stage('Run Selenium Tests') {
            steps {
                echo "Running Selenium tests..."
                sh """
                    rm -rf ${WORKSPACE}/test-results
                    mkdir -p ${WORKSPACE}/test-results
                    docker run --rm \
                        --volumes-from jenkins \
                        -e BASE_URL=${APP_URL} \
                        ${IMAGE_NAME}:${BUILD_NUMBER} \
                        pytest tests/ -v --junit-xml=${WORKSPACE}/test-results/results.xml
                """
            }
        }

        stage('Publish Results') {
            steps {
                echo "Publishing test results..."
                junit allowEmptyResults: false,
                      testResults: 'test-results/results.xml'
            }
        }

        stage('Cleanup') {
            steps {
                sh """
                    docker stop shopease-app || true
                    docker rm shopease-app || true
                    docker rmi ${IMAGE_NAME}:${BUILD_NUMBER} || true
                    docker rmi ${APP_IMAGE}:${BUILD_NUMBER} || true
                """
            }
        }
    }

    post {
        always {
            script {
                def statusColor = currentBuild.result == 'SUCCESS' ? '#16a34a' : '#dc2626'
                def statusEmoji = currentBuild.result == 'SUCCESS' ? '✅' : '❌'
                emailext(
                    subject: "${statusEmoji} ShopEase Tests — ${currentBuild.result} [Build #${BUILD_NUMBER}]",
                    mimeType: 'text/html',
                    to: 'qasimalik@gmail.com',
                    body: """
                        <div style="font-family:Arial;">
                          <h2 style="color:${statusColor};">
                            ${statusEmoji} ShopEase CI/CD Report
                          </h2>
                          <p><b>Build:</b> #${BUILD_NUMBER}</p>
                          <p><b>Status:</b> ${currentBuild.result}</p>
                          <p><b>App:</b> ${APP_URL}</p>
                          <p><b>Duration:</b> ${currentBuild.durationString}</p>
                        </div>
                    """,
                    recipientProviders: [
                        [$class: 'RequesterRecipientProvider']
                    ]
                )
            }
        }
    }
}